"""
Utilities for TaskMaster shared by CLI and MCP adapters
"""

from typing import Any


def project_resolution_error_msg(exc: Exception) -> str:
    """Format a consistent user-facing error message when project resolution fails.

    Returns a short sentence that suggests remedies (use `--project` or prefix the path).
    """
    return f"✗ {exc}. Provide a project with `--project <name>` or prefix the path with 'project/'."
