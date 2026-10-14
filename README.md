# BI for Non-Techies

A **multi-agent RAG + Text-to-SQL** assistant so non-technical users at an Indian
omnichannel retailer can ask questions in plain English.

Built as a self-contained portfolio project (LangGraph orchestration, local
Ollama LLM, ChromaDB, SQLite). Sample company details are **generic and fictional**
— no real retailer brands, GSTINs, or customer phones.

## Architecture

```
User Query → Router → [RAG / SQL / General] → Grader → Generator
                ↑                                 │
                └──────── Rewriter (retry) ←──────┘
```

Memory: LangGraph `SqliteSaver` keyed by `thread_id`.

## Tech stack (and why)

| Choice | Why |
|--------|-----|
| **LangGraph** | Explicit multi-node control flow (router, grade, rewrite) you can draw on a whiteboard |
| **Pydantic structured outputs** | Router/grader return typed fields instead of fragile free text |
| **Ollama (local LLM)** | No API key; demos work offline on a laptop |
| **HuggingFace MiniLM embeddings** | Small, local, free |
| **ChromaDB** | Simple persistent vector store for policy docs |
| **SQLite** | Zero-ops analytics DB + checkpoint DB |
| **FastAPI** | Thin HTTP API for `/query` and `/ingest` |
| **Docker Compose** | Reproducible API container; Ollama stays on the host |

## Quick start

```bash
cd bi-for-non-techies
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Local LLM
ollama pull llama3.1
ollama serve   # if not already running

make setup     # builds data/retail.db (deterministic seed)
make ingest    # embeds data/documents into vectordb/
make run       # uvicorn on :8000
```

### Example curls (Indian demos)

```bash
# SQL
curl -s -X POST http://localhost:8000/query \
  -H 'Content-Type: application/json' \
  -d '{"question":"What were total sales in Chennai?"}'

# RAG
curl -s -X POST http://localhost:8000/query \
  -H 'Content-Type: application/json' \
  -d '{"question":"What is the refund timeline for a COD order?"}'

# General
curl -s -X POST http://localhost:8000/query \
  -H 'Content-Type: application/json' \
  -d '{"question":"Hi, what can you do?"}'
```

### Terminal CLI Chat (No API or curls needed)

You can chat directly with the agent in your terminal:

```bash
make chat
# or: python cli.py
```

It runs like a standard terminal agent chat. If the FastAPI/Docker backend is running, it connects over HTTP; otherwise, it falls back to running directly in-process.

Smoke test (API must be running): `make smoke`

### Docker

Ollama must listen on the host (`11434`). Compose maps it via `host.docker.internal`:

```bash
make docker-up
# then: curl the same /query examples on localhost:8000
```

## Project layout

```
bi-for-non-techies/
├── app/                 # FastAPI + settings
├── graph/               # state, nodes, tools, workflow
├── core/                # DB (read-only SQL), embeddings, vectorstore, INR helpers
├── data/
│   ├── documents/       # internal policy Markdown (committed)
│   └── schema.md        # schema text injected into the SQL tool
├── scripts/             # setup_database, ingest_documents, smoke_test
├── docs/                # architecture, build guide, demo questions, troubleshooting
├── Makefile
├── Dockerfile
└── docker-compose.yml
```

Generated (gitignored): `data/retail.db`, `vectordb/`, `checkpoints.db*`.

## SQL safety

The SQL path is **read-only**: statement must be a single `SELECT`/`WITH`, forbidden
keywords (`INSERT`/`UPDATE`/`DELETE`/`DROP`/`ATTACH`/`PRAGMA`/…) are rejected, the
DB opens with SQLite `mode=ro`, and a row `LIMIT` is enforced. Details in
`docs/ARCHITECTURE.md`.

## Known limitation

The router picks **one** route (`rag` *or* `sql` *or* `general`). Mixed questions
like “Is Bengaluru’s return rate within the policy limit?” are **not** answered by
running both tools in one turn — see `docs/DEMO_QUESTIONS.md`.

## Credits

Upstream learning scaffold: [Agentic RAG with LangGraph](https://github.com/)
style multi-agent RAG (router / grader / rewriter) using LangGraph + Ollama.

**What this portfolio version changes / adds:**
- Self-contained project (no dependency on the upstream folder layout)
- Indian retail sample DB (stores, products, customers, orders, inventory, returns)
- Internal policy corpus + curated `schema.md`
- Read-only SQL guards and INR / fiscal-year helpers
- Docker Compose wiring to host Ollama
- Interview-oriented docs (`docs/`) and removal of promotional “talking points”

## More docs

- [Architecture](docs/ARCHITECTURE.md)
- [Build from scratch](docs/BUILD_GUIDE.md)
- [Demo questions](docs/DEMO_QUESTIONS.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
