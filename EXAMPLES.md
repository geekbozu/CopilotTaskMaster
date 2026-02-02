# CopilotTaskMaster Examples

This directory contains example configurations and scripts for using CopilotTaskMaster.

## MCP Server Configuration

To use CopilotTaskMaster with Claude Desktop or other MCP clients, add this configuration:

### Claude Desktop Configuration

Add to your Claude Desktop config file (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "taskmaster": {
      "command": "python",
      "args": ["-m", "taskmaster.mcp_server"],
      "env": {
        "TASKMASTER_TASKS_DIR": "/path/to/your/tasks"
      }
    }
  }
}
```

### Using with Docker

```json
{
  "mcpServers": {
    "taskmaster": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-v",
        "/path/to/your/tasks:/tasks",
        "copilot-taskmaster",
        "python",
        "-m",
        "taskmaster.mcp_server"
      ]
    }
  }
}
```

## Example Usage Scenarios

### 1. Project Task Management

```bash
# Create project structure
taskmaster create projectA/feature-1.md "User Authentication" \
  --status "in-progress" --priority "high" --tags "auth" --tags "backend"

taskmaster create projectA/feature-2.md "Dashboard UI" \
  --status "open" --priority "medium" --tags "frontend" --tags "ui"

# View project structure
taskmaster tree --subpath projectA

# Search within project
taskmaster search --path-pattern "projectA/**" --status "in-progress"
```

### 2. Sprint Planning

```bash
# Create sprint tasks
taskmaster create sprints/sprint-1/task-1.md "API Endpoints" --tags "sprint-1"
taskmaster create sprints/sprint-1/task-2.md "Database Schema" --tags "sprint-1"
taskmaster create sprints/sprint-1/task-3.md "Unit Tests" --tags "sprint-1"

# List all sprint tasks
taskmaster search --tags "sprint-1"

# Update status as work progresses
taskmaster update sprints/sprint-1/task-1.md --status "done"
```

### 3. Bug Tracking

```bash
# Create bug report
taskmaster create bugs/bug-001.md "Login fails with special chars" \
  --priority "critical" --tags "bug" --tags "auth"

# Search for critical bugs
taskmaster search --priority "critical" --tags "bug"
```

## MCP Tool Examples

When using with an LLM via MCP, you can ask:

1. **"Show me all high priority tasks"**
   - Uses `search_tasks` with priority filter

2. **"Create a new task for implementing the payment system"**
   - Uses `create_task` with appropriate metadata

3. **"What's the current project structure?"**
   - Uses `get_structure` for overview

4. **"Find all tasks related to authentication"**
   - Uses `search_tasks` with text query

5. **"Mark task X as completed"**
   - Uses `update_task` to change status

## Token Efficiency Tips

The MCP server is designed for token efficiency:

1. **Use `list_tasks`** instead of reading individual tasks when you need an overview
2. **Use `search_tasks`** with filters to narrow results before reading full content
3. **Use `get_structure`** to understand organization without reading all tasks
4. **Metadata queries** (status, priority, tags) are much cheaper than full-text search
5. **Snippets** are provided automatically for search results to minimize tokens

## Best Practices

### Task Organization

```
tasks/
├── projects/
│   ├── project-a/
│   │   ├── features/
│   │   ├── bugs/
│   │   └── docs/
│   └── project-b/
├── sprints/
│   ├── sprint-1/
│   └── sprint-2/
└── backlog/
```

### Metadata Standards

Use consistent metadata across tasks:

- **status**: `open`, `in-progress`, `blocked`, `done`, `cancelled`
- **priority**: `low`, `medium`, `high`, `critical`
- **tags**: Use lowercase, hyphen-separated tags (e.g., `auth`, `backend`, `bug-fix`)

### Content Format

Keep task content structured:

```markdown
---
title: Task Title
status: open
priority: medium
tags: [tag1, tag2]
---

# Overview

Brief description of what needs to be done.

## Requirements

- Requirement 1
- Requirement 2

## Tasks

- [ ] Subtask 1
- [ ] Subtask 2

## Notes

Additional context and information.
```
