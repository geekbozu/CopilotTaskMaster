"""
CLI - Command-line interface for TaskMaster
"""

import os
import sys
import json
from pathlib import Path
import click
from .task_manager import TaskManager
from .search import TaskSearcher


@click.group()
@click.option('--tasks-dir', default=None, help='Path to tasks directory')
@click.pass_context
def main(ctx, tasks_dir):
    """CopilotTaskMaster - Manage markdown task cards"""
    ctx.ensure_object(dict)
    
    if tasks_dir is None:
        tasks_dir = os.environ.get('TASKMASTER_TASKS_DIR', './tasks')
    
    ctx.obj['tasks_dir'] = tasks_dir
    ctx.obj['manager'] = TaskManager(tasks_dir)
    ctx.obj['searcher'] = TaskSearcher(tasks_dir)


@main.command()
@click.argument('path')
@click.argument('title')
@click.option('--content', default="", help='Task content')
@click.option('--status', default='open', help='Task status')
@click.option('--priority', default='medium', help='Task priority')
@click.option('--tags', multiple=True, help='Task tags')
@click.pass_context
def create(ctx, path, title, content, status, priority, tags):
    """Create a new task card"""
    manager = ctx.obj['manager']
    
    metadata = {
        'status': status,
        'priority': priority
    }
    
    if tags:
        metadata['tags'] = list(tags)
    
    result = manager.create_task(path, title, content, metadata)
    click.echo(f"✓ Created task: {result['path']}")
    click.echo(f"  Title: {result['title']}")
    click.echo(f"  Created: {result['created']}")


@main.command()
@click.argument('path')
@click.option('--full', is_flag=True, help='Show full content')
@click.pass_context
def show(ctx, path, full):
    """Show a task card"""
    manager = ctx.obj['manager']
    
    task = manager.read_task(path)
    if not task:
        click.echo(f"✗ Task not found: {path}", err=True)
        sys.exit(1)
    
    click.echo(f"Path: {task['path']}")
    click.echo(f"Title: {task['title']}")
    click.echo(f"\nMetadata:")
    for key, value in task['metadata'].items():
        click.echo(f"  {key}: {value}")
    
    if full:
        click.echo(f"\nContent:\n{task['content']}")


@main.command()
@click.argument('path')
@click.option('--title', default=None, help='New title')
@click.option('--content', default=None, help='New content')
@click.option('--status', default=None, help='New status')
@click.option('--priority', default=None, help='New priority')
@click.option('--add-tag', multiple=True, help='Add tags')
@click.pass_context
def update(ctx, path, title, content, status, priority, add_tag):
    """Update a task card"""
    manager = ctx.obj['manager']
    
    metadata = {}
    if status:
        metadata['status'] = status
    if priority:
        metadata['priority'] = priority
    
    if add_tag:
        # Read existing tags first
        task = manager.read_task(path)
        if task:
            existing_tags = task['metadata'].get('tags', [])
            if isinstance(existing_tags, str):
                existing_tags = [existing_tags]
            metadata['tags'] = list(set(existing_tags + list(add_tag)))
    
    result = manager.update_task(path, title, content, metadata)
    if not result:
        click.echo(f"✗ Task not found: {path}", err=True)
        sys.exit(1)
    
    click.echo(f"✓ Updated task: {result['path']}")


@main.command()
@click.argument('path')
@click.pass_context
def delete(ctx, path):
    """Delete a task card"""
    manager = ctx.obj['manager']
    
    if manager.delete_task(path):
        click.echo(f"✓ Deleted task: {path}")
    else:
        click.echo(f"✗ Task not found: {path}", err=True)
        sys.exit(1)


@main.command()
@click.option('--subpath', default="", help='Subdirectory to list')
@click.option('--recursive/--no-recursive', default=True, help='Include subdirectories')
@click.option('--full', is_flag=True, help='Show full content')
@click.pass_context
def list(ctx, subpath, recursive, full):
    """List all tasks"""
    manager = ctx.obj['manager']
    
    tasks = manager.list_tasks(subpath, recursive, full)
    
    if not tasks:
        click.echo("No tasks found.")
        return
    
    click.echo(f"Found {len(tasks)} task(s):\n")
    for task in tasks:
        click.echo(f"• {task['path']}")
        click.echo(f"  {task['title']}")
        
        if 'status' in task['metadata']:
            click.echo(f"  Status: {task['metadata']['status']}")
        
        if full and 'content' in task:
            click.echo(f"  Content: {task['content'][:100]}...")
        
        click.echo()


@main.command()
@click.option('--subpath', default="", help='Subdirectory to show structure for')
@click.pass_context
def tree(ctx, subpath):
    """Show hierarchical structure of tasks"""
    manager = ctx.obj['manager']
    
    structure = manager.get_structure(subpath)
    
    def print_tree(node, prefix="", is_last=True):
        connector = "└── " if is_last else "├── "
        click.echo(f"{prefix}{connector}{node['name']}")
        
        if node['type'] == 'directory' and 'children' in node:
            extension = "    " if is_last else "│   "
            for i, child in enumerate(node['children']):
                is_last_child = i == len(node['children']) - 1
                print_tree(child, prefix + extension, is_last_child)
        elif node['type'] == 'task':
            if 'title' in node and node['title']:
                extension = "    " if is_last else "│   "
                click.echo(f"{prefix}{extension}    {node['title']}")
    
    print_tree(structure, "", True)


@main.command()
@click.option('--query', default="", help='Text to search for')
@click.option('--status', default=None, help='Filter by status')
@click.option('--priority', default=None, help='Filter by priority')
@click.option('--tags', multiple=True, help='Filter by tags')
@click.option('--path-pattern', default="", help='Path pattern to search')
@click.option('--max-results', default=50, help='Maximum results')
@click.option('--full', is_flag=True, help='Show full content')
@click.pass_context
def search(ctx, query, status, priority, tags, path_pattern, max_results, full):
    """Search for tasks"""
    searcher = ctx.obj['searcher']
    
    metadata_filters = {}
    if status:
        metadata_filters['status'] = status
    if priority:
        metadata_filters['priority'] = priority
    if tags:
        metadata_filters['tags'] = list(tags)
    
    results = searcher.search(
        query=query,
        metadata_filters=metadata_filters if metadata_filters else None,
        path_pattern=path_pattern,
        max_results=max_results,
        include_content=full
    )
    
    if not results:
        click.echo("No tasks found.")
        return
    
    click.echo(f"Found {len(results)} task(s):\n")
    for result in results:
        click.echo(f"• {result['path']} (score: {result['score']})")
        click.echo(f"  {result['title']}")
        
        if 'snippet' in result:
            click.echo(f"  {result['snippet']}")
        
        if full and 'content' in result:
            click.echo(f"\n{result['content']}\n")
        
        click.echo()


@main.command()
@click.pass_context
def tags(ctx):
    """List all tags"""
    searcher = ctx.obj['searcher']
    
    all_tags = searcher.get_all_tags()
    
    if not all_tags:
        click.echo("No tags found.")
        return
    
    click.echo("Tags:")
    for tag in sorted(all_tags):
        click.echo(f"  • {tag}")


@main.command()
@click.argument('old_path')
@click.argument('new_path')
@click.pass_context
def move(ctx, old_path, new_path):
    """Move/rename a task"""
    manager = ctx.obj['manager']
    
    if manager.move_task(old_path, new_path):
        click.echo(f"✓ Moved task from {old_path} to {new_path}")
    else:
        click.echo(f"✗ Failed to move task", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
