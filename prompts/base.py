"""Base class for autoclaude prompts."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

# Directory where prompt .md files live
PROMPTS_DIR = Path(__file__).parent


@dataclass
class IterationContext:
    """Context passed to prompts to decide if they should run.

    Attributes:
        iteration: Current iteration number (1-indexed).
        cycle_position: Position in the 7-iteration cycle (iteration % 7).
        beans_pending: Number of beans with status todo/in-progress/draft.
        beans_completed: Number of beans with status completed/scrapped.
        last_run: Dict mapping prompt name to last iteration it ran.
    """

    iteration: int
    cycle_position: int
    beans_pending: int
    beans_completed: int
    last_run: dict[str, int] = field(default_factory=dict)

    def iterations_since(self, prompt_name: str) -> int | None:
        """Get iterations since a prompt last ran, or None if never ran."""
        if prompt_name not in self.last_run:
            return None
        return self.iteration - self.last_run[prompt_name]


class BasePrompt(ABC):
    """Abstract base class for all autoclaude prompts.

    Each prompt defines:
    - should_run(ctx): Whether to run given the current context
    - emoji: Icon shown in logs when running
    - description: Short description for logs
    - build(whiteboard_path): Generate the prompt content
    """

    @property
    @abstractmethod
    def emoji(self) -> str:
        """Emoji icon for this prompt type."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Short description shown when running."""
        ...

    @property
    def name(self) -> str:
        """Name of the prompt (derived from class name)."""
        return self.__class__.__name__.replace("Prompt", "").lower()

    @abstractmethod
    def should_run(self, ctx: IterationContext) -> bool:
        """Determine if this prompt should run given the current context.

        Args:
            ctx: Current iteration context with beans count, history, etc.

        Returns:
            True if this prompt should run.
        """
        ...

    def build(self, whiteboard_path: Path) -> str:
        """Build the prompt content by loading from .md file.

        Loads the prompt from a .md file with the same name as the prompt
        (e.g., TaskPrompt loads from task.md). Replaces {whiteboard_path}
        placeholder with the actual path.

        Args:
            whiteboard_path: Path to the WHITEBOARD.md file.

        Returns:
            The complete prompt string to send to Claude.
        """
        md_file = PROMPTS_DIR / f"{self.name}.md"
        if not md_file.exists():
            raise FileNotFoundError(f"Prompt file not found: {md_file}")

        content = md_file.read_text()
        # Replace placeholders
        content = content.replace("{whiteboard_path}", str(whiteboard_path))
        return content
