"""
Task Manager - Core functionality for managing markdown task cards
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import frontmatter


class TaskManager:
    """Manages markdown task cards in a hierarchical folder structure"""
    
    def __init__(self, base_path: str = None):
        """
        Initialize TaskManager
        
        Args:
            base_path: Root directory for task cards. Defaults to TASKMASTER_TASKS_DIR env var or ./tasks
        """
        if base_path is None:
            base_path = os.environ.get('TASKMASTER_TASKS_DIR', './tasks')
        self.base_path = Path(base_path).resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def create_task(
        self, 
        path: str, 
        title: str, 
        content: str = "", 
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new task card
        
        Args:
            path: Relative path within base_path (e.g., 'project1/task1.md')
            title: Task title
            content: Task content (markdown)
            metadata: Additional metadata (status, priority, tags, etc.)
        
        Returns:
            Dict with task information
        """
        full_path = self.base_path / path
        
        # Ensure parent directories exist
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create frontmatter document
        post = frontmatter.Post(content)
        post['title'] = title
        post['created'] = datetime.now().isoformat()
        post['updated'] = datetime.now().isoformat()
        
        if metadata:
            post.metadata.update(metadata)
        
        # Write to file
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(frontmatter.dumps(post))
        
        return {
            'path': str(full_path.relative_to(self.base_path)),
            'title': title,
            'created': post['created'],
            'metadata': post.metadata
        }
    
    def read_task(self, path: str) -> Optional[Dict[str, Any]]:
        """
        Read a task card
        
        Args:
            path: Relative path within base_path
        
        Returns:
            Dict with task information or None if not found
        """
        full_path = self.base_path / path
        
        if not full_path.exists():
            return None
        
        with open(full_path, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)
        
        return {
            'path': str(full_path.relative_to(self.base_path)),
            'title': post.get('title', ''),
            'content': post.content,
            'metadata': post.metadata
        }
    
    def update_task(
        self, 
        path: str, 
        title: Optional[str] = None,
        content: Optional[str] = None, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update an existing task card
        
        Args:
            path: Relative path within base_path
            title: New title (optional)
            content: New content (optional)
            metadata: Metadata to update (merged with existing)
        
        Returns:
            Dict with updated task information or None if not found
        """
        full_path = self.base_path / path
        
        if not full_path.exists():
            return None
        
        with open(full_path, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)
        
        if title is not None:
            post['title'] = title
        
        if content is not None:
            post.content = content
        
        if metadata:
            post.metadata.update(metadata)
        
        post['updated'] = datetime.now().isoformat()
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(frontmatter.dumps(post))
        
        return {
            'path': str(full_path.relative_to(self.base_path)),
            'title': post.get('title', ''),
            'content': post.content,
            'metadata': post.metadata
        }
    
    def delete_task(self, path: str) -> bool:
        """
        Delete a task card
        
        Args:
            path: Relative path within base_path
        
        Returns:
            True if deleted, False if not found
        """
        full_path = self.base_path / path
        
        if not full_path.exists():
            return False
        
        full_path.unlink()
        
        # Clean up empty parent directories
        try:
            parent = full_path.parent
            while parent != self.base_path and not any(parent.iterdir()):
                parent.rmdir()
                parent = parent.parent
        except:
            pass
        
        return True
    
    def list_tasks(
        self, 
        subpath: str = "", 
        recursive: bool = True,
        include_content: bool = False
    ) -> List[Dict[str, Any]]:
        """
        List all tasks in a directory
        
        Args:
            subpath: Subdirectory within base_path (empty for all)
            recursive: Include subdirectories
            include_content: Include full content in results (token-expensive)
        
        Returns:
            List of task dictionaries
        """
        search_path = self.base_path / subpath if subpath else self.base_path
        
        if not search_path.exists():
            return []
        
        pattern = "**/*.md" if recursive else "*.md"
        tasks = []
        
        for md_file in search_path.glob(pattern):
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    post = frontmatter.load(f)
                
                task_info = {
                    'path': str(md_file.relative_to(self.base_path)),
                    'title': post.get('title', ''),
                    'metadata': post.metadata
                }
                
                if include_content:
                    task_info['content'] = post.content
                
                tasks.append(task_info)
            except Exception as e:
                # Skip files that can't be parsed
                continue
        
        return tasks
    
    def get_structure(self, subpath: str = "") -> Dict[str, Any]:
        """
        Get the hierarchical structure of tasks
        
        Args:
            subpath: Subdirectory within base_path
        
        Returns:
            Nested dictionary representing folder structure
        """
        search_path = self.base_path / subpath if subpath else self.base_path
        
        def build_tree(path: Path) -> Dict[str, Any]:
            tree = {
                'type': 'directory',
                'name': path.name or 'root',
                'children': []
            }
            
            try:
                for item in sorted(path.iterdir()):
                    if item.is_dir():
                        tree['children'].append(build_tree(item))
                    elif item.suffix == '.md':
                        try:
                            with open(item, 'r', encoding='utf-8') as f:
                                post = frontmatter.load(f)
                            
                            tree['children'].append({
                                'type': 'task',
                                'name': item.name,
                                'path': str(item.relative_to(self.base_path)),
                                'title': post.get('title', ''),
                                'metadata': {k: v for k, v in post.metadata.items() 
                                           if k in ['status', 'priority', 'tags']}
                            })
                        except:
                            continue
            except:
                pass
            
            return tree
        
        return build_tree(search_path)
    
    def move_task(self, old_path: str, new_path: str) -> bool:
        """
        Move/rename a task card
        
        Args:
            old_path: Current relative path
            new_path: New relative path
        
        Returns:
            True if moved, False if source not found or destination exists
        """
        old_full = self.base_path / old_path
        new_full = self.base_path / new_path
        
        if not old_full.exists() or new_full.exists():
            return False
        
        new_full.parent.mkdir(parents=True, exist_ok=True)
        old_full.rename(new_full)
        
        # Clean up empty parent directories
        try:
            parent = old_full.parent
            while parent != self.base_path and not any(parent.iterdir()):
                parent.rmdir()
                parent = parent.parent
        except:
            pass
        
        return True
