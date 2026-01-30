"""CLI commands for autoclaude."""

import argparse
import signal
import sys
import time
from datetime import datetime

from .performers.registry import (
    build_context,
    get_performer,
    get_performer_for_context,
    get_performer_names,
    record_run,
    should_terminate,
)

import uvicorn

from .beans import count_beans, query_beans
from .claude import run_claude, run_single_prompt
from .paths import get_whiteboard_path
from .rate_limit import is_credit_error, parse_reset_time, wait_for_reset
from .time_band import is_within_allowed_hours, wait_for_allowed_hours


def cmd_run(args: argparse.Namespace) -> int:
    """Run Claude to implement tasks in a loop."""
    whiteboard_path = get_whiteboard_path()

    if args.print_only:
        name = args.performer or "task"
        performer = get_performer(name)
        content = performer.build(whiteboard_path)
        print(f"Content that would be sent to Claude ({name}):")
        print("-" * 40)
        print(content)
        print("-" * 40)
        return 0

    # Run a specific performer once if requested
    if args.performer:
        performer = get_performer(args.performer)
        content = performer.build(whiteboard_path)
        description = f"{performer.emoji} {performer.description}"
        return run_single_prompt(content, description, performer.emoji)

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
    terminating = False

    def handle_sigint(_signum, _frame):
        nonlocal terminating
        if terminating:
            # Second Ctrl+C - exit immediately
            print("\n\n⏹ Force quit")
            sys.exit(130)
        terminating = True
        print("\n\n⏹ Finishing current iteration... (Ctrl+C again to force quit)")

    signal.signal(signal.SIGINT, handle_sigint)

    while True:
        # Check allowed hours before each iteration
        if not is_within_allowed_hours(args.start_hour, args.end_hour):
            if args.wait_for_time_band:
                wait_for_allowed_hours(args.start_hour, args.end_hour)
            else:
                print(
                    f"\n⏸ Outside allowed hours ({args.start_hour}:00-{args.end_hour}:00). Exiting."
                )
                print("   Use --wait-for-time-band to wait instead.")
                return 0

        iteration += 1
        done, pending = count_beans()

        # Cyan header
        print(f"\n\033[1;36m{'=' * 60}")
        iter_info = f"ITERATION {iteration}"
        if max_iterations > 0:
            iter_info += f"/{max_iterations}"
        print(f"{iter_info} | Done: {done} | Pending: {pending}")
        print(f"{'=' * 60}\033[0m")

        if max_iterations > 0 and iteration > max_iterations:
            print(f"\n🛑 Reached max iterations ({max_iterations}). Stopping.")
            return 0

        # Build context and determine which performer to run
        ctx = build_context(iteration, pending, done)

        # Check if we should terminate (no tasks and all special performers ran)
        if should_terminate(ctx):
            print("\n🎉 All stories are completed!")
            return 0

        performer = get_performer_for_context(ctx)

        # Cyan bold for prefix to make it stand out
        # Use lambda so terminating status is evaluated at print time
        def get_prefix():
            term_marker = (
                " \033[1;31m(Terminating...)\033[1;32m" if terminating else ""
            )
            timestamp = datetime.now().strftime("%H:%M")
            return f"\033[1;32m[{timestamp}] I{iteration:02d} ({performer.emoji}){term_marker}>\033[0m "

        content = performer.build(whiteboard_path)
        print(f"\n{performer.emoji} {performer.description}\n")

        # Record that this performer ran
        record_run(performer.name, iteration, pending)

        try:
            returncode, last_result, stderr_output = run_claude(
                content,
                prefix_fn=get_prefix,
                start_new_session=True,
            )

            # Check for credit/rate limit errors in result or stderr
            error_text = last_result + "\n" + stderr_output
            if is_credit_error(error_text):
                reset_time = parse_reset_time(error_text)
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
            print(f"\n{get_prefix()}Error: {e}")
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
        elif performer.name == "task" and new_done == done and new_pending == pending:
            # Only count "no progress" for task performer when beans didn't change
            no_progress_count += 1
            print(f"\n⚠ No progress detected ({no_progress_count}/{max_no_progress})")
        # Special performers (cleanup, deploy, ui) don't affect no_progress_count

        # Stop after too many iterations without progress
        if no_progress_count >= max_no_progress:
            print(f"\n🛑 No progress in {max_no_progress} iterations. Stopping.")
            return 1

        # Check if user requested graceful termination
        if terminating:
            print("\n⏹ Terminated by user after iteration completed.")
            return 0


def cmd_ui(args: argparse.Namespace) -> int:
    """Run the AutoClaude UI server."""
    uvicorn.run(
        "ui.server.app:create_app",
        factory=True,
        host=args.host,
        port=args.port,
        reload=args.reload,
    )
    return 0


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
  autoclaude run -p deploy   # Run deploy performer once
  autoclaude run -p ui       # Run UI review performer once
  autoclaude run -p cleanup  # Run cleanup performer once
  autoclaude ui              # Launch the web UI on 0.0.0.0:8080
  autoclaude ui --port 3000  # Launch on custom port
  autoclaude ui --reload     # Launch with auto-reload (dev mode)
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
        "--performer",
        choices=get_performer_names(),
        help="Run a specific performer once instead of the normal cycle",
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
        help="Just print the content, don't run Claude",
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

    # ui command
    ui_parser = subparsers.add_parser(
        "ui", help="Launch the AutoClaude web UI", allow_abbrev=False
    )
    ui_parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0 for network access)",
    )
    ui_parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to bind to (default: 8080)",
    )
    ui_parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    commands = {
        "list": cmd_list,
        "run": cmd_run,
        "ui": cmd_ui,
    }

    return commands[args.command](args)
