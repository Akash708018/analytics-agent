"""CSV and delimited-text loading into DuckDB.

Phase 2, Step 5. See build guide Section 4.2 and 4.2.1 (the verified read path),
locked decision 4 (previews never load the whole file), F5 (everything typed
VARCHAR).

The interface is deliberately primitive: paths, integers and lists of strings,
not an IngestSpec. Phase 3 builds IngestSpec and maps it onto these same
arguments, so nothing here is rewritten -- and Phase 2 stays testable without
pulling the conversation layer forward.

The 4.2.1 rule, verified on DuckDB 1.5.5:

    Naive:   read_csv(path, header=true)
             -> a second header row is read as data, every column VARCHAR
    Correct: read_csv(path, skip=N, header=false, names=[...])
             -> units BIGINT, unit_price DOUBLE, order_date DATE

Two behaviours found by testing, both guarded against below:

  1. Supplying MORE names than the file has columns raises a sniffing error.
  2. Supplying FEWER names does NOT error. DuckDB pads the tail with
     'column7'. Data is not shifted, but you get a silently misnamed column.
     load_csv counts the columns first and refuses on any mismatch.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import duckdb

from ..config import CSV_PREVIEW_LINES, DEFAULT_NA_VALUES
from ..util import db
from . import sizegate

# A dataset name becomes a SQL identifier. Validate rather than quote-and-hope.
_IDENT_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,62}$")


@dataclass
class LoadResult:
    dataset_name: str
    row_count: int
    column_count: int
    columns: list[tuple[str, str]] = field(default_factory=list)
    gate_verdict: str = "OK"
    gate_message: str = ""

    def summary(self) -> str:
        lines = [
            f"Loaded {self.dataset_name}: {self.row_count:,} rows, "
            f"{self.column_count} columns.",
        ]
        if self.gate_message:
            lines.append(f"NOTE: {self.gate_message}")
        lines.append("")
        lines.append("| column | type |")
        lines.append("| --- | --- |")
        for name, dtype in self.columns:
            lines.append(f"| {name} | {dtype} |")
        return "\n".join(lines)


class LoadRefused(Exception):
    """Raised when a load must not proceed. The message is user-facing and
    always carries a NEXT STEP -- see guide 8.2."""


def validate_dataset_name(name: str) -> str:
    if not _IDENT_RE.match(name or ""):
        raise LoadRefused(
            f"BLOCKED: {name!r} is not a usable table name.\n"
            f"WHY: it becomes a SQL identifier, so it must start with a letter "
            f"and contain only letters, digits and underscores.\n"
            f"NEXT STEP: try something like 'sales_2024'."
        )
    return name


def _sql_path(path: Path) -> str:
    """Single-quoted SQL literal for a path. Doubles any embedded quote."""
    return "'" + str(path).replace("'", "''") + "'"


def preview_lines(path: Path | str, n: int = CSV_PREVIEW_LINES) -> list[str]:
    """First n lines as raw text. Never reads the whole file.

    Locked decision 4. This is what the header conversation in Phase 3 reads,
    and why a 1.5 GB file previews instantly: it stops after n lines rather
    than scanning to the end.
    """
    path = Path(path)
    out: list[str] = []
    with path.open("r", encoding="utf-8", errors="replace", newline="") as f:
        for i, line in enumerate(f):
            if i >= n:
                break
            out.append(line.rstrip("\r\n"))
    return out


def detect_column_count(
    con: duckdb.DuckDBPyConnection, path: Path, skip: int = 0
) -> int:
    """Column count without reading any rows.

    LIMIT 0 makes DuckDB sniff the structure and return no data, so this costs
    a few kilobytes regardless of file size.
    """
    rel = con.execute(
        f"SELECT * FROM read_csv({_sql_path(path)}, skip={skip}, "
        f"header=false, sample_size=1024) LIMIT 0"
    )
    return len(rel.description)


def load_csv(
    con: duckdb.DuckDBPyConnection,
    path: Path | str,
    dataset_name: str,
    header_rows: int = 1,
    names: list[str] | None = None,
    na_values: list[str] | None = None,
    delimiter: str | None = None,
    sample_size: int = 20_480,
    replace: bool = True,
) -> LoadResult:
    """Load a delimited file into a DuckDB table and register it.

    header_rows  How many rows at the top are headers, not data. 1 is the
                 ordinary case. 2 or more requires `names`, because DuckDB
                 cannot infer a column name spread over several rows.
    names        Explicit column names. Required when header_rows != 1.
                 Must match the file's column count exactly.
    na_values    Tokens to read as NULL. Defaults to config.DEFAULT_NA_VALUES.
                 Empty fields are already NULL in DuckDB without this.
    sample_size  Rows scanned to infer types. DuckDB's default is 20480. Pass
                 -1 to scan everything -- correct but slow on a large file, and
                 worth it when a column turns to text partway down.
    """
    path = Path(path)
    validate_dataset_name(dataset_name)

    gate = sizegate.check_file(path, "csv")
    if not gate.allowed:
        raise LoadRefused(gate.message)

    if header_rows < 0:
        raise LoadRefused(
            f"BLOCKED: header_rows cannot be negative (got {header_rows}).\n"
            f"NEXT STEP: use 0 for a file with no header, 1 for the usual case."
        )
    if header_rows != 1 and not names:
        raise LoadRefused(
            f"BLOCKED: header_rows={header_rows} but no column names were "
            f"given.\n"
            f"WHY: with more than one header row DuckDB cannot work out the "
            f"names itself, and reading them as data types every column "
            f"VARCHAR.\n"
            f"NEXT STEP: pass names=[...], one per column."
        )

    # Guard the silent-padding trap: fewer names than columns does not error
    # in DuckDB, it just appends 'column7'.
    if names:
        actual = detect_column_count(con, path, skip=header_rows)
        if len(names) != actual:
            raise LoadRefused(
                f"BLOCKED: {len(names)} column names given but "
                f"{path.name} has {actual} columns after skipping "
                f"{header_rows} header row(s).\n"
                f"WHY: DuckDB does not reject a short list -- it silently names "
                f"the leftover column 'column{actual - 1}', which is easy to "
                f"miss.\n"
                f"NEXT STEP: supply exactly {actual} names, or check "
                f"header_rows is right."
            )

    nulls = list(na_values) if na_values is not None else list(DEFAULT_NA_VALUES)

    opts = [f"sample_size={sample_size}", f"nullstr={nulls!r}"]
    if delimiter:
        opts.append(f"delim='{delimiter}'")
    if names:
        opts.append(f"skip={header_rows}")
        opts.append("header=false")
        opts.append(f"names={names!r}")
    else:
        opts.append("header=true" if header_rows == 1 else "header=false")
        if header_rows > 1:
            opts.append(f"skip={header_rows}")

    verb = "CREATE OR REPLACE TABLE" if replace else "CREATE TABLE"
    sql = (f'{verb} "{dataset_name}" AS SELECT * FROM '
           f'read_csv({_sql_path(path)}, {", ".join(opts)})')

    try:
        con.execute(sql)
    except duckdb.Error as exc:
        raise LoadRefused(
            f"BLOCKED: DuckDB could not read {path.name}.\n"
            f"DuckDB said: {exc}\n"
            f"NEXT STEP: check the delimiter and the number of header rows. "
            f"Call preview_lines() to see the first lines as they actually are."
        ) from exc

    rows, cols = db.table_shape(con, dataset_name)
    columns = [
        (r[0], r[1])
        for r in con.execute(
            """SELECT column_name, data_type FROM information_schema.columns
               WHERE table_schema='main' AND table_name=?
               ORDER BY ordinal_position""",
            [dataset_name],
        ).fetchall()
    ]

    db.register_dataset(
        con,
        dataset_name=dataset_name,
        source_type="csv",
        source_detail=str(path),
        row_count=rows,
        column_count=cols,
        notes=f"header_rows={header_rows}",
    )

    return LoadResult(
        dataset_name=dataset_name,
        row_count=rows,
        column_count=cols,
        columns=columns,
        gate_verdict=gate.verdict.value,
        gate_message=gate.message,
    )
