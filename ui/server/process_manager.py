"""Process manager for controlling the autoclaude subprocess."""

import asyncio
import signal
from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from .models import ProcessStatus


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

        # Build command
        cmd = ["autoclaude", "run"]
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
            self._state.status = ProcessStatus.STOPPED
            return True, None

        try:
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

    def _parse_output_line(self, line: str) -> None:
        """Parse output line to update process state."""
        # Parse iteration start
        if "Starting iteration" in line:
            try:
                # Format: "Starting iteration X with performer..."
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "iteration":
                        self._state.iteration = int(parts[i + 1])
                        break
            except (IndexError, ValueError):
                pass

        # Parse performer
        if "performer:" in line.lower() or "running performer" in line.lower():
            # Try to extract performer name
            pass

        # Parse rate limit
        if "rate limit" in line.lower():
            self._state.status = ProcessStatus.RATE_LIMITED

        # Parse no progress
        if "no progress" in line.lower():
            self._state.no_progress_count += 1


# Singleton instance
_manager: ProcessManager | None = None


def get_process_manager() -> ProcessManager:
    """Get the singleton process manager instance."""
    global _manager
    if _manager is None:
        _manager = ProcessManager()
    return _manager
