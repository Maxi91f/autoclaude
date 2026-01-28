"""Registry of all available prompts."""

from pathlib import Path

from .base import BasePrompt, IterationContext
from .cleanup import CleanupPrompt
from .deploy import DeployPrompt
from .task import TaskPrompt
from .ui import UIPrompt

# All available prompts (order matters for priority when multiple match)
ALL_PROMPTS: list[type[BasePrompt]] = [
    CleanupPrompt,  # Highest priority special prompt
    DeployPrompt,
    UIPrompt,
    TaskPrompt,  # Fallback
]

# Prompt instances (lazily initialized)
_instances: dict[str, BasePrompt] = {}

# Track last run iteration per prompt
_last_run: dict[str, int] = {}


def _ensure_instances() -> None:
    """Lazily initialize prompt instances."""
    if not _instances:
        for prompt_cls in ALL_PROMPTS:
            instance = prompt_cls()
            _instances[instance.name] = instance


def get_prompt(name: str) -> BasePrompt:
    """Get a prompt instance by name.

    Args:
        name: The prompt name (e.g., "task", "cleanup", "deploy", "ui").

    Returns:
        The prompt instance.

    Raises:
        KeyError: If no prompt with that name exists.
    """
    _ensure_instances()
    return _instances[name]


def get_prompt_for_context(ctx: IterationContext) -> BasePrompt:
    """Get the appropriate prompt for a given context.

    Checks prompts in priority order and returns the first one that
    should run. Task prompt is the fallback.

    Args:
        ctx: The current iteration context.

    Returns:
        The prompt that should run.

    Raises:
        ValueError: If no prompt wants to run (shouldn't happen with TaskPrompt as fallback).
    """
    _ensure_instances()

    # Check prompts in priority order
    for prompt in _instances.values():
        if prompt.should_run(ctx):
            return prompt

    raise ValueError(f"No prompt wants to run at iteration {ctx.iteration}")


def record_run(prompt_name: str, iteration: int) -> None:
    """Record that a prompt ran at a given iteration.

    Args:
        prompt_name: The prompt that ran.
        iteration: The iteration number.
    """
    _last_run[prompt_name] = iteration


def get_last_run() -> dict[str, int]:
    """Get the last run iteration for all prompts.

    Returns:
        Dict mapping prompt name to last iteration it ran.
    """
    return _last_run.copy()


def build_context(
    iteration: int, beans_pending: int, beans_completed: int
) -> IterationContext:
    """Build an IterationContext for the given iteration.

    Args:
        iteration: Current iteration number (1-indexed).
        beans_pending: Number of pending beans.
        beans_completed: Number of completed beans.

    Returns:
        An IterationContext with all the info prompts need.
    """
    return IterationContext(
        iteration=iteration,
        cycle_position=iteration % 7,
        beans_pending=beans_pending,
        beans_completed=beans_completed,
        last_run=get_last_run(),
    )


def get_all_prompts() -> list[BasePrompt]:
    """Get all prompt instances.

    Returns:
        List of all prompt instances.
    """
    _ensure_instances()
    return list(_instances.values())


def get_prompt_names() -> list[str]:
    """Get all available prompt names.

    Returns:
        List of prompt names (e.g., ["task", "cleanup", "deploy", "ui"]).
    """
    _ensure_instances()
    return list(_instances.keys())


def build_prompt(name: str, whiteboard_path: Path) -> tuple[str, str]:
    """Build a prompt by name with its description.

    Args:
        name: The prompt name.
        whiteboard_path: Path to the WHITEBOARD.md file.

    Returns:
        Tuple of (prompt_content, display_description_with_emoji).
    """
    prompt = get_prompt(name)
    return prompt.build(whiteboard_path), f"{prompt.emoji} {prompt.description}"
