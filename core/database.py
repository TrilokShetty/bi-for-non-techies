"""Read-only SQLite access for Text-to-SQL.

Why read-only + statement filter: the LLM can invent harmful SQL. We never
open a writable connection for queries, and we reject anything that is not a
single SELECT/WITH (CTE) statement.
"""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Any

from app.config import settings

# Keywords that must never appear in user-driven SQL (defense in depth).
_FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|REPLACE|ATTACH|DETACH|"
    r"PRAGMA|VACUUM|REINDEX|TRUNCATE|GRANT|REVOKE|INTO)\b",
    re.IGNORECASE,
)


def _readonly_uri(path: Path) -> str:
    # mode=ro fails if the file does not exist; callers should ensure setup ran.
    return f"file:{path.resolve()}?mode=ro"


def get_connection() -> sqlite3.Connection:
    """Open the retail DB in SQLite read-only mode."""
    conn = sqlite3.connect(_readonly_uri(settings.DATABASE_PATH), uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def load_schema_description() -> str:
    """Prefer the curated schema.md; fall back to PRAGMA introspection."""
    if settings.SCHEMA_PATH.exists():
        return settings.SCHEMA_PATH.read_text(encoding="utf-8")
    return _introspect_schema()


def _introspect_schema() -> str:
    conn = get_connection()
    try:
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
        parts = []
        for (table_name,) in tables:
            cols = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
            col_defs = [f"  {c[1]} {c[2]}" for c in cols]
            parts.append(f"TABLE {table_name}:\n" + "\n".join(col_defs))
        return "\n\n".join(parts)
    finally:
        conn.close()


def validate_select_only(sql: str) -> str | None:
    """Return an error message if SQL is not a safe read query, else None."""
    cleaned = sql.strip().rstrip(";")
    if not cleaned:
        return "Empty SQL."
    if ";" in cleaned:
        return "Multiple statements are not allowed."
    if _FORBIDDEN.search(cleaned):
        return "Only read-only SELECT queries are allowed."
    # Allow WITH ... SELECT and plain SELECT
    if not re.match(r"^(WITH|SELECT)\b", cleaned, re.IGNORECASE):
        return "Query must start with SELECT or WITH."
    return None


def _ensure_limit(sql: str, limit: int) -> str:
    """Append LIMIT if the model forgot — caps result size for the LLM context."""
    if re.search(r"\bLIMIT\b", sql, re.IGNORECASE):
        return sql
    return f"{sql.rstrip().rstrip(';')} LIMIT {limit}"


def execute_sql(sql: str, row_limit: int | None = None) -> dict[str, Any]:
    """Validate, force a row cap, execute read-only, return rows or error."""
    limit = row_limit or settings.SQL_ROW_LIMIT
    err = validate_select_only(sql)
    if err:
        return {"success": False, "error": err}

    safe_sql = _ensure_limit(sql.strip().rstrip(";"), limit)
    try:
        conn = get_connection()
        try:
            cursor = conn.execute(safe_sql)
            rows = cursor.fetchall()
            columns = [d[0] for d in cursor.description] if cursor.description else []
            data = [dict(row) for row in rows]
            return {
                "success": True,
                "sql": safe_sql,
                "columns": columns,
                "data": data,
                "row_count": len(data),
            }
        finally:
            conn.close()
    except Exception as e:
        return {"success": False, "error": str(e), "sql": safe_sql}
