"""History storage for iteration records using SQLite."""

import os
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Iterator


class IterationResult(str, Enum):
    """Result of an iteration."""

    SUCCESS = "success"
    NO_PROGRESS = "no_progress"
    ERROR = "error"
    RATE_LIMITED = "rate_limited"
    CANCELLED = "cancelled"


@dataclass
class IterationRecord:
    """Record of a single iteration."""

    id: int | None
    iteration_number: int
    performer_name: str
    performer_emoji: str
    result: IterationResult
    tasks_before: int
    tasks_after: int
    duration_seconds: float
    started_at: datetime
    ended_at: datetime
    error_message: str | None = None


def _get_db_path() -> str:
    """Get the path to the history database."""
    data_dir = os.environ.get("AUTOCLAUDE_DATA_DIR", os.path.expanduser("~/.autoclaude"))
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "history.db")


@contextmanager
def _get_connection() -> Iterator[sqlite3.Connection]:
    """Get a database connection with row factory."""
    conn = sqlite3.connect(_get_db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    """Initialize the database schema."""
    with _get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS iterations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                iteration_number INTEGER NOT NULL,
                performer_name TEXT NOT NULL,
                performer_emoji TEXT NOT NULL DEFAULT '',
                result TEXT NOT NULL,
                tasks_before INTEGER NOT NULL DEFAULT 0,
                tasks_after INTEGER NOT NULL DEFAULT 0,
                duration_seconds REAL NOT NULL DEFAULT 0,
                started_at TEXT NOT NULL,
                ended_at TEXT NOT NULL,
                error_message TEXT
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_iterations_ended_at
            ON iterations(ended_at DESC)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_iterations_result
            ON iterations(result)
        """)
        conn.commit()


def save_iteration(record: IterationRecord) -> int:
    """Save an iteration record to the database.

    Returns the ID of the inserted record.
    """
    with _get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO iterations (
                iteration_number, performer_name, performer_emoji, result,
                tasks_before, tasks_after, duration_seconds,
                started_at, ended_at, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.iteration_number,
                record.performer_name,
                record.performer_emoji,
                record.result.value,
                record.tasks_before,
                record.tasks_after,
                record.duration_seconds,
                record.started_at.isoformat(),
                record.ended_at.isoformat(),
                record.error_message,
            ),
        )
        conn.commit()
        return cursor.lastrowid or 0


def get_iterations(
    limit: int = 50,
    offset: int = 0,
    result_filter: IterationResult | None = None,
    performer_filter: str | None = None,
) -> tuple[list[IterationRecord], int]:
    """Get iteration records with pagination.

    Returns: (records, total_count)
    """
    with _get_connection() as conn:
        # Build query
        where_clauses = []
        params: list = []

        if result_filter:
            where_clauses.append("result = ?")
            params.append(result_filter.value)

        if performer_filter:
            where_clauses.append("performer_name = ?")
            params.append(performer_filter)

        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        # Get total count
        count_result = conn.execute(
            f"SELECT COUNT(*) as cnt FROM iterations {where_sql}",
            params,
        ).fetchone()
        total_count = count_result["cnt"] if count_result else 0

        # Get records
        query_params = params + [limit, offset]
        rows = conn.execute(
            f"""
            SELECT * FROM iterations
            {where_sql}
            ORDER BY ended_at DESC
            LIMIT ? OFFSET ?
            """,
            query_params,
        ).fetchall()

        records = [
            IterationRecord(
                id=row["id"],
                iteration_number=row["iteration_number"],
                performer_name=row["performer_name"],
                performer_emoji=row["performer_emoji"],
                result=IterationResult(row["result"]),
                tasks_before=row["tasks_before"],
                tasks_after=row["tasks_after"],
                duration_seconds=row["duration_seconds"],
                started_at=datetime.fromisoformat(row["started_at"]),
                ended_at=datetime.fromisoformat(row["ended_at"]),
                error_message=row["error_message"],
            )
            for row in rows
        ]

        return records, total_count


def get_performers() -> list[str]:
    """Get list of unique performer names from history."""
    with _get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT performer_name FROM iterations ORDER BY performer_name"
        ).fetchall()
        return [row["performer_name"] for row in rows]


def get_stats() -> dict:
    """Get summary statistics."""
    with _get_connection() as conn:
        result = conn.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN result = 'success' THEN 1 ELSE 0 END) as success_count,
                SUM(CASE WHEN result = 'no_progress' THEN 1 ELSE 0 END) as no_progress_count,
                SUM(CASE WHEN result = 'error' THEN 1 ELSE 0 END) as error_count,
                AVG(duration_seconds) as avg_duration
            FROM iterations
        """).fetchone()

        return {
            "total": result["total"] or 0,
            "success_count": result["success_count"] or 0,
            "no_progress_count": result["no_progress_count"] or 0,
            "error_count": result["error_count"] or 0,
            "avg_duration_seconds": result["avg_duration"] or 0,
        }


# Initialize database on module import
init_db()
