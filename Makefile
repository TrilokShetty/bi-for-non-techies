.PHONY: setup ingest run smoke chat trace docker-up docker-down

setup:
	python scripts/setup_database.py

ingest:
	python scripts/ingest_documents.py

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

smoke:
	python scripts/smoke_test.py

chat:
	python cli.py

# usage: make trace Q="What were total sales in Chennai last month?"
trace:
	python scripts/trace_query.py "$(Q)"

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down

