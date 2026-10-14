"""Retrieval tools used by graph nodes.

These are plain callables wrapped as LangChain Tools for clarity. The graph
does NOT use ToolNode / tool-calling agents — the router picks a node, and that
node calls one tool. That keeps the control flow explicit for interviews.
"""
from langchain_core.tools import Tool
from langchain_ollama import ChatOllama

from app.config import settings
from core.database import execute_sql, load_schema_description
from core.formatting import fiscal_context_for_prompt, format_sql_rows
from core.vectorstore import VectorStoreManager

vectorstore_manager = VectorStoreManager()
llm = ChatOllama(
    model=settings.OLLAMA_MODEL,
    base_url=settings.OLLAMA_BASE_URL,
    temperature=0,
)


def search_documents(query: str) -> str:
    """Semantic search over internal policy / guideline documents."""
    docs = vectorstore_manager.search(query)
    if not docs:
        return "No relevant documents found."

    parts = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "unknown")
        parts.append(f"[Source {i}: {source}]\n{doc.page_content}")
    return "\n\n---\n\n".join(parts)


tool_rag = Tool(
    name="search_documents",
    func=search_documents,
    description=(
        "Search internal retail policies, SOPs, and guidelines. "
        "Use for procedures, refunds, GST handbook questions, KPI definitions."
    ),
)


def query_database(question: str) -> str:
    """Text-to-SQL against the sample retail SQLite DB (SELECT-only, read-only)."""
    schema = load_schema_description()
    fiscal = fiscal_context_for_prompt()

    prompt = f"""You are a SQLite expert for an Indian omnichannel retail chain.

Schema and notes:
{schema}

{fiscal}

Write ONE SQLite query to answer: {question}

Rules:
- Only a single SELECT (or WITH ... SELECT). No writes, no PRAGMA, no ATTACH.
- Prefer columns ending in _inr for money; never invent currencies.
- Limit to at most {settings.SQL_ROW_LIMIT} rows unless the question asks for a single aggregate.
- Return ONLY the SQL, no markdown fences, no commentary.
"""

    response = llm.invoke(prompt)
    sql = response.content.strip().replace("```sql", "").replace("```", "").strip()

    result = execute_sql(sql)
    if result["success"]:
        preview = format_sql_rows(result["columns"], result["data"][: settings.SQL_ROW_LIMIT])
        return (
            f"SQL: {result['sql']}\n\n"
            f"Results ({result['row_count']} rows):\n{preview}"
        )
    return f"SQL Error: {result.get('error')}\nAttempted SQL: {result.get('sql', sql)}"


tool_sql = Tool(
    name="query_database",
    func=query_database,
    description=(
        "Query the retail SQLite database for sales, inventory, returns, "
        "customers, and store metrics. Use when exact numbers are required."
    ),
)
