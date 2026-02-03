"""
CopilotTaskMaster - Markdown task card management with MCP integration
"""

import os
from importlib.metadata import PackageNotFoundError, version as _version

# Resolve package version with a simple precedence:
# 1) TASKMASTER_VERSION env var (CI / Docker build-arg)
# 2) setuptools_scm-generated file `taskmaster/_version.py` (if present)
# 3) installed package metadata (importlib.metadata)
# 4) fallback to "0.0.0"

v = os.environ.get("TASKMASTER_VERSION")
if v:
    __version__ = v
else:
    # Prefer the file written by setuptools_scm at build time
    ver_file = os.path.join(os.path.dirname(__file__), "_version.py")
    if os.path.exists(ver_file):
        try:
            data = {}
            with open(ver_file, "r", encoding="utf-8") as f:
                exec(f.read(), data)
            __version__ = data.get("version") or data.get("__version__")
            if not __version__:
                raise ValueError("no version in _version.py")
        except Exception:
            __version__ = "0.0.0"
    else:
        try:
            __version__ = _version("CopilotTaskMaster")
        except PackageNotFoundError:
            __version__ = "0.0.0"

from .task_manager import TaskManager
from .search import TaskSearcher

__all__ = ["TaskManager", "TaskSearcher", "__version__"]
