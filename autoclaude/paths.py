"""Path utilities for autoclaude."""

import subprocess
from pathlib import Path


def get_git_root() -> Path | None:
    """Get the root directory of the git repository, or None if not in a git repo."""
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return Path(result.stdout.strip())
    return None


def get_project_root() -> Path:
    """Get the project root directory (git root or current working directory)."""
    return get_git_root() or Path.cwd()


def get_whiteboard_path() -> Path:
    """Get the path to WHITEBOARD.md in the project root."""
    return get_project_root() / "WHITEBOARD.md"
