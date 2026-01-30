"""UI review performer for autoclaude."""

from .base import BasePerformer, IterationContext


class UIPerformer(BasePerformer):
    """UI/UX review performer.

    Runs at cycle position 6 (every 7 iterations).
    Reviews the UI for issues but does NOT implement fixes.
    """

    @property
    def emoji(self) -> str:
        return "\U0001f3a8"  # palette

    @property
    def description(self) -> str:
        return "Running UI review iteration..."

    def should_run(self, ctx: IterationContext) -> bool:
        # Run in final round (no tasks left) if not already ran
        if ctx.beans_pending == 0 and self.name not in ctx.final_round_ran:
            return True
        # Run at cycle position 6
        return ctx.cycle_position == 6
