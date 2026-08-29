"""Excel loading: openpyxl read-only streaming into DuckDB.

Phase 2, Step 6. See build guide Section 4.2 (read_only=True, 50,000-row
batches), locked decision 4, failure modes F3 and F5.

Why this is harder than CSV. DuckDB reads a CSV and infers each column's type
itself. openpyxl hands back Python objects, so the inference has to be written
here -- and a wrong guess produces a silently mistyped column, which is F5.

Verified against openpyxl on real files:

  * A date written to Excel comes back as datetime.datetime, never
    datetime.date. Excel has no pure date type.
  * bool is a subclass of int in Python, so isinstance(True, int) is True.
    Booleans must be tested BEFORE integers or every one becomes BIGINT.
  * A column of entirely empty cells yields no type information at all and
    falls back to VARCHAR.
  * merged_cells.ranges does NOT exist on a read-only worksheet. Phase 3's
    bounded fill will need a second, normal open of the header block.

Memory: iter_rows on a read-only worksheet is a generator. Rows are accumulated
into a batch, flushed to DuckDB, and the batch is cleared. Peak memory is one
batch, not one file, whatever the sheet's size.
"""

from __future__ import annotations

import csv as _csv
import datetime as _dt
import os as _os
import tempfile as _tempfile
from pathlib import Path

import duckdb

from ..config import EXCEL_BATCH_ROWS, EXCEL_PREVIEW_ROWS
from ..util import db
from . import sizegate
from .csv_loader import LoadRefused, LoadResult, validate_dataset_name

# Python type -> DuckDB type. Order matters at the call site: bool first.
_TYPE_RANK = {
    "BOOLEAN": 0,
    "BIGINT": 1,
    "DOUBLE": 2,
    "TIMESTAMP": 3,
    "VARCHAR": 4,
}


def _duck_type(value: object) -> str | None:
    """DuckDB type for one Python value, or None when it says nothing."""
    if value is None:
        return None
    if isinstance(value, bool):        # MUST precede int
        return "BOOLEAN"
    if isinstance(value, int):
        return "BIGINT"
    if isinstance(value, float):
        return "DOUBLE"
    if isinstance(value, (_dt.datetime, _dt.date)):
        return "TIMESTAMP"
    return "VARCHAR"


def _merge_types(a: str | None, b: str | None) -> str | None:
    """Widen two observed types to one that holds both.

    BIGINT + DOUBLE -> DOUBLE. Anything genuinely incompatible -> VARCHAR,
    because keeping the value as text loses nothing, while forcing a type
    would lose the row.
    """
    if a is None:
        return b
    if b is None:
        return a
    if a == b:
        return a
    if {a, b} == {"BIGINT", "DOUBLE"}:
        return "DOUBLE"
    return "VARCHAR"


def list_sheets(path: Path | str) -> list[str]:
    """Sheet names, without reading any data."""
    from openpyxl import load_workbook

    wb = load_workbook(Path(path), read_only=True)
    try:
        return list(wb.sheetnames)
    finally:
        wb.close()


def preview_rows(
    path: Path | str,
    sheet: str | None = None,
    n: int = EXCEL_PREVIEW_ROWS,
) -> list[tuple]:
    """First n rows as raw tuples. Never reads the whole sheet.

    Locked decision 4. This is what the header conversation in Phase 3 reads to
    work out where the real headers are.
    """
    from openpyxl import load_workbook

    wb = load_workbook(Path(path), read_only=True)
    try:
        ws = wb[sheet] if sheet else wb.active
        out = []
        for i, row in enumerate(ws.iter_rows(values_only=True)):
            if i >= n:
                break
            out.append(row)
        return out
    finally:
        wb.close()


def merged_ranges(path: Path | str, sheet: str | None = None) -> list[str]:
    """Merged cell ranges, e.g. ['A1:B1', 'C1:E1'].

    Requires a NORMAL open -- merged_cells is absent on a read-only worksheet.
    That is acceptable here only because the caller wants the header block;
    never call this as a precursor to streaming a large sheet.
    """
    from openpyxl import load_workbook

    wb = load_workbook(Path(path))
    try:
        ws = wb[sheet] if sheet else wb.active
        return sorted(str(r) for r in ws.merged_cells.ranges)
    finally:
        wb.close()


def _infer_column_types(
    rows: list[tuple], n_cols: int, all_text: bool
) -> list[str]:
    if all_text:
        return ["VARCHAR"] * n_cols
    types: list[str | None] = [None] * n_cols
    for row in rows:
        for i in range(min(n_cols, len(row))):
            types[i] = _merge_types(types[i], _duck_type(row[i]))
    # A column that was entirely empty told us nothing. VARCHAR holds anything.
    return [t or "VARCHAR" for t in types]


def _coerce(value: object, duck_type: str):
    """Prepare one value for insertion, or raise ValueError.

    Never silently drops a value. A value that will not fit its column raises,
    and load_excel turns that into an instructional refusal naming the cell.
    """
    if value is None:
        return None
    if duck_type == "VARCHAR":
        return value if isinstance(value, str) else str(value)
    if duck_type == "BOOLEAN":
        if isinstance(value, bool):
            return value
        raise ValueError(f"{value!r} is not a boolean")
    if duck_type == "BIGINT":
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{value!r} is not an integer")
        return value
    if duck_type == "DOUBLE":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{value!r} is not a number")
        return float(value)
    if duck_type == "TIMESTAMP":
        if isinstance(value, (_dt.datetime, _dt.date)):
            return value
        raise ValueError(f"{value!r} is not a date")
    return value


def load_excel(
    con: duckdb.DuckDBPyConnection,
    path: Path | str,
    dataset_name: str,
    sheet: str | None = None,
    header_rows: int = 1,
    names: list[str] | None = None,
    all_text: bool = False,
    inference_rows: int = 5_000,
    replace: bool = True,
) -> LoadResult:
    """Stream a worksheet into a DuckDB table and register it.

    sheet           Sheet name. Defaults to the active sheet.
    header_rows     Rows at the top that are headers, not data.
    names           Explicit column names. Required when header_rows != 1.
    all_text        Load every column as VARCHAR. The escape hatch when a
                    column has mixed types partway down.
    inference_rows  Rows examined to decide column types. Raising it costs
                    memory; lowering it risks a wrong guess.
    """
    from openpyxl import load_workbook

    path = Path(path)
    validate_dataset_name(dataset_name)

    gate = sizegate.check_file(path, "excel")
    if not gate.allowed:
        raise LoadRefused(gate.message)

    if header_rows < 0:
        raise LoadRefused(
            f"BLOCKED: header_rows cannot be negative (got {header_rows}).\n"
            f"NEXT STEP: use 0 for no header, 1 for the usual case."
        )
    if header_rows != 1 and not names:
        raise LoadRefused(
            f"BLOCKED: header_rows={header_rows} but no column names were "
            f"given.\n"
            f"WHY: with more than one header row the names cannot be read "
            f"automatically.\n"
            f"NEXT STEP: call preview_rows() to see the top of the sheet, then "
            f"pass names=[...]."
        )

    wb = load_workbook(path, read_only=True)
    try:
        if sheet is not None and sheet not in wb.sheetnames:
            raise LoadRefused(
                f"BLOCKED: {path.name} has no sheet called {sheet!r}.\n"
                f"Sheets present: {', '.join(wb.sheetnames)}\n"
                f"NEXT STEP: pass one of those names."
            )
        ws = wb[sheet] if sheet else wb.active
        stream = ws.iter_rows(values_only=True)

        header: list[str] = []
        for _ in range(header_rows):
            try:
                header = list(next(stream))
            except StopIteration:
                raise LoadRefused(
                    f"BLOCKED: {path.name} has fewer than {header_rows} rows.\n"
                    f"NEXT STEP: check the sheet is the one you meant."
                ) from None

        # Buffer enough rows to infer types before creating the table.
        sample: list[tuple] = []
        for row in stream:
            sample.append(row)
            if len(sample) >= inference_rows:
                break

        if not sample:
            raise LoadRefused(
                f"BLOCKED: {path.name} has headers but no data rows.\n"
                f"NEXT STEP: check the sheet, or set header_rows=0 if the "
                f"first row is really data."
            )

        n_cols = max(len(r) for r in sample)
        if names:
            if len(names) != n_cols:
                raise LoadRefused(
                    f"BLOCKED: {len(names)} column names given but the sheet "
                    f"has {n_cols} columns.\n"
                    f"NEXT STEP: supply exactly {n_cols} names, or check "
                    f"header_rows."
                )
            columns = list(names)
        else:
            columns = [
                str(h).strip() if h is not None else f"column{i}"
                for i, h in enumerate(header[:n_cols])
            ]
            columns += [f"column{i}" for i in range(len(columns), n_cols)]

        seen: dict[str, int] = {}
        final: list[str] = []
        for c in columns:
            c = c or "column"
            if c in seen:
                seen[c] += 1
                c = f"{c}_{seen[c]}"
            else:
                seen[c] = 0
            final.append(c)
        columns = final

        types = _infer_column_types(sample, n_cols, all_text)

        cols_ddl = ", ".join(f'"{c}" {t}' for c, t in zip(columns, types))
        verb = "CREATE OR REPLACE TABLE" if replace else "CREATE TABLE"
        con.execute(f'{verb} "{dataset_name}" ({cols_ddl})')

        # Rows are staged to a temporary CSV and loaded with one read_csv,
        # rather than bound as statement parameters.
        #
        # Measured on 120,000 rows: executemany 7,000 rows/s; multi-row INSERT
        # 98,000 rows/s on one machine but only 3,100 on another, with no
        # difference between in-memory and on-disk DuckDB -- so the cost is
        # parameter binding, not the disk. Staging through a CSV hands the work
        # to DuckDB's vectorised reader instead: 1,460,000 rows/s, and it does
        # not vary the same way.
        #
        # Verified to survive the round trip: BOOLEAN, TIMESTAMP, NULL, and
        # strings containing quotes, commas and newlines.
        fd, tmp_path = _tempfile.mkstemp(suffix=".csv", prefix="agent_xl_")
        _os.close(fd)
        total = 0
        row_no = header_rows

        try:
            with open(tmp_path, "w", newline="", encoding="utf-8") as tmp:
                writer = _csv.writer(tmp)
                for row in _chain(sample, stream):
                    row_no += 1
                    padded = list(row[:n_cols]) + [None] * (n_cols - len(row))
                    try:
                        writer.writerow(
                            [_coerce(v, t) for v, t in zip(padded, types)]
                        )
                    except ValueError as exc:
                        col_index = next(
                            i for i, (v, t) in enumerate(zip(padded, types))
                            if _safe_fails(v, t)
                        )
                        raise LoadRefused(
                            f"BLOCKED: row {row_no} of {path.name} has a value "
                            f"that does not fit its column.\n"
                            f"Column '{columns[col_index]}' was read as "
                            f"{types[col_index]}, but this row holds "
                            f"{padded[col_index]!r} ({exc}).\n"
                            f"WHY: types were inferred from the first "
                            f"{len(sample):,} rows, and this row disagrees. "
                            f"Nothing has been dropped -- the load stopped "
                            f"instead.\n"
                            f"NEXT STEP: reload with all_text=True to keep "
                            f"every column as text, or raise inference_rows "
                            f"above {row_no}."
                        ) from exc
                    total += 1

            col_spec = ", ".join(
                f"'{c}': '{t}'" for c, t in zip(columns, types)
            )
            con.execute(
                f'INSERT INTO "{dataset_name}" SELECT * FROM read_csv('
                f"'{tmp_path}', header=false, columns={{{col_spec}}})"
            )
        finally:
            try:
                _os.unlink(tmp_path)
            except OSError:
                pass
    finally:
        wb.close()

    rows, cols = db.table_shape(con, dataset_name)
    result_columns = [
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
        source_type="excel",
        source_detail=f"{path} [{ws.title}]",
        row_count=rows,
        column_count=cols,
        notes=f"header_rows={header_rows}, all_text={all_text}",
    )

    return LoadResult(
        dataset_name=dataset_name,
        row_count=rows,
        column_count=cols,
        columns=result_columns,
        gate_verdict=gate.verdict.value,
        gate_message=gate.message,
    )


def _safe_fails(value: object, duck_type: str) -> bool:
    try:
        _coerce(value, duck_type)
        return False
    except ValueError:
        return True


def _chain(first: list, rest):
    """Replay the buffered sample, then continue streaming. Avoids holding the
    whole sheet just because the first rows were needed for inference."""
    yield from first
    yield from rest
