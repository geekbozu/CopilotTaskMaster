"""
CopilotTaskMaster - Markdown task card management with MCP integration
"""

__version__ = "0.1.0"

from .task_manager import TaskManager
from .search import TaskSearcher

__all__ = ["TaskManager", "TaskSearcher"]
