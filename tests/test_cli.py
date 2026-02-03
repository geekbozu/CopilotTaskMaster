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
    result = runner.invoke(main, ['--tasks-dir', temp_tasks_dir, 'create', 'task1.md', 'Title'])
    assert result.exit_code != 0
    assert 'Provide a project' in result.output


def test_create_with_project_flag(temp_tasks_dir):
    runner = CliRunner()
    res = runner.invoke(main, ['--tasks-dir', temp_tasks_dir, 'create', '--project', 'cli', 'task1.md', 'Title'])
    assert res.exit_code == 0
    assert 'Created task' in res.output

    # Verify file exists
    manager = TaskManager(temp_tasks_dir)
    task = manager.read_task('task1.md', project='cli')
    assert task is not None
    assert task['title'] == 'Title'


def test_show_requires_project_when_missing(temp_tasks_dir):
    runner = CliRunner()

    # create a task explicitly (bypass CLI)
    manager = TaskManager(temp_tasks_dir)
    manager.create_task('task1.md', 'Title', project='proj')

    # calling show without project should error when path lacks project prefix
    res = runner.invoke(main, ['--tasks-dir', temp_tasks_dir, 'show', 'task1.md'])
    assert res.exit_code != 0
    assert 'Provide a project' in res.output


def test_move_with_project_flag(temp_tasks_dir):
    runner = CliRunner()
    manager = TaskManager(temp_tasks_dir)
    manager.create_task('task1.md', 'Title', project='mv')

    res = runner.invoke(main, ['--tasks-dir', temp_tasks_dir, 'move', '--project', 'mv', 'task1.md', 'other/task1.md'])
    assert res.exit_code == 0
    assert 'Moved task' in res.output

    assert manager.read_task('other/task1.md', project='mv') is not None


def test_cli_version():
    runner = CliRunner()
    res = runner.invoke(main, ['--version'])
    assert res.exit_code == 0
    assert __version__ in res.output
