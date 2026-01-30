"""Process manager for controlling the autoclaude subprocess."""

import asyncio
import json
import signal
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable

from .models import ProcessStatus


@dataclass
class IterationData:
    """Data for tracking the current iteration."""

    number: int
    performer_name: str
    performer_emoji: str
    started_at: datetime
    tasks_before: int = 0


@dataclass
class ProcessState:
    """Current state of the autoclaude process."""

    status: ProcessStatus = ProcessStatus.STOPPED
    pid: int | None = None
    iteration: int | None = None
    performer: str | None = None
    performer_emoji: str | None = None
    started_at: datetime | None = None
    rate_limited_until: datetime | None = None
    no_progress_count: int = 0
    current_iteration_data: IterationData | None = None


class ProcessManager:
    """Manages the autoclaude subprocess lifecycle."""

    def __init__(self) -> None:
        self._process: asyncio.subprocess.Process | None = None
        self._state = ProcessState()
        self._output_callback: Callable[[str], None] | None = None
        self._read_task: asyncio.Task | None = None

    @property
    def state(self) -> ProcessState:
        """Get current process state."""
        return self._state

    @property
    def is_running(self) -> bool:
        """Check if process is currently running."""
        return (
            self._process is not None
            and self._process.returncode is None
            and self._state.status == ProcessStatus.RUNNING
        )

    def set_output_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for output lines."""
        self._output_callback = callback

    async def start(
        self,
        max_iterations: int | None = None,
        performer: str | None = None,
        start_hour: int = 0,
        end_hour: int = 24,
    ) -> tuple[bool, int | None, str | None]:
        """Start the autoclaude process.

        Returns: (success, pid, error_message)
        """
        if self.is_running:
            return False, None, "Process is already running"

        # Build command - always use --json-events for UI communication
        cmd = ["autoclaude", "run", "--json-events"]
        if max_iterations:
            cmd.extend(["--max-iterations", str(max_iterations)])
        if performer:
            cmd.extend(["--performer", performer])
        cmd.extend(["--start-hour", str(start_hour)])
        cmd.extend(["--end-hour", str(end_hour)])

        try:
            self._process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )

            self._state = ProcessState(
                status=ProcessStatus.RUNNING,
                pid=self._process.pid,
                started_at=datetime.now(),
            )

            # Start reading output
            self._read_task = asyncio.create_task(self._read_output())

            return True, self._process.pid, None

        except Exception as e:
            self._state.status = ProcessStatus.STOPPED
            return False, None, str(e)

    async def stop(self, force: bool = False) -> tuple[bool, str | None]:
        """Stop the autoclaude process.

        Returns: (success, error_message)
        """
        if self._process is None or self._process.returncode is not None:
            # Save any ongoing iteration as cancelled
            if self._state.current_iteration_data:
                self._save_iteration_history("cancelled")
            self._state.status = ProcessStatus.STOPPED
            return True, None

        try:
            # Save any ongoing iteration as cancelled
            if self._state.current_iteration_data:
                self._save_iteration_history("cancelled")

            if force:
                self._process.kill()
            else:
                # Send SIGTERM for graceful shutdown
                self._process.send_signal(signal.SIGTERM)

            # Wait for process to exit
            await asyncio.wait_for(self._process.wait(), timeout=10.0)

            self._state.status = ProcessStatus.STOPPED
            self._state.pid = None
            return True, None

        except asyncio.TimeoutError:
            # Force kill if graceful shutdown times out
            self._process.kill()
            await self._process.wait()
            self._state.status = ProcessStatus.STOPPED
            self._state.pid = None
            return True, "Process killed after timeout"

        except Exception as e:
            return False, str(e)

    async def pause(self) -> tuple[bool, str | None]:
        """Pause the process (sends SIGUSR1 for graceful pause)."""
        if not self.is_running:
            return False, "Process is not running"

        try:
            # SIGUSR1 is used for graceful pause - waits for current iteration to finish
            self._process.send_signal(signal.SIGUSR1)
            self._state.status = ProcessStatus.PAUSED
            return True, None
        except Exception as e:
            return False, str(e)

    async def resume(self) -> tuple[bool, str | None]:
        """Resume the paused process (sends SIGUSR2)."""
        if self._state.status != ProcessStatus.PAUSED:
            return False, "Process is not paused"

        try:
            self._process.send_signal(signal.SIGUSR2)
            self._state.status = ProcessStatus.RUNNING
            return True, None
        except Exception as e:
            return False, str(e)

    async def _read_output(self) -> None:
        """Read output from process and call callback."""
        if self._process is None or self._process.stdout is None:
            return

        try:
            while True:
                line = await self._process.stdout.readline()
                if not line:
                    break

                decoded = line.decode("utf-8", errors="replace").rstrip()
                if decoded and self._output_callback:
                    self._output_callback(decoded)

                # Parse line to update state
                self._parse_output_line(decoded)

        except Exception:
            pass
        finally:
            # Process ended
            if self._process.returncode is not None:
                self._state.status = ProcessStatus.STOPPED
                self._state.pid = None

    def _count_pending_beans(self) -> int:
        """Count beans with todo or in-progress status."""
        import json

        try:
            result = subprocess.run(
                [
                    "beans",
                    "query",
                    '{ beans(filter: { tags: ["autoclaude"], status: ["todo", "in-progress"] }) { id } }',
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return len(data.get("beans", []))
        except Exception:
            pass
        return 0

    def _save_iteration_history(self, result: str, error_message: str | None = None) -> None:
        """Save the current iteration to history."""
        from .history import IterationResult, IterationRecord, save_iteration

        if not self._state.current_iteration_data:
            return

        iter_data = self._state.current_iteration_data
        now = datetime.now()

        # Map result string to enum
        result_map = {
            "success": IterationResult.SUCCESS,
            "no_progress": IterationResult.NO_PROGRESS,
            "error": IterationResult.ERROR,
            "rate_limited": IterationResult.RATE_LIMITED,
            "cancelled": IterationResult.CANCELLED,
        }
        iteration_result = result_map.get(result, IterationResult.SUCCESS)

        tasks_after = self._count_pending_beans()
        duration = (now - iter_data.started_at).total_seconds()

        record = IterationRecord(
            id=None,
            iteration_number=iter_data.number,
            performer_name=iter_data.performer_name,
            performer_emoji=iter_data.performer_emoji,
            result=iteration_result,
            tasks_before=iter_data.tasks_before,
            tasks_after=tasks_after,
            duration_seconds=duration,
            started_at=iter_data.started_at,
            ended_at=now,
            error_message=error_message,
        )

        try:
            save_iteration(record)
        except Exception:
            pass

        # Clear current iteration data
        self._state.current_iteration_data = None

    def _parse_output_line(self, line: str) -> None:
        """Parse output line to update process state.

        First tries to parse as JSON event. Falls back to legacy string parsing
        for backwards compatibility.
        """
        # Try to parse as JSON event first
        if line.strip().startswith("{"):
            try:
                event = json.loads(line)
                self._handle_json_event(event)
                return
            except json.JSONDecodeError:
                pass  # Not valid JSON, fall through to legacy parsing

        # Legacy string-based parsing (for backwards compatibility)
        self._parse_output_line_legacy(line)

    def _handle_json_event(self, event: dict) -> None:
        """Handle a structured JSON event from autoclaude."""
        event_type = event.get("event")

        if event_type == "iteration_start":
            # If there was a previous iteration without an end event, save it
            if self._state.current_iteration_data:
                self._save_iteration_history("success")

            self._state.iteration = event.get("iteration")
            self._state.performer = event.get("performer")
            self._state.performer_emoji = event.get("emoji")

            self._state.current_iteration_data = IterationData(
                number=event.get("iteration", 0),
                performer_name=event.get("performer", "unknown"),
                performer_emoji=event.get("emoji", ""),
                started_at=datetime.now(),
                tasks_before=event.get("tasks_pending", 0) + event.get("tasks_done", 0),
            )

        elif event_type == "iteration_end":
            result = event.get("result", "success")
            self._state.no_progress_count = event.get("no_progress_count", 0)

            if self._state.current_iteration_data:
                error_msg = event.get("error_message")
                self._save_iteration_history(result, error_message=error_msg)

        elif event_type == "rate_limited":
            self._state.status = ProcessStatus.RATE_LIMITED
            reset_time_str = event.get("reset_time")
            if reset_time_str:
                try:
                    self._state.rate_limited_until = datetime.fromisoformat(reset_time_str)
                except ValueError:
                    pass

        elif event_type == "paused":
            self._state.status = ProcessStatus.PAUSED

        elif event_type == "resumed":
            self._state.status = ProcessStatus.RUNNING

        elif event_type == "completed":
            # Process is finishing
            if self._state.current_iteration_data:
                self._save_iteration_history("success")

        elif event_type == "terminated":
            # Process was terminated by user
            if self._state.current_iteration_data:
                self._save_iteration_history("cancelled")

        elif event_type == "error":
            if self._state.current_iteration_data:
                self._save_iteration_history("error", error_message=event.get("message"))

    def _parse_output_line_legacy(self, line: str) -> None:
        """Legacy string-based parsing for backwards compatibility."""
        # Parse iteration start - format varies but usually contains "iteration X"
        if "Starting iteration" in line or "iteration" in line.lower():
            try:
                # Try to extract iteration number
                parts = line.split()
                for i, part in enumerate(parts):
                    if part.lower() == "iteration" and i + 1 < len(parts):
                        num_str = parts[i + 1].rstrip(".:,")
                        if num_str.isdigit():
                            new_iteration = int(num_str)

                            # If there was a previous iteration, save it as success
                            if self._state.current_iteration_data:
                                self._save_iteration_history("success")

                            self._state.iteration = new_iteration

                            # Start tracking new iteration
                            performer_name = self._state.performer or "unknown"
                            performer_emoji = self._state.performer_emoji or ""
                            tasks_before = self._count_pending_beans()

                            self._state.current_iteration_data = IterationData(
                                number=new_iteration,
                                performer_name=performer_name,
                                performer_emoji=performer_emoji,
                                started_at=datetime.now(),
                                tasks_before=tasks_before,
                            )
                            break
            except (IndexError, ValueError):
                pass

        # Parse performer - look for patterns like "performer: task" or emoji + name
        if "performer:" in line.lower() or "running performer" in line.lower():
            try:
                parts = line.split("performer")
                if len(parts) > 1:
                    performer_part = parts[1].strip().lstrip(":").strip()
                    if performer_part:
                        # First word is likely the performer name
                        name = performer_part.split()[0].strip()
                        if name and not name.startswith("("):
                            self._state.performer = name
            except Exception:
                pass

        # Parse rate limit
        if "rate limit" in line.lower():
            self._state.status = ProcessStatus.RATE_LIMITED
            # Save iteration as rate limited
            if self._state.current_iteration_data:
                self._save_iteration_history("rate_limited")

        # Parse no progress
        if "no progress" in line.lower():
            self._state.no_progress_count += 1
            # Save iteration as no progress
            if self._state.current_iteration_data:
                self._save_iteration_history("no_progress")

        # Parse errors
        if line.lower().startswith("error:") or "fatal error" in line.lower():
            if self._state.current_iteration_data:
                self._save_iteration_history("error", error_message=line)

        # Parse completion messages
        if "completed successfully" in line.lower() or "iteration complete" in line.lower():
            if self._state.current_iteration_data:
                self._save_iteration_history("success")


# Singleton instance
_manager: ProcessManager | None = None


def get_process_manager() -> ProcessManager:
    """Get the singleton process manager instance."""
    global _manager
    if _manager is None:
        _manager = ProcessManager()
    return _manager
