"""Shared LangGraph state.

Why TypedDict + add_messages: LangGraph checkpoints this dict per thread_id.
Keeping original_question separate from rewritten follow-ups avoids the grader
and generator answering the rewrite instead of what the user asked.
"""
from typing import Annotated, Literal, Optional, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    original_question: Optional[str]
    query_type: Optional[Literal["rag", "sql", "general"]]
    route_reasoning: Optional[str]
    context: Optional[str]
    is_relevant: bool
    relevance_score: float
    retry_count: int
    final_answer: Optional[str]
