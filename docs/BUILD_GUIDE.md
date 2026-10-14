# Build guide (from scratch)

Order matters: config → data → embeddings → tools → state → nodes → workflow → API → Docker.

## 1. Config (`app/config.py`)

**Create:** `Settings` with Ollama URL/model, paths, chunk size, `MAX_RETRIES`, `SQL_ROW_LIMIT`.  
**Why:** one place for env overrides (local vs Docker).  
**Test:** `python -c "from app.config import settings; print(settings.DATABASE_PATH)"`

## 2. Database & seed (`scripts/setup_database.py`)

**Create:** tables for stores, products, customers, orders, order_items, inventory, returns + small view.  
**Why:** Text-to-SQL needs real-looking Indian retail facts; fixed `random.seed(42)` keeps demos reproducible.  
**Test:** `make setup` then open DB and `SELECT COUNT(*) FROM orders;`

## 3. Schema prompt (`data/schema.md`)

**Create:** human-readable schema, FY notes, sample values.  
**Why:** LLMs write better SQL from curated notes than raw `PRAGMA` alone.  
**Test:** print `load_schema_description()` from `core.database`.

## 4. Embeddings & vectorstore (`core/embeddings.py`, `core/vectorstore.py`)

**Create:** HuggingFace embeddings + Chroma persist + ingest for `.md`/`.txt`.  
**Why:** policy questions need semantic retrieval, not SQL.  
**Test:** `make ingest` → non-zero chunk count.

## 5. Formatting helpers (`core/formatting.py`)

**Create:** Indian digit grouping, lakh/crore hints, FY/quarter helpers.  
**Why:** answers and SQL prompts should speak “₹ / FY25-26 / Q1=Apr–Jun”.  
**Test:** `format_inr(1234567) == '₹12,34,567'`

## 6. Safe SQL (`core/database.py`)

**Create:** read-only URI, keyword filter, limit injection, `execute_sql`.  
**Why:** never let the model `DROP` or write.  
**Test:** `execute_sql("DELETE FROM orders")` returns an error; a `SELECT` works.

## 7. Tools (`graph/tools.py`)

**Create:** `search_documents`, `query_database` as LangChain `Tool`s.  
**Why:** nodes stay thin; tools are unit-testable.  
**Test:** call each function with a hard-coded string (Ollama required for SQL).

## 8. State (`graph/state.py`)

**Create:** `AgentState` TypedDict including `original_question`.  
**Why:** LangGraph checkpoints this object per thread.

## 9. Nodes (`graph/nodes.py`)

**Create:** router, rag, sql, general, grader, rewriter, generator with Pydantic structured outputs for router/grader.  
**Why:** each box on the architecture diagram is one function.  
**Test:** invoke router alone on a few questions and print `query_type`.

## 10. Workflow (`graph/workflow.py`)

**Create:** `StateGraph`, conditional edges, SqliteSaver, `run_query`.  
**Why:** wires the loop (rewrite → router).  
**Test:** `run_query("Hi")` returns a `general` answer.

## 11. API (`app/main.py`)

**Create:** `/query`, `/ingest`, `/history/{thread_id}`, `/health`.  
**Why:** interviewers can curl without a UI.  
**Test:** `make run` then `make smoke`.

## 12. Docker

**Create:** `Dockerfile` + `docker-compose.yml` with `host.docker.internal` → host Ollama.  
**Why:** shows you can ship the API separately from the LLM process.  
**Test:** `make docker-up` and hit `/health`.
