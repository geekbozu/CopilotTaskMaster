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
```bash
docker build -t taskmaster .
# Run via Compose
docker-compose run taskmaster list
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

# Update & Move
taskmaster update backend/login.md --status in-progress
taskmaster move backend/login.md backend/completed/login.md
```

### MCP Server
Integrate TaskMaster with LLMs (like Cursor or VS Code Copilot) using the MCP server.

```bash
# Run server
python -m taskmaster.mcp_server
```

**Available Tools:** `create_task`, `read_task`, `update_task`, `delete_task`, `list_tasks`, `search_tasks`, `move_task`, `get_structure`, `get_all_tags`.

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
