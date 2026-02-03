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
        metadata={"status": "open", "priority": "high"}
    )
    
    assert result['title'] == "Test Task"
    assert result['path'] == "test/task1.md"
    assert 'created' in result


def test_read_task(temp_tasks_dir):
    """Test reading a task"""
    manager = TaskManager(temp_tasks_dir)
    
    # Create task
    manager.create_task(
        path="test/task1.md",
        title="Test Task",
        content="Test content"
    )
    
    # Read task
    task = manager.read_task("test/task1.md")
    
    assert task is not None
    assert task['title'] == "Test Task"
    assert task['content'] == "Test content"


def test_update_task(temp_tasks_dir):
    """Test updating a task"""
    manager = TaskManager(temp_tasks_dir)
    
    # Create task
    manager.create_task(
        path="test/task1.md",
        title="Test Task",
        content="Original content",
        metadata={"status": "open"}
    )
    
    # Update task
    result = manager.update_task(
        path="test/task1.md",
        content="Updated content",
        metadata={"status": "done"}
    )
    
    assert result is not None
    assert result['content'] == "Updated content"
    assert result['metadata']['status'] == "done"


def test_delete_task(temp_tasks_dir):
    """Test deleting a task"""
    manager = TaskManager(temp_tasks_dir)
    
    # Create task
    manager.create_task(
        path="test/task1.md",
        title="Test Task"
    )
    
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
        metadata={"status": "open", "tags": ["auth", "backend"]}
    )
    manager.create_task(
        "test/task2.md",
        "UI Task",
        content="Design login page",
        metadata={"status": "in-progress", "tags": ["frontend"]}
    )
    
    # Search by text
    results = searcher.search(query="authentication")
    assert len(results) > 0
    assert "Authentication Task" in results[0]['title']
    
    # Search by metadata
    results = searcher.search(metadata_filters={"status": "open"})
    assert len(results) == 1
    
    # Search by tags
    results = searcher.search_by_tags(["auth"])
    assert len(results) == 1


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
    
    assert structure['type'] == 'directory'
    assert len(structure['children']) > 0


def test_tags(temp_tasks_dir):
    """Test tag operations"""
    manager = TaskManager(temp_tasks_dir)
    searcher = TaskSearcher(temp_tasks_dir)
    
    # Create tasks with tags
    manager.create_task(
        "project1/task1.md",
        "Task 1",
        metadata={"tags": ["python", "backend"]}
    )
    manager.create_task(
        "project1/task2.md",
        "Task 2",
        metadata={"tags": ["javascript", "frontend"]}
    )
    
    # Get all tags
    tags = searcher.get_all_tags()
    assert "python" in tags
    assert "backend" in tags
    assert "javascript" in tags
    assert "frontend" in tags


def test_path_validation_create_task(temp_tasks_dir):
    """Test that create_task requires a project folder in path"""
    manager = TaskManager(temp_tasks_dir)
    
    # Valid path with project folder should work
    result = manager.create_task("project1/task1.md", "Valid Task")
    assert result['path'] == "project1/task1.md"
    
    # Invalid path without project folder should raise ValueError
    with pytest.raises(ValueError) as exc_info:
        manager.create_task("task1.md", "Invalid Task")
    
    assert "project folder" in str(exc_info.value).lower()
    assert "task1.md" in str(exc_info.value)


def test_path_validation_read_task(temp_tasks_dir):
    """Test that read_task requires a project folder in path"""
    manager = TaskManager(temp_tasks_dir)
    
    # Create a valid task first
    manager.create_task("project1/task1.md", "Test Task")
    
    # Valid path should work
    task = manager.read_task("project1/task1.md")
    assert task is not None
    
    # Invalid path without project folder should raise ValueError
    with pytest.raises(ValueError) as exc_info:
        manager.read_task("task1.md")
    
    assert "project folder" in str(exc_info.value).lower()


def test_path_validation_update_task(temp_tasks_dir):
    """Test that update_task requires a project folder in path"""
    manager = TaskManager(temp_tasks_dir)
    
    # Create a valid task first
    manager.create_task("project1/task1.md", "Test Task")
    
    # Valid path should work
    result = manager.update_task("project1/task1.md", title="Updated Task")
    assert result is not None
    
    # Invalid path without project folder should raise ValueError
    with pytest.raises(ValueError) as exc_info:
        manager.update_task("task1.md", title="Invalid Update")
    
    assert "project folder" in str(exc_info.value).lower()


def test_path_validation_delete_task(temp_tasks_dir):
    """Test that delete_task requires a project folder in path"""
    manager = TaskManager(temp_tasks_dir)
    
    # Create a valid task first
    manager.create_task("project1/task1.md", "Test Task")
    
    # Invalid path without project folder should raise ValueError
    with pytest.raises(ValueError) as exc_info:
        manager.delete_task("task1.md")
    
    assert "project folder" in str(exc_info.value).lower()
    
    # Valid path should work
    success = manager.delete_task("project1/task1.md")
    assert success is True


def test_path_validation_move_task(temp_tasks_dir):
    """Test that move_task requires a project folder in both paths"""
    manager = TaskManager(temp_tasks_dir)
    
    # Create a valid task first
    manager.create_task("project1/task1.md", "Test Task")
    
    # Valid paths should work
    success = manager.move_task("project1/task1.md", "project2/task1.md")
    assert success is True
    
    # Create another task for testing invalid paths
    manager.create_task("project1/task2.md", "Test Task 2")
    
    # Invalid old_path without project folder should raise ValueError
    with pytest.raises(ValueError) as exc_info:
        manager.move_task("task2.md", "project1/task3.md")
    
    assert "project folder" in str(exc_info.value).lower()
    
    # Invalid new_path without project folder should raise ValueError
    with pytest.raises(ValueError) as exc_info:
        manager.move_task("project1/task2.md", "task3.md")
    
    assert "project folder" in str(exc_info.value).lower()


def test_path_validation_with_subdirectories(temp_tasks_dir):
    """Test that paths with multiple levels still work"""
    manager = TaskManager(temp_tasks_dir)
    
    # Valid path with multiple subdirectories should work
    result = manager.create_task(
        "project1/features/auth/task1.md", 
        "Multi-level Task"
    )
    assert result['path'] == "project1/features/auth/task1.md"
    
    # Can read it back
    task = manager.read_task("project1/features/auth/task1.md")
    assert task is not None
    assert task['title'] == "Multi-level Task"
