#!/usr/bin/env python3
"""
Simple Terminal CLI for BI for Non-Techies (Retail Assistant).

Connects to the FastAPI backend (http://127.0.0.1:8000) or runs in-process
if the API server is not active.
"""
from __future__ import annotations

import json
import sys
import uuid
import urllib.error
import urllib.request
from pathlib import Path

# Add project root to sys.path for direct in-process fallback
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

API_URL = "http://127.0.0.1:8000"


def check_api_server() -> bool:
    """Check if the FastAPI backend is running."""
    try:
        req = urllib.request.Request(f"{API_URL}/health", method="GET")
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            return resp.status == 200
    except Exception:
        return False


def query_api(question: str, thread_id: str) -> dict:
    """Send question to the running FastAPI server."""
    payload = json.dumps({"question": question, "thread_id": thread_id}).encode("utf-8")
    req = urllib.request.Request(
        f"{API_URL}/query",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        return json.loads(resp.read().decode("utf-8"))


def query_in_process(question: str, thread_id: str) -> dict:
    """Direct in-process execution fallback."""
    from graph.workflow import run_query

    result = run_query(question, thread_id=thread_id)
    result["thread_id"] = thread_id
    return result


def main():
    thread_id = str(uuid.uuid4())[:8]

    print("=" * 64)
    print("           Retail Business Intelligence (CLI)")
    print("=" * 64)
    print("Ask retail questions in plain English (Sales, Inventory, Policies).")
    print("Commands: 'exit' or 'quit' to close, 'new' to start a new thread.\n")

    is_api_running = check_api_server()
    mode = "Docker / FastAPI Backend" if is_api_running else "Local In-Process Engine"
    print(f"Mode       : {mode}")
    print(f"Session ID : {thread_id}")
    print(f"Log file   : logs/{thread_id}.log")
    print("-" * 64)

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nSession ended. Goodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit", "q"):
            print("\nSession ended. Goodbye!")
            break

        if user_input.lower() == "new":
            thread_id = str(uuid.uuid4())[:8]
            print(f"\n[New conversation started. Session ID: {thread_id}, log: logs/{thread_id}.log]")
            continue

        print("\nThinking...")

        try:
            if is_api_running:
                res = query_api(user_input, thread_id)
            else:
                res = query_in_process(user_input, thread_id)

            route = (res.get("query_type") or "unknown").upper()
            answer = res.get("answer") or "No response generated."
            retries = res.get("retries", 0)
            model_used = res.get("model") or "unknown"

            retry_note = f" (Retries: {retries})" if retries > 0 else ""

            print(f"\nAssistant [{route}] [Model: {model_used}]{retry_note}:")
            print(f"{answer}")

        except Exception as err:
            print(f"\nError processing query: {err}")
            print("Tip: Ensure Ollama is running ('ollama serve') and accessible.")


if __name__ == "__main__":
    main()

