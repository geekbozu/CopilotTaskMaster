# CopilotTaskMaster

Python tools and MCP server for managing markdown task cards with LLM integration.

## Overview

CopilotTaskMaster is a system for managing tasks as markdown files in a hierarchical folder structure. It provides:
- **Command-line interface** for task management
- **MCP (Model Context Protocol) server** for LLM interaction
- **Token-efficient** responses optimized for AI assistants
- **Docker support** for easy deployment
- **Hierarchical organization** with projects, tasks, and groupings
- **Project-based organization** - all tasks must be organized under a project folder

## Important: Project Requirement

**All tasks must be organized under a project folder.** Task paths must include at least one directory level (the project folder) before the task file name.

✅ **Valid paths:**
- `project1/task1.md`
- `project1/features/auth.md`
- `my-app/bugs/issue-123.md`

❌ **Invalid paths:**
- `task1.md` (no project folder)
- `auth.md` (no project folder)

This requirement ensures proper organization and prevents tasks from being scattered at the root level. You can still edit markdown files directly using standard text editors or file tools, but when using TaskMaster's create, read, update, delete, or move operations, a project folder is mandatory.

## Features

- ✅ Create, read, update, and delete task cards
- 🔍 Full-text search across tasks
- 🏷️ Tag-based organization and filtering
- 📁 Hierarchical folder structure
- 🤖 MCP server for seamless LLM integration
- 🐳 Docker containerization
- 📊 Metadata support (status, priority, tags, dates)

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/geekbozu/CopilotTaskMaster.git
cd CopilotTaskMaster

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

### Using Docker

```bash
# Build the image
docker build -t copilot-taskmaster .

# Run with docker-compose
docker-compose up
```

## Usage

### Command-Line Interface

#### Create a Task

```bash
taskmaster create project1/task1.md "Implement login feature" \
  --content "Build user authentication system" \
  --status "in-progress" \
  --priority "high" \
  --tags "auth" --tags "backend"
```

#### List Tasks

```bash
# List all tasks
taskmaster list

# List tasks in a specific directory
taskmaster list --subpath project1

# Show full content
taskmaster list --full
```

#### Show Task Details

```bash
taskmaster show project1/task1.md --full
```

#### Search Tasks

```bash
# Text search
taskmaster search --query "authentication"

# Filter by status
taskmaster search --status "in-progress"

# Filter by tags
taskmaster search --tags "backend" --tags "auth"

# Combined filters
taskmaster search --query "login" --priority "high" --max-results 10
```

#### Update Task

```bash
taskmaster update project1/task1.md \
  --status "done" \
  --add-tag "reviewed"
```

#### Show Hierarchy

```bash
# Show entire structure
taskmaster tree

# Show structure of subdirectory
taskmaster tree --subpath project1
```

#### Move/Rename Task

```bash
taskmaster move project1/task1.md project1/completed/task1.md
```

#### Delete Task

```bash
taskmaster delete project1/task1.md
```

#### List All Tags

```bash
taskmaster tags
```

### MCP Server

The MCP server provides LLM-friendly tools for task management.

#### Running the MCP Server

```bash
# Set tasks directory (optional)
export TASKMASTER_TASKS_DIR=/path/to/tasks

# Run the server
python -m taskmaster.mcp_server
```

#### Available MCP Tools

1. **create_task** - Create a new task card
2. **read_task** - Read a task by path
3. **update_task** - Update existing task
4. **delete_task** - Delete a task
5. **list_tasks** - List tasks (token-efficient summary)
6. **search_tasks** - Search with filters (token-efficient)
7. **get_structure** - Get hierarchical overview
8. **move_task** - Move/rename tasks
9. **get_all_tags** - List all tags

All MCP responses are optimized for token efficiency while maintaining usefulness.

### Docker Usage

#### Interactive Mode

```bash
docker run -it -v $(pwd)/tasks:/tasks copilot-taskmaster list
```

#### Run Specific Commands

```bash
# Create a task
docker run -v $(pwd)/tasks:/tasks copilot-taskmaster \
  create project1/task1.md "My Task"

# Search tasks
docker run -v $(pwd)/tasks:/tasks copilot-taskmaster \
  search --query "login"
```

#### Using Docker Compose

```bash
# Start the container
docker-compose run taskmaster list

# Create tasks
docker-compose run taskmaster create project1/task1.md "Task Title"
```

## Task Structure

Tasks are markdown files with YAML frontmatter:

```markdown
---
title: Implement User Authentication
created: 2024-02-02T10:00:00
updated: 2024-02-02T15:30:00
status: in-progress
priority: high
tags:
  - auth
  - backend
  - security
---

# Implementation Details

Build a secure authentication system with:
- JWT tokens
- Password hashing
- Session management

## Tasks
- [x] Set up auth routes
- [ ] Implement password hashing
- [ ] Add JWT middleware
```

## Configuration

### Environment Variables

- `TASKMASTER_TASKS_DIR` - Path to tasks directory (default: `./tasks`)

### Command-Line Options

Most commands accept `--tasks-dir` to override the tasks directory:

```bash
taskmaster --tasks-dir /path/to/tasks list
```

## Project Structure

```
CopilotTaskMaster/
├── taskmaster/
│   ├── __init__.py
│   ├── task_manager.py    # Core task management
│   ├── search.py          # Search functionality
│   ├── cli.py             # CLI interface
│   └── mcp_server.py      # MCP server
├── tasks/                 # Default tasks directory
├── pyproject.toml         # Package configuration
├── requirements.txt       # Dependencies
├── Dockerfile            # Docker image
└── docker-compose.yml    # Docker Compose config
```

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black taskmaster/
ruff check taskmaster/
```

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
