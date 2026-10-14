#!/usr/bin/env python3
"""Hit /query with one question per route and check answer + thread_id."""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"

CASES = [
    ("sql", "What were total delivered sales in Chennai?"),
    ("rag", "What is the refund timeline for a COD order?"),
    ("general", "Hello, what can you help me with?"),
]


def post_query(question: str) -> dict:
    data = json.dumps({"question": question}).encode()
    req = urllib.request.Request(
        f"{BASE}/query",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        return json.loads(resp.read().decode())


def main() -> int:
    # Health first
    try:
        with urllib.request.urlopen(f"{BASE}/health", timeout=10) as resp:
            health = json.loads(resp.read().decode())
    except Exception as e:
        print(f"FAIL health: {e}")
        return 1
    print(f"health: {health}")

    failed = 0
    for expected_route, question in CASES:
        print(f"\n=== {expected_route}: {question}")
        try:
            body = post_query(question)
        except urllib.error.URLError as e:
            print(f"FAIL request: {e}")
            failed += 1
            continue

        ok = True
        if not body.get("thread_id"):
            print("FAIL missing thread_id")
            ok = False
        answer = body.get("answer") or ""
        if len(answer.strip()) < 5:
            print("FAIL empty/short answer")
            ok = False
        print(
            f"query_type={body.get('query_type')} retries={body.get('retries')} "
            f"relevant={body.get('is_relevant')} score={body.get('relevance_score')}"
        )
        print(f"answer[:240]={answer[:240]!r}")
        # Soft check: route may differ with small models
        if body.get("query_type") and body.get("query_type") != expected_route:
            print(
                f"NOTE: expected route {expected_route}, got {body.get('query_type')} "
                "(allowed for small local models)"
            )
        if ok:
            print("PASS")
        else:
            failed += 1

    print(f"\nSummary: {len(CASES) - failed}/{len(CASES)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
