# Architecture

## State schema (`graph/state.py`)

| Field | Role |
|-------|------|
| `messages` | Chat transcript with `add_messages` reducer (checkpointed) |
| `original_question` | First user question — grader/generator always use this |
| `query_type` | `rag` \| `sql` \| `general` |
| `context` | Retrieved docs or SQL result text |
| `is_relevant` / `relevance_score` | Grader output |
| `retry_count` | Rewrite loop counter (`MAX_RETRIES`, default 2) |
| `final_answer` | User-facing string |

## Nodes

| Node | Responsibility |
|------|----------------|
| **router** | Structured classify → rag/sql/general |
| **rag_node** | Chroma similarity search over policy docs |
| **sql_node** | LLM writes SQL → validated read-only execute |
| **general_node** | Direct LLM reply; skips grader |
| **grader** | Structured relevance score vs **original** question |
| **rewriter** | Clarifies ambiguous asks; appends new HumanMessage |
| **generator** | Final answer; INR / FY hints in prompt |

## Routing & retry

1. Entry → `router`
2. `route_by_type` → rag / sql / general
3. rag & sql → `grader`
4. If relevant → `generator` → END
5. If not relevant and `retry_count < MAX_RETRIES` → `rewriter` → `router` again
6. Else → `generator` anyway (best effort)
7. general → END

Rewrites change the **latest** human message (used for retrieval).  
`original_question` stays fixed so answers address what the user typed.

## Memory & `thread_id`

`SqliteSaver` persists graph state in `checkpoints.db`.  
`POST /query` accepts optional `thread_id` (UUID if omitted).  
`GET /history/{thread_id}` reads the checkpointed `messages`.

## SQL safety

Implemented in `core/database.py`:

- Open with `file:…?mode=ro`
- Reject multiple statements and forbidden keywords
- Require `SELECT` or `WITH … SELECT`
- Append `LIMIT` if missing (`SQL_ROW_LIMIT`)

## Request walkthrough (Indian example)

**Question:** “What were total sales in Chennai last month?”

1. API creates `thread_id`, calls `run_query`.
2. Router → `sql` (needs numbers).
3. SQL tool loads `data/schema.md` + fiscal context, asks Ollama for SQL.
4. Example shape: sum `total_amount_inr` from `v_order_metrics` where `city='Chennai'`, `status='delivered'`, date in prior calendar month.
5. Result rows formatted with `₹` Indian grouping when columns end in `_inr`.
6. Grader checks relevance to the original question.
7. Generator writes a short business answer (e.g. total in ₹ / lakh).

**Policy example:** “What is the refund timeline for a COD order?” → `rag` → chunk from `01_returns_refunds_exchange.md` → grade → generate.
