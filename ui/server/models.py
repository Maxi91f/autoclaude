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


class TaskPriority(str, Enum):
    """Task priority levels."""

    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"
    DEFERRED = "deferred"


class TaskType(str, Enum):
    """Task types."""

    FEATURE = "feature"
    BUG = "bug"
    TASK = "task"
    EPIC = "epic"
    CHORE = "chore"


class TaskStatus(str, Enum):
    """Task status levels."""

    TODO = "todo"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskInfo(BaseModel):
    """Information about a task from beans."""

    model_config = ConfigDict(strict=False)

    id: str
    title: str
    status: str
    type: str
    priority: str
    body: str | None = None


class TasksResponse(BaseModel):
    """Response for /api/tasks endpoint."""

    model_config = ConfigDict(strict=False)

    tasks: list[TaskInfo]


class WhiteboardResponse(BaseModel):
    """Response for GET /api/whiteboard endpoint."""

    model_config = ConfigDict(strict=False)

    content: str
    last_modified: datetime | None = None


class WhiteboardUpdateRequest(BaseModel):
    """Request body for POST /api/whiteboard endpoint."""

    model_config = ConfigDict(strict=False)

    content: str


class IterationResult(str, Enum):
    """Result of an iteration."""

    SUCCESS = "success"
    NO_PROGRESS = "no_progress"
    ERROR = "error"
    RATE_LIMITED = "rate_limited"
    CANCELLED = "cancelled"


class IterationInfo(BaseModel):
    """Information about a single iteration."""

    model_config = ConfigDict(strict=False)

    id: int
    iteration_number: int
    performer_name: str
    performer_emoji: str
    result: str
    tasks_before: int
    tasks_after: int
    duration_seconds: float
    started_at: datetime
    ended_at: datetime
    error_message: str | None = None


class HistoryResponse(BaseModel):
    """Response for GET /api/history endpoint."""

    model_config = ConfigDict(strict=False)

    iterations: list[IterationInfo]
    total: int
    has_more: bool


class HistoryStatsResponse(BaseModel):
    """Response for GET /api/history/stats endpoint."""

    model_config = ConfigDict(strict=False)

    total: int
    success_count: int
    no_progress_count: int
    error_count: int
    avg_duration_seconds: float


class HistoryPerformersResponse(BaseModel):
    """Response for GET /api/history/performers endpoint."""

    model_config = ConfigDict(strict=False)

    performers: list[str]
