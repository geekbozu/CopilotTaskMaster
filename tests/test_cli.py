import os
import tempfile
import shutil
from click.testing import CliRunner
import pytest

from taskmaster.cli import main
from taskmaster.task_manager import TaskManager
from taskmaster import __version__


@pytest.fixture
def temp_tasks_dir():
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


def test_create_requires_project_when_missing(temp_tasks_dir):
    runner = CliRunner()
    result = runner.invoke(main, ["--tasks-dir", temp_tasks_dir, "create", "task1.md", "Title"])
    assert result.exit_code != 0
    assert "Provide a project" in result.output


def test_create_with_project_flag(temp_tasks_dir):
    runner = CliRunner()
    res = runner.invoke(
        main, ["--tasks-dir", temp_tasks_dir, "create", "--project", "cli", "task1.md", "Title"]
    )
    assert res.exit_code == 0
    assert "Created task" in res.output

    # Verify file exists
    manager = TaskManager(temp_tasks_dir)
    task = manager.read_task("task1.md", project="cli")
    assert task is not None
    assert task["title"] == "Title"


def test_show_requires_project_when_missing(temp_tasks_dir):
    runner = CliRunner()

    # create a task explicitly (bypass CLI)
    manager = TaskManager(temp_tasks_dir)
    manager.create_task("task1.md", "Title", project="proj")

    # calling show without project should error when path lacks project prefix
    res = runner.invoke(main, ["--tasks-dir", temp_tasks_dir, "show", "task1.md"])
    assert res.exit_code != 0
    assert "Provide a project" in res.output


def test_move_with_project_flag(temp_tasks_dir):
    runner = CliRunner()
    manager = TaskManager(temp_tasks_dir)
    manager.create_task("task1.md", "Title", project="mv")

    res = runner.invoke(
        main,
        ["--tasks-dir", temp_tasks_dir, "move", "--project", "mv", "task1.md", "other/task1.md"],
    )
    assert res.exit_code == 0
    assert "Moved task" in res.output

    assert manager.read_task("other/task1.md", project="mv") is not None


def test_cli_version():
    runner = CliRunner()
    res = runner.invoke(main, ["--version"])
    assert res.exit_code == 0
    assert __version__ in res.output


def test_create_without_args_shows_help(temp_tasks_dir):
    """Test that create command shows help text when invoked without arguments"""
    runner = CliRunner()
    result = runner.invoke(main, ["--tasks-dir", temp_tasks_dir, "create"])
    assert result.exit_code == 2
    assert "Usage: main create" in result.output
    assert "Create a new task card" in result.output
    assert "Creates a markdown file with YAML frontmatter" in result.output


def test_show_without_args_shows_help(temp_tasks_dir):
    """Test that show command shows help text when invoked without arguments"""
    runner = CliRunner()
    result = runner.invoke(main, ["--tasks-dir", temp_tasks_dir, "show"])
    assert result.exit_code == 2
    assert "Usage: main show" in result.output
    assert "Show a task card" in result.output
    assert "Displays the task's metadata" in result.output


def test_update_without_args_shows_help(temp_tasks_dir):
    """Test that update command shows help text when invoked without arguments"""
    runner = CliRunner()
    result = runner.invoke(main, ["--tasks-dir", temp_tasks_dir, "update"])
    assert result.exit_code == 2
    assert "Usage: main update" in result.output
    assert "Update a task card" in result.output
    assert "Modifies an existing task's metadata" in result.output


def test_delete_without_args_shows_help(temp_tasks_dir):
    """Test that delete command shows help text when invoked without arguments"""
    runner = CliRunner()
    result = runner.invoke(main, ["--tasks-dir", temp_tasks_dir, "delete"])
    assert result.exit_code == 2
    assert "Usage: main delete" in result.output
    assert "Delete a task card" in result.output
    assert "Permanently removes a task file" in result.output


def test_move_without_args_shows_help(temp_tasks_dir):
    """Test that move command shows help text when invoked without arguments"""
    runner = CliRunner()
    result = runner.invoke(main, ["--tasks-dir", temp_tasks_dir, "move"])
    assert result.exit_code == 2
    assert "Usage: main move" in result.output
    assert "Move/rename a task" in result.output
    assert "Moves a task file to a new location" in result.output
