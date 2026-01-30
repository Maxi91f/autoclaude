"""Beans query functions for autoclaude."""

import json
import subprocess

from .paths import get_project_root


def query_beans() -> list[dict]:
    """Query beans with autoclaude tag. Returns list of beans."""
    result = subprocess.run(
        [
            "beans",
            "query",
            "--json",
            '{ beans(filter: { tags: ["autoclaude"] }) { id title status type priority } }',
        ],
        cwd=get_project_root(),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return []
    try:
        data = json.loads(result.stdout)
        return data.get("beans", [])
    except json.JSONDecodeError:
        return []


def count_beans() -> tuple[int, int]:
    """Count done and pending beans with autoclaude tag. Returns (done, pending)."""
    beans = query_beans()
    done = sum(1 for b in beans if b.get("status") in ("completed", "scrapped"))
    pending = sum(
        1 for b in beans if b.get("status") in ("todo", "in-progress", "draft")
    )
    return done, pending
