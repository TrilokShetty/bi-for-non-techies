"""LangGraph node functions.

Each node does one job and returns a partial state update. Structured outputs
(Pydantic) keep the router and grader from returning free-form text we would
have to parse with regex.
"""
from __future__ import annotations

from typing import Any, Dict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field

from app.config import settings
from core.formatting import fiscal_context_for_prompt, inr_in_words_hint
from graph.state import AgentState
from graph.tools import tool_rag, tool_sql

llm = ChatOllama(
    model=settings.OLLAMA_MODEL,
    base_url=settings.OLLAMA_BASE_URL,
    temperature=0,
)


class RouterOutput(BaseModel):
    """Forced shape for routing decisions."""

    query_type: str = Field(description="One of: rag, sql, general")
    reasoning: str = Field(description="Why this route was chosen")


class GraderOutput(BaseModel):
    """Forced shape for relevance grading."""

    is_relevant: bool = Field(description="Whether the context can answer the question")
    score: float = Field(description="Relevance score from 0.0 to 1.0")
    feedback: str = Field(description="Short explanation")


router_llm = llm.with_structured_output(RouterOutput)
grader_llm = llm.with_structured_output(GraderOutput)


def _latest_human(state: AgentState) -> str:
    """Most recent human message — used after rewrites for retrieval."""
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage) or getattr(msg, "type", None) == "human":
            return msg.content if hasattr(msg, "content") else str(msg)
    return state.get("original_question") or ""


def _original_question(state: AgentState) -> str:
    return state.get("original_question") or _latest_human(state)


def router_node(state: AgentState) -> Dict[str, Any]:
    """Classify the (possibly rewritten) question into rag / sql / general."""
    question = _latest_human(state)
    updates: Dict[str, Any] = {}
    # Persist the first user question once so grading/generation stay on-intent.
    if not state.get("original_question"):
        updates["original_question"] = question

    system = """You are a query router for an Indian retail business assistant.
Classify the question into exactly one of:
- "sql": needs numbers from the database (sales, inventory, returns, rankings, AOV, COD rates)
- "rag": needs policies, SOPs, GST handbook, refund timelines, KPI definitions, grievance matrix
- "general": greetings, capability questions, or clearly out-of-scope topics

If the question mixes policy + numbers, pick the dominant intent (usually sql for
metrics, rag for "what does policy say"). Do not invent a mixed route."""

    result = router_llm.invoke(
        [SystemMessage(content=system), HumanMessage(content=f"Classify: {question}")]
    )
    print(f"[Router] {result.query_type} — {result.reasoning}")
    updates.update(
        {
            "query_type": result.query_type,
            "messages": [AIMessage(content=f"Routing to: {result.query_type}")],
        }
    )
    return updates


def rag_node(state: AgentState) -> Dict[str, Any]:
    """Retrieve policy chunks via embeddings / Chroma."""
    question = _latest_human(state)
    context = tool_rag.invoke(question)
    print(f"[RAG] context chars={len(context)}")
    return {
        "context": context,
        "messages": [AIMessage(content="Retrieved policy documents.")],
    }


def sql_node(state: AgentState) -> Dict[str, Any]:
    """Generate and run a read-only SQL query."""
    question = _latest_human(state)
    context = tool_sql.invoke(question)
    print(f"[SQL] context chars={len(context)}")
    return {
        "context": context,
        "messages": [AIMessage(content="Ran a database query.")],
    }


def general_node(state: AgentState) -> Dict[str, Any]:
    """Answer without retrieval — greetings, capabilities, soft refusals."""
    question = _original_question(state)
    prompt = f"""You are a helpful assistant for non-technical users at an Indian
omnichannel retail company. You can explain store/sales/inventory questions
(via SQL) and internal policy questions (via documents).

Respond briefly to: {question}

If the topic is outside retail ops / this demo, say so politely and suggest
asking about sales, inventory, returns, or company policies."""
    response = llm.invoke(prompt)
    return {
        "context": "",
        "final_answer": response.content,
        "is_relevant": True,
        "relevance_score": 1.0,
        "messages": [AIMessage(content=response.content)],
    }


def grader_node(state: AgentState) -> Dict[str, Any]:
    """Score whether retrieved context is enough to answer the original question."""
    question = _original_question(state)
    context = state.get("context") or ""
    if not context:
        return {
            "is_relevant": False,
            "relevance_score": 0.0,
            "messages": [AIMessage(content="No context to grade")],
        }

    system = (
        "You grade whether CONTEXT contains enough information to answer QUESTION. "
        "Score 0.0–1.0; mark relevant if score >= 0.6. Be strict about missing numbers."
    )
    result = grader_llm.invoke(
        [
            SystemMessage(content=system),
            HumanMessage(
                content=f"QUESTION: {question}\n\nCONTEXT:\n{context[:2500]}\n\nGrade."
            ),
        ]
    )
    print(f"[Grader] relevant={result.is_relevant} score={result.score}")
    return {
        "is_relevant": result.is_relevant,
        "relevance_score": result.score,
        "messages": [AIMessage(content=f"Grader: {result.feedback}")],
    }


def rewriter_node(state: AgentState) -> Dict[str, Any]:
    """Rewrite an ambiguous question so the next retrieval pass is sharper."""
    question = _original_question(state)
    retry = state.get("retry_count", 0)
    prompt = f"""The previous retrieval/query was not relevant enough.

Original user question: {question}
Route so far: {state.get('query_type')}

Rewrite the question to be more specific for an Indian retail analytics /
policy assistant. Expand vague phrases like "the south", "festive numbers",
or "how are we doing" into concrete metrics, regions (North/South/East/West),
cities, or policy document topics. Keep it as ONE question.
Return only the rewritten question."""
    rewritten = llm.invoke(prompt).content.strip()
    print(f"[Rewriter] retry={retry + 1}: {rewritten}")
    return {
        "retry_count": retry + 1,
        # New HumanMessage becomes the retrieval target; original_question stays put.
        "messages": [HumanMessage(content=rewritten)],
    }


def generator_node(state: AgentState) -> Dict[str, Any]:
    """Write the final user-facing answer from context + original question."""
    question = _original_question(state)
    context = state.get("context") or "No context available."
    fiscal = fiscal_context_for_prompt()

    prompt = f"""Answer for a non-technical business user in clear English.
Use Indian Rupee formatting in words when helpful (example style: {inr_in_words_hint(1234567)}).
{fiscal}

Context:
{context}

Question: {question}

Rules:
- Stick to the context; if data is missing, say what is missing.
- Mention the SQL or document source briefly when useful.
- Do not invent store brands or legal citations beyond the documents."""

    answer = llm.invoke(prompt).content
    print("[Generator] answer ready")
    return {
        "final_answer": answer,
        "messages": [AIMessage(content=answer)],
    }
