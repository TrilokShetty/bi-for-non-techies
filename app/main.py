"""FastAPI entrypoint for the multi-agent retail assistant."""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from core.vectorstore import VectorStoreManager
from graph.workflow import run_query, workflow

app = FastAPI(
    title="BI for Non-Techies",
    description=(
        "LangGraph multi-agent assistant: route → RAG/SQL/General → grade → "
        "generate or rewrite. Built for an Indian retail demo dataset."
    ),
    version="1.0.0",
)


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1)
    thread_id: Optional[str] = None


class QueryResponse(BaseModel):
    question: str
    query_type: Optional[str]
    answer: str
    is_relevant: bool
    relevance_score: float
    retries: int
    thread_id: str
    model: Optional[str] = None


class IngestResponse(BaseModel):
    message: str
    chunks: int


@app.get("/")
async def root():
    return {
        "service": "BI for Non-Techies",
        "status": "running",
        "endpoints": ["/query", "/ingest", "/health", "/history/{thread_id}"],
    }


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Run one question through the LangGraph workflow."""
    try:
        thread_id = request.thread_id or str(uuid.uuid4())
        result = run_query(request.question, thread_id)
        return QueryResponse(
            question=result["question"],
            query_type=result["query_type"],
            answer=result["answer"],
            is_relevant=bool(result["is_relevant"]),
            relevance_score=float(result["relevance_score"] or 0.0),
            retries=int(result["retries"] or 0),
            thread_id=thread_id,
            model=result.get("model"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/ingest", response_model=IngestResponse)
async def ingest():
    """Embed documents from data/documents into ChromaDB."""
    try:
        manager = VectorStoreManager()
        chunks = manager.ingest_documents()
        return IngestResponse(message="Documents ingested successfully", chunks=chunks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/history/{thread_id}")
async def get_history(thread_id: str):
    """Return recent checkpointed messages for a thread_id."""
    try:
        config = {"configurable": {"thread_id": thread_id}}
        state = workflow.get_state(config)
        if state.values:
            messages = state.values.get("messages", [])
            return {
                "thread_id": thread_id,
                "message_count": len(messages),
                "messages": [
                    {
                        "role": getattr(m, "type", "unknown"),
                        "content": getattr(m, "content", str(m)),
                    }
                    for m in messages[-10:]
                ],
            }
        return {"thread_id": thread_id, "messages": []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/health")
async def health():
    return {"status": "healthy"}
