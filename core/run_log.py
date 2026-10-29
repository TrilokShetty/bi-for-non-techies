"""Per-thread run logs: one file per conversation under logs/<thread_id>.log.

Why a plain text file: the CLI and API only return the final answer, so the
node-by-node decisions (route, SQL, retrieved chunks, grades, rewrites) are
otherwise lost. Appending per thread keeps a whole conversation in one place.
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from app.config import settings


def log_path(thread_id: str) -> Path:
    # thread_id comes from API callers; keep it to a safe file name.
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", thread_id)[:64] or "default"
    return settings.LOGS_DIR / f"{safe}.log"


def format_update(step: int, node: str, changes: dict, elapsed: float) -> str:
    """Render one node's state update as readable text."""
    lines = [f"\n{'=' * 20} STEP {step}: {node} ({elapsed:.2f}s) {'=' * 20}"]
    for key, value in (changes or {}).items():
        if key == "messages":
            for msg in value:
                content = getattr(msg, "content", msg)
                lines.append(f"  message  -> {type(msg).__name__}: {content}")
        else:
            lines.append(f"  {key:<9}-> {value}")
    return "\n".join(lines)


class RunLog:
    """Collects one question's trace, then appends it to the thread's file."""

    def __init__(self, thread_id: str, question: str) -> None:
        self.path = log_path(thread_id)
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.parts = [f"\n{'#' * 64}\n[{stamp}] thread={thread_id}\nQUESTION: {question}"]

    def add(self, text: str) -> None:
        self.parts.append(text)

    def save(self) -> None:
        # Logging must never break answering, so failures are reported, not raised.
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as f:
                f.write("\n".join(self.parts) + "\n")
        except OSError as e:
            print(f"[RunLog] could not write {self.path}: {e}")
