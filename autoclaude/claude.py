"""Claude runner for autoclaude."""

import json
import subprocess
from collections.abc import Callable
from datetime import datetime

from .paths import get_project_root


def run_claude(
    prompt: str,
    prefix_fn: Callable[[], str] | None = None,
    start_new_session: bool = False,
) -> tuple[int, str, str]:
    """Run Claude with a prompt and stream output.

    Args:
        prompt: The prompt to send to Claude
        prefix_fn: Optional callable that returns a prefix string for output lines
        start_new_session: If True, don't forward Ctrl+C to claude subprocess

    Returns:
        Tuple of (return_code, last_result, stderr_output)
    """
    prefix = prefix_fn or (lambda: "")

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
        start_new_session=start_new_session,
    )

    proc.stdin.write(prompt.encode("utf-8"))
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
                                input_str = json.dumps(tool_input, ensure_ascii=False)
                                if len(input_str) > 200:
                                    input_str = input_str[:200] + "..."
                                print(
                                    f"\n{prefix()}🔧 {tool}: {input_str}",
                                    flush=True,
                                )
                            else:
                                print(f"\n{prefix()}🔧 {tool}", flush=True)

                elif event_type == "assistant":
                    # Tool use events come as assistant messages
                    subtype = event.get("subtype", "")
                    if subtype == "tool_use":
                        tool = event.get("name", "unknown")
                        print(f"\n{prefix()}🔧 Tool: {tool}", flush=True)
                    elif subtype == "tool_result":
                        print(f"\n{prefix()}✓ Tool done", flush=True)

                elif event_type == "user":
                    # Tool result - show completion
                    msg = event.get("message", {})
                    content = msg.get("content", [])
                    if content and isinstance(content, list):
                        for item in content:
                            if item.get("type") == "tool_result":
                                print(f"\n{prefix()}✓ Tool done", flush=True)
                                break

                elif event_type == "result":
                    result_text = event.get("result", "")
                    if result_text:
                        last_result = result_text
                        print(
                            f"\n{prefix()}📋 Result: {result_text[:300]}...",
                            flush=True,
                        )

            except json.JSONDecodeError:
                pass

    returncode = proc.wait()
    stderr_output = proc.stderr.read().decode("utf-8", errors="replace")
    print()  # Final newline

    return returncode, last_result, stderr_output


def run_single_prompt(prompt: str, description: str, emoji: str) -> int:
    """Run a single prompt and return exit code."""
    print(f"\n{description}\n")

    def get_prefix():
        timestamp = datetime.now().strftime("%H:%M")
        return f"\033[1;32m[{timestamp}] UL ({emoji})>\033[0m "

    try:
        returncode, _, _ = run_claude(prompt, prefix_fn=get_prefix)
        return returncode
    except Exception as e:
        print(f"\nError: {e}")
        return 1
