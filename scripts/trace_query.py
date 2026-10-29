#!/usr/bin/env python3
"""Run one question and print what every node decided, step by step.

Uses the same run_query() as the CLI/API, so the output is exactly what gets
written to logs/<thread_id>.log.

Usage: python scripts/trace_query.py "What were total sales in Chennai last month?"
"""
from __future__ import annotations

import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.run_log import log_path
from graph.workflow import run_query


def main() -> None:
    question = " ".join(sys.argv[1:]) or "What were total sales in Chennai last month?"
    thread_id = f"trace-{uuid.uuid4().hex[:8]}"
    run_query(question, thread_id=thread_id)

    path = log_path(thread_id)
    print(path.read_text(encoding="utf-8"))
    print(f"\nSaved to: {path}")


if __name__ == "__main__":
    main()
