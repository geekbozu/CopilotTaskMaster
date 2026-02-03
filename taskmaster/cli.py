"""
CLI - Command-line interface for TaskMaster
"""

import os
import sys
import json
from pathlib import Path
import click
from . import __version__
from .task_manager import TaskManager
from .search import TaskSearcher


@click.group()
@click.version_option(__version__, prog_name="CopilotTaskMaster")
@click.option("--tasks-dir", default=None, help="Path to tasks directory")
@click.pass_context
def main(ctx, tasks_dir):
    """CopilotTaskMaster - Manage markdown task cards"""
    ctx.ensure_object(dict)

    if tasks_dir is None:
        tasks_dir = os.environ.get("TASKMASTER_TASKS_DIR", "./tasks")

    ctx.obj["tasks_dir"] = tasks_dir
    ctx.obj["manager"] = TaskManager(tasks_dir)
    ctx.obj["searcher"] = TaskSearcher(tasks_dir)


@main.command()
@click.argument("path", required=False)
@click.argument("title", required=False)
@click.option("--content", default="", help="Task content")
@click.option("--status", default="open", help="Task status")
@click.option("--priority", default="medium", help="Task priority")
@click.option("--tags", multiple=True, help="Task tags")
@click.option("--project", default=None, help="Project name to scope operation")
@click.pass_context
def create(ctx, path, title, content, status, priority, tags, project):
    """Create a new task card.

    Creates a markdown file with YAML frontmatter containing task metadata.
    The PATH should include the filename (e.g., 'backend/auth.md').
    Project can be specified via --project flag or as a path prefix.
    """
    if path is None or title is None:
        click.echo(ctx.get_help())
        sys.exit(0)

    manager = ctx.obj["manager"]

    metadata = {"status": status, "priority": priority}

    if tags:
        metadata["tags"] = list(tags)

    from .utils import project_resolution_error_msg

    try:
        result = manager.create_task(path, title, content, metadata, project=project)
    except ValueError as e:
        click.echo(project_resolution_error_msg(e), err=True)
        sys.exit(2)

    click.echo(f"✓ Created task: {result['path']}")
    click.echo(f"  Title: {result['title']}")
    click.echo(f"  Created: {result['created']}")


@main.command()
@click.argument("path", required=False)
@click.option("--full", is_flag=True, help="Show full content")
@click.option("--project", default=None, help="Project name to scope operation")
@click.pass_context
def show(ctx, path, full, project):
    """Show a task card.

    Displays the task's metadata (title, status, priority, tags) and optionally
    the full content with --full flag. PATH should be relative to project root.
    """
    if path is None:
        click.echo(ctx.get_help())
        sys.exit(0)

    manager = ctx.obj["manager"]

    from .utils import project_resolution_error_msg

    try:
        task = manager.read_task(path, project=project)
    except ValueError as e:
        click.echo(project_resolution_error_msg(e), err=True)
        sys.exit(2)

    if not task:
        click.echo(f"✗ Task not found: {path}", err=True)
        sys.exit(1)

    click.echo(f"Path: {task['path']}")
    click.echo(f"Title: {task['title']}")
    click.echo(f"\nMetadata:")
    for key, value in task["metadata"].items():
        click.echo(f"  {key}: {value}")

    if full:
        click.echo(f"\nContent:\n{task['content']}")


@main.command()
@click.argument("path", required=False)
@click.option("--title", default=None, help="New title")
@click.option("--content", default=None, help="New content")
@click.option("--status", default=None, help="New status")
@click.option("--priority", default=None, help="New priority")
@click.option("--add-tag", multiple=True, help="Add tags")
@click.option("--project", default=None, help="Project name to scope operation")
@click.pass_context
def update(ctx, path, title, content, status, priority, add_tag, project):
    """Update a task card.

    Modifies an existing task's metadata or content. You can update title, content,
    status, priority, or add tags. Only specified fields will be updated.
    """
    if path is None:
        click.echo(ctx.get_help())
        sys.exit(0)

    manager = ctx.obj["manager"]

    metadata = {}
    if status:
        metadata["status"] = status
    if priority:
        metadata["priority"] = priority

    from .utils import project_resolution_error_msg

    try:
        if add_tag:
            # Read existing tags first
            task = manager.read_task(path, project=project)
            if task:
                existing_tags = task["metadata"].get("tags", [])
                if isinstance(existing_tags, str):
                    existing_tags = [existing_tags]
                metadata["tags"] = list(set(existing_tags + list(add_tag)))

        result = manager.update_task(path, title, content, metadata, project=project)
    except ValueError as e:
        click.echo(project_resolution_error_msg(e), err=True)
        sys.exit(2)

    if not result:
        click.echo(f"✗ Task not found: {path}", err=True)
        sys.exit(1)

    click.echo(f"✓ Updated task: {result['path']}")


@main.command()
@click.argument("path", required=False)
@click.option("--project", default=None, help="Project name to scope operation")
@click.pass_context
def delete(ctx, path, project):
    """Delete a task card.

    Permanently removes a task file from the filesystem. This action cannot be undone.
    """
    if path is None:
        click.echo(ctx.get_help())
        sys.exit(0)

    manager = ctx.obj["manager"]

    from .utils import project_resolution_error_msg

    try:
        success = manager.delete_task(path, project=project)
    except ValueError as e:
        click.echo(project_resolution_error_msg(e), err=True)
        sys.exit(2)

    if success:
        click.echo(f"✓ Deleted task: {path}")
    else:
        click.echo(f"✗ Task not found: {path}", err=True)
        sys.exit(1)


@main.command()
@click.option("--subpath", default="", help="Subdirectory to list")
@click.option("--recursive/--no-recursive", default=True, help="Include subdirectories")
@click.option("--full", is_flag=True, help="Show full content")
@click.option("--project", default=None, help="Project name to scope operation")
@click.pass_context
def list(ctx, subpath, recursive, full, project):
    """List all tasks.

    Shows all tasks in the workspace or within a specific project/subpath.
    Use --project to scope to a project, --subpath to narrow to a directory,
    and --full to include content previews.
    """
    manager = ctx.obj["manager"]

    from .utils import project_resolution_error_msg

    try:
        tasks = manager.list_tasks(
            subpath=subpath, recursive=recursive, include_content=full, project=project
        )
    except ValueError as e:
        click.echo(project_resolution_error_msg(e), err=True)
        sys.exit(2)

    if not tasks:
        click.echo("No tasks found.")
        return

    click.echo(f"Found {len(tasks)} task(s):\n")
    for task in tasks:
        click.echo(f"• {task['path']}")
        click.echo(f"  {task['title']}")

        if "status" in task["metadata"]:
            click.echo(f"  Status: {task['metadata']['status']}")

        if full and "content" in task:
            click.echo(f"  Content: {task['content'][:100]}...")

        click.echo()


@main.command()
@click.option("--subpath", default="", help="Subdirectory to show structure for")
@click.option("--project", default=None, help="Project name to scope operation")
@click.pass_context
def tree(ctx, subpath, project):
    """Show hierarchical structure of tasks.

    Displays a tree view of the task workspace showing folders and task files.
    Use --project to scope to a specific project.
    """
    manager = ctx.obj["manager"]

    from .utils import project_resolution_error_msg

    try:
        structure = manager.get_structure(subpath, project=project)
    except ValueError as e:
        click.echo(project_resolution_error_msg(e), err=True)
        sys.exit(2)

    def print_tree(node, prefix="", is_last=True):
        connector = "└── " if is_last else "├── "
        click.echo(f"{prefix}{connector}{node['name']}")

        if node["type"] == "directory" and "children" in node:
            extension = "    " if is_last else "│   "
            for i, child in enumerate(node["children"]):
                is_last_child = i == len(node["children"]) - 1
                print_tree(child, prefix + extension, is_last_child)
        elif node["type"] == "task":
            if "title" in node and node["title"]:
                extension = "    " if is_last else "│   "
                click.echo(f"{prefix}{extension}    {node['title']}")

    print_tree(structure, "", True)


@main.command()
@click.option("--query", default="", help="Text to search for")
@click.option("--status", default=None, help="Filter by status")
@click.option("--priority", default=None, help="Filter by priority")
@click.option("--tags", multiple=True, help="Filter by tags")
@click.option("--path-pattern", default="", help="Path pattern to search")
@click.option("--max-results", default=50, help="Maximum results")
@click.option("--full", is_flag=True, help="Show full content")
@click.pass_context
def search(ctx, query, status, priority, tags, path_pattern, max_results, full):
    """Search for tasks.

    Performs full-text search across task titles and content, with optional
    filters for metadata (status, priority, tags). Returns ranked results.
    """
    searcher = ctx.obj["searcher"]

    metadata_filters = {}
    if status:
        metadata_filters["status"] = status
    if priority:
        metadata_filters["priority"] = priority
    if tags:
        metadata_filters["tags"] = list(tags)

    results = searcher.search(
        query=query,
        metadata_filters=metadata_filters if metadata_filters else None,
        path_pattern=path_pattern,
        max_results=max_results,
        include_content=full,
    )

    if not results:
        click.echo("No tasks found.")
        return

    click.echo(f"Found {len(results)} task(s):\n")
    for result in results:
        click.echo(f"• {result['path']} (score: {result['score']})")
        click.echo(f"  {result['title']}")

        if "snippet" in result:
            click.echo(f"  {result['snippet']}")

        if full and "content" in result:
            click.echo(f"\n{result['content']}\n")

        click.echo()


@main.command()
@click.option("--project", default=None, help="Project name to scope operation")
@click.pass_context
def tags(ctx, project):
    """List all tags.

    Shows all unique tags used across tasks. Use --project to scope to a specific project.
    """
    searcher = ctx.obj["searcher"]

    all_tags = searcher.get_all_tags(project=project)

    if not all_tags:
        click.echo("No tags found.")
        return

    click.echo("Tags:")
    for tag in sorted(all_tags):
        click.echo(f"  • {tag}")


@main.command()
@click.argument("old_path", required=False)
@click.argument("new_path", required=False)
@click.option("--project", default=None, help="Project name to scope operation")
@click.pass_context
def move(ctx, old_path, new_path, project):
    """Move/rename a task.

    Moves a task file to a new location or renames it. The task's content and
    metadata are preserved. Directories are created as needed.
    """
    if old_path is None or new_path is None:
        click.echo(ctx.get_help())
        sys.exit(0)

    manager = ctx.obj["manager"]

    from .utils import project_resolution_error_msg

    try:
        success = manager.move_task(old_path, new_path, project=project)
    except ValueError as e:
        click.echo(project_resolution_error_msg(e), err=True)
        sys.exit(2)

    if success:
        click.echo(f"✓ Moved task from {old_path} to {new_path}")
    else:
        click.echo(f"✗ Failed to move task", err=True)
        sys.exit(1)


@main.command(name="mcp-server")
@click.pass_context
def mcp_server_cmd(ctx):
    """Start the MCP server for LLM integration.

    Starts a Model Context Protocol (MCP) server that exposes task management
    functionality as tools for AI assistants and LLMs.
    """
    from .mcp_server import main as run_mcp

    # Pass the tasks directory to the MCP server via environment variable
    os.environ["TASKMASTER_TASKS_DIR"] = ctx.obj["tasks_dir"]

    run_mcp()


if __name__ == "__main__":
    main()
