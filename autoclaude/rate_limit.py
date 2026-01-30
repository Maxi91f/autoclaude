"""Rate limit handling for autoclaude."""

import re
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


def is_credit_error(output: str) -> bool:
    """Check if the error is related to credits/billing.

    Uses specific patterns to avoid false positives when Claude
    mentions words like 'limit' in normal responses.
    """
    # Look for the specific rate limit message format from Claude CLI
    # Example: "You've hit your limit · resets 5am (America/Asuncion)"
    # Must have both "hit your limit" AND the reset time format
    return bool(
        re.search(r"hit your limit .* resets \d{1,2}(am|pm)", output, re.IGNORECASE)
    )


def parse_reset_time(output: str) -> datetime | None:
    """Parse reset time from rate limit message.

    Example: "You've hit your limit · resets 5am (America/Asuncion)"
    Returns datetime when limit resets, or None if can't parse.
    """
    # Match patterns like "resets 5am (America/Asuncion)" or "resets 12pm (UTC)"
    match = re.search(
        r"resets\s+(\d{1,2})(am|pm)\s*\(([^)]+)\)", output, re.IGNORECASE
    )
    if not match:
        return None

    hour = int(match.group(1))
    am_pm = match.group(2).lower()
    tz_name = match.group(3)

    # Convert to 24-hour format
    if am_pm == "pm" and hour != 12:
        hour += 12
    elif am_pm == "am" and hour == 12:
        hour = 0

    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        return None

    now = datetime.now(tz)
    reset_time = now.replace(hour=hour, minute=0, second=0, microsecond=0)

    # If reset time is in the past, it's tomorrow
    if reset_time <= now:
        reset_time = reset_time + timedelta(days=1)

    return reset_time


def wait_for_reset(reset_time: datetime) -> None:
    """Wait until the reset time, showing countdown."""
    now = datetime.now(reset_time.tzinfo)
    wait_seconds = (reset_time - now).total_seconds()

    if wait_seconds <= 0:
        return

    print(f"\n⏳ Rate limit hit. Waiting until {reset_time.strftime('%H:%M %Z')}...")
    print(f"   ({wait_seconds / 60:.0f} minutes)")

    # Sleep with periodic status updates
    while wait_seconds > 0:
        sleep_chunk = min(300, wait_seconds)  # Update every 5 min max
        time.sleep(sleep_chunk)
        wait_seconds -= sleep_chunk
        if wait_seconds > 0:
            print(f"   {wait_seconds / 60:.0f} minutes remaining...")

    print("   ✓ Ready to continue!")
