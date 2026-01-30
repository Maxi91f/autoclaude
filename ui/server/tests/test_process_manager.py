"""Tests for process_manager.py subprocess management."""

import asyncio
import signal
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ui.server.models import ProcessStatus
from ui.server.process_manager import (
    IterationData,
    ProcessManager,
    ProcessState,
    get_process_manager,
)


class TestProcessState:
    """Tests for ProcessState dataclass."""

    def test_default_state(self):
        """
        GIVEN ProcessState is created
        WHEN no arguments are provided
        THEN has stopped status and default values.
        """
        # WHEN
        state = ProcessState()

        # THEN
        assert state.status == ProcessStatus.STOPPED
        assert state.pid is None
        assert state.iteration is None
        assert state.performer is None
        assert state.no_progress_count == 0


class TestIterationData:
    """Tests for IterationData dataclass."""

    def test_creates_iteration_data(self):
        """
        GIVEN iteration parameters
        WHEN IterationData is created
        THEN stores all values correctly.
        """
        # GIVEN
        now = datetime.now()

        # WHEN
        data = IterationData(
            number=5,
            performer_name="task",
            performer_emoji="📋",
            started_at=now,
            tasks_before=10,
        )

        # THEN
        assert data.number == 5
        assert data.performer_name == "task"
        assert data.performer_emoji == "📋"
        assert data.started_at == now
        assert data.tasks_before == 10


class TestProcessManager:
    """Tests for ProcessManager class."""

    @pytest.fixture
    def manager(self):
        """Create a fresh ProcessManager for each test."""
        return ProcessManager()

    def test_initial_state(self, manager):
        """
        GIVEN a new ProcessManager
        WHEN checking state
        THEN is stopped with no process.
        """
        # THEN
        assert manager.is_running is False
        assert manager.state.status == ProcessStatus.STOPPED
        assert manager.state.pid is None

    @pytest.mark.asyncio
    async def test_start_launches_subprocess(self, manager):
        """
        GIVEN a stopped ProcessManager
        WHEN start is called
        THEN launches subprocess and updates state.
        """
        # GIVEN
        mock_process = AsyncMock()
        mock_process.pid = 12345
        mock_process.returncode = None
        mock_process.stdout = AsyncMock()
        mock_process.stdout.readline = AsyncMock(return_value=b"")

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            # WHEN
            success, pid, error = await manager.start()

            # THEN
            assert success is True
            assert pid == 12345
            assert error is None
            assert manager.state.status == ProcessStatus.RUNNING
            assert manager.state.pid == 12345

    @pytest.mark.asyncio
    async def test_start_with_options(self, manager):
        """
        GIVEN custom start options
        WHEN start is called
        THEN builds command with options.
        """
        # GIVEN
        mock_process = AsyncMock()
        mock_process.pid = 12345
        mock_process.returncode = None
        mock_process.stdout = AsyncMock()
        mock_process.stdout.readline = AsyncMock(return_value=b"")

        with patch("asyncio.create_subprocess_exec", return_value=mock_process) as mock_exec:
            # WHEN
            await manager.start(
                max_iterations=10,
                performer="task",
                start_hour=8,
                end_hour=18,
            )

            # THEN
            call_args = mock_exec.call_args[0]
            assert "autoclaude" in call_args
            assert "--max-iterations" in call_args
            assert "10" in call_args
            assert "--performer" in call_args
            assert "task" in call_args
            assert "--start-hour" in call_args
            assert "8" in call_args
            assert "--end-hour" in call_args
            assert "18" in call_args

    @pytest.mark.asyncio
    async def test_start_fails_when_already_running(self, manager):
        """
        GIVEN process is already running
        WHEN start is called
        THEN returns error.
        """
        # GIVEN
        mock_process = AsyncMock()
        mock_process.pid = 12345
        mock_process.returncode = None
        mock_process.stdout = AsyncMock()
        mock_process.stdout.readline = AsyncMock(return_value=b"")
        manager._process = mock_process
        manager._state.status = ProcessStatus.RUNNING

        # WHEN
        success, pid, error = await manager.start()

        # THEN
        assert success is False
        assert pid is None
        assert "already running" in error

    @pytest.mark.asyncio
    async def test_start_handles_exception(self, manager):
        """
        GIVEN subprocess creation fails
        WHEN start is called
        THEN returns error and resets state.
        """
        # GIVEN
        with patch("asyncio.create_subprocess_exec", side_effect=Exception("Failed to start")):
            # WHEN
            success, pid, error = await manager.start()

            # THEN
            assert success is False
            assert pid is None
            assert "Failed to start" in error
            assert manager.state.status == ProcessStatus.STOPPED

    @pytest.mark.asyncio
    async def test_stop_terminates_process_gracefully(self, manager):
        """
        GIVEN a running process
        WHEN stop is called
        THEN sends SIGTERM and waits.
        """
        # GIVEN
        mock_process = AsyncMock()
        mock_process.pid = 12345
        mock_process.returncode = None
        mock_process.send_signal = MagicMock()
        mock_process.wait = AsyncMock()
        manager._process = mock_process
        manager._state.status = ProcessStatus.RUNNING

        # WHEN
        success, error = await manager.stop()

        # THEN
        assert success is True
        mock_process.send_signal.assert_called_once_with(signal.SIGTERM)
        assert manager.state.status == ProcessStatus.STOPPED

    @pytest.mark.asyncio
    async def test_stop_force_kills_process(self, manager):
        """
        GIVEN a running process
        WHEN stop is called with force=True
        THEN kills the process immediately.
        """
        # GIVEN
        mock_process = AsyncMock()
        mock_process.pid = 12345
        mock_process.returncode = None
        mock_process.kill = MagicMock()
        mock_process.wait = AsyncMock()
        manager._process = mock_process
        manager._state.status = ProcessStatus.RUNNING

        # WHEN
        success, error = await manager.stop(force=True)

        # THEN
        assert success is True
        mock_process.kill.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_handles_timeout(self, manager):
        """
        GIVEN a process that doesn't terminate
        WHEN stop times out
        THEN force kills the process.
        """
        # GIVEN
        mock_process = AsyncMock()
        mock_process.pid = 12345
        mock_process.returncode = None
        mock_process.send_signal = MagicMock()
        mock_process.kill = MagicMock()
        mock_process.wait = AsyncMock(side_effect=[asyncio.TimeoutError, None])
        manager._process = mock_process
        manager._state.status = ProcessStatus.RUNNING

        # WHEN
        success, error = await manager.stop()

        # THEN
        assert success is True
        mock_process.kill.assert_called_once()
        assert "timeout" in error.lower()

    @pytest.mark.asyncio
    async def test_stop_when_already_stopped(self, manager):
        """
        GIVEN process is already stopped
        WHEN stop is called
        THEN returns success.
        """
        # WHEN
        success, error = await manager.stop()

        # THEN
        assert success is True
        assert error is None

    @pytest.mark.asyncio
    async def test_pause_sends_sigusr1(self, manager):
        """
        GIVEN a running process
        WHEN pause is called
        THEN sends SIGUSR1 and updates state.
        """
        # GIVEN
        mock_process = AsyncMock()
        mock_process.pid = 12345
        mock_process.returncode = None
        mock_process.send_signal = MagicMock()
        manager._process = mock_process
        manager._state.status = ProcessStatus.RUNNING

        # WHEN
        success, error = await manager.pause()

        # THEN
        assert success is True
        mock_process.send_signal.assert_called_once_with(signal.SIGUSR1)
        assert manager.state.status == ProcessStatus.PAUSED

    @pytest.mark.asyncio
    async def test_pause_fails_when_not_running(self, manager):
        """
        GIVEN process is not running
        WHEN pause is called
        THEN returns error.
        """
        # WHEN
        success, error = await manager.pause()

        # THEN
        assert success is False
        assert "not running" in error

    @pytest.mark.asyncio
    async def test_resume_sends_sigusr2(self, manager):
        """
        GIVEN a paused process
        WHEN resume is called
        THEN sends SIGUSR2 and updates state.
        """
        # GIVEN
        mock_process = AsyncMock()
        mock_process.pid = 12345
        mock_process.returncode = None
        mock_process.send_signal = MagicMock()
        manager._process = mock_process
        manager._state.status = ProcessStatus.PAUSED

        # WHEN
        success, error = await manager.resume()

        # THEN
        assert success is True
        mock_process.send_signal.assert_called_once_with(signal.SIGUSR2)
        assert manager.state.status == ProcessStatus.RUNNING

    @pytest.mark.asyncio
    async def test_resume_fails_when_not_paused(self, manager):
        """
        GIVEN process is not paused
        WHEN resume is called
        THEN returns error.
        """
        # GIVEN
        manager._state.status = ProcessStatus.RUNNING

        # WHEN
        success, error = await manager.resume()

        # THEN
        assert success is False
        assert "not paused" in error

    def test_set_output_callback(self, manager):
        """
        GIVEN a ProcessManager
        WHEN set_output_callback is called
        THEN stores the callback.
        """
        # GIVEN
        callback = MagicMock()

        # WHEN
        manager.set_output_callback(callback)

        # THEN
        assert manager._output_callback is callback


class TestProcessManagerOutputParsing:
    """Tests for output line parsing."""

    @pytest.fixture
    def manager(self):
        """Create a fresh ProcessManager for each test."""
        return ProcessManager()

    def test_parses_iteration_number(self, manager, mock_beans_query):
        """
        GIVEN an output line with iteration number
        WHEN _parse_output_line is called
        THEN updates state iteration.
        """
        # WHEN
        manager._parse_output_line("Starting iteration 5")

        # THEN
        assert manager.state.iteration == 5

    def test_parses_performer(self, manager):
        """
        GIVEN an output line with performer
        WHEN _parse_output_line is called
        THEN updates state performer.
        """
        # WHEN
        manager._parse_output_line("Running performer: task")

        # THEN
        assert manager.state.performer == "task"

    def test_detects_rate_limit(self, manager, mock_beans_query):
        """
        GIVEN an output line indicating rate limit
        WHEN _parse_output_line is called
        THEN updates status to rate limited.
        """
        # WHEN
        manager._parse_output_line("Rate limit reached, waiting...")

        # THEN
        assert manager.state.status == ProcessStatus.RATE_LIMITED

    def test_counts_no_progress(self, manager, mock_beans_query):
        """
        GIVEN an output line indicating no progress
        WHEN _parse_output_line is called
        THEN increments no_progress_count.
        """
        # GIVEN
        assert manager.state.no_progress_count == 0

        # WHEN
        manager._parse_output_line("No progress made in this iteration")
        manager._parse_output_line("Detected no progress")

        # THEN
        assert manager.state.no_progress_count == 2


class TestGetProcessManager:
    """Tests for get_process_manager singleton."""

    def test_returns_same_instance(self):
        """
        GIVEN get_process_manager is called multiple times
        WHEN comparing returned instances
        THEN they are the same object.
        """
        # Reset singleton for clean test
        import ui.server.process_manager as pm_module
        pm_module._manager = None

        # WHEN
        manager1 = get_process_manager()
        manager2 = get_process_manager()

        # THEN
        assert manager1 is manager2

        # Cleanup
        pm_module._manager = None
