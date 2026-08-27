"""Workspace paths and reset.

The workspace id is a PARAMETER, never generated at import. Claude Desktop keeps
this process alive across chats, so a module-level uuid would leak state between
unrelated tasks. Track A passes a stable id; Track B will pass a session id.
"""
import shutil
from pathlib import Path

from .config import WORKSPACE_ROOT, DEFAULT_WORKSPACE_ID


def workspace_dir(workspace_id: str = DEFAULT_WORKSPACE_ID) -> Path:
    d = WORKSPACE_ROOT / workspace_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def duckdb_path(workspace_id: str = DEFAULT_WORKSPACE_ID) -> Path:
    return workspace_dir(workspace_id) / "session.duckdb"


def outputs_dir(workspace_id: str = DEFAULT_WORKSPACE_ID) -> Path:
    d = workspace_dir(workspace_id) / "outputs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def reset(workspace_id: str = DEFAULT_WORKSPACE_ID) -> dict:
    """Delete everything in this workspace. Returns what was removed."""
    d = WORKSPACE_ROOT / workspace_id
    if not d.exists():
        return {"existed": False, "removed_files": 0, "bytes": 0}
    files = [p for p in d.rglob("*") if p.is_file()]
    total = sum(p.stat().st_size for p in files)
    shutil.rmtree(d)
    workspace_dir(workspace_id)
    return {"existed": True, "removed_files": len(files), "bytes": total}