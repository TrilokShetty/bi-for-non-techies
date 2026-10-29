"""Compile the LangGraph StateGraph with SQLite checkpointing.

Why SqliteSaver: thread_id lets the API resume conversation state across
requests without a separate Redis/Postgres dependency for a laptop demo.
"""
from __future__ import annotations

import sqlite3
import time

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, StateGraph

from app.config import settings
from core.llm import model_name
from core.run_log import RunLog, format_update
from graph.nodes import (
    general_node,
    generator_node,
    grader_node,
    rag_node,
    rewriter_node,
    router_node,
    sql_node,
)
from graph.state import AgentState


def route_by_type(state: AgentState) -> str:
    """Map router classification to the next node name."""
    return {
        "rag": "rag_node",
        "sql": "sql_node",
        "general": "general_node",
    }.get(state.get("query_type") or "rag", "rag_node")


def route_after_grading(state: AgentState) -> str:
    """Generate if relevant (or out of retries); otherwise rewrite and loop."""
    if state.get("is_relevant"):
        return "generator"
    if state.get("retry_count", 0) < settings.MAX_RETRIES:
        return "rewriter"
    return "generator"


def create_workflow():
    graph = StateGraph(AgentState)

    graph.add_node("router", router_node)
    graph.add_node("rag_node", rag_node)
    graph.add_node("sql_node", sql_node)
    graph.add_node("general_node", general_node)
    graph.add_node("grader", grader_node)
    graph.add_node("rewriter", rewriter_node)
    graph.add_node("generator", generator_node)

    graph.set_entry_point("router")
    graph.add_conditional_edges(
        "router",
        route_by_type,
        {
            "rag_node": "rag_node",
            "sql_node": "sql_node",
            "general_node": "general_node",
        },
    )
    graph.add_edge("rag_node", "grader")
    graph.add_edge("sql_node", "grader")
    graph.add_edge("general_node", END)
    graph.add_conditional_edges(
        "grader",
        route_after_grading,
        {"generator": "generator", "rewriter": "rewriter"},
    )
    graph.add_edge("rewriter", "router")
    graph.add_edge("generator", END)

    settings.CHECKPOINT_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(settings.CHECKPOINT_DB), check_same_thread=False)
    memory = SqliteSaver(conn)
    return graph.compile(checkpointer=memory)


workflow = create_workflow()


def run_query(question: str, thread_id: str = "default") -> dict:
    """Run the graph once, log every node's update, and shape the API response fields."""
    config = {"configurable": {"thread_id": thread_id}}
    initial_state = {
        "messages": [{"role": "user", "content": question}],
        "original_question": question,
        "query_type": None,
        "route_reasoning": None,
        "context": None,
        "is_relevant": False,
        "relevance_score": 0.0,
        "retry_count": 0,
        "final_answer": None,
    }

    # stream() instead of invoke() so each node's decision can be logged as it happens.
    run_log = RunLog(thread_id, question)
    started = last = time.perf_counter()
    try:
        updates = workflow.stream(initial_state, config=config, stream_mode="updates")
        for step, update in enumerate(updates, 1):
            now = time.perf_counter()
            for node, changes in update.items():
                run_log.add(format_update(step, node, changes, now - last))
            last = now
    except Exception as e:
        run_log.add(f"\nERROR: {type(e).__name__}: {e}")
        raise
    finally:
        run_log.add(f"\nTOTAL: {time.perf_counter() - started:.2f}s")
        run_log.save()

    result = workflow.get_state(config).values
    return {
        "question": question,
        "query_type": result.get("query_type"),
        "answer": result.get("final_answer") or "No answer generated",
        "is_relevant": result.get("is_relevant"),
        "relevance_score": result.get("relevance_score"),
        "retries": result.get("retry_count", 0),
        "model": model_name(),
    }
