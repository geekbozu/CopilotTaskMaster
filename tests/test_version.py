import importlib
import os
import shutil
from pathlib import Path

import pytest

import taskmaster


def reload_pkg():
    importlib.invalidate_caches()
    importlib.reload(taskmaster)
    return taskmaster.__version__


def test_env_var_overrides(tmp_path, monkeypatch):
    monkeypatch.setenv("TASKMASTER_VERSION", "1.2.3-env")
    v = reload_pkg()
    assert v == "1.2.3-env"
    monkeypatch.delenv("TASKMASTER_VERSION")
    reload_pkg()


def test_scm_written_version_used(tmp_path, monkeypatch):
    # Simulate setuptools_scm write_to file by creating taskmaster/_version.py
    ver_file = Path(taskmaster.__file__).parent / "_version.py"
    backup = None
    if ver_file.exists():
        backup = ver_file.read_text()
    try:
        ver_file.write_text('version = "9.9.9-test"\n')
        v = reload_pkg()
        assert v == "9.9.9-test"
    finally:
        if backup is not None:
            ver_file.write_text(backup)
        else:
            try:
                ver_file.unlink()
            except FileNotFoundError:
                pass
        reload_pkg()
