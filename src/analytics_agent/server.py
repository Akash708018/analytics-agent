"""MCP server: every tool the agent exposes to Claude Desktop.

Phase 2, Step 8. Full re-delivery -- this replaces the Phase 1 server.py.

The Phase 1 tools (ping, reset_workspace) are unchanged in behaviour. Everything
else is new and wires up the loaders from Steps 4 to 7.

Tool annotations (guide 8.1, and the mcp-builder guidance): each tool declares
whether it only reads, whether it can destroy data, and whether calling it twice
is the same as calling it once. Claude Desktop uses these to decide what needs
confirming, so reset_workspace is marked destructive and every describe_/list_
tool is marked read-only.

Every tool returns a string. Refusals carry BLOCKED / WHY / NEXT STEP per
Section 8.2, so a failure tells the user what to do rather than what went wrong
internally.
"""

from __future__ import annotations

from pathlib import Path

from fastmcp import FastMCP

from .config import (
    DEFAULT_WORKSPACE_ID,
    MAX_EXCEL_MB,
    MAX_INLINE_ROWS,
    SERVER_NAME,
    SERVER_VERSION,
    WARN_CSV_MB,
    describe_size_gates,
)
from . import workspace
from .util import db
from .util.formatting import format_kv
from .ingest import csv_loader, excel, postgres, sizegate
from .ingest.csv_loader import LoadRefused

mcp = FastMCP(SERVER_NAME)

READ_ONLY = {"readOnlyHint": True, "openWorldHint": False}
READ_EXTERNAL = {"readOnlyHint": True, "openWorldHint": True}
WRITES = {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True}
DESTRUCTIVE = {"readOnlyHint": False, "destructiveHint": True}


def _refusal(exc: Exception) -> str:
    """Refusals are the user's to read, not a traceback."""
    return str(exc)


# ---------------------------------------------------------------------------
# Phase 1 tools, unchanged
# ---------------------------------------------------------------------------


@mcp.tool(annotations=READ_ONLY)
def ping() -> str:
    """Confirm the analytics agent is running and show its configuration."""
    return format_kv([
        ("server", SERVER_NAME),
        ("version", SERVER_VERSION),
        ("status", "alive"),
        ("workspace", DEFAULT_WORKSPACE_ID),
        ("workspace path", workspace.workspace_dir()),
        ("max excel MB", MAX_EXCEL_MB),
        ("warn csv MB", WARN_CSV_MB),
    ])


@mcp.tool(annotations=DESTRUCTIVE)
def reset_workspace(confirm: bool = False, workspace_id: str | None = None) -> str:
    """Delete everything loaded in the workspace. Cannot be undone.

    Requires confirm=True. Ask the user before calling with confirm=True.
    """
    wid = workspace_id or DEFAULT_WORKSPACE_ID
    if not confirm:
        return (
            "BLOCKED: reset_workspace deletes all loaded data and cannot be "
            "undone.\n\n"
            "NEXT STEP: ask the user to confirm, then call "
            "reset_workspace(confirm=True)."
        )
    info = workspace.reset(wid)
    if not info["existed"]:
        return f"Workspace '{wid}' did not exist. Nothing to remove."
    return (
        f"Workspace '{wid}' reset. Removed {info['removed_files']} file(s), "
        f"{info['bytes'] / 1024 / 1024:.1f} MB."
    )


# ---------------------------------------------------------------------------
# Inspecting before loading
# ---------------------------------------------------------------------------


@mcp.tool(annotations=READ_ONLY)
def check_file(path: str) -> str:
    """Check a file's size against the load limits WITHOUT reading it.

    Call this first when a file might be large. Reports OK, a warning, or a
    refusal explaining what to do instead.
    """
    result = sizegate.check_file(path)
    if result.verdict.value == "OK":
        return f"{Path(path).name}: within limits. Safe to load."
    return f"[{result.verdict.value}] {result.message}"


@mcp.tool(annotations=READ_ONLY)
def preview_file(path: str, sheet: str | None = None, lines: int = 15) -> str:
    """Show the first lines of a CSV or the first rows of an Excel sheet.

    Reads only the top of the file, never the whole thing, so this is safe on a
    file of any size. Use it to see where the real headers are before loading.
    """
    p = Path(path)
    if not p.exists():
        return f"BLOCKED: no file at {path}.\nNEXT STEP: check the path."

    try:
        if sizegate.source_type_for(p) == "excel":
            sheets = excel.list_sheets(p)
            rows = excel.preview_rows(p, sheet, n=lines)
            head = f"{p.name} - sheets: {', '.join(sheets)}\n\n"
            body = "\n".join(f"row {i}: {r}" for i, r in enumerate(rows, 1))
            merged = excel.merged_ranges(p, sheet)
            if merged:
                body += f"\n\nMerged cells: {', '.join(merged)}"
            return head + body
        out = csv_loader.preview_lines(p, n=lines)
        return f"{p.name} - first {len(out)} lines\n\n" + "\n".join(
            f"{i}: {line}" for i, line in enumerate(out, 1)
        )
    except Exception as exc:
        return f"BLOCKED: could not preview {p.name}.\nDetail: {exc}"


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


@mcp.tool(annotations=WRITES)
def load_csv(
    path: str,
    dataset_name: str,
    header_rows: int = 1,
    names: list[str] | None = None,
    delimiter: str | None = None,
    workspace_id: str | None = None,
) -> str:
    """Load a CSV or other delimited file into the workspace.

    header_rows  Rows at the top that are headers. Use 2+ for stacked headers,
                 and then names must be supplied.
    names        Explicit column names, one per column. Required when
                 header_rows is not 1. Call preview_file first to see them.
    """
    con = db.connect(workspace_id or DEFAULT_WORKSPACE_ID)
    try:
        r = csv_loader.load_csv(
            con, path, dataset_name,
            header_rows=header_rows, names=names, delimiter=delimiter,
        )
        return r.summary()
    except LoadRefused as exc:
        return _refusal(exc)
    finally:
        con.close()


@mcp.tool(annotations=WRITES)
def load_excel(
    path: str,
    dataset_name: str,
    sheet: str | None = None,
    header_rows: int = 1,
    names: list[str] | None = None,
    all_text: bool = False,
    workspace_id: str | None = None,
) -> str:
    """Load one worksheet from an Excel file into the workspace.

    all_text  Load every column as text. Use when a column changes type
              partway down and a normal load refuses.
    """
    con = db.connect(workspace_id or DEFAULT_WORKSPACE_ID)
    try:
        r = excel.load_excel(
            con, path, dataset_name,
            sheet=sheet, header_rows=header_rows, names=names,
            all_text=all_text,
        )
        return r.summary()
    except LoadRefused as exc:
        return _refusal(exc)
    finally:
        con.close()


# ---------------------------------------------------------------------------
# Postgres
# ---------------------------------------------------------------------------


@mcp.tool(annotations=READ_ONLY)
def list_sources() -> str:
    """List configured database sources. Connection strings are redacted."""
    return postgres.list_sources()


@mcp.tool(annotations=READ_EXTERNAL)
def describe_source(alias: str, workspace_id: str | None = None) -> str:
    """List the tables and views in a configured database, with row counts.

    Copies nothing. The connection is always read-only.
    """
    con = db.connect(workspace_id or DEFAULT_WORKSPACE_ID)
    try:
        return postgres.describe_source(con, alias)
    except LoadRefused as exc:
        return _refusal(exc)
    finally:
        con.close()


@mcp.tool(annotations=WRITES)
def load_postgres_table(
    alias: str,
    table: str,
    dataset_name: str | None = None,
    schema: str = "public",
    where: str | None = None,
    limit: int | None = None,
    workspace_id: str | None = None,
) -> str:
    """Copy a table from a configured database into the workspace.

    Prefer query_source for exploring -- it copies nothing and has no size
    limit. Copy when the data will be cleaned or joined repeatedly.

    where  SQL predicate applied on the database side, so only matching rows
           are transferred.
    """
    con = db.connect(workspace_id or DEFAULT_WORKSPACE_ID)
    try:
        r = postgres.load_table(
            con, alias, table, dataset_name,
            schema=schema, where=where, limit=limit,
        )
        return r.summary()
    except LoadRefused as exc:
        return _refusal(exc)
    finally:
        con.close()


@mcp.tool(annotations=READ_EXTERNAL)
def query_source(alias: str, sql: str, workspace_id: str | None = None) -> str:
    """Run a read-only SELECT against a configured database without copying it.

    Reference tables as <alias>.<schema>.<table>, for example
    olist.public.orders. Writes are rejected by the connection itself.
    """
    con = db.connect(workspace_id or DEFAULT_WORKSPACE_ID)
    try:
        postgres.attach(con, alias)
        rows = con.execute(sql).fetchmany(MAX_INLINE_ROWS)
        names = [d[0] for d in con.description]
        if not rows:
            return "Query returned no rows."
        lines = ["| " + " | ".join(names) + " |",
                 "| " + " | ".join("---" for _ in names) + " |"]
        lines += ["| " + " | ".join(str(v) for v in r) + " |" for r in rows]
        if len(rows) == MAX_INLINE_ROWS:
            lines.append(f"\n(first {MAX_INLINE_ROWS} rows)")
        return "\n".join(lines)
    except LoadRefused as exc:
        return _refusal(exc)
    except Exception as exc:
        return (f"BLOCKED: query failed.\nDetail: {exc}\n"
                f"NEXT STEP: reference tables as {alias}.schema.table.")
    finally:
        con.close()


# ---------------------------------------------------------------------------
# Workspace state
# ---------------------------------------------------------------------------


@mcp.tool(annotations=READ_ONLY)
def list_datasets(workspace_id: str | None = None) -> str:
    """Show every dataset loaded in the workspace and when it was loaded.

    Load times matter: this server stays running between chats, so a dataset
    may be left over from an earlier conversation.
    """
    return db.workspace_summary(workspace_id or DEFAULT_WORKSPACE_ID)


@mcp.tool(annotations=READ_ONLY)
def describe_dataset(
    dataset_name: str,
    workspace_id: str | None = None,
    sample_rows: int = 5,
) -> str:
    """Describe a loaded dataset: shape, columns, types, nulls, and a sample.

    This is a structural description, not a full profile. Profiling with
    distributions and outliers comes later in the workflow.
    """
    wid = workspace_id or DEFAULT_WORKSPACE_ID
    con = db.connect(wid)
    try:
        if dataset_name not in db.user_tables(con):
            available = ", ".join(db.user_tables(con)) or "(none loaded)"
            return (
                f"BLOCKED: no dataset called '{dataset_name}' in workspace "
                f"'{wid}'.\n"
                f"Loaded: {available}\n"
                f"NEXT STEP: call list_datasets to see what is available."
            )

        rows, ncols = db.table_shape(con, dataset_name)
        record = db.get_dataset(con, dataset_name)

        header = [f"# {dataset_name}", "",
                  f"{rows:,} rows, {ncols} columns"]
        if record:
            header.append(
                f"Source: {record.source_type} - {record.source_detail}"
            )
            header.append(record.age_phrase())
        else:
            header.append(
                "NOTE: no load record. This table was not created by a loader."
            )

        cols = con.execute(
            """SELECT column_name, data_type FROM information_schema.columns
               WHERE table_schema='main' AND table_name=?
               ORDER BY ordinal_position""",
            [dataset_name],
        ).fetchall()

        body = ["", "| column | type | nulls | distinct |",
                "| --- | --- | --- | --- |"]
        for name, dtype in cols:
            n_null, n_distinct = con.execute(
                f'SELECT count(*) FILTER (WHERE "{name}" IS NULL), '
                f'count(DISTINCT "{name}") FROM "{dataset_name}"'
            ).fetchone()
            pct = f" ({n_null / rows * 100:.1f}%)" if rows and n_null else ""
            body.append(
                f"| {name} | {dtype} | {n_null:,}{pct} | {n_distinct:,} |"
            )

        sample = con.execute(
            f'SELECT * FROM "{dataset_name}" LIMIT {int(sample_rows)}'
        ).fetchall()
        names = [c[0] for c in cols]
        body += ["", f"Sample ({len(sample)} rows)", "",
                 "| " + " | ".join(names) + " |",
                 "| " + " | ".join("---" for _ in names) + " |"]
        body += ["| " + " | ".join(str(v) for v in r) + " |" for r in sample]

        return "\n".join(header + body)
    finally:
        con.close()


@mcp.tool(annotations=READ_ONLY)
def show_limits() -> str:
    """Show the size limits that apply to loading on this machine."""
    return describe_size_gates()


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
