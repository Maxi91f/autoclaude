"""REST API endpoints for the UI."""

import subprocess
from typing import Any

from fastapi import APIRouter

from .models import (
    PerformersResponse,
    SimpleResponse,
    StartRequest,
    StartResponse,
    StatusResponse,
    StopRequest,
    TaskInfo,
    TasksResponse,
)
from .process_manager import get_process_manager
from .websocket import create_output_handler, get_connection_manager

router = APIRouter(prefix="/api")


def _count_beans(status: str) -> int:
    """Count beans with a given status using beans CLI."""
    try:
        result = subprocess.run(
            [
                "beans",
                "query",
                f'{{ beans(filter: {{ tags: ["autoclaude"], status: ["{status}"] }}) {{ id }} }}',
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            import json

            data = json.loads(result.stdout)
            return len(data.get("beans", []))
    except Exception:
        pass
    return 0


@router.get("/status", response_model=StatusResponse)
async def get_status() -> StatusResponse:
    """Get current status of the autoclaude process."""
    pm = get_process_manager()
    state = pm.state

    # Count beans
    beans_pending = _count_beans("todo") + _count_beans("in-progress")
    beans_completed = _count_beans("completed")

    return StatusResponse(
        running=pm.is_running,
        paused=state.status.value == "paused",
        iteration=state.iteration,
        performer=state.performer,
        performer_emoji=state.performer_emoji,
        beans_pending=beans_pending,
        beans_completed=beans_completed,
        no_progress_count=state.no_progress_count,
        started_at=state.started_at,
        rate_limited_until=state.rate_limited_until,
    )


@router.post("/start", response_model=StartResponse)
async def start_process(request: StartRequest) -> StartResponse:
    """Start the autoclaude process."""
    pm = get_process_manager()
    cm = get_connection_manager()

    # Set up output handler to broadcast to websocket clients
    pm.set_output_callback(create_output_handler(cm))

    success, pid, error = await pm.start(
        max_iterations=request.max_iterations,
        performer=request.performer,
        start_hour=request.start_hour,
        end_hour=request.end_hour,
    )

    return StartResponse(success=success, pid=pid, error=error)


@router.post("/stop", response_model=SimpleResponse)
async def stop_process(request: StopRequest) -> SimpleResponse:
    """Stop the autoclaude process."""
    pm = get_process_manager()
    success, error = await pm.stop(force=request.force)
    return SimpleResponse(success=success, error=error)


@router.post("/pause", response_model=SimpleResponse)
async def pause_process() -> SimpleResponse:
    """Pause the autoclaude process."""
    pm = get_process_manager()
    success, error = await pm.pause()
    return SimpleResponse(success=success, error=error)


@router.post("/resume", response_model=SimpleResponse)
async def resume_process() -> SimpleResponse:
    """Resume the autoclaude process."""
    pm = get_process_manager()
    success, error = await pm.resume()
    return SimpleResponse(success=success, error=error)


@router.get("/tasks", response_model=TasksResponse)
async def list_tasks() -> TasksResponse:
    """List tasks from beans CLI."""
    import json

    try:
        result = subprocess.run(
            [
                "beans",
                "query",
                '{ beans(filter: { tags: ["autoclaude"] }) { id title status type priority body } }',
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            tasks = [
                TaskInfo(
                    id=bean["id"],
                    title=bean["title"],
                    status=bean.get("status", "todo"),
                    type=bean.get("type", "task"),
                    priority=bean.get("priority", "normal"),
                    body=bean.get("body"),
                )
                for bean in data.get("beans", [])
            ]
            return TasksResponse(tasks=tasks)
    except Exception as e:
        # Return empty list on error
        pass
    return TasksResponse(tasks=[])


@router.get("/performers", response_model=PerformersResponse)
async def list_performers() -> PerformersResponse:
    """List available performers."""
    try:
        from autoclaude.performers.registry import get_all_performers

        performers = []
        for p in get_all_performers():
            performers.append({
                "name": p.name,
                "emoji": p.emoji,
                "description": p.description,
            })
        return PerformersResponse(performers=performers)
    except ImportError:
        # Fallback if autoclaude module not available
        return PerformersResponse(performers=[
            {"name": "task", "emoji": "📋", "description": "Task performer"},
            {"name": "ui", "emoji": "🎨", "description": "UI performer"},
            {"name": "cleanup", "emoji": "🧹", "description": "Cleanup performer"},
            {"name": "deploy", "emoji": "🚀", "description": "Deploy performer"},
        ])
