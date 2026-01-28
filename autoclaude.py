#!/usr/bin/env python3
"""Autoclaude - Automatically implement tasks with Claude.

Simple approach: just invoke Claude with a prompt that tells it to query
beans with the 'autoclaude' tag and implement the next pending task.
Claude handles all the interpretation itself.

Runs in a loop until:
- All tasks are completed
- Claude runs out of credits
"""

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from prompts.registry import (
    build_context,
    build_prompt,
    get_prompt_for_context,
    get_prompt_names,
    record_run,
)


def get_git_root() -> Path | None:
    """Get the root directory of the git repository, or None if not in a git repo."""
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return Path(result.stdout.strip())
    return None


def get_project_root() -> Path:
    """Get the project root directory (git root or current working directory)."""
    return get_git_root() or Path.cwd()


def get_whiteboard_path() -> Path:
    """Get the path to WHITEBOARD.md in the project root."""
    return get_project_root() / "WHITEBOARD.md"


def query_beans() -> list[dict]:
    """Query beans with autoclaude tag. Returns list of beans."""
    result = subprocess.run(
        [
            "beans",
            "query",
            "--json",
            '{ beans(filter: { tags: ["autoclaude"] }) { id title status type priority } }',
        ],
        cwd=get_project_root(),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return []
    try:
        data = json.loads(result.stdout)
        return data.get("beans", [])
    except json.JSONDecodeError:
        return []


def count_beans() -> tuple[int, int]:
    """Count done and pending beans with autoclaude tag. Returns (done, pending)."""
    beans = query_beans()
    done = sum(1 for b in beans if b.get("status") in ("completed", "scrapped"))
    pending = sum(
        1 for b in beans if b.get("status") in ("todo", "in-progress", "draft")
    )
    return done, pending


def is_credit_error(output: str) -> bool:
    """Check if the error is related to credits/billing."""
    credit_indicators = [
        "credit",
        "billing",
        "quota",
        "rate limit",
        "insufficient",
        "payment",
        "hit your limit",
        "limit exceeded",
    ]
    output_lower = output.lower()
    return any(indicator in output_lower for indicator in credit_indicators)


def parse_reset_time(output: str) -> datetime | None:
    """Parse reset time from rate limit message.

    Example: "You've hit your limit · resets 5am (America/Asuncion)"
    Returns datetime when limit resets, or None if can't parse.
    """
    # Match patterns like "resets 5am (America/Asuncion)" or "resets 12pm (UTC)"
    match = re.search(r"resets\s+(\d{1,2})(am|pm)\s*\(([^)]+)\)", output, re.IGNORECASE)
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
        print(f"\r⏸ Outside allowed hours ({start_hour}:00-{end_hour}:00). "
              f"Current: {now.strftime('%H:%M')}. Waiting...", end="", flush=True)
        time.sleep(60)
    print()  # Clear the waiting line


def run_single_prompt(prompt: str, description: str) -> int:
    """Run a single prompt and return exit code."""
    print(f"\n{description}\n")

    try:
        proc = subprocess.Popen(
            [
                "claude",
                "-p",
                "--dangerously-skip-permissions",
                "--output-format",
                "stream-json",
                "--include-partial-messages",
                "--verbose",
            ],
            cwd=get_project_root(),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        proc.stdin.write(prompt.encode("utf-8"))
        proc.stdin.close()

        # Process streaming output
        import json

        buffer = ""
        while True:
            chunk = proc.stdout.read1(4096).decode("utf-8", errors="replace")
            if not chunk:
                if proc.poll() is not None:
                    break
                continue

            buffer += chunk
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                    event_type = event.get("type", "")
                    if event_type == "stream_event":
                        inner = event.get("event", {})
                        inner_type = inner.get("type", "")
                        if inner_type == "content_block_delta":
                            delta = inner.get("delta", {})
                            if delta.get("type") == "text_delta":
                                print(delta.get("text", ""), end="", flush=True)
                except json.JSONDecodeError:
                    pass

        print()
        return proc.wait()

    except Exception as e:
        print(f"\nError: {e}")
        return 1


def cmd_run(args: argparse.Namespace) -> int:
    """Run Claude to implement tasks in a loop."""
    whiteboard_path = get_whiteboard_path()

    if args.print_only:
        prompt_name = args.prompt or "task"
        prompt_content, _ = build_prompt(prompt_name, whiteboard_path)
        print(f"Prompt that would be sent to Claude ({prompt_name}):")
        print("-" * 40)
        print(prompt_content)
        print("-" * 40)
        return 0

    # Run a specific prompt once if requested
    if args.prompt:
        prompt_content, description = build_prompt(args.prompt, whiteboard_path)
        return run_single_prompt(prompt_content, description)

    # Confirm before running (only if --ask flag is provided)
    if args.ask:
        done, pending = count_beans()
        print(f"Tasks (autoclaude tag): {done} done, {pending} pending")
        print("\nAbout to run Claude in a loop until all tasks are done.")
        print("Will stop if: all tasks completed OR credits exhausted.")
        response = input("\nContinue? [y/N] ").strip().lower()
        if response != "y":
            print("Aborted.")
            return 0

    iteration = 0
    no_progress_count = 0
    max_no_progress = 5
    max_iterations = args.max_iterations

    while True:
        # Check allowed hours before each iteration
        if not is_within_allowed_hours(args.start_hour, args.end_hour):
            if args.wait_for_time_band:
                wait_for_allowed_hours(args.start_hour, args.end_hour)
            else:
                print(f"\n⏸ Outside allowed hours ({args.start_hour}:00-{args.end_hour}:00). Exiting.")
                print("   Use --wait-for-time-band to wait instead.")
                return 0

        iteration += 1
        done, pending = count_beans()

        print(f"\n{'=' * 60}")
        iter_info = f"ITERATION {iteration}"
        if max_iterations > 0:
            iter_info += f"/{max_iterations}"
        print(f"{iter_info} | Done: {done} | Pending: {pending}")
        print("=" * 60)

        if pending == 0:
            print("\n🎉 All stories are completed!")
            return 0

        if max_iterations > 0 and iteration > max_iterations:
            print(f"\n🛑 Reached max iterations ({max_iterations}). Stopping.")
            return 0

        # Build context and determine which prompt to run
        ctx = build_context(iteration, pending, done)
        prompt_obj = get_prompt_for_context(ctx)
        prefix = f"I{iteration:02d}> "

        current_prompt = prompt_obj.build(whiteboard_path)
        print(f"\n{prompt_obj.emoji} {prompt_obj.description}\n")

        # Record that this prompt ran
        record_run(prompt_obj.name, iteration)

        try:
            proc = subprocess.Popen(
                [
                    "claude",
                    "-p",
                    "--dangerously-skip-permissions",
                    "--output-format",
                    "stream-json",
                    "--include-partial-messages",
                    "--verbose",
                ],
                cwd=get_project_root(),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # Send prompt and close stdin
            proc.stdin.write(current_prompt.encode("utf-8"))
            proc.stdin.close()

            # Process streaming JSON output using read1() for true unbuffered reading
            buffer = ""
            last_result = ""
            while True:
                # read1() reads available bytes without waiting for EOF
                chunk = proc.stdout.read1(4096).decode("utf-8", errors="replace")
                if not chunk:
                    if proc.poll() is not None:
                        break
                    continue

                buffer += chunk
                # Process complete lines
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        event = json.loads(line)
                        event_type = event.get("type", "")

                        if event_type == "stream_event":
                            inner = event.get("event", {})
                            inner_type = inner.get("type", "")

                            if inner_type == "content_block_delta":
                                delta = inner.get("delta", {})
                                delta_type = delta.get("type", "")
                                if delta_type == "text_delta":
                                    text = delta.get("text", "")
                                    print(text, end="", flush=True)
                                elif delta_type == "thinking_delta":
                                    text = delta.get("thinking", "")
                                    print(f"💭 {text}", end="", flush=True)
                                elif delta_type == "input_json_delta":
                                    # Tool input streaming - show partial input
                                    partial = delta.get("partial_json", "")
                                    if partial:
                                        print(partial, end="", flush=True)
                            elif inner_type == "content_block_start":
                                # Check for tool use start
                                block = inner.get("content_block", {})
                                if block.get("type") == "tool_use":
                                    tool = block.get("name", "unknown")
                                    tool_input = block.get("input", {})
                                    # Format input for display
                                    if tool_input:
                                        input_str = json.dumps(
                                            tool_input, ensure_ascii=False
                                        )
                                        if len(input_str) > 200:
                                            input_str = input_str[:200] + "..."
                                        print(
                                            f"\n{prefix}🔧 {tool}: {input_str}",
                                            flush=True,
                                        )
                                    else:
                                        print(f"\n{prefix}🔧 {tool}", flush=True)

                        elif event_type == "assistant":
                            # Tool use events come as assistant messages
                            subtype = event.get("subtype", "")
                            if subtype == "tool_use":
                                tool = event.get("name", "unknown")
                                print(f"\n{prefix}🔧 Tool: {tool}", flush=True)
                            elif subtype == "tool_result":
                                print(f"{prefix}✓ Tool done", flush=True)

                        elif event_type == "user":
                            # Tool result - show completion
                            msg = event.get("message", {})
                            content = msg.get("content", [])
                            if content and isinstance(content, list):
                                for item in content:
                                    if item.get("type") == "tool_result":
                                        print(f"{prefix}✓ Tool done", flush=True)
                                        break

                        elif event_type == "result":
                            result_text = event.get("result", "")
                            if result_text:
                                last_result = result_text
                                print(
                                    f"\n{prefix}📋 Result: {result_text[:300]}...",
                                    flush=True,
                                )

                    except json.JSONDecodeError:
                        pass

            returncode = proc.wait()
            print()  # Final newline

            # Check for credit/rate limit errors - wait and retry
            if is_credit_error(last_result):
                reset_time = parse_reset_time(last_result)
                if reset_time:
                    wait_for_reset(reset_time)
                    no_progress_count = 0  # Reset counter after waiting
                    continue  # Retry the iteration
                else:
                    # Can't parse reset time, wait 1 hour as fallback
                    print("\n⏳ Rate limit hit. Waiting 1 hour...")
                    time.sleep(3600)
                    no_progress_count = 0
                    continue

        except Exception as e:
            print(f"\n{prefix}Error: {e}")
            no_progress_count += 1
            continue

        # Check return code
        if returncode != 0:
            pass  # Will be handled below

        # Check if any progress was made
        new_done, new_pending = count_beans()
        if new_done > done:
            total = new_done + new_pending
            pct = new_done * 100 // total if total > 0 else 0
            print(f"\n✓ Task completed! ({new_done}/{total} - {pct}%)")
            no_progress_count = 0
        elif returncode != 0:
            print(f"\n⚠ Claude exited with code {returncode}, continuing...")
            no_progress_count += 1
        else:
            no_progress_count += 1

        # Stop after too many iterations without progress
        if no_progress_count >= max_no_progress:
            print(f"\n🛑 No progress in {max_no_progress} iterations. Stopping.")
            return 1

        if new_done == done and new_pending == pending:
            print(f"\n⚠ No progress detected ({no_progress_count}/{max_no_progress})")


def cmd_list(_args: argparse.Namespace) -> int:
    """List tasks with autoclaude tag."""
    beans = query_beans()

    if not beans:
        print("No tasks found with 'autoclaude' tag.")
        return 0

    # Group by status
    by_status: dict[str, list[dict]] = {}
    for bean in beans:
        status = bean.get("status", "unknown")
        by_status.setdefault(status, []).append(bean)

    # Display order
    status_order = ["in-progress", "todo", "draft", "completed", "scrapped"]

    for status in status_order:
        if status not in by_status:
            continue
        print(f"\n## {status.upper()}")
        for bean in by_status[status]:
            priority = bean.get("priority", "normal")
            priority_icon = {
                "critical": "🔴",
                "high": "🟠",
                "normal": "🟢",
                "low": "🔵",
                "deferred": "⚪",
            }.get(priority, "")
            print(f"  {priority_icon} {bean['id']}: {bean['title']}")

    done, pending = count_beans()
    total = done + pending
    print("\n" + "=" * 40)
    print(
        f"Total: {done}/{total} tasks completed ({done * 100 // total if total > 0 else 0}%)"
    )

    return 0


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Autoclaude - Automatically implement tasks with Claude",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        allow_abbrev=False,
        epilog="""
Examples:
  autoclaude list            # Show all tasks with 'autoclaude' tag
  autoclaude run             # Implement all tasks with Claude (loop)
  autoclaude run --ask       # Ask for confirmation before running
  autoclaude run -n 3        # Run max 3 iterations
  autoclaude run --print-only # Just print the prompt
  autoclaude run -p deploy   # Run deploy prompt once
  autoclaude run -p ui       # Run UI review prompt once
  autoclaude run -p cleanup  # Run cleanup prompt once
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # list command
    subparsers.add_parser(
        "list", help="List all tasks with 'autoclaude' tag", allow_abbrev=False
    )

    # run command
    run_parser = subparsers.add_parser(
        "run", help="Run Claude to implement tasks", allow_abbrev=False
    )
    run_parser.add_argument(
        "--ask",
        action="store_true",
        help="Ask for confirmation before running (default: run without asking)",
    )
    run_parser.add_argument(
        "-p",
        "--prompt",
        choices=get_prompt_names(),
        help="Run a specific prompt once instead of the normal cycle",
    )
    run_parser.add_argument(
        "-n",
        "--max-iterations",
        type=int,
        default=0,
        help="Max iterations to run (0 = unlimited)",
    )
    run_parser.add_argument(
        "--print-only",
        action="store_true",
        help="Just print the prompt, don't run Claude",
    )
    run_parser.add_argument(
        "--start-hour",
        type=int,
        default=22,
        help="Start of allowed hours (default: 22)",
    )
    run_parser.add_argument(
        "--end-hour",
        type=int,
        default=8,
        help="End of allowed hours (default: 8)",
    )
    run_parser.add_argument(
        "--wait-for-time-band",
        action="store_true",
        help="Wait for allowed hours instead of exiting",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    commands = {
        "list": cmd_list,
        "run": cmd_run,
    }

    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
