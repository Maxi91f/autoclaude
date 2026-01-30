"""Registry of all available performers."""

from pathlib import Path

from .base import BasePerformer, IterationContext
from .cleanup import CleanupPerformer
from .deploy import DeployPerformer
from .task import TaskPerformer
from .ui import UIPerformer

# All available performers (order matters for priority when multiple match)
ALL_PERFORMERS: list[type[BasePerformer]] = [
    DeployPerformer,  # First in final round
    UIPerformer,
    CleanupPerformer,
    TaskPerformer,  # Fallback
]

# Performer instances (lazily initialized)
_instances: dict[str, BasePerformer] = {}

# Track last run iteration per performer
_last_run: dict[str, int] = {}

# Track which special performers ran in the final round (when no tasks remain)
_final_round_ran: set[str] = set()


def _ensure_instances() -> None:
    """Lazily initialize performer instances."""
    if not _instances:
        for performer_cls in ALL_PERFORMERS:
            instance = performer_cls()
            _instances[instance.name] = instance


def get_performer(name: str) -> BasePerformer:
    """Get a performer instance by name."""
    _ensure_instances()
    return _instances[name]


def get_performer_for_context(ctx: IterationContext) -> BasePerformer:
    """Get the appropriate performer for a given context."""
    _ensure_instances()

    for performer in _instances.values():
        if performer.should_run(ctx):
            return performer

    raise ValueError(f"No performer wants to run at iteration {ctx.iteration}")


def record_run(performer_name: str, iteration: int, beans_pending: int) -> None:
    """Record that a performer ran at a given iteration."""
    _last_run[performer_name] = iteration
    if beans_pending == 0:
        _final_round_ran.add(performer_name)


def reset_final_round() -> None:
    """Reset the final round tracking. Call when new tasks appear."""
    _final_round_ran.clear()


def get_last_run() -> dict[str, int]:
    """Get the last run iteration for all performers."""
    return _last_run.copy()


def build_context(
    iteration: int, beans_pending: int, beans_completed: int
) -> IterationContext:
    """Build an IterationContext for the given iteration."""
    if beans_pending > 0:
        reset_final_round()

    return IterationContext(
        iteration=iteration,
        cycle_position=iteration % 7,
        beans_pending=beans_pending,
        beans_completed=beans_completed,
        last_run=get_last_run(),
        final_round_ran=_final_round_ran.copy(),
    )


def should_terminate(ctx: IterationContext) -> bool:
    """Check if the system should terminate."""
    if ctx.beans_pending > 0:
        return False

    _ensure_instances()
    special_performers = [name for name in _instances.keys() if name != "task"]
    return all(name in ctx.final_round_ran for name in special_performers)


def get_all_performers() -> list[BasePerformer]:
    """Get all performer instances."""
    _ensure_instances()
    return list(_instances.values())


def get_performer_names() -> list[str]:
    """Get all available performer names."""
    _ensure_instances()
    return list(_instances.keys())


def build_performer(name: str, whiteboard_path: Path) -> tuple[str, str]:
    """Build a performer by name with its description."""
    performer = get_performer(name)
    return performer.build(whiteboard_path), f"{performer.emoji} {performer.description}"
