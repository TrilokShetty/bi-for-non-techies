#!/usr/bin/env python3
"""Embed policy documents into ChromaDB. Run from project root."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from core.vectorstore import VectorStoreManager


def main() -> None:
    print(f"Ingesting from: {settings.DOCUMENTS_DIR}")
    manager = VectorStoreManager()
    chunks = manager.ingest_documents()
    print(f"Ingested {chunks} new chunks")
    print(f"Total ids in collection: {manager.chunk_count()}")
    print(f"Persisted at: {settings.VECTORDB_PATH}")


if __name__ == "__main__":
    main()
