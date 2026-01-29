"""Scoring functions for lab experiments."""

import re
import subprocess
from dataclasses import dataclass, field


@dataclass
class ScoreResult:
    score: float  # 0.0 to 1.0
    passed: bool
    details: dict[str, any] = field(default_factory=dict)


@dataclass
class BeanScore:
    count: int
    quality_score: float  # 0.0 to 1.0
    beans: list[dict]
    quality_details: list[dict]


def score_contains(output: str, patterns: list[str]) -> ScoreResult:
    """Score based on whether output contains expected patterns."""
    details = {}
    for pattern in patterns:
        details[pattern] = pattern.lower() in output.lower()

    passed_count = sum(details.values())
    score = passed_count / len(patterns) if patterns else 1.0

    return ScoreResult(
        score=score,
        passed=score >= 1.0,
        details=details,
    )


def score_regex(output: str, patterns: list[str]) -> ScoreResult:
    """Score based on regex pattern matches."""
    details = {}
    for pattern in patterns:
        details[pattern] = bool(re.search(pattern, output, re.MULTILINE))

    passed_count = sum(details.values())
    score = passed_count / len(patterns) if patterns else 1.0

    return ScoreResult(
        score=score,
        passed=score >= 1.0,
        details=details,
    )


def score_code_quality(output: str) -> ScoreResult:
    """Score code quality indicators."""
    checks = {
        "has_docstring": '"""' in output or "'''" in output,
        "has_type_hints": "->" in output or ": str" in output or ": int" in output,
        "has_error_handling": "raise" in output or "try:" in output,
        "no_syntax_errors": "SyntaxError" not in output,
    }

    passed_count = sum(checks.values())
    score = passed_count / len(checks)

    return ScoreResult(
        score=score,
        passed=score >= 0.75,
        details=checks,
    )


def get_beans_by_tag(tag: str) -> list[dict]:
    """Query beans with specific tag."""
    import json
    from pathlib import Path

    lab_dir = Path(__file__).parent

    query = f'{{ beans(filter: {{ tags: ["{tag}"] }}) {{ id title status type priority body createdAt }} }}'
    result = subprocess.run(
        ["beans", "query", "--json", query],
        capture_output=True,
        text=True,
        cwd=lab_dir,
    )
    if result.returncode != 0:
        return []

    try:
        data = json.loads(result.stdout)
        return data.get("beans", [])
    except json.JSONDecodeError:
        return []


def delete_beans_by_tag(tag: str) -> int:
    """Delete all beans with specific tag. Returns count deleted."""
    from pathlib import Path

    lab_dir = Path(__file__).parent
    beans = get_beans_by_tag(tag)
    for bean in beans:
        subprocess.run(
            ["beans", "delete", bean["id"], "--force"],
            capture_output=True,
            cwd=lab_dir,
        )
    return len(beans)


def score_bean_quality(bean: dict) -> dict:
    """Score individual bean quality."""
    title = bean.get("title", "")
    body = bean.get("body", "")

    checks = {
        # Title quality
        "title_not_generic": not any(
            g in title.lower()
            for g in ["fix bug", "issue", "problem", "todo", "update"]
        ),
        "title_specific": len(title.split()) >= 3,
        "title_not_too_long": len(title) <= 80,
        # Body quality
        "has_body": len(body) > 20,
        "body_has_context": any(
            w in body.lower() for w in ["because", "when", "where", "user", "expected"]
        ),
        "body_actionable": any(
            w in body.lower() for w in ["should", "need", "must", "change", "add", "fix"]
        ),
        # Metadata
        "has_priority": bean.get("priority") is not None,
        "has_type": bean.get("type") in ["bug", "feature", "task", "improvement"],
    }

    score = sum(checks.values()) / len(checks)
    return {
        "bean_id": bean.get("id"),
        "title": title[:50],
        "score": score,
        "checks": checks,
    }


def score_beans(tag: str) -> BeanScore:
    """Score all beans with specific tag for quantity and quality."""
    beans = get_beans_by_tag(tag)

    if not beans:
        return BeanScore(
            count=0,
            quality_score=0.0,
            beans=[],
            quality_details=[],
        )

    quality_details = [score_bean_quality(b) for b in beans]
    avg_quality = sum(d["score"] for d in quality_details) / len(quality_details)

    return BeanScore(
        count=len(beans),
        quality_score=avg_quality,
        beans=beans,
        quality_details=quality_details,
    )


def score_custom(output: str, fn: callable) -> ScoreResult:
    """Score using a custom function that returns (score, details)."""
    score, details = fn(output)
    return ScoreResult(
        score=score,
        passed=score >= 0.8,
        details=details,
    )
