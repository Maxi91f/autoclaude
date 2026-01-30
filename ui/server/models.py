"""Pydantic models for the UI API."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


class ProcessStatus(str, Enum):
    """Status of the autoclaude process."""

    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    RATE_LIMITED = "rate_limited"


class StatusResponse(BaseModel):
    """Response for /api/status endpoint."""

    model_config = ConfigDict(strict=False)

    running: bool
    paused: bool
    iteration: int | None
    performer: str | None
    performer_emoji: str | None
    beans_pending: int
    beans_completed: int
    no_progress_count: int
    started_at: datetime | None
    rate_limited_until: datetime | None


class StartRequest(BaseModel):
    """Request body for /api/start endpoint."""

    model_config = ConfigDict(strict=False)

    max_iterations: int | None = None
    performer: str | None = None
    start_hour: int = 0
    end_hour: int = 24


class StartResponse(BaseModel):
    """Response for /api/start endpoint."""

    model_config = ConfigDict(strict=False)

    success: bool
    pid: int | None = None
    error: str | None = None


class StopRequest(BaseModel):
    """Request body for /api/stop endpoint."""

    model_config = ConfigDict(strict=False)

    force: bool = False


class SimpleResponse(BaseModel):
    """Simple success/error response."""

    model_config = ConfigDict(strict=False)

    success: bool
    error: str | None = None


class OutputLineType(str, Enum):
    """Type of output line from Claude."""

    TEXT = "text"
    THINKING = "thinking"
    TOOL_USE = "tool_use"
    TOOL_RESULT = "tool_result"
    ERROR = "error"


class WSEvent(str, Enum):
    """WebSocket event types."""

    STATUS_CHANGE = "status_change"
    ITERATION_START = "iteration_start"
    OUTPUT_LINE = "output_line"
    ITERATION_END = "iteration_end"
    TASK_COMPLETED = "task_completed"
    RATE_LIMITED = "rate_limited"
    ERROR = "error"
    PONG = "pong"


class WSMessage(BaseModel):
    """WebSocket message from server to client."""

    model_config = ConfigDict(strict=False)

    event: WSEvent
    data: dict


class WSClientMessage(BaseModel):
    """WebSocket message from client to server."""

    model_config = ConfigDict(strict=False)

    action: str


class PerformerInfo(BaseModel):
    """Information about a performer."""

    model_config = ConfigDict(strict=False)

    name: str
    emoji: str
    description: str


class PerformersResponse(BaseModel):
    """Response for /api/performers endpoint."""

    model_config = ConfigDict(strict=False)

    performers: list[PerformerInfo]
