"""UI review prompt for autoclaude."""

from .base import BasePrompt, IterationContext


class UIPrompt(BasePrompt):
    """UI/UX review prompt.

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
        # Run at cycle position 6
        return ctx.cycle_position == 6
