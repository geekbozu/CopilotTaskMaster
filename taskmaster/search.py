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
                    'path': md_file.relative_to(self.base_path).as_posix(),
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

                # Early exit for performance: stop scanning once we have enough results
                if len(results) >= max_results:
                    break

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
        results = []
        if not tags_lower:
            return results

        for md_file in self.base_path.glob("**/*.md"):
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    post = frontmatter.load(f)

                if self._matches_metadata(post.metadata, {'tags': tags_lower}, match_all=match_all):
                    results.append({
                        'path': md_file.relative_to(self.base_path).as_posix(),
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
                # Normalize tags to lowercase strings
                tags.update(str(t).lower() for t in task_tags)
            except Exception:
                continue
        
        return tags
    
    def _matches_metadata(self, metadata: Dict[str, Any], filters: Dict[str, Any], match_all: bool = False) -> bool:
        """Check if metadata matches all filters (case-insensitive, flexible list/scalar handling)

        For list-valued filters:
            - if match_all is False (default): return True if any filter value is present in metadata
            - if match_all is True: return True only if all filter values are present in metadata
        """
        for key, value in filters.items():
            if key not in metadata:
                return False

            meta_value = metadata[key]

            # Normalize metadata values to list of lowercase strings
            if isinstance(meta_value, str):
                meta_list = [meta_value.lower()]
            elif isinstance(meta_value, list):
                meta_list = [str(v).lower() for v in meta_value]
            else:
                meta_list = [str(meta_value).lower()]

            # Normalize filter values to list of lowercase strings
            if isinstance(value, list):
                filter_list = [str(v).lower() for v in value]
                if match_all:
                    if not all(f in meta_list for f in filter_list):
                        return False
                else:
                    if not any(f in meta_list for f in filter_list):
                        return False
            else:
                if str(value).lower() not in meta_list:
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
