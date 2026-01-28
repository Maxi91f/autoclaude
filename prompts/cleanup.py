"""Cleanup/verification prompt for autoclaude."""

from .base import BasePrompt, IterationContext


class CleanupPrompt(BasePrompt):
    """Cleanup and verification prompt.

    Runs every 7th iteration (position 0) to verify task statuses.
    Also runs if it's been 10+ iterations since last cleanup.
    """

    @property
    def emoji(self) -> str:
        return "\U0001f9f9"  # broom

    @property
    def description(self) -> str:
        return "Running cleanup/verification iteration..."

    def should_run(self, ctx: IterationContext) -> bool:
        # Run at cycle position 0 (every 7th iteration)
        if ctx.cycle_position == 0 and ctx.iteration > 0:
            return True
        # Also run if it's been too long since last cleanup
        since = ctx.iterations_since(self.name)
        if since is not None and since >= 10:
            return True
        return False
