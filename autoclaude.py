#!/usr/bin/env python3
"""Autoclaude - Automatically implement user stories with Claude.

Simple approach: just invoke Claude with a prompt that tells it to read
STORIES.md and implement the next unchecked story. Claude handles all
the interpretation itself.

Runs in a loop until:
- All stories are completed
- Claude runs out of credits
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


def get_stories_path() -> Path:
    """Get the path to STORIES.md in the current directory."""
    return Path.cwd() / "STORIES.md"


def get_whiteboard_path() -> Path:
    """Get the path to WHITEBOARD.md in the current directory."""
    return Path.cwd() / "WHITEBOARD.md"


def count_stories(stories_path: Path) -> tuple[int, int]:
    """Count done and pending stories. Returns (done, pending)."""
    content = stories_path.read_text()
    done = content.count("- [x]")
    pending = content.count("- [ ]")
    return done, pending


def build_prompt(stories_path: Path, whiteboard_path: Path) -> str:
    """Build the prompt for Claude."""
    return f"""You are an autonomous agent implementing user stories.

## Whiteboard

You have a whiteboard file at {whiteboard_path} for communication with future Claude instances.

**Read the whiteboard FIRST** before starting any work. It may contain important notes, blockers, or decisions from previous runs.

**Use the whiteboard to:**
- Document blockers you encounter
- Leave notes about things you learned
- Record technical decisions made
- Warn about things that don't work

**Maintain the whiteboard:**
- Add timestamps to new entries (YYYY-MM-DD HH:MM)
- Remove entries older than 24 hours or no longer relevant
- Keep it under 300 lines - if it exceeds this, summarize older content
- Use sections: ## Blockers, ## Notes, ## Decisions

## Stories

Read {stories_path} which contains user stories in markdown format.

Stories are marked with checkboxes:
- `- [ ]` means the story is NOT implemented yet
- `- [x]` means the story IS implemented

## Your Task

1. Read the whiteboard first
2. Find the FIRST story that is NOT implemented (has `- [ ]`)
3. Implement that story completely
4. Update {stories_path} to mark the story as done (change `- [ ]` to `- [x]`)
5. Update the whiteboard with any relevant notes
6. Commit your changes with a meaningful commit message

If all stories are already implemented, say so and exit.

Start by reading the whiteboard and stories files."""


def build_cleanup_prompt(stories_path: Path, whiteboard_path: Path) -> str:
    """Build the prompt for cleanup/verification iteration."""
    return f"""You are an autonomous agent verifying user stories.

## Whiteboard

Read {whiteboard_path} first for context from previous runs.

## Your Task: VERIFICATION

This is a **cleanup iteration**. Your job is to verify that stories are correctly marked.

1. Read {stories_path} which contains user stories with checkboxes
2. For EACH story marked as done (`- [x]`):
   - Check the actual codebase to verify the feature is implemented
   - If NOT actually implemented, change it back to `- [ ]`
3. For EACH story marked as pending (`- [ ]`):
   - Check if it might already be implemented in the code
   - If it IS actually implemented, change it to `- [x]`
4. Update the whiteboard with any corrections made
5. Commit any changes with message "fix: correct story status after verification"

Be thorough but efficient. Focus on verifying the implementation exists, not on code quality.

If everything is correctly marked, just say so and exit without making changes."""


def is_credit_error(output: str) -> bool:
    """Check if the error is related to credits/billing."""
    credit_indicators = [
        "credit",
        "billing",
        "quota",
        "rate limit",
        "insufficient",
        "payment",
    ]
    output_lower = output.lower()
    return any(indicator in output_lower for indicator in credit_indicators)


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


def cmd_run(args: argparse.Namespace) -> int:
    """Run Claude to implement stories in a loop."""
    stories_path = get_stories_path()

    if not stories_path.exists():
        print(f"Error: {stories_path} not found")
        return 1

    whiteboard_path = get_whiteboard_path()

    if args.print_only:
        prompt = build_prompt(stories_path, whiteboard_path)
        print("Prompt that would be sent to Claude:")
        print("-" * 40)
        print(prompt)
        print("-" * 40)
        return 0

    # Confirm before running
    if not args.yes:
        done, pending = count_stories(stories_path)
        print(f"Stories: {done} done, {pending} pending")
        print("\nAbout to run Claude in a loop until all stories are done.")
        print("Will stop if: all stories completed OR credits exhausted.")
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
            wait_for_allowed_hours(args.start_hour, args.end_hour)

        iteration += 1
        done, pending = count_stories(stories_path)

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

        # Determine if this is a cleanup iteration (every 5 iterations)
        is_cleanup = iteration % 5 == 0 and iteration > 0
        prefix = f"I{iteration:02d}> "

        if is_cleanup:
            current_prompt = build_cleanup_prompt(stories_path, whiteboard_path)
            print("\n🧹 Running cleanup/verification iteration...\n")
        else:
            current_prompt = build_prompt(stories_path, whiteboard_path)
            print(f"\nStarting Claude for story {done + 1}...\n")

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
                cwd=Path.cwd(),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # Send prompt and close stdin
            proc.stdin.write(current_prompt.encode("utf-8"))
            proc.stdin.close()

            # Process streaming JSON output using read1() for true unbuffered reading
            buffer = ""
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
                                print(
                                    f"\n{prefix}📋 Result: {result_text[:300]}...",
                                    flush=True,
                                )

                    except json.JSONDecodeError:
                        pass

            returncode = proc.wait()
            print()  # Final newline

        except Exception as e:
            print(f"\n{prefix}Error: {e}")
            no_progress_count += 1
            continue

        # Check return code
        if returncode != 0:
            pass  # Will be handled below

        # Check if any progress was made
        new_done, new_pending = count_stories(stories_path)
        if new_done > done:
            total = new_done + new_pending
            pct = new_done * 100 // total if total > 0 else 0
            print(f"\n✓ Story completed! ({new_done}/{total} - {pct}%)")
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
    """List stories by reading the file directly."""
    stories_path = get_stories_path()

    if not stories_path.exists():
        print(f"Error: {stories_path} not found")
        return 1

    content = stories_path.read_text()
    done, pending = count_stories(stories_path)
    total = done + pending

    print(content)
    print("=" * 40)
    print(
        f"Total: {done}/{total} stories completed ({done * 100 // total if total > 0 else 0}%)"
    )

    return 0


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Autoclaude - Automatically implement user stories with Claude",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  autoclaude list          # Show all stories
  autoclaude run           # Implement all stories with Claude (loop)
  autoclaude run -y        # Skip confirmation
  autoclaude run -n 3      # Run max 3 iterations
  autoclaude run --print   # Just print the prompt
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # list command
    subparsers.add_parser("list", help="List all stories with status")

    # run command
    run_parser = subparsers.add_parser("run", help="Run Claude to implement stories")
    run_parser.add_argument(
        "-y", "--yes", action="store_true", help="Skip confirmation"
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
