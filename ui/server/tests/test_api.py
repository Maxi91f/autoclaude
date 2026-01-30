"""Tests for api.py REST endpoints."""

import json
import os
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from ui.server.app import create_app
from ui.server.models import ProcessStatus


@pytest.fixture
def client():
    """Create a test client for the API."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def mock_process_manager():
    """Create a mocked process manager."""
    with patch("ui.server.api.get_process_manager") as mock_get_pm:
        pm = MagicMock()
        pm.state = MagicMock(
            status=ProcessStatus.STOPPED,
            pid=None,
            iteration=None,
            performer=None,
            performer_emoji=None,
            started_at=None,
            rate_limited_until=None,
            no_progress_count=0,
        )
        pm.is_running = False
        pm.start = AsyncMock(return_value=(True, 12345, None))
        pm.stop = AsyncMock(return_value=(True, None))
        pm.pause = AsyncMock(return_value=(True, None))
        pm.resume = AsyncMock(return_value=(True, None))
        pm.set_output_callback = MagicMock()
        mock_get_pm.return_value = pm
        yield pm


class TestStatusEndpoint:
    """Tests for GET /api/status endpoint."""

    def test_returns_status_when_stopped(self, client, mock_process_manager, mock_beans_query):
        """
        GIVEN the process is stopped
        WHEN GET /api/status is called
        THEN returns status with running=False.
        """
        # WHEN
        response = client.get("/api/status")

        # THEN
        assert response.status_code == 200
        data = response.json()
        assert data["running"] is False
        assert data["paused"] is False

    def test_returns_status_when_running(self, client, mock_process_manager, mock_beans_query):
        """
        GIVEN the process is running
        WHEN GET /api/status is called
        THEN returns status with running=True.
        """
        # GIVEN
        mock_process_manager.is_running = True
        mock_process_manager.state.status = ProcessStatus.RUNNING
        mock_process_manager.state.iteration = 5
        mock_process_manager.state.performer = "task"

        # WHEN
        response = client.get("/api/status")

        # THEN
        assert response.status_code == 200
        data = response.json()
        assert data["running"] is True
        assert data["iteration"] == 5
        assert data["performer"] == "task"

    def test_returns_bean_counts(self, client, mock_process_manager, mock_subprocess_run):
        """
        GIVEN beans CLI returns counts
        WHEN GET /api/status is called
        THEN includes bean counts in response.
        """
        # GIVEN
        def mock_beans(cmd, *args, **kwargs):
            query = cmd[2]  # The GraphQL query is the third argument
            if '"todo"' in query:
                return MagicMock(returncode=0, stdout='{"beans": [{"id": "1"}, {"id": "2"}]}')
            elif '"in-progress"' in query:
                return MagicMock(returncode=0, stdout='{"beans": [{"id": "3"}]}')
            elif '"completed"' in query:
                return MagicMock(returncode=0, stdout='{"beans": [{"id": "4"}, {"id": "5"}, {"id": "6"}]}')
            return MagicMock(returncode=0, stdout='{"beans": []}')

        mock_subprocess_run.side_effect = mock_beans

        # WHEN
        response = client.get("/api/status")

        # THEN
        assert response.status_code == 200
        data = response.json()
        assert data["beans_pending"] == 3  # 2 todo + 1 in-progress
        assert data["beans_completed"] == 3


class TestStartEndpoint:
    """Tests for POST /api/start endpoint."""

    def test_starts_process_successfully(self, client, mock_process_manager):
        """
        GIVEN the process is not running
        WHEN POST /api/start is called
        THEN starts the process and returns success.
        """
        # GIVEN
        with patch("ui.server.api.get_connection_manager") as mock_cm:
            mock_cm.return_value = MagicMock()

            # WHEN
            response = client.post("/api/start", json={})

            # THEN
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["pid"] == 12345

    def test_starts_with_custom_options(self, client, mock_process_manager):
        """
        GIVEN custom start options
        WHEN POST /api/start is called with options
        THEN passes options to process manager.
        """
        # GIVEN
        with patch("ui.server.api.get_connection_manager") as mock_cm:
            mock_cm.return_value = MagicMock()

            # WHEN
            response = client.post(
                "/api/start",
                json={
                    "max_iterations": 10,
                    "performer": "task",
                    "start_hour": 8,
                    "end_hour": 18,
                },
            )

            # THEN
            assert response.status_code == 200
            mock_process_manager.start.assert_called_once_with(
                max_iterations=10,
                performer="task",
                start_hour=8,
                end_hour=18,
            )

    def test_returns_error_when_already_running(self, client, mock_process_manager):
        """
        GIVEN the process is already running
        WHEN POST /api/start is called
        THEN returns error.
        """
        # GIVEN
        mock_process_manager.start = AsyncMock(return_value=(False, None, "Process is already running"))
        with patch("ui.server.api.get_connection_manager") as mock_cm:
            mock_cm.return_value = MagicMock()

            # WHEN
            response = client.post("/api/start", json={})

            # THEN
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert "already running" in data["error"]


class TestStopEndpoint:
    """Tests for POST /api/stop endpoint."""

    def test_stops_process_gracefully(self, client, mock_process_manager):
        """
        GIVEN the process is running
        WHEN POST /api/stop is called
        THEN stops gracefully.
        """
        # WHEN
        response = client.post("/api/stop", json={})

        # THEN
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        mock_process_manager.stop.assert_called_once_with(force=False)

    def test_force_stops_process(self, client, mock_process_manager):
        """
        GIVEN the process is running
        WHEN POST /api/stop is called with force=True
        THEN force stops the process.
        """
        # WHEN
        response = client.post("/api/stop", json={"force": True})

        # THEN
        assert response.status_code == 200
        mock_process_manager.stop.assert_called_once_with(force=True)


class TestPauseEndpoint:
    """Tests for POST /api/pause endpoint."""

    def test_pauses_running_process(self, client, mock_process_manager):
        """
        GIVEN the process is running
        WHEN POST /api/pause is called
        THEN pauses the process.
        """
        # WHEN
        response = client.post("/api/pause")

        # THEN
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        mock_process_manager.pause.assert_called_once()

    def test_returns_error_when_not_running(self, client, mock_process_manager):
        """
        GIVEN the process is not running
        WHEN POST /api/pause is called
        THEN returns error.
        """
        # GIVEN
        mock_process_manager.pause = AsyncMock(return_value=(False, "Process is not running"))

        # WHEN
        response = client.post("/api/pause")

        # THEN
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False


class TestResumeEndpoint:
    """Tests for POST /api/resume endpoint."""

    def test_resumes_paused_process(self, client, mock_process_manager):
        """
        GIVEN the process is paused
        WHEN POST /api/resume is called
        THEN resumes the process.
        """
        # WHEN
        response = client.post("/api/resume")

        # THEN
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        mock_process_manager.resume.assert_called_once()


class TestTasksEndpoint:
    """Tests for GET /api/tasks endpoint."""

    def test_returns_tasks_list(self, client, mock_subprocess_run):
        """
        GIVEN beans CLI returns tasks
        WHEN GET /api/tasks is called
        THEN returns formatted tasks.
        """
        # GIVEN
        mock_subprocess_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({
                "beans": [
                    {
                        "id": "task-1",
                        "title": "Implement feature",
                        "status": "todo",
                        "type": "feature",
                        "priority": "high",
                        "body": "Feature description",
                    },
                    {
                        "id": "task-2",
                        "title": "Fix bug",
                        "status": "in-progress",
                        "type": "bug",
                        "priority": "critical",
                        "body": None,
                    },
                ]
            }),
        )

        # WHEN
        response = client.get("/api/tasks")

        # THEN
        assert response.status_code == 200
        data = response.json()
        assert len(data["tasks"]) == 2
        assert data["tasks"][0]["id"] == "task-1"
        assert data["tasks"][0]["priority"] == "high"
        assert data["tasks"][1]["status"] == "in-progress"

    def test_returns_empty_on_error(self, client, mock_subprocess_run):
        """
        GIVEN beans CLI fails
        WHEN GET /api/tasks is called
        THEN returns empty list.
        """
        # GIVEN
        mock_subprocess_run.return_value = MagicMock(returncode=1, stdout="", stderr="Error")

        # WHEN
        response = client.get("/api/tasks")

        # THEN
        assert response.status_code == 200
        data = response.json()
        assert data["tasks"] == []


class TestPerformersEndpoint:
    """Tests for GET /api/performers endpoint."""

    def test_returns_performers_from_registry(self, client):
        """
        GIVEN autoclaude performers are available
        WHEN GET /api/performers is called
        THEN returns performers from registry.
        """
        # GIVEN - MagicMock's name parameter is special, so configure_mock is needed
        mock_performer1 = MagicMock()
        mock_performer1.configure_mock(name="task", emoji="📋", description="Task performer")
        mock_performer2 = MagicMock()
        mock_performer2.configure_mock(name="cleanup", emoji="🧹", description="Cleanup performer")
        mock_performers = [mock_performer1, mock_performer2]
        with patch(
            "autoclaude.performers.registry.get_all_performers",
            return_value=mock_performers,
        ):
            # WHEN
            response = client.get("/api/performers")

            # THEN
            assert response.status_code == 200
            data = response.json()
            assert len(data["performers"]) == 2

    def test_returns_fallback_when_import_fails(self, client):
        """
        GIVEN autoclaude module is not available
        WHEN GET /api/performers is called
        THEN returns fallback performers.
        """
        # GIVEN - the import will fail naturally if autoclaude is not installed

        # WHEN
        response = client.get("/api/performers")

        # THEN
        assert response.status_code == 200
        data = response.json()
        # Should have fallback performers
        assert len(data["performers"]) >= 1


class TestWhiteboardEndpoints:
    """Tests for whiteboard GET/POST endpoints."""

    def test_get_whiteboard_returns_content(self, client, tmp_path):
        """
        GIVEN a whiteboard file exists
        WHEN GET /api/whiteboard is called
        THEN returns content and last modified.
        """
        # GIVEN
        whiteboard_path = tmp_path / "WHITEBOARD.md"
        whiteboard_path.write_text("# Test Content\n\nHello world.")

        with patch("ui.server.api._get_whiteboard_path", return_value=str(whiteboard_path)):
            # WHEN
            response = client.get("/api/whiteboard")

            # THEN
            assert response.status_code == 200
            data = response.json()
            assert "# Test Content" in data["content"]
            assert data["last_modified"] is not None

    def test_get_whiteboard_handles_missing_file(self, client, tmp_path):
        """
        GIVEN whiteboard file doesn't exist
        WHEN GET /api/whiteboard is called
        THEN returns empty content.
        """
        # GIVEN
        whiteboard_path = tmp_path / "nonexistent.md"

        with patch("ui.server.api._get_whiteboard_path", return_value=str(whiteboard_path)):
            # WHEN
            response = client.get("/api/whiteboard")

            # THEN
            assert response.status_code == 200
            data = response.json()
            assert data["content"] == ""

    def test_post_whiteboard_updates_content(self, client, tmp_path):
        """
        GIVEN whiteboard file exists
        WHEN POST /api/whiteboard is called with new content
        THEN updates the file.
        """
        # GIVEN
        whiteboard_path = tmp_path / "WHITEBOARD.md"
        whiteboard_path.write_text("Old content")

        with patch("ui.server.api._get_whiteboard_path", return_value=str(whiteboard_path)):
            # WHEN
            response = client.post("/api/whiteboard", json={"content": "# New Content"})

            # THEN
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert whiteboard_path.read_text() == "# New Content"


class TestHistoryEndpoints:
    """Tests for history-related endpoints."""

    def test_get_history_returns_iterations(self, client, temp_db_path):
        """
        GIVEN iteration records exist
        WHEN GET /api/history is called
        THEN returns paginated iterations.
        """
        # GIVEN
        from ui.server.history import IterationRecord, IterationResult, init_db, save_iteration

        init_db()
        save_iteration(
            IterationRecord(
                id=None,
                iteration_number=1,
                performer_name="task",
                performer_emoji="📋",
                result=IterationResult.SUCCESS,
                tasks_before=5,
                tasks_after=4,
                duration_seconds=60.0,
                started_at=datetime(2024, 1, 15, 10, 0, 0),
                ended_at=datetime(2024, 1, 15, 10, 1, 0),
            )
        )

        # WHEN
        response = client.get("/api/history")

        # THEN
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["iterations"]) == 1
        assert data["iterations"][0]["performer_name"] == "task"

    def test_get_history_with_filters(self, client, temp_db_path):
        """
        GIVEN iteration records with different results
        WHEN GET /api/history is called with filters
        THEN returns filtered results.
        """
        # GIVEN
        from ui.server.history import IterationRecord, IterationResult, init_db, save_iteration

        init_db()
        for result in [IterationResult.SUCCESS, IterationResult.ERROR, IterationResult.SUCCESS]:
            save_iteration(
                IterationRecord(
                    id=None,
                    iteration_number=1,
                    performer_name="task",
                    performer_emoji="📋",
                    result=result,
                    tasks_before=5,
                    tasks_after=4,
                    duration_seconds=60.0,
                    started_at=datetime.now(),
                    ended_at=datetime.now(),
                )
            )

        # WHEN
        response = client.get("/api/history?result=error")

        # THEN
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    def test_get_history_stats(self, client, temp_db_path):
        """
        GIVEN iteration records exist
        WHEN GET /api/history/stats is called
        THEN returns statistics.
        """
        # GIVEN
        from ui.server.history import IterationRecord, IterationResult, init_db, save_iteration

        init_db()
        for _ in range(3):
            save_iteration(
                IterationRecord(
                    id=None,
                    iteration_number=1,
                    performer_name="task",
                    performer_emoji="📋",
                    result=IterationResult.SUCCESS,
                    tasks_before=5,
                    tasks_after=4,
                    duration_seconds=60.0,
                    started_at=datetime.now(),
                    ended_at=datetime.now(),
                )
            )

        # WHEN
        response = client.get("/api/history/stats")

        # THEN
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert data["success_count"] == 3

    def test_get_history_performers(self, client, temp_db_path):
        """
        GIVEN iteration records with different performers
        WHEN GET /api/history/performers is called
        THEN returns unique performer names.
        """
        # GIVEN
        from ui.server.history import IterationRecord, IterationResult, init_db, save_iteration

        init_db()
        for name in ["task", "cleanup", "task"]:
            save_iteration(
                IterationRecord(
                    id=None,
                    iteration_number=1,
                    performer_name=name,
                    performer_emoji="",
                    result=IterationResult.SUCCESS,
                    tasks_before=1,
                    tasks_after=1,
                    duration_seconds=1.0,
                    started_at=datetime.now(),
                    ended_at=datetime.now(),
                )
            )

        # WHEN
        response = client.get("/api/history/performers")

        # THEN
        assert response.status_code == 200
        data = response.json()
        assert sorted(data["performers"]) == ["cleanup", "task"]
