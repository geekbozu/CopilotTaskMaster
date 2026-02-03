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

    def _resolve_path(self, project: Optional[str], path: str):
        """Resolve a (project, path) pair into a filesystem Path and a POSIX relative path.

        Rules:
        - If `path` includes a top-level folder (e.g., 'project/file.md'), that folder will be
          treated as the project when `project` is not specified.
        - If `project` is provided and `path` also includes a different project prefix, a
          ValueError is raised to avoid ambiguity.
        - If neither a project argument nor a project prefix in the path is available, a
          ValueError is raised — callers must explicitly provide a project.
        - `path` must be relative and must not contain parent ('..') references.
        """
        p = Path(path)
        if p.is_absolute():
            raise ValueError("path must be relative")
        if any(part == ".." for part in p.parts):
            raise ValueError("path must not contain parent references")

        # If project is not provided, the first path part is treated as project when present.
        if project is None:
            if len(p.parts) >= 2:
                project = p.parts[0]
                rest = Path(*p.parts[1:])
            else:
                # No project specified anywhere: error out — callers must be explicit
                raise ValueError("project must be specified either as argument or as the top-level folder in path")
        else:
            # Project was provided explicitly — interpret the path relative to that project.
            # If the path redundantly includes the same project prefix (e.g., 'proj/file'), strip it.
            if len(p.parts) >= 2 and p.parts[0] == project:
                rest = Path(*p.parts[1:])
            else:
                rest = p

        full_path = self.base_path / project / rest
        relative_posix = full_path.relative_to(self.base_path).as_posix()
        return full_path, relative_posix
    
    def create_task(
        self,
        path: str,
        title: str,
        content: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        project: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new task card
        
        Args:
            path: Relative path within project (e.g., 'task1.md') or with project prefix ('project1/task1.md')
            project: Optional project name. If omitted, project will be inferred from the path or
                     `default_project` will be used if configured.
            title: Task title
            content: Task content (markdown)
            metadata: Additional metadata (status, priority, tags, etc.)
        
        Returns:
            Dict with task information
        """
        full_path, rel_path = self._resolve_path(project, path)

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
            'path': rel_path,
            'title': title,
            'created': post['created'],
            'metadata': post.metadata
        }
    
    def read_task(self, path: str, project: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Read a task card
        
        Args:
            path: Relative path within project or with project prefix
            project: Optional project name to scope the read
        
        Returns:
            Dict with task information or None if not found
        """
        full_path, rel_path = self._resolve_path(project, path)
        
        if not full_path.exists():
            return None
        
        with open(full_path, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)
        
        return {
            'path': rel_path,
            'title': post.get('title', ''),
            'content': post.content,
            'metadata': post.metadata
        }
    
    def update_task(
        self,
        path: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        project: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update an existing task card
        
        Args:
            path: Relative path within project or with project prefix
            project: Optional project name to scope the update
            title: New title (optional)
            content: New content (optional)
            metadata: Metadata to update (merged with existing)
        
        Returns:
            Dict with updated task information or None if not found
        """
        full_path, rel_path = self._resolve_path(project, path)
        
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
            'path': rel_path,
            'title': post.get('title', ''),
            'content': post.content,
            'metadata': post.metadata
        }
    
    def delete_task(self, path: str, project: Optional[str] = None) -> bool:
        """
        Delete a task card
        
        Args:
            path: Relative path within project or with project prefix
            project: Optional project name to scope the delete
        
        Returns:
            True if deleted, False if not found
        """
        full_path, rel_path = self._resolve_path(project, path)
        
        if not full_path.exists():
            return False
        
        full_path.unlink()
        
        # Clean up empty parent directories
        try:
            parent = full_path.parent
            while parent != self.base_path and not any(parent.iterdir()):
                parent.rmdir()
                parent = parent.parent
        except Exception:
            pass
        
        return True
    
    def list_tasks(
        self,
        subpath: str = "",
        recursive: bool = True,
        include_content: bool = False,
        project: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List all tasks in a directory
        
        Args:
            subpath: Subdirectory within project or a project name when `project` is omitted
            recursive: Include subdirectories
            include_content: Include full content in results (token-expensive)
            project: Optional project name to scope the listing
        
        Returns:
            List of task dictionaries
        """
        # Resolve search path based on project and subpath
        if subpath:
            sp = Path(subpath)
            if project is None:
                # If subpath looks like 'project/...' or a single project name, take it as the project
                if len(sp.parts) >= 2:
                    project = sp.parts[0]
                    sub = Path(*sp.parts[1:])
                else:
                    project = sp.parts[0]
                    sub = Path()
            else:
                sub = Path(subpath)
        else:
            sub = Path()

        if project is None:
            search_path = self.base_path
        else:
            search_path = self.base_path / project / sub

        if not search_path.exists():
            return []

        pattern = "**/*.md" if recursive else "*.md"
        tasks = []

        for md_file in search_path.glob(pattern):
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    post = frontmatter.load(f)

                task_info = {
                    'path': md_file.relative_to(self.base_path).as_posix(),
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
    
    def get_structure(self, subpath: str = "", project: Optional[str] = None) -> Dict[str, Any]:
        """
        Get the hierarchical structure of tasks
        
        Args:
            subpath: Subdirectory within base_path or a project/subpath when `project` is omitted
            project: Optional project name to scope the structure
        
        Returns:
            Nested dictionary representing folder structure
        """
        # Resolve search path similarly to `list_tasks` to support the same CLI semantics
        if subpath:
            sp = Path(subpath)
            if project is None:
                # If subpath looks like 'project/...' or a single project name, take it as the project
                if len(sp.parts) >= 2:
                    project = sp.parts[0]
                    sub = Path(*sp.parts[1:])
                else:
                    project = sp.parts[0]
                    sub = Path()
            else:
                sub = Path(subpath)
        else:
            sub = Path()

        # Validate relative path usage
        if any(part == ".." for part in sub.parts):
            raise ValueError("path must not contain parent references")

        if project is None:
            search_path = self.base_path
        else:
            search_path = self.base_path / project / sub

        if project is not None and not search_path.exists():
            # Signal a project resolution failure to callers (CLI / MCP handlers expect ValueError)
            raise ValueError(f"project '{project}' not found")

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
                                'path': item.relative_to(self.base_path).as_posix(),
                                'title': post.get('title', ''),
                                'metadata': {k: v for k, v in post.metadata.items() 
                                           if k in ['status', 'priority', 'tags']}
                            })
                        except Exception:
                            continue
            except Exception:
                pass
            
            return tree
        
        return build_tree(search_path)
    
    def move_task(self, old_path: str, new_path: str, project: Optional[str] = None) -> bool:
        """
        Move/rename a task card
        
        Args:
            old_path: Current relative path within project or with project prefix
            new_path: New relative path within project or with project prefix
            project: Optional project name to scope the move (applies to both paths if provided)
        
        Returns:
            True if moved, False if source not found or destination exists
        """
        old_full, old_rel = self._resolve_path(project, old_path)
        new_full, new_rel = self._resolve_path(project, new_path)
        
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
        except Exception:
            pass
        
        return True
