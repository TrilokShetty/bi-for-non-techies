# Troubleshooting

## Ollama not running

Symptoms: connection errors to `localhost:11434`, `/query` 500s.  
Fix: install Ollama, run `ollama serve`, confirm `curl http://localhost:11434/api/tags`.

## Model not pulled

Symptoms: model not found.  
Fix: `ollama pull llama3.1` (or set `OLLAMA_MODEL` in `.env` to a model you have).

## Chroma / vectordb path

Symptoms: RAG returns “No relevant documents”, or ingest errors.  
Fix: run `make ingest` from the project root; ensure `data/documents` has `.md`/`.txt`.  
Delete `vectordb/` and re-ingest if the collection looks corrupt. Path is
`PROJECT_ROOT/vectordb` from `app/config.py`.

## SQLite locking / WAL

Symptoms: `database is locked` on checkpoints or retail DB.  
Fix: only one API process should own `checkpoints.db`. Stop duplicate uvicorn
workers. Retail queries use **read-only** mode and should not write WAL for
analytics. Delete orphan `checkpoints.db-shm` / `-wal` if the main DB was removed.

## Docker networking to Ollama

Compose sets `OLLAMA_BASE_URL=http://host.docker.internal:11434` and
`extra_hosts: host.docker.internal:host-gateway` for Linux Engine.  
If it still fails on WSL2: ensure Ollama listens on `0.0.0.0:11434` (not only
loopback), and that Windows firewall allows the port.

## WSL-specific

- Prefer running the API **inside WSL** against Ollama installed in WSL, or
  Docker Desktop’s WSL backend consistently — mixing paths gets confusing.
- `*:Zone.Identifier` files appear after Windows downloads; they are gitignored
  and safe to delete (`find . -name '*Zone.Identifier' -delete`).
- Line endings: keep scripts LF; if bash complains about `\r`, run `sed -i 's/\r$//'`.

## SQL tool rejects query

Intentional if the model emits `INSERT`/`PRAGMA`/multiple statements. Check API
logs for `SQL Error:` and inspect the attempted SQL in the tool output.

## Imports fail (`ModuleNotFoundError: app`)

Always run from project root (`bi-for-non-techies/`) with the venv active so
`app`, `core`, and `graph` resolve as top-level packages.
