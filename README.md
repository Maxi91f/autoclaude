# AutoClaude

Autonomous agent that implements user stories by invoking Claude in a loop.

## How it works

1. Reads user stories from a `STORIES.md` file (checkbox format)
2. Finds the first unchecked story
3. Asks Claude to implement it
4. Repeats until all stories are done or no progress is made

The `WHITEBOARD.md` file serves as communication between Claude instances, maintaining context about blockers, decisions, and learnings across runs.

## Installation

```bash
uv tool install .
```

### Recommended

- Install [Beans](https://www.beans.cm/) for better tracking of tasks and credit usage
- Write a good `CLAUDE.md` file in your project to provide context and instructions

## Usage

```bash
# List current stories and progress
autoclaude list

# Run the autonomous loop
autoclaude run

# Run without confirmation prompt
autoclaude run -y

# Limit to N iterations
autoclaude run -n 10

# Just print the prompt (for debugging)
autoclaude run --print

# Run only during specific hours (default: 22:00-08:00)
autoclaude run --start-hour 22 --end-hour 8
```

## Configuration

AutoClaude expects:
- A `STORIES.md` file with checkbox-style user stories (`- [ ]` pending, `- [x]` done)
- A `WHITEBOARD.md` file for inter-instance communication

AutoClaude looks for these files in the current working directory where you run the command.

## Features

- **Streaming output**: Real-time display of Claude's responses and tool usage
- **Progress tracking**: Stops after 5 consecutive iterations with no progress
- **Cleanup mode**: Every 5 iterations, verifies stories are correctly marked
- **Credit detection**: Waits gracefully when Claude runs out of credits until credits are replenished
- **Time bands**: Only runs during allowed hours (default: 22:00-08:00, 2 5-hour cycles), waits otherwise. When you wake up you will have credits.

## Requirements

- Python 3.12+
- Claude CLI (`claude`) installed and configured, probably you will want a PRO subscription
- uv package manager

## Future

- Refactor as a uv script with better path handling
- Parallel tasks with a smart orchestrator
- Better in-the-middle agents: testing, UX review, re-planning, cleanup
- Better testing instructions
