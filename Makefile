.PHONY: setup ingest run smoke chat docker-up docker-down

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

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down

