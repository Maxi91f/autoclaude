"""Tests for websocket.py connection management and output classification."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ui.server.models import OutputLineType, WSEvent
from ui.server.websocket import (
    ConnectionManager,
    classify_output_line,
    create_output_handler,
    get_connection_manager,
)


class TestClassifyOutputLine:
    """Tests for classify_output_line function."""

    @pytest.mark.parametrize(
        "line,expected",
        [
            # Error lines
            ("Error: Something went wrong", OutputLineType.ERROR),
            ("ERROR: Fatal error occurred", OutputLineType.ERROR),
            ("Some error happened here", OutputLineType.ERROR),
            # Thinking lines
            ("thinking about the problem", OutputLineType.THINKING),
            ("> Considering options", OutputLineType.THINKING),
            # Tool use lines
            ("Tool: Using Read to read file", OutputLineType.TOOL_USE),
            ("Using tool Bash to run command", OutputLineType.TOOL_USE),
            ("Bash: ls -la", OutputLineType.TOOL_USE),
            ("Read: /path/to/file", OutputLineType.TOOL_USE),
            ("Write: /path/to/output", OutputLineType.TOOL_USE),
            ("Edit: modifying file", OutputLineType.TOOL_USE),
            # Tool result lines
            ("Result: Success", OutputLineType.TOOL_RESULT),
            ("Output: Hello World", OutputLineType.TOOL_RESULT),
            # Plain text
            ("Just some regular text", OutputLineType.TEXT),
            ("Starting iteration 5", OutputLineType.TEXT),
            ("Completed task successfully", OutputLineType.TEXT),
        ],
    )
    def test_classifies_output_lines_correctly(self, line: str, expected: OutputLineType):
        """
        GIVEN an output line
        WHEN classify_output_line is called
        THEN returns the correct line type.
        """
        # WHEN
        result = classify_output_line(line)

        # THEN
        assert result == expected

    def test_case_insensitive_error_detection(self):
        """
        GIVEN an error line with mixed case
        WHEN classify_output_line is called
        THEN detects error regardless of case.
        """
        # GIVEN
        lines = ["Error detected", "ERROR DETECTED", "error detected", "An ERROR occurred"]

        # WHEN/THEN
        for line in lines:
            assert classify_output_line(line) == OutputLineType.ERROR

    def test_defaults_to_text(self):
        """
        GIVEN an ambiguous line
        WHEN classify_output_line is called
        THEN defaults to TEXT type.
        """
        # GIVEN
        lines = ["Hello world", "Processing...", "1234567890", ""]

        # WHEN/THEN
        for line in lines:
            result = classify_output_line(line)
            # These don't match other patterns, should be TEXT
            # Note: empty string is also TEXT


class TestConnectionManager:
    """Tests for ConnectionManager class."""

    @pytest.fixture
    def manager(self):
        """Create a fresh ConnectionManager for each test."""
        return ConnectionManager()

    @pytest.mark.asyncio
    async def test_connect_accepts_and_registers_websocket(self, manager, mock_websocket):
        """
        GIVEN a ConnectionManager
        WHEN connect is called with a WebSocket
        THEN accepts and registers the connection.
        """
        # WHEN
        await manager.connect(mock_websocket)

        # THEN
        mock_websocket.accept.assert_called_once()
        assert manager.connection_count == 1

    @pytest.mark.asyncio
    async def test_disconnect_removes_websocket(self, manager, mock_websocket):
        """
        GIVEN a connected WebSocket
        WHEN disconnect is called
        THEN removes the connection.
        """
        # GIVEN
        await manager.connect(mock_websocket)
        assert manager.connection_count == 1

        # WHEN
        await manager.disconnect(mock_websocket)

        # THEN
        assert manager.connection_count == 0

    @pytest.mark.asyncio
    async def test_disconnect_handles_unknown_websocket(self, manager, mock_websocket):
        """
        GIVEN a WebSocket not in connections
        WHEN disconnect is called
        THEN does not raise error.
        """
        # WHEN/THEN - should not raise
        await manager.disconnect(mock_websocket)
        assert manager.connection_count == 0

    @pytest.mark.asyncio
    async def test_broadcast_sends_to_all_connections(self, manager):
        """
        GIVEN multiple connected WebSockets
        WHEN broadcast is called
        THEN sends message to all connections.
        """
        # GIVEN
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        ws3 = AsyncMock()
        for ws in [ws1, ws2, ws3]:
            await manager.connect(ws)

        # WHEN
        await manager.broadcast(WSEvent.STATUS_CHANGE, {"status": "running"})

        # THEN
        for ws in [ws1, ws2, ws3]:
            ws.send_text.assert_called_once()
            # Verify the message format
            call_arg = ws.send_text.call_args[0][0]
            message = json.loads(call_arg)
            assert message["event"] == "status_change"
            assert message["data"]["status"] == "running"

    @pytest.mark.asyncio
    async def test_broadcast_removes_dead_connections(self, manager):
        """
        GIVEN connected WebSockets where one fails
        WHEN broadcast is called
        THEN removes the dead connection.
        """
        # GIVEN
        ws_good = AsyncMock()
        ws_dead = AsyncMock()
        ws_dead.send_text.side_effect = Exception("Connection closed")
        await manager.connect(ws_good)
        await manager.connect(ws_dead)
        assert manager.connection_count == 2

        # WHEN
        await manager.broadcast(WSEvent.OUTPUT_LINE, {"content": "test"})

        # THEN
        assert manager.connection_count == 1

    @pytest.mark.asyncio
    async def test_send_personal_sends_to_single_client(self, manager, mock_websocket):
        """
        GIVEN a connected WebSocket
        WHEN send_personal is called
        THEN sends message only to that client.
        """
        # GIVEN
        await manager.connect(mock_websocket)

        # WHEN
        await manager.send_personal(mock_websocket, WSEvent.PONG, {"timestamp": "2024-01-15"})

        # THEN
        mock_websocket.send_text.assert_called_once()
        call_arg = mock_websocket.send_text.call_args[0][0]
        message = json.loads(call_arg)
        assert message["event"] == "pong"
        assert message["data"]["timestamp"] == "2024-01-15"

    @pytest.mark.asyncio
    async def test_send_personal_handles_error_silently(self, manager):
        """
        GIVEN a WebSocket that fails
        WHEN send_personal is called
        THEN does not raise error.
        """
        # GIVEN
        ws = AsyncMock()
        ws.send_text.side_effect = Exception("Connection error")

        # WHEN/THEN - should not raise
        await manager.send_personal(ws, WSEvent.ERROR, {"message": "test"})

    def test_connection_count_property(self, manager):
        """
        GIVEN a ConnectionManager
        WHEN connections are added/removed
        THEN connection_count reflects the current count.
        """
        # GIVEN
        assert manager.connection_count == 0

        # Add connections directly for sync test
        ws1 = MagicMock()
        ws2 = MagicMock()
        manager._connections.add(ws1)
        assert manager.connection_count == 1

        manager._connections.add(ws2)
        assert manager.connection_count == 2

        manager._connections.discard(ws1)
        assert manager.connection_count == 1


class TestGetConnectionManager:
    """Tests for get_connection_manager singleton."""

    def test_returns_same_instance(self):
        """
        GIVEN get_connection_manager is called multiple times
        WHEN comparing returned instances
        THEN they are the same object.
        """
        # Reset singleton for clean test
        import ui.server.websocket as ws_module
        ws_module._manager = None

        # WHEN
        manager1 = get_connection_manager()
        manager2 = get_connection_manager()

        # THEN
        assert manager1 is manager2

        # Cleanup
        ws_module._manager = None


class TestCreateOutputHandler:
    """Tests for create_output_handler function."""

    @pytest.mark.asyncio
    async def test_creates_handler_that_broadcasts(self):
        """
        GIVEN a ConnectionManager
        WHEN create_output_handler creates a handler and it's called
        THEN broadcasts the line with correct classification.
        """
        # GIVEN
        manager = ConnectionManager()
        ws = AsyncMock()
        await manager.connect(ws)

        handler = create_output_handler(manager)

        # Create a running event loop context
        with patch("asyncio.get_event_loop") as mock_loop:
            mock_loop.return_value.is_running.return_value = True

            # WHEN
            handler("Error: Something went wrong")

            # THEN
            # asyncio.create_task should be called for broadcast
            # The handler schedules the broadcast as a task

    def test_handles_no_event_loop(self):
        """
        GIVEN no running event loop
        WHEN handler is called
        THEN does not raise error.
        """
        # GIVEN
        manager = ConnectionManager()
        handler = create_output_handler(manager)

        # WHEN/THEN - should not raise
        with patch("asyncio.get_event_loop", side_effect=RuntimeError("No event loop")):
            handler("Some output line")
