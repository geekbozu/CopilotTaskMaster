"""
Task Searcher - Search functionality for task cards
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
import frontmatter


class TaskSearcher:
    """Searches markdown task cards efficiently"""
    
    def __init__(self, base_path: str):
        """
        Initialize TaskSearcher
        
        Args:
            base_path: Root directory for task cards
        """
        self.base_path = Path(base_path).resolve()
    
    def search(
        self,
        query: str = "",
        metadata_filters: Optional[Dict[str, Any]] = None,
        path_pattern: str = "",
        max_results: int = 50,
        include_content: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Search tasks with text and metadata filters
        
        Args:
            query: Text to search in title and content
            metadata_filters: Dict of metadata key-value pairs to filter by
            path_pattern: Glob pattern to filter paths (e.g., 'project1/**')
            max_results: Maximum number of results to return
            include_content: Include full content in results (token-expensive)
        
        Returns:
            List of matching tasks with relevance scores
        """
        if not self.base_path.exists():
            return []
        
        pattern = f"{path_pattern}/*.md" if path_pattern and not path_pattern.endswith('.md') else "**/*.md"
        results = []
        query_lower = query.lower() if query else ""
        
        for md_file in self.base_path.glob(pattern):
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    post = frontmatter.load(f)
                
                # Apply metadata filters
                if metadata_filters:
                    if not self._matches_metadata(post.metadata, metadata_filters):
                        continue
                
                # Calculate relevance score
                score = 0
                title = post.get('title', '')
                content = post.content
                
                if query_lower:
                    # Title matches are weighted higher
                    if query_lower in title.lower():
                        score += 10
                    
                    # Content matches
                    content_matches = content.lower().count(query_lower)
                    score += content_matches
                    
                    # Skip if no matches
                    if score == 0:
                        continue
                else:
                    # If no query, all filtered tasks get score 1
                    score = 1
                
                result = {
                    'path': str(md_file.relative_to(self.base_path)),
                    'title': title,
                    'score': score,
                    'metadata': post.metadata
                }
                
                if include_content:
                    result['content'] = content
                else:
                    # Include a snippet if there's a query match
                    if query_lower and query_lower in content.lower():
                        result['snippet'] = self._extract_snippet(content, query_lower)
                
                results.append(result)
                
            except Exception as e:
                continue
        
        # Sort by relevance score
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return results[:max_results]
    
    def search_by_tags(
        self,
        tags: List[str],
        match_all: bool = False,
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search tasks by tags
        
        Args:
            tags: List of tags to search for
            match_all: If True, task must have all tags. If False, any tag matches
            max_results: Maximum number of results
        
        Returns:
            List of matching tasks
        """
        tags_lower = [tag.lower() for tag in tags]
        metadata_filter = {'tags': tags_lower} if tags else None
        
        results = []
        
        for md_file in self.base_path.glob("**/*.md"):
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    post = frontmatter.load(f)
                
                task_tags = post.metadata.get('tags', [])
                if isinstance(task_tags, str):
                    task_tags = [task_tags]
                
                task_tags_lower = [tag.lower() for tag in task_tags]
                
                if match_all:
                    if all(tag in task_tags_lower for tag in tags_lower):
                        results.append({
                            'path': str(md_file.relative_to(self.base_path)),
                            'title': post.get('title', ''),
                            'metadata': post.metadata
                        })
                else:
                    if any(tag in task_tags_lower for tag in tags_lower):
                        results.append({
                            'path': str(md_file.relative_to(self.base_path)),
                            'title': post.get('title', ''),
                            'metadata': post.metadata
                        })
                
                if len(results) >= max_results:
                    break
                    
            except Exception:
                continue
        
        return results
    
    def get_all_tags(self) -> Set[str]:
        """
        Get all unique tags across all tasks
        
        Returns:
            Set of all tags
        """
        tags = set()
        
        for md_file in self.base_path.glob("**/*.md"):
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    post = frontmatter.load(f)
                
                task_tags = post.metadata.get('tags', [])
                if isinstance(task_tags, str):
                    task_tags = [task_tags]
                
                tags.update(task_tags)
            except Exception:
                continue
        
        return tags
    
    def _matches_metadata(self, metadata: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if metadata matches all filters"""
        for key, value in filters.items():
            if key not in metadata:
                return False
            
            meta_value = metadata[key]
            
            # Handle list values (like tags)
            if isinstance(value, list):
                if isinstance(meta_value, str):
                    meta_value = [meta_value]
                if not isinstance(meta_value, list):
                    return False
                if not any(v in meta_value for v in value):
                    return False
            else:
                if meta_value != value:
                    return False
        
        return True
    
    def _extract_snippet(self, content: str, query: str, context_chars: int = 100) -> str:
        """Extract a snippet around the query match"""
        query_lower = query.lower()
        content_lower = content.lower()
        
        index = content_lower.find(query_lower)
        if index == -1:
            return content[:200] + "..." if len(content) > 200 else content
        
        start = max(0, index - context_chars)
        end = min(len(content), index + len(query) + context_chars)
        
        snippet = content[start:end]
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."
        
        return snippet
