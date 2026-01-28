"""Task implementation prompt for autoclaude."""

from .base import BasePrompt, IterationContext


class TaskPrompt(BasePrompt):
    """Main task implementation prompt.

    Runs when there are pending beans and no special prompt is due.
    This is the default/fallback prompt.
    """

    @property
    def emoji(self) -> str:
        return "\U0001f527"  # wrench

    @property
    def description(self) -> str:
        return "Running task prompt..."

    def should_run(self, ctx: IterationContext) -> bool:
        # Task is the fallback - runs when there's work and no special prompt scheduled
        # Special prompts run at specific cycle positions
        if ctx.beans_pending == 0:
            return False
        # Don't run if it's time for cleanup (pos 0), deploy (pos 5), or ui (pos 6)
        return ctx.cycle_position not in [0, 5, 6]
