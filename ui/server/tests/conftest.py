"""Pytest configuration and fixtures for UI server tests."""

import os
import tempfile
from collections.abc import Iterator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def temp_db_path(tmp_path) -> Iterator[str]:
    """
    GIVEN a temporary directory
    WHEN setting AUTOCLAUDE_DATA_DIR environment variable
    THEN provides an isolated database path for tests.
    """
    db_path = str(tmp_path)
    with patch.dict(os.environ, {"AUTOCLAUDE_DATA_DIR": db_path}):
        yield db_path


@pytest.fixture
def temp_whiteboard(tmp_path) -> Iterator[str]:
    """
    GIVEN a temporary directory
    WHEN a whiteboard file is needed
    THEN provides an isolated whiteboard path for tests.
    """
    whiteboard_path = tmp_path / "WHITEBOARD.md"
    whiteboard_path.write_text("# Test Whiteboard\n\nInitial content.")
    yield str(whiteboard_path)


@pytest.fixture
def mock_subprocess_run():
    """
    GIVEN the need to mock subprocess.run
    WHEN testing code that calls external CLI commands
    THEN provides a mock that can be configured per test.
    """
    with patch("subprocess.run") as mock_run:
        yield mock_run


@pytest.fixture
def mock_beans_query(mock_subprocess_run):
    """
    GIVEN a mocked subprocess.run
    WHEN testing code that queries beans CLI
    THEN provides a pre-configured mock returning empty beans list.
    """
    mock_subprocess_run.return_value = MagicMock(
        returncode=0,
        stdout='{"beans": []}',
        stderr="",
    )
    return mock_subprocess_run


@pytest.fixture
def mock_websocket():
    """
    GIVEN the need to test WebSocket functionality
    WHEN testing websocket connections
    THEN provides a mock WebSocket object.
    """
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_text = AsyncMock()
    ws.receive_text = AsyncMock()
    ws.close = AsyncMock()
    return ws
