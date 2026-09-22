"""CSV and delimited-text loading into DuckDB.

Phase 2, Step 5; extended in Phase 3, Step 5. See build guide Section 4.2 and
4.2.1 (the verified read path), locked decision 4 (previews never load the whole
file), F5 (everything typed VARCHAR), F9 (coercion failures counted, never
silent).

The interface is deliberately primitive: paths, integers and lists of strings,
not an IngestSpec. IngestSpec.to_loader_kwargs() maps onto these same arguments,
so nothing here is rewritten -- and Phase 2 stays testable without pulling the
conversation layer forward.

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

Three more, found while adding footer skipping and coercion counts:

  3. A read_csv scan preserves file order, so `LIMIT n` keeps the FIRST n rows.
     Verified on a 20,000-row file at threads=8 with preserve_insertion_order
     at its default: the kept ids were exactly 1..20000, in order. That is what
     makes footer_skip_rows implementable, since read_csv has no skipfooter.
  4. DuckDB's type inference WIDENS rather than fails. A column of integers
     with one 'oops' in it comes back VARCHAR, not BIGINT-with-an-error. So a
     coercion failure count is only meaningful once the target types are
     pinned, which is what on_error='null' does.
  5. store_rejects=true reports per-column counts, but it drops the whole ROW
     and writes into persistent reject tables that accumulate across loads.
     TRY_CAST is used instead: it nulls the offending CELL, keeps the row, and
     needs no side tables. Verified on a 53-row file -- 53 rows kept,
     {'units': 1, 'price': 2} counted.
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

# What to do with a value that will not fit its column.
ON_ERROR_STOP = "stop"
ON_ERROR_NULL = "null"
ON_ERROR_MODES = (ON_ERROR_STOP, ON_ERROR_NULL)


@dataclass
class LoadResult:
    dataset_name: str
    row_count: int
    column_count: int
    columns: list[tuple[str, str]] = field(default_factory=list)
    gate_verdict: str = "OK"
    gate_message: str = ""
    coercion_failures: dict[str, int] = field(default_factory=dict)
    #: Per column, per token: values read as NULL because they matched a missing-value token.
    #: Blank fields are not listed -- every reader makes them null (Cleanup Step 12, RF-O4).
    null_tokens: dict[str, dict[str, int]] = field(default_factory=dict)

    @property
    def coercion_total(self) -> int:
        return sum(self.coercion_failures.values())

    def summary(self) -> str:
        lines = [
            f"Loaded {self.dataset_name}: {self.row_count:,} rows, "
            f"{self.column_count} columns.",
        ]
        if self.gate_message:
            lines.append(f"NOTE: {self.gate_message}")
        if self.null_tokens:
            total = sum(n for per in self.null_tokens.values() for n in per.values())
            said = "; ".join(
                f"{col} (" + ", ".join(f"{tok!r} {n:,}" for tok, n in sorted(
                    per.items(), key=lambda kv: (-kv[1], kv[0]))) + ")"
                for col, per in self.null_tokens.items())
            lines.append(
                f"NOTE: {total:,} value(s) matched a missing-value token and were read as NULL: "
                f"{said}. A token is data until someone says it means absent -- reload with "
                f"na_values=[] to keep them as text, or na_values=[...] to choose which.")
        if self.coercion_failures:
            worst = ", ".join(
                f"{c} ({n:,})"
                for c, n in sorted(
                    self.coercion_failures.items(), key=lambda kv: -kv[1]
                )
            )
            lines.append(
                f"NOTE: {self.coercion_total:,} value(s) did not fit their "
                f"column and were stored as NULL: {worst}. The rows were kept. "
                f"Reload with on_error='stop' to see the first one, or force "
                f"those columns to text."
            )
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


def validate_on_error(mode: str) -> str:
    if mode not in ON_ERROR_MODES:
        raise LoadRefused(
            f"BLOCKED: on_error={mode!r} is not a mode.\n"
            f"WHY: 'stop' refuses the load at the first value that does not "
            f"fit its column, naming the row. 'null' stores that cell as NULL, "
            f"keeps the row, and counts the failures per column.\n"
            f"NEXT STEP: pass one of {ON_ERROR_MODES}."
        )
    return mode


def _sql_path(path: Path) -> str:
    """Single-quoted SQL literal for a path. Doubles any embedded quote."""
    return "'" + str(path).replace("'", "''") + "'"


def _q(name: str) -> str:
    """Double-quoted SQL identifier. Doubles any embedded quote."""
    return '"' + name.replace('"', '""') + '"'


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


def _sniff_types(
    con: duckdb.DuckDBPyConnection, read_expr: str
) -> list[tuple[str, str]]:
    """(name, DuckDB type) per column, sniffed without loading any rows."""
    rel = con.execute(f"SELECT * FROM {read_expr} LIMIT 0")
    return [(d[0], str(d[1])) for d in rel.description]


def load_csv(
    con: duckdb.DuckDBPyConnection,
    path: Path | str,
    dataset_name: str,
    header_rows: int = 1,
    names: list[str] | None = None,
    na_values: list[str] | None = None,
    delimiter: str | None = None,
    footer_skip_rows: int = 0,
    dtypes: dict[str, str] | None = None,
    on_error: str = ON_ERROR_STOP,
    sample_size: int = 20_480,
    replace: bool = True,
) -> LoadResult:
    """Load a delimited file into a DuckDB table and register it.

    header_rows       How many rows at the top are headers, not data. 1 is the
                      ordinary case. 2 or more requires `names`, because DuckDB
                      cannot infer a column name spread over several rows.
    names             Explicit column names. Required when header_rows != 1.
                      Must match the file's column count exactly.
    na_values         Tokens to read as NULL. Defaults to
                      config.DEFAULT_NA_VALUES. An empty list means no token
                      is null. Empty FIELDS are already NULL in DuckDB either
                      way, so this only ever affects a literal token such as
                      'N/A' or '-'.
    delimiter         Field separator. Sniffed when omitted.
    footer_skip_rows  Data rows at the END of the file to drop -- a totals row,
                      a 'generated on' line. Costs one extra count(*) pass,
                      because read_csv has no skipfooter and the row total has
                      to be known before the tail can be cut.
    dtypes            Pin specific columns to a type, e.g.
                      {'order_id': 'VARCHAR'}. Columns not named here are
                      inferred as usual.
    on_error          'stop' (default) leaves DuckDB to refuse a value that
                      will not convert. 'null' stores that cell as NULL, keeps
                      the row, and counts the failures per column into
                      LoadResult.coercion_failures -- F9.
    sample_size       Rows scanned to infer types. DuckDB's default is 20480.
                      Pass -1 to scan everything -- correct but slow on a large
                      file, and worth it when a column turns to text partway
                      down.
    """
    path = Path(path)
    validate_dataset_name(dataset_name)
    validate_on_error(on_error)

    gate = sizegate.check_file(path, "csv")
    if not gate.allowed:
        raise LoadRefused(gate.message)

    if header_rows < 0:
        raise LoadRefused(
            f"BLOCKED: header_rows cannot be negative (got {header_rows}).\n"
            f"NEXT STEP: use 0 for a file with no header, 1 for the usual case."
        )
    if footer_skip_rows < 0:
        raise LoadRefused(
            f"BLOCKED: footer_skip_rows cannot be negative (got "
            f"{footer_skip_rows}).\n"
            f"NEXT STEP: use 0 to keep every data row."
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

    # An empty list is a legitimate "nothing is a null token", but DuckDB
    # rejects nullstr=[] outright: "requires a non-empty list of possible null
    # strings". Omitting the option is what an empty list has to mean.
    opts = [f"sample_size={sample_size}"]
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

    # The same read with every value as text and no token nulled: what the tokens were, counted
    # after the load (RF-O4). Built before nullstr joins the options, so it cannot drift from them.
    text_read = f'read_csv({_sql_path(path)}, {", ".join(opts + ["all_varchar=true"])})'
    if nulls:
        opts.append(f"nullstr={nulls!r}")
    read_expr = f'read_csv({_sql_path(path)}, {", ".join(opts)})'

    coercion: dict[str, int] = {}
    verb = "CREATE OR REPLACE TABLE" if replace else "CREATE TABLE"

    try:
        if on_error == ON_ERROR_NULL:
            coercion = _load_with_coercion_counts(
                con, read_expr, dataset_name, dtypes, footer_skip_rows, verb
            )
        else:
            select = "SELECT * FROM " + read_expr
            if dtypes:
                sniffed = _sniff_types(con, read_expr)
                select = (
                    "SELECT "
                    + ", ".join(
                        f"CAST({_q(c)} AS {dtypes[c]}) AS {_q(c)}"
                        if c in dtypes
                        else _q(c)
                        for c, _t in sniffed
                    )
                    + " FROM "
                    + read_expr
                )
            if footer_skip_rows:
                select = _apply_footer_skip(con, select, read_expr, footer_skip_rows, path)
            con.execute(f"{verb} {_q(dataset_name)} AS {select}")
    except duckdb.Error as exc:
        raise LoadRefused(
            f"BLOCKED: DuckDB could not read {path.name}.\n"
            f"DuckDB said: {exc}\n"
            f"NEXT STEP: check the delimiter and the number of header rows. "
            f"Call preview_lines() to see the first lines as they actually "
            f"are. If a single bad value is the problem, on_error='null' "
            f"stores it as NULL and counts it instead of stopping."
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

    null_tokens = _count_null_tokens(
        con, text_read, [c for c, _t in columns], [t for t in nulls if t != ""],
        footer_skip_rows, path)

    db.register_dataset(
        con,
        dataset_name=dataset_name,
        source_type="csv",
        source_detail=str(path),
        row_count=rows,
        column_count=cols,
        notes=(
            f"header_rows={header_rows}, footer_skip_rows={footer_skip_rows}, "
            f"on_error={on_error}"
        ),
    )

    return LoadResult(
        dataset_name=dataset_name,
        row_count=rows,
        column_count=cols,
        columns=columns,
        gate_verdict=gate.verdict.value,
        gate_message=gate.message,
        coercion_failures=coercion,
        null_tokens=null_tokens,
    )


def _count_null_tokens(con, text_read: str, columns: list[str], tokens: list[str],
                       footer_skip_rows: int, path: Path) -> dict[str, dict[str, int]]:
    """How many values each missing-value token turned into NULL, per column.

    One more pass over the file, read as text with no token nulled. The load itself cannot say:
    after it, a nulled 'NA' and an empty field are the same NULL. The retail run lost 8,069 'NA'
    and 5,353 '-' from rating this way with nothing in the reply (Cleanup Step 12, RF-O4).
    """
    if not tokens or not columns:
        return {}
    select = f"SELECT * FROM {text_read}"
    if footer_skip_rows:
        select = _apply_footer_skip(con, select, text_read, footer_skip_rows, path)
    pairs = [(c, t) for c in columns for t in tokens]
    exprs = ", ".join(
        f"count(*) FILTER (WHERE {_q(c)} = '{t.replace(chr(39), chr(39) * 2)}')" for c, t in pairs)
    row = con.execute(f"SELECT {exprs} FROM ({select})").fetchone()
    out: dict[str, dict[str, int]] = {}
    for (c, t), n in zip(pairs, row):
        if n:
            out.setdefault(c, {})[t] = n
    return out


def _apply_footer_skip(
    con: duckdb.DuckDBPyConnection,
    select: str,
    read_expr: str,
    footer_skip_rows: int,
    path: Path,
) -> str:
    """Wrap a SELECT so the last `footer_skip_rows` data rows are dropped.

    read_csv has no skipfooter, so the total has to be counted first. A scan
    preserves file order (verified at threads=8 on 20,000 rows), so LIMIT keeps
    the first n rows rather than an arbitrary n.
    """
    total = con.execute(f"SELECT count(*) FROM {read_expr}").fetchone()[0]
    keep = total - footer_skip_rows
    if keep < 0:
        raise LoadRefused(
            f"BLOCKED: footer_skip_rows={footer_skip_rows} but {path.name} has "
            f"only {total} data row(s).\n"
            f"NEXT STEP: lower footer_skip_rows, or check header_rows is right."
        )
    return f"{select} LIMIT {keep}"


def _load_with_coercion_counts(
    con: duckdb.DuckDBPyConnection,
    read_expr: str,
    dataset_name: str,
    dtypes: dict[str, str] | None,
    footer_skip_rows: int,
    verb: str,
) -> dict[str, int]:
    """
    Load with cell-level coercion, counting what did not fit.

    DuckDB's own store_rejects reports per-column counts but drops the whole
    row and writes into persistent side tables. TRY_CAST is used instead: the
    offending cell becomes NULL, the row survives, and the count is one extra
    aggregate over the staged text.

    Target types come from `dtypes` where given and from DuckDB's own sniff
    otherwise. That matters because inference WIDENS -- a column of integers
    containing one 'oops' is sniffed as VARCHAR, and nothing can fail to
    convert to VARCHAR. Pinning the type is what makes a failure countable.
    """
    sniffed = _sniff_types(con, read_expr)
    targets = {c: (dtypes or {}).get(c, t) for c, t in sniffed}

    staging = f"_stage_{dataset_name}"
    text_expr = read_expr.replace("read_csv(", "read_csv(", 1)
    # all_varchar keeps every value as text so TRY_CAST has something to fail
    # against; without it DuckDB has already widened the column.
    text_expr = text_expr[:-1] + ", all_varchar=true)"

    # The footer is trimmed HERE, before anything is counted. Counting first
    # and trimming afterwards reports a coercion failure for a 'TOTAL' row
    # that is then thrown away -- verified: it counted id=1 on a file whose
    # only bad value was in the footer.
    stage_select = f"SELECT * FROM {text_expr}"
    if footer_skip_rows:
        total = con.execute(f"SELECT count(*) FROM {text_expr}").fetchone()[0]
        keep = total - footer_skip_rows
        if keep < 0:
            raise LoadRefused(
                f"BLOCKED: footer_skip_rows={footer_skip_rows} but the file "
                f"has only {total} data row(s).\n"
                f"NEXT STEP: lower footer_skip_rows."
            )
        stage_select = f"{stage_select} LIMIT {keep}"

    con.execute(f"CREATE OR REPLACE TEMP TABLE {_q(staging)} AS {stage_select}")
    try:
        countable = [
            (c, t) for c, t in targets.items() if t.upper() not in ("VARCHAR", "TEXT")
        ]
        coercion: dict[str, int] = {}
        if countable:
            exprs = ", ".join(
                f"count(*) FILTER (WHERE {_q(c)} IS NOT NULL "
                f"AND TRY_CAST({_q(c)} AS {t}) IS NULL) AS {_q(c)}"
                for c, t in countable
            )
            row = con.execute(f"SELECT {exprs} FROM {_q(staging)}").fetchone()
            coercion = {c: n for (c, _t), n in zip(countable, row) if n}

        select = "SELECT " + ", ".join(
            f"TRY_CAST({_q(c)} AS {t}) AS {_q(c)}" if t.upper() not in ("VARCHAR", "TEXT")
            else _q(c)
            for c, t in targets.items()
        ) + f" FROM {_q(staging)}"

        con.execute(f"{verb} {_q(dataset_name)} AS {select}")
        return coercion
    finally:
        con.execute(f"DROP TABLE IF EXISTS {_q(staging)}")
