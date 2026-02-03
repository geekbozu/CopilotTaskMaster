import os
import tempfile
import shutil
import asyncio

from mcp.types import TextContent

from taskmaster.mcp_server import call_tool, task_manager, task_searcher
from taskmaster.task_manager import TaskManager
from taskmaster.search import TaskSearcher


def test_mcp_create_requires_project_when_missing(tmp_path):
    # Use a fresh TaskManager/Test searcher for the MCP server module
    task_manager.base_path = TaskManager(str(tmp_path)).base_path
    task_searcher.base_path = TaskSearcher(str(tmp_path)).base_path

    # Call create_task without project should return an error message about project
    result = asyncio.run(call_tool("create_task", {"path": "task1.md", "title": "Title"}))
    assert isinstance(result, list)
    assert isinstance(result[0], TextContent)
    assert "Provide a project" in result[0].text


def test_mcp_create_with_project(tmp_path):
    task_manager.base_path = TaskManager(str(tmp_path)).base_path
    task_searcher.base_path = TaskSearcher(str(tmp_path)).base_path

    # create with explicit project
    res = asyncio.run(call_tool("create_task", {"path": "task1.md", "title": "Title", "project": "mcp"}))
    assert "Created task" in res[0].text

    # verify file exists using TaskManager
    manager = TaskManager(str(tmp_path))
    task = manager.read_task("task1.md", project="mcp")
    assert task is not None
    assert task['title'] == 'Title'


def test_mcp_read_requires_project_when_missing(tmp_path):
    task_manager.base_path = TaskManager(str(tmp_path)).base_path
    task_searcher.base_path = TaskSearcher(str(tmp_path)).base_path

    # first create a task under a project
    manager = TaskManager(str(tmp_path))
    manager.create_task('task1.md', 'Title', project='proj')

    result = asyncio.run(call_tool("read_task", {"path": "task1.md"}))
    assert "Provide a project" in result[0].text


def test_mcp_move_with_project(tmp_path):
    task_manager.base_path = TaskManager(str(tmp_path)).base_path
    task_searcher.base_path = TaskSearcher(str(tmp_path)).base_path

    manager = TaskManager(str(tmp_path))
    manager.create_task('task1.md', 'Title', project='mv')

    res = asyncio.run(call_tool("move_task", {"old_path": "task1.md", "new_path": "other/task1.md", "project": "mv"}))
    assert 'Moved task' in res[0].text
    assert manager.read_task('other/task1.md', project='mv') is not None
