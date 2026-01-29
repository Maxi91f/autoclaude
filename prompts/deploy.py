"""Deploy and test prompt for autoclaude."""

from .base import BasePrompt, IterationContext


class DeployPrompt(BasePrompt):
    """Deploy and production testing prompt.

    Runs at cycle position 5 (every 7 iterations).
    Can also be triggered if many beans completed since last deploy.
    """

    @property
    def emoji(self) -> str:
        return "\U0001f680"  # rocket

    @property
    def description(self) -> str:
        return "Running deploy and test iteration..."

    def should_run(self, ctx: IterationContext) -> bool:
        # Run in final round (no tasks left) if not already ran
        if ctx.beans_pending == 0 and self.name not in ctx.final_round_ran:
            return True
        # Run at cycle position 5
        if ctx.cycle_position == 5:
            return True
        # Also run if 5+ beans completed and it's been at least 4 iterations
        since = ctx.iterations_since(self.name)
        if since is not None and since >= 4 and ctx.beans_completed >= 5:
            return True
        return False
