"""JSON event emitter for structured UI communication."""

import json
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Literal


EventType = Literal[
    "iteration_start",
    "iteration_end",
    "output",
    "paused",
    "resumed",
    "rate_limited",
    "error",
    "completed",
    "terminated",
]


@dataclass
class Event:
    """Base event structure."""

    event: EventType
    timestamp: str

    def __init__(self, event: EventType):
        self.event = event
        self.timestamp = datetime.now().isoformat()


def _emit(data: dict) -> None:
    """Emit a JSON event to stdout."""
    print(json.dumps(data), flush=True)


def emit_iteration_start(
    iteration: int,
    performer: str,
    emoji: str,
    tasks_done: int,
    tasks_pending: int,
    max_iterations: int,
) -> None:
    """Emit iteration start event."""
    _emit({
        "event": "iteration_start",
        "timestamp": datetime.now().isoformat(),
        "iteration": iteration,
        "performer": performer,
        "emoji": emoji,
        "tasks_done": tasks_done,
        "tasks_pending": tasks_pending,
        "max_iterations": max_iterations,
    })


def emit_iteration_end(
    iteration: int,
    result: Literal["success", "no_progress", "error", "rate_limited"],
    tasks_done: int,
    tasks_pending: int,
    no_progress_count: int,
    error_message: str | None = None,
) -> None:
    """Emit iteration end event."""
    data = {
        "event": "iteration_end",
        "timestamp": datetime.now().isoformat(),
        "iteration": iteration,
        "result": result,
        "tasks_done": tasks_done,
        "tasks_pending": tasks_pending,
        "no_progress_count": no_progress_count,
    }
    if error_message:
        data["error_message"] = error_message
    _emit(data)


def emit_output(
    output_type: Literal["thinking", "tool_use", "tool_result", "text", "info"],
    content: str,
) -> None:
    """Emit output event."""
    _emit({
        "event": "output",
        "timestamp": datetime.now().isoformat(),
        "type": output_type,
        "content": content,
    })


def emit_paused(after_iteration: int) -> None:
    """Emit paused event."""
    _emit({
        "event": "paused",
        "timestamp": datetime.now().isoformat(),
        "after_iteration": after_iteration,
    })


def emit_resumed() -> None:
    """Emit resumed event."""
    _emit({
        "event": "resumed",
        "timestamp": datetime.now().isoformat(),
    })


def emit_rate_limited(reset_time: str | None = None) -> None:
    """Emit rate limited event."""
    data = {
        "event": "rate_limited",
        "timestamp": datetime.now().isoformat(),
    }
    if reset_time:
        data["reset_time"] = reset_time
    _emit(data)


def emit_error(message: str, code: int | None = None) -> None:
    """Emit error event."""
    data = {
        "event": "error",
        "timestamp": datetime.now().isoformat(),
        "message": message,
    }
    if code is not None:
        data["code"] = code
    _emit(data)


def emit_completed(
    reason: Literal["all_tasks_done", "max_iterations", "no_progress", "outside_hours"],
    total_iterations: int,
    tasks_done: int,
    tasks_pending: int,
) -> None:
    """Emit completion event."""
    _emit({
        "event": "completed",
        "timestamp": datetime.now().isoformat(),
        "reason": reason,
        "total_iterations": total_iterations,
        "tasks_done": tasks_done,
        "tasks_pending": tasks_pending,
    })


def emit_terminated(by_user: bool, after_iteration: int) -> None:
    """Emit terminated event."""
    _emit({
        "event": "terminated",
        "timestamp": datetime.now().isoformat(),
        "by_user": by_user,
        "after_iteration": after_iteration,
    })
