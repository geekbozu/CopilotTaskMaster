# CopilotTaskMaster

Markdown-based task management for humans and AI agents. Manage tasks via CLI or MCP (Model Context Protocol).

## Features

- **Project-Scoped:** All tasks are organized by project folders.
- **Agent Optimized:** Token-efficient responses designed for LLM integration.
- **Markdown First:** Tasks are stored as plain `.md` files with YAML frontmatter.
- **Dual Interface:** Full parity between CLI and MCP server tools.
- **Hierarchical:** Supports nested subpaths and tag-based filtering.

## Installation

### From Source
```bash
git clone https://github.com/geekbozu/CopilotTaskMaster.git
cd CopilotTaskMaster
pip install -e .
```

### Via Docker
Pull the pre-built image from GHCR:
```bash
docker pull ghcr.io/geekbozu/copilottaskmaster:latest
```

Or build locally:
```bash
docker build -t taskmaster .
```

## Usage

### CLI Basics
All operations require a **project** scope, either via `--project` or as a path prefix.

```bash
# Create
taskmaster create backend/login.md "Implement Auth" --status open --priority high

# List & Search
taskmaster list --project backend
taskmaster search --query "Auth" --status open

taskmaster tags --project backend  # list tags for a project (omit --project to list all tags)

# Update & Move
taskmaster update backend/login.md --status in-progress
taskmaster move backend/login.md backend/completed/login.md

# Show Structure
# Show the whole workspace tree
taskmaster tree
# Show tree scoped to a project
taskmaster tree --project backend
```

### MCP Server (VS Code)
Enable task management tools in VS Code by adding the server to your settings:

```json
{
  "servers  ": {
    "taskmaster": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm", 
        "-v", "${workspaceFolder}/tasks:/tasks", 
        "ghcr.io/geekbozu/copilottaskmaster:latest", 
        "mcp-server"
      ]
    }
  }
}
```

**Available Tools:** `create_task`, `read_task`, `update_task`, `delete_task`, `list_tasks`, `search_tasks`, `move_task`, `get_structure`, `get_all_tags`.

Tool details (selected):

- `get_structure(subpath: str = "", project: Optional[str] = None)`: Return hierarchical folder/task structure. When `project` is provided, the structure is scoped to that project (raises ValueError if the project does not exist).
- `get_all_tags(project: Optional[str] = None)`: Return the set of tags used across tasks. When `project` is provided, tags are collected only from that project's tasks (returns empty set if the project does not exist).

## Task Format
Tasks are standard Markdown files:

```markdown
---
title: Implement Auth
status: open
priority: high
tags: [auth, security]
---
# Implementation Details
- [ ] Setup JWT
- [ ] Hash Passwords
```

## Configuration
- `TASKMASTER_TASKS_DIR`: Path to storage (default: `./tasks`).
- Use `--tasks-dir` on any CLI command to override.

## Development
```bash
pytest                 # Run tests
black taskmaster/      # Format code
```

## License
MIT
