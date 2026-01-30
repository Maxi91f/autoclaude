"""Base class for autoclaude performers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

# Directory where performer .md files live
PERFORMERS_DIR = Path(__file__).parent


@dataclass
class IterationContext:
    """Context passed to performers to decide if they should run."""

    iteration: int
    cycle_position: int
    beans_pending: int
    beans_completed: int
    last_run: dict[str, int] = field(default_factory=dict)
    final_round_ran: set[str] = field(default_factory=set)

    def iterations_since(self, performer_name: str) -> int | None:
        """Get iterations since a performer last ran, or None if never ran."""
        if performer_name not in self.last_run:
            return None
        return self.iteration - self.last_run[performer_name]


class BasePerformer(ABC):
    """Abstract base class for all autoclaude performers."""

    @property
    @abstractmethod
    def emoji(self) -> str:
        """Emoji icon for this performer type."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Short description shown when running."""
        ...

    @property
    def name(self) -> str:
        """Name of the performer (derived from class name)."""
        return self.__class__.__name__.replace("Performer", "").lower()

    @abstractmethod
    def should_run(self, ctx: IterationContext) -> bool:
        """Determine if this performer should run given the current context."""
        ...

    def build(self, whiteboard_path: Path) -> str:
        """Build the performer content by loading from .md file."""
        md_file = PERFORMERS_DIR / f"{self.name}.md"
        if not md_file.exists():
            raise FileNotFoundError(f"Performer file not found: {md_file}")

        content = md_file.read_text()
        content = content.replace("{whiteboard_path}", str(whiteboard_path))
        return content
