"""MCP server. Tool REGISTRATION only -- no business logic lives here.

Keeping this file logic-free is what makes Phase 14 (Track B) a transport swap
instead of a rewrite.
"""
from fastmcp import FastMCP

from .config import SERVER_NAME, SERVER_VERSION, DEFAULT_WORKSPACE_ID, MAX_EXCEL_MB, WARN_CSV_MB
from . import workspace
from .util.formatting import format_kv

mcp = FastMCP(name=SERVER_NAME, version=SERVER_VERSION)


@mcp.tool
def ping() -> str:
    """Check the analytics agent server is alive. Call this first if anything
    seems wrong. Takes no arguments and changes nothing."""
    return format_kv([
        ("server", SERVER_NAME),
        ("version", SERVER_VERSION),
        ("status", "alive"),
        ("workspace", DEFAULT_WORKSPACE_ID),
        ("workspace path", workspace.workspace_dir()),
        ("max excel MB", MAX_EXCEL_MB),
        ("warn csv MB", WARN_CSV_MB),
    ])


@mcp.tool
def reset_workspace(confirm: bool = False) -> str:
    """Delete all loaded data, ledgers and outputs in the workspace.

    Requires confirm=True. Call this when starting an unrelated task, because
    this server process stays alive across chats and old datasets remain visible.
    """
    if not confirm:
        return ("BLOCKED: reset_workspace deletes all loaded data and cannot be undone.\n\n"
                "NEXT STEP: ask the user to confirm, then call "
                "reset_workspace(confirm=True).")
    r = workspace.reset()
    return format_kv([
        ("workspace", DEFAULT_WORKSPACE_ID),
        ("existed", r["existed"]),
        ("files removed", r["removed_files"]),
        ("bytes freed", r["bytes"]),
        ("status", "workspace is now empty"),
    ])


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()