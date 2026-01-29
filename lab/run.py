#!/usr/bin/env python3
"""Lab runner - execute prompts and score results."""

import argparse
import subprocess
import sys
from pathlib import Path

from scoring import (
    BeanScore,
    delete_beans_by_tag,
    score_beans,
)

LAB_DIR = Path(__file__).parent


def load_prompt(prompt_path: Path, tag: str) -> str:
    """Load prompt from markdown file and substitute tag."""
    content = prompt_path.read_text()
    return content.replace("{tag}", tag)


def run_claude(prompt: str) -> int:
    """Run claude with prompt and return exit code."""
    result = subprocess.run(
        [
            "claude",
            "-p",
            "--dangerously-skip-permissions",
        ],
        cwd=LAB_DIR,
        input=prompt,
        text=True,
    )
    return result.returncode


def generate_tag(prompt_path: Path) -> str:
    """Generate a unique tag from prompt filename."""
    # e.g., ui_review_structured.md -> lab-structured
    name = prompt_path.stem.replace("ui_review_", "").replace("_", "-")
    return f"lab-{name}"


def run_experiment(prompt_path: Path) -> BeanScore:
    """Run a single experiment."""
    tag = generate_tag(prompt_path)

    print(f"\n{'='*60}")
    print(f"Running: {prompt_path.name} (tag: {tag})")
    print(f"{'='*60}\n")

    prompt = load_prompt(prompt_path, tag)
    exitcode = run_claude(prompt)

    print(f"\n{'='*60}")
    print(f"Exit code: {exitcode}")

    result = score_beans(tag)
    print(f"\nBeans created: {result.count}")
    print(f"Quality score: {result.quality_score:.2%}")
    print("\nPer-bean quality:")
    for detail in result.quality_details:
        status = "✓" if detail["score"] >= 0.7 else "✗"
        print(f"  {status} [{detail['score']:.0%}] {detail['title']}...")

    return result


def compare_prompts(prompt_a: Path, prompt_b: Path) -> None:
    """Compare two prompts using beans scoring."""
    results = {}
    tags = {
        "A": generate_tag(prompt_a),
        "B": generate_tag(prompt_b),
    }

    # Clean up all tags before starting
    for tag in tags.values():
        deleted = delete_beans_by_tag(tag)
        if deleted:
            print(f"(Cleaned up {deleted} beans with tag '{tag}')")

    for label, prompt_path in [("A", prompt_a), ("B", prompt_b)]:
        print(f"\n{'#'*60}")
        print(f"# PROMPT {label}: {prompt_path.name}")
        print(f"{'#'*60}")

        result = run_experiment(prompt_path)
        results[label] = result

    # Summary
    print(f"\n{'='*60}")
    print("COMPARISON SUMMARY")
    print(f"{'='*60}")

    a, b = results["A"], results["B"]

    print(f"\n{'Metric':<25} {'Prompt A':>15} {'Prompt B':>15} {'Winner':>10}")
    print("-" * 65)

    # Count
    count_winner = "A" if a.count > b.count else ("B" if b.count > a.count else "Tie")
    print(f"{'Beans created':<25} {a.count:>15} {b.count:>15} {count_winner:>10}")

    # Quality
    qual_winner = (
        "A"
        if a.quality_score > b.quality_score
        else ("B" if b.quality_score > a.quality_score else "Tie")
    )
    print(
        f"{'Quality score':<25} {a.quality_score:>14.1%} {b.quality_score:>14.1%} {qual_winner:>10}"
    )

    # Combined score (count * quality)
    combined_a = a.count * a.quality_score
    combined_b = b.count * b.quality_score
    combined_winner = (
        "A" if combined_a > combined_b else ("B" if combined_b > combined_a else "Tie")
    )
    print(
        f"{'Combined (count×quality)':<25} {combined_a:>15.2f} {combined_b:>15.2f} {combined_winner:>10}"
    )

    print(f"\n🏆 Overall winner: Prompt {combined_winner}")


def main():
    parser = argparse.ArgumentParser(description="Run lab experiments")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Run command
    run_parser = subparsers.add_parser("run", help="Run a single prompt")
    run_parser.add_argument("prompt", type=Path, help="Path to prompt markdown file")

    # Compare command
    compare_parser = subparsers.add_parser("compare", help="Compare two prompts")
    compare_parser.add_argument("prompt_a", type=Path, help="First prompt")
    compare_parser.add_argument("prompt_b", type=Path, help="Second prompt")

    # Clean command
    clean_parser = subparsers.add_parser("clean", help="Delete beans by tag")
    clean_parser.add_argument("tag", help="Tag to clean (e.g., lab-structured)")

    args = parser.parse_args()

    if args.command == "run":
        if not args.prompt.exists():
            print(f"Error: Prompt file not found: {args.prompt}")
            sys.exit(1)

        # Clean up before starting
        tag = generate_tag(args.prompt)
        deleted = delete_beans_by_tag(tag)
        if deleted:
            print(f"(Cleaned up {deleted} beans with tag '{tag}')")

        result = run_experiment(args.prompt)
        sys.exit(0 if result.count > 0 else 1)

    elif args.command == "compare":
        if not args.prompt_a.exists():
            print(f"Error: Prompt file not found: {args.prompt_a}")
            sys.exit(1)
        if not args.prompt_b.exists():
            print(f"Error: Prompt file not found: {args.prompt_b}")
            sys.exit(1)

        compare_prompts(args.prompt_a, args.prompt_b)

    elif args.command == "clean":
        deleted = delete_beans_by_tag(args.tag)
        print(f"Deleted {deleted} beans with tag '{args.tag}'")


if __name__ == "__main__":
    main()
