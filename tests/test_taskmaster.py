"""
Basic tests for TaskMaster functionality
"""

import os
import tempfile
import shutil
from pathlib import Path
import pytest

from taskmaster.task_manager import TaskManager
from taskmaster.search import TaskSearcher


@pytest.fixture
def temp_tasks_dir():
    """Create a temporary directory for tests"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


def test_create_task(temp_tasks_dir):
    """Test creating a task"""
    manager = TaskManager(temp_tasks_dir)

    result = manager.create_task(
        path="test/task1.md",
        title="Test Task",
        content="Test content",
        metadata={"status": "open", "priority": "high"},
    )

    assert result["title"] == "Test Task"
    assert result["path"] == "test/task1.md"
    assert "created" in result


def test_read_task(temp_tasks_dir):
    """Test reading a task"""
    manager = TaskManager(temp_tasks_dir)

    # Create task
    manager.create_task(path="test/task1.md", title="Test Task", content="Test content")

    # Read task
    task = manager.read_task("test/task1.md")

    assert task is not None
    assert task["title"] == "Test Task"
    assert task["content"] == "Test content"


def test_update_task(temp_tasks_dir):
    """Test updating a task"""
    manager = TaskManager(temp_tasks_dir)

    # Create task
    manager.create_task(
        path="test/task1.md",
        title="Test Task",
        content="Original content",
        metadata={"status": "open"},
    )

    # Update task
    result = manager.update_task(
        path="test/task1.md", content="Updated content", metadata={"status": "done"}
    )

    assert result is not None
    assert result["content"] == "Updated content"
    assert result["metadata"]["status"] == "done"


def test_delete_task(temp_tasks_dir):
    """Test deleting a task"""
    manager = TaskManager(temp_tasks_dir)

    # Create task
    manager.create_task(path="test/task1.md", title="Test Task")

    # Delete task
    success = manager.delete_task("test/task1.md")
    assert success is True

    # Verify deleted
    task = manager.read_task("test/task1.md")
    assert task is None


def test_list_tasks(temp_tasks_dir):
    """Test listing tasks"""
    manager = TaskManager(temp_tasks_dir)

    # Create multiple tasks
    manager.create_task("test/task1.md", "Task 1")
    manager.create_task("test/task2.md", "Task 2")
    manager.create_task("other/task3.md", "Task 3")

    # List all tasks
    tasks = manager.list_tasks()
    assert len(tasks) == 3

    # List tasks in subdirectory
    tasks = manager.list_tasks(subpath="test")
    assert len(tasks) == 2


def test_search_tasks(temp_tasks_dir):
    """Test searching tasks"""
    manager = TaskManager(temp_tasks_dir)
    searcher = TaskSearcher(temp_tasks_dir)

    # Create tasks with different content
    manager.create_task(
        "test/task1.md",
        "Authentication Task",
        content="Implement JWT authentication",
        metadata={"status": "open", "tags": ["auth", "backend"]},
    )
    manager.create_task(
        "test/task2.md",
        "UI Task",
        content="Design login page",
        metadata={"status": "in-progress", "tags": ["frontend"]},
    )

    # Search by text
    results = searcher.search(query="authentication")
    assert len(results) > 0
    assert "Authentication Task" in results[0]["title"]

    # Search by metadata
    results = searcher.search(metadata_filters={"status": "open"})
    assert len(results) == 1

    # Search by tags
    results = searcher.search_by_tags(["auth"])
    assert len(results) == 1


def test_metadata_case_insensitive(temp_tasks_dir):
    """Metadata filters should be case-insensitive"""
    manager = TaskManager(temp_tasks_dir)
    searcher = TaskSearcher(temp_tasks_dir)

    manager.create_task("case/task1.md", "Case Task", metadata={"status": "Open"})

    results = searcher.search(metadata_filters={"status": "open"})
    assert len(results) == 1


def test_metadata_list_scalar_flexibility(temp_tasks_dir):
    """Filters should match list metadata and scalar metadata interchangeably"""
    manager = TaskManager(temp_tasks_dir)
    searcher = TaskSearcher(temp_tasks_dir)

    manager.create_task("flex/task1.md", "Flex Task", metadata={"tags": "Auth"})

    # filter given as list should match scalar metadata
    results = searcher.search(metadata_filters={"tags": ["auth"]})
    assert len(results) == 1

    # filter given as scalar should also match
    results2 = searcher.search(metadata_filters={"tags": "Auth"})
    assert len(results2) == 1


def test_search_early_exit(temp_tasks_dir):
    """Search should stop when max_results is reached"""
    manager = TaskManager(temp_tasks_dir)
    searcher = TaskSearcher(temp_tasks_dir)

    for i in range(20):
        manager.create_task(f"bulk/task{i}.md", f"Task {i}")

    results = searcher.search(max_results=5)
    assert len(results) == 5


def test_move_task(temp_tasks_dir):
    """Test moving a task"""
    manager = TaskManager(temp_tasks_dir)

    # Create task
    manager.create_task("test/task1.md", "Task 1")

    # Move task
    success = manager.move_task("test/task1.md", "other/task1.md")
    assert success is True

    # Verify moved
    task = manager.read_task("other/task1.md")
    assert task is not None

    old_task = manager.read_task("test/task1.md")
    assert old_task is None


def test_get_structure(temp_tasks_dir):
    """Test getting task structure"""
    manager = TaskManager(temp_tasks_dir)

    # Create tasks in hierarchy
    manager.create_task("project1/task1.md", "Task 1")
    manager.create_task("project1/subtasks/task2.md", "Task 2")
    manager.create_task("project2/task3.md", "Task 3")

    # Get structure
    structure = manager.get_structure()

    assert structure["type"] == "directory"
    assert len(structure["children"]) > 0


def test_get_structure_with_project_param(temp_tasks_dir):
    """Test get_structure when project is passed explicitly"""
    manager = TaskManager(temp_tasks_dir)

    manager.create_task("project1/task1.md", "Task 1")
    manager.create_task("project1/subtasks/task2.md", "Task 2")

    structure = manager.get_structure(project="project1")

    assert structure["type"] == "directory"
    assert structure["name"] == "project1"

    def collect_paths(tree):
        ps = []
        for c in tree.get("children", []):
            if c.get("type") == "task":
                ps.append(c.get("path"))
            elif c.get("type") == "directory":
                ps.extend(collect_paths(c))
        return ps

    paths = collect_paths(structure)
    assert any("project1/" in p for p in paths)


def test_get_structure_project_not_found_raises(temp_tasks_dir):
    """Requesting a non-existent project should raise ValueError"""
    manager = TaskManager(temp_tasks_dir)

    with pytest.raises(ValueError):
        manager.get_structure(project="no_such_project")


def test_tags(temp_tasks_dir):
    """Test tag operations"""
    manager = TaskManager(temp_tasks_dir)
    searcher = TaskSearcher(temp_tasks_dir)

    # Create tasks with tags in one project
    manager.create_task(
        "task1.md", "Task 1", metadata={"tags": ["python", "backend"]}, project="tagsproj"
    )
    manager.create_task(
        "task2.md", "Task 2", metadata={"tags": ["javascript", "frontend"]}, project="tagsproj"
    )

    # Create a task with tags in another project to ensure scoping works
    manager.create_task(
        "task3.md", "Task 3", metadata={"tags": ["go", "backend"]}, project="otherproj"
    )

    # Get all tags (global)
    tags = searcher.get_all_tags()
    assert "python" in tags
    assert "backend" in tags
    assert "javascript" in tags
    assert "frontend" in tags
    assert "go" in tags

    # Get tags scoped to tagsproj
    tags_tagsproj = searcher.get_all_tags(project="tagsproj")
    assert "python" in tags_tagsproj
    assert "javascript" in tags_tagsproj
    assert "go" not in tags_tagsproj


def test_get_all_tags_project_not_found_returns_empty(temp_tasks_dir):
    """Requesting tags for a non-existent project returns an empty set"""
    searcher = TaskSearcher(temp_tasks_dir)

    tags = searcher.get_all_tags(project="no_such_proj")
    assert tags == set()


def test_requires_project_when_missing(temp_tasks_dir):
    """Operations without a project and without a leading project in the path should fail"""
    manager = TaskManager(temp_tasks_dir)

    with pytest.raises(ValueError):
        manager.create_task("task1.md", "No project")


def test_project_param_project_prefix_ignored(temp_tasks_dir):
    """When a project is provided explicitly, a path with a different leading folder is treated
    as a subpath under the provided project (no error)."""
    manager = TaskManager(temp_tasks_dir)

    result = manager.create_task("other/task1.md", "Placed", project="proj")
    assert result["path"] == "proj/other/task1.md"

    task = manager.read_task("other/task1.md", project="proj")
    assert task is not None
    assert task["path"] == "proj/other/task1.md"


def test_explicit_project_parameter(temp_tasks_dir):
    """Passing project explicitly should place tasks under that project"""
    manager = TaskManager(temp_tasks_dir)

    result = manager.create_task("task1.md", "Explicit", project="explicit")
    assert result["path"] == "explicit/task1.md"

    task = manager.read_task("task1.md", project="explicit")
    assert task is not None
    assert task["path"] == "explicit/task1.md"


def test_paths_are_posix(temp_tasks_dir):
    """Ensure returned paths use POSIX-style separators (forward slashes)"""
    manager = TaskManager(temp_tasks_dir)

    # Create tasks in nested and flat paths
    result = manager.create_task("dir/sub/task.md", "Task 1")
    manager.create_task("other/task2.md", "Task 2")

    # create_task should return POSIX-style path
    assert "/" in result["path"] and "\\" not in result["path"]

    # read_task should return POSIX-style path
    task = manager.read_task("dir/sub/task.md")
    assert task is not None
    assert "/" in task["path"] and "\\" not in task["path"]

    # list_tasks should return POSIX-style paths
    tasks = manager.list_tasks()
    assert any("/" in t["path"] and "\\" not in t["path"] for t in tasks)

    # get_structure should include POSIX-style paths for task nodes
    structure = manager.get_structure()

    def collect_paths(tree):
        ps = []
        for c in tree.get("children", []):
            if c.get("type") == "task":
                ps.append(c.get("path"))
            elif c.get("type") == "directory":
                ps.extend(collect_paths(c))
        return ps

    for p in collect_paths(structure):
        assert "/" in p and "\\" not in p
