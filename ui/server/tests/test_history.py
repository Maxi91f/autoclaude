"""Tests for history.py SQLite operations."""

import os
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from ui.server.history import (
    IterationRecord,
    IterationResult,
    _get_db_path,
    get_iterations,
    get_performers,
    get_stats,
    init_db,
    save_iteration,
)


class TestGetDbPath:
    """Tests for _get_db_path function."""

    def test_uses_default_path_when_env_not_set(self, tmp_path):
        """
        GIVEN no AUTOCLAUDE_DATA_DIR environment variable
        WHEN _get_db_path is called
        THEN returns path in ~/.autoclaude directory.
        """
        # GIVEN
        with patch.dict(os.environ, {}, clear=True):
            with patch("os.path.expanduser", return_value=str(tmp_path)):
                # WHEN
                path = _get_db_path()

                # THEN
                assert "history.db" in path

    def test_uses_env_var_when_set(self, tmp_path):
        """
        GIVEN AUTOCLAUDE_DATA_DIR is set
        WHEN _get_db_path is called
        THEN returns path in the specified directory.
        """
        # GIVEN
        custom_dir = str(tmp_path / "custom")
        with patch.dict(os.environ, {"AUTOCLAUDE_DATA_DIR": custom_dir}):
            # WHEN
            path = _get_db_path()

            # THEN
            assert path == os.path.join(custom_dir, "history.db")


class TestInitDb:
    """Tests for init_db function."""

    def test_creates_iterations_table(self, temp_db_path):
        """
        GIVEN a fresh database
        WHEN init_db is called
        THEN creates the iterations table with correct schema.
        """
        # GIVEN/WHEN - init_db is called on module import, reinitialize
        init_db()

        # THEN - save and retrieve should work
        record = IterationRecord(
            id=None,
            iteration_number=1,
            performer_name="test",
            performer_emoji="🧪",
            result=IterationResult.SUCCESS,
            tasks_before=5,
            tasks_after=4,
            duration_seconds=10.5,
            started_at=datetime.now(),
            ended_at=datetime.now(),
        )
        record_id = save_iteration(record)
        assert record_id > 0

    def test_is_idempotent(self, temp_db_path):
        """
        GIVEN init_db has been called
        WHEN init_db is called again
        THEN does not raise an error.
        """
        # GIVEN
        init_db()

        # WHEN/THEN - should not raise
        init_db()
        init_db()


class TestSaveIteration:
    """Tests for save_iteration function."""

    def test_saves_record_and_returns_id(self, temp_db_path):
        """
        GIVEN an IterationRecord
        WHEN save_iteration is called
        THEN saves the record and returns the ID.
        """
        # GIVEN
        init_db()
        record = IterationRecord(
            id=None,
            iteration_number=1,
            performer_name="task",
            performer_emoji="📋",
            result=IterationResult.SUCCESS,
            tasks_before=3,
            tasks_after=2,
            duration_seconds=120.5,
            started_at=datetime(2024, 1, 15, 10, 0, 0),
            ended_at=datetime(2024, 1, 15, 10, 2, 0),
        )

        # WHEN
        record_id = save_iteration(record)

        # THEN
        assert record_id > 0

    def test_saves_record_with_error_message(self, temp_db_path):
        """
        GIVEN an IterationRecord with an error message
        WHEN save_iteration is called
        THEN saves the error message correctly.
        """
        # GIVEN
        init_db()
        record = IterationRecord(
            id=None,
            iteration_number=2,
            performer_name="deploy",
            performer_emoji="🚀",
            result=IterationResult.ERROR,
            tasks_before=1,
            tasks_after=1,
            duration_seconds=5.0,
            started_at=datetime(2024, 1, 15, 11, 0, 0),
            ended_at=datetime(2024, 1, 15, 11, 0, 5),
            error_message="Deploy script not found",
        )

        # WHEN
        save_iteration(record)
        records, _ = get_iterations()

        # THEN
        assert len(records) == 1
        assert records[0].error_message == "Deploy script not found"


class TestGetIterations:
    """Tests for get_iterations function."""

    @pytest.fixture
    def sample_records(self, temp_db_path):
        """Create sample records for testing."""
        init_db()
        records = [
            IterationRecord(
                id=None,
                iteration_number=i,
                performer_name="task" if i % 2 == 0 else "cleanup",
                performer_emoji="📋" if i % 2 == 0 else "🧹",
                result=IterationResult.SUCCESS if i % 3 != 0 else IterationResult.NO_PROGRESS,
                tasks_before=10 - i,
                tasks_after=9 - i,
                duration_seconds=60.0 + i * 10,
                started_at=datetime(2024, 1, 15, 10, i, 0),
                ended_at=datetime(2024, 1, 15, 10, i + 1, 0),
            )
            for i in range(1, 11)
        ]
        for r in records:
            save_iteration(r)
        return records

    def test_returns_records_with_pagination(self, sample_records):
        """
        GIVEN multiple records in database
        WHEN get_iterations is called with limit
        THEN returns limited records and total count.
        """
        # WHEN
        records, total = get_iterations(limit=5)

        # THEN
        assert len(records) == 5
        assert total == 10

    def test_returns_records_with_offset(self, sample_records):
        """
        GIVEN multiple records in database
        WHEN get_iterations is called with offset
        THEN skips the specified number of records.
        """
        # WHEN
        records, total = get_iterations(limit=5, offset=5)

        # THEN
        assert len(records) == 5
        assert total == 10

    def test_filters_by_result(self, sample_records):
        """
        GIVEN records with different results
        WHEN get_iterations is called with result filter
        THEN returns only matching records.
        """
        # WHEN
        records, total = get_iterations(result_filter=IterationResult.NO_PROGRESS)

        # THEN - iterations 3, 6, 9 have no_progress (i % 3 == 0)
        assert total == 3
        for r in records:
            assert r.result == IterationResult.NO_PROGRESS

    def test_filters_by_performer(self, sample_records):
        """
        GIVEN records with different performers
        WHEN get_iterations is called with performer filter
        THEN returns only matching records.
        """
        # WHEN
        records, total = get_iterations(performer_filter="task")

        # THEN - even iterations are "task"
        assert total == 5
        for r in records:
            assert r.performer_name == "task"

    def test_combines_filters(self, sample_records):
        """
        GIVEN records with various properties
        WHEN get_iterations is called with multiple filters
        THEN applies all filters.
        """
        # WHEN
        records, total = get_iterations(
            result_filter=IterationResult.SUCCESS,
            performer_filter="task",
        )

        # THEN - even iterations that are also successful
        for r in records:
            assert r.performer_name == "task"
            assert r.result == IterationResult.SUCCESS

    def test_orders_by_ended_at_desc(self, sample_records):
        """
        GIVEN multiple records
        WHEN get_iterations is called
        THEN returns records ordered by ended_at descending.
        """
        # WHEN
        records, _ = get_iterations()

        # THEN
        for i in range(len(records) - 1):
            assert records[i].ended_at >= records[i + 1].ended_at

    def test_returns_empty_when_no_matches(self, temp_db_path):
        """
        GIVEN an empty database
        WHEN get_iterations is called
        THEN returns empty list and zero count.
        """
        # GIVEN
        init_db()

        # WHEN
        records, total = get_iterations()

        # THEN
        assert records == []
        assert total == 0


class TestGetPerformers:
    """Tests for get_performers function."""

    def test_returns_unique_performers(self, temp_db_path):
        """
        GIVEN records with different performers
        WHEN get_performers is called
        THEN returns unique performer names.
        """
        # GIVEN
        init_db()
        for name in ["task", "cleanup", "task", "deploy", "cleanup"]:
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
        performers = get_performers()

        # THEN
        assert sorted(performers) == ["cleanup", "deploy", "task"]

    def test_returns_empty_when_no_records(self, temp_db_path):
        """
        GIVEN an empty database
        WHEN get_performers is called
        THEN returns empty list.
        """
        # GIVEN
        init_db()

        # WHEN
        performers = get_performers()

        # THEN
        assert performers == []


class TestGetStats:
    """Tests for get_stats function."""

    def test_returns_correct_counts(self, temp_db_path):
        """
        GIVEN records with different results
        WHEN get_stats is called
        THEN returns correct counts for each result type.
        """
        # GIVEN
        init_db()
        result_counts = {
            IterationResult.SUCCESS: 5,
            IterationResult.NO_PROGRESS: 3,
            IterationResult.ERROR: 2,
        }
        for result, count in result_counts.items():
            for _ in range(count):
                save_iteration(
                    IterationRecord(
                        id=None,
                        iteration_number=1,
                        performer_name="test",
                        performer_emoji="",
                        result=result,
                        tasks_before=1,
                        tasks_after=1,
                        duration_seconds=60.0,
                        started_at=datetime.now(),
                        ended_at=datetime.now(),
                    )
                )

        # WHEN
        stats = get_stats()

        # THEN
        assert stats["total"] == 10
        assert stats["success_count"] == 5
        assert stats["no_progress_count"] == 3
        assert stats["error_count"] == 2

    def test_calculates_average_duration(self, temp_db_path):
        """
        GIVEN records with different durations
        WHEN get_stats is called
        THEN returns correct average duration.
        """
        # GIVEN
        init_db()
        durations = [30.0, 60.0, 90.0]  # avg = 60
        for duration in durations:
            save_iteration(
                IterationRecord(
                    id=None,
                    iteration_number=1,
                    performer_name="test",
                    performer_emoji="",
                    result=IterationResult.SUCCESS,
                    tasks_before=1,
                    tasks_after=1,
                    duration_seconds=duration,
                    started_at=datetime.now(),
                    ended_at=datetime.now(),
                )
            )

        # WHEN
        stats = get_stats()

        # THEN
        assert stats["avg_duration_seconds"] == 60.0

    def test_returns_zeros_when_empty(self, temp_db_path):
        """
        GIVEN an empty database
        WHEN get_stats is called
        THEN returns zero for all counts.
        """
        # GIVEN
        init_db()

        # WHEN
        stats = get_stats()

        # THEN
        assert stats["total"] == 0
        assert stats["success_count"] == 0
        assert stats["no_progress_count"] == 0
        assert stats["error_count"] == 0
        assert stats["avg_duration_seconds"] == 0
