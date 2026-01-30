"""Task implementation performer for autoclaude."""

from .base import BasePerformer, IterationContext


class TaskPerformer(BasePerformer):
    """Main task implementation performer.

    Runs when there are pending beans and no special performer is due.
    This is the default/fallback performer.
    """

    @property
    def emoji(self) -> str:
        return "\U0001f527"  # wrench

    @property
    def description(self) -> str:
        return "Running task performer..."

    def should_run(self, ctx: IterationContext) -> bool:
        # Task is the fallback - runs when there's work and no special performer scheduled
        # Special performers run at specific cycle positions
        if ctx.beans_pending == 0:
            return False
        # Don't run if it's time for cleanup (pos 0), deploy (pos 5), or ui (pos 6)
        return ctx.cycle_position not in [0, 5, 6]
