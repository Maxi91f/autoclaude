# AutoClaude

Autonomous agent that implements tasks by invoking Claude in a loop.

## How it works

1. Queries tasks from [Beans](https://www.beans.cm/) with the `autoclaude` tag
2. Finds the first pending task
3. Runs Claude with a specialized prompt to implement it
4. Repeats until all tasks are done or no progress is made

The `WHITEBOARD.md` file serves as communication between Claude instances, maintaining context about blockers, decisions, and learnings across runs.

## Requirements

- Python 3.12+
- Claude CLI (`claude`) installed and configured, probably you will want a PRO subscription
- uv package manager

## Installation

```bash
# Install as global tool (editable mode - changes reflect immediately)
uv tool install --editable /path/to/autoclaude

# Or standard install (need to reinstall after changes)
uv tool install /path/to/autoclaude
```

## Setup

1. Install Beans and create tasks with the `autoclaude` tag
2. Write a good `CLAUDE.md` file in your project for context and instructions
3. Run `autoclaude` from your project directory

## Usage

```bash
# List tasks with 'autoclaude' tag
autoclaude list

# Run the autonomous loop
autoclaude run

# Ask for confirmation before starting
autoclaude run --ask

# Limit to N iterations
autoclaude run -n 10

# Just print the prompt (for debugging)
autoclaude run --print-only

# Exits if outside allowed hours (default: 22:00-08:00)
autoclaude run --start-hour 22 --end-hour 8

# Wait for allowed hours instead of exiting
autoclaude run --wait-for-time-band
```

### Specialized Prompts

Run specific prompts instead of the normal task loop:

```bash
# Run a single task implementation
autoclaude run -p task

# Cleanup: verify task statuses are correct
autoclaude run -p cleanup

# Deploy: create PR and deploy changes
autoclaude run -p deploy

# UI review: check UI/UX of recent changes
autoclaude run -p ui
```

## Features

- **Beans integration**: Queries tasks via Beans CLI with `autoclaude` tag
- **Modular prompts**: Specialized prompts for different phases (task, cleanup, deploy, ui)
- **Streaming output**: Real-time display of Claude's responses and tool usage
- **Progress tracking**: Stops after 5 consecutive iterations with no progress
- **Credit detection**: Waits gracefully when rate limited until reset
- **Time bands**: Exits if outside allowed hours (default: 22:00-08:00), use `--wait-for-time-band` to wait instead

## Future

- Refactor as a uv script with better path handling
- Parallel tasks with a smart orchestrator
- Better in-the-middle agents: testing, UX review, re-planning, cleanup
- Better testing instructions
