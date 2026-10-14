"""Embedding model factory.

Why HuggingFace local embeddings: no paid API key, works offline next to Ollama,
and all-MiniLM-L6-v2 is small enough for a laptop demo.
"""
from langchain_huggingface import HuggingFaceEmbeddings

from app.config import settings


def get_embeddings() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(
        model_name=settings.EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
