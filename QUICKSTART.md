# Quick Start Guide

## Important: Project Requirement

**All tasks must be organized under a project folder.** When creating or managing tasks with TaskMaster, you must include a project folder in the path:

✅ **Valid:** `project/task.md`, `my-app/feature.md`, `project1/subfolder/task.md`  
❌ **Invalid:** `task.md`, `feature.md` (no project folder)

This ensures proper organization. You can edit markdown files directly with any editor, but TaskMaster operations require a project folder.

## Installation

### Local Installation

```bash
# Clone repository
git clone https://github.com/geekbozu/CopilotTaskMaster.git
cd CopilotTaskMaster

# Install
pip install -e .
```

### Docker Installation

```bash
# Build image
docker build -t copilot-taskmaster .

# Or use docker-compose
docker-compose build
```

## Basic Usage

### Create Your First Task

```bash
# Create a task directory (optional - will be created automatically)
mkdir -p ./tasks

# Create a task
taskmaster create projects/my-first-task.md "My First Task" \
  --content "This is my first task using CopilotTaskMaster" \
  --status "open" \
  --priority "medium"
```

### View Your Task

```bash
# Show task details
taskmaster show projects/my-first-task.md --full

# List all tasks
taskmaster list

# View as tree
taskmaster tree
```

### Search Tasks

```bash
# Search by text
taskmaster search --query "first task"

# Search by status
taskmaster search --status "open"

# Search by priority
taskmaster search --priority "medium"
```

### Update Task

```bash
# Update status
taskmaster update projects/my-first-task.md --status "done"

# Update content
taskmaster update projects/my-first-task.md \
  --content "Updated task description"
```

## Using with MCP (Claude Desktop)

### 1. Configure Claude Desktop

Edit your Claude Desktop config file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`  
**Linux**: `~/.config/Claude/claude_desktop_config.json`

Add:

```json
{
  "mcpServers": {
    "taskmaster": {
      "command": "taskmaster-mcp",
      "env": {
        "TASKMASTER_TASKS_DIR": "/path/to/your/tasks"
      }
    }
  }
}
```

### 2. Restart Claude Desktop

After configuring, restart Claude Desktop to load the MCP server.

### 3. Use with Claude

You can now ask Claude to manage your tasks:

- "Create a new task for implementing user authentication"
- "Show me all high priority tasks"
- "Search for tasks related to the API"
- "Mark task X as completed"
- "What's the current project structure?"

## Using with Docker

### Run CLI Commands

```bash
# List tasks
docker run --rm -v $(pwd)/tasks:/tasks copilot-taskmaster list

# Create task
docker run --rm -v $(pwd)/tasks:/tasks copilot-taskmaster \
  create project1/task1.md "My Task"

# Search tasks
docker run --rm -v $(pwd)/tasks:/tasks copilot-taskmaster \
  search --status open
```

### Run MCP Server with Docker

Add to Claude Desktop config:

```json
{
  "mcpServers": {
    "taskmaster": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-v", "/absolute/path/to/tasks:/tasks",
        "copilot-taskmaster",
        "taskmaster-mcp"
      ]
    }
  }
}
```

## Environment Variables

- `TASKMASTER_TASKS_DIR` - Path to tasks directory (default: `./tasks`)

## Common Workflows

### Daily Task Management

```bash
# Morning: Check tasks
taskmaster list

# Create new task
taskmaster create daily/2024-02-02.md "Today's Tasks" \
  --content "- [ ] Review PRs\n- [ ] Write documentation"

# Update progress
taskmaster update daily/2024-02-02.md --status "in-progress"

# End of day: Mark complete
taskmaster update daily/2024-02-02.md --status "done"
```

### Project Organization

```bash
# Create project structure
mkdir -p tasks/project-alpha/{features,bugs,docs}

# Add tasks
taskmaster create project-alpha/features/auth.md "User Authentication"
taskmaster create project-alpha/features/api.md "REST API"
taskmaster create project-alpha/bugs/login-bug.md "Login Issue"

# View project
taskmaster tree --subpath project-alpha
```

### Sprint Planning

```bash
# Tag sprint tasks
taskmaster create sprint-5/task-1.md "Feature X" --tags sprint-5 --tags backend
taskmaster create sprint-5/task-2.md "Feature Y" --tags sprint-5 --tags frontend

# Review sprint
taskmaster search --tags sprint-5

# Track progress
taskmaster search --tags sprint-5 --status done
```

## Next Steps

- See [EXAMPLES.md](EXAMPLES.md) for more usage scenarios
- See [README.md](README.md) for complete documentation
- Check out example tasks in `tasks/examples/`

## Troubleshooting

### Command not found: taskmaster

Reinstall the package:
```bash
pip install -e .
```

### MCP Server not connecting

1. Check Claude Desktop config file syntax
2. Verify path to tasks directory exists
3. Check Claude Desktop logs
4. Restart Claude Desktop

### Tasks not showing

Check tasks directory:
```bash
echo $TASKMASTER_TASKS_DIR
ls -la ./tasks
```
