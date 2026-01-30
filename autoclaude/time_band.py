"""Time band utilities for autoclaude."""

import time
from datetime import datetime


def is_within_allowed_hours(start_hour: int, end_hour: int) -> bool:
    """Check if current time is within allowed hours.

    Handles ranges that cross midnight (e.g., 22-8 means 22:00 to 08:00).
    """
    current_hour = datetime.now().hour
    if start_hour <= end_hour:
        # Simple range (e.g., 9-17)
        return start_hour <= current_hour < end_hour
    else:
        # Range crosses midnight (e.g., 22-8)
        return current_hour >= start_hour or current_hour < end_hour


def wait_for_allowed_hours(start_hour: int, end_hour: int) -> None:
    """Wait until we're within allowed hours, checking every minute."""
    while not is_within_allowed_hours(start_hour, end_hour):
        now = datetime.now()
        print(
            f"\r⏸ Outside allowed hours ({start_hour}:00-{end_hour}:00). "
            f"Current: {now.strftime('%H:%M')}. Waiting...",
            end="",
            flush=True,
        )
        time.sleep(60)
    print()  # Clear the waiting line
