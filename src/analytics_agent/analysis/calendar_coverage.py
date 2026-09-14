"""Which periods the data covers, and which ones are not there at all.

**Absence cannot be selected from the data.** A GROUP BY over the date column
returns the periods that have rows; a period with no rows has no row of its own
to return, so it is not in the output as a zero -- it is not in the output.
Measured in Step 1 (P9-D1): four months and a NULL group where five months were
in the span. So the periods come off a generated calendar and the table is LEFT
JOINed onto it, and every later Tier 3 analysis reads its periods the same way.

**The calendar is generated from truncated bounds.** P9-D2: a monthly series
started at an observed minimum of 2017-01-31 walks Feb 28, Mar 28, Apr 28 --
February's clamp sticks -- and none of those is a value date_trunc will ever
produce, so every period would read as missing. The bounds are truncated to the
grain first, in SQL, and `generate_series` is used rather than `range` because
it includes the upper bound (P9-D3); `range` drops the last period, which on
Olist is October 2018.

**A window and a span are not the same claim.** P9-D9: `analysis_window` is a
decision somebody made and the observed span is a fact about the data. Both can
bound a calendar and the summary says which one did. Phase 4 already ruled that
the window is reported and never proposed, so this does not invent one when the
contract has none.

**An undated row is not a missing period.** P9-D5: its period is in the window
and the row is in scope. When the contract has no window, `scope_for` leaves
those rows in `analysed` -- there is no window to be outside of -- so they are
counted here and named, and the reconciliation below expects them.
"""

from __future__ import annotations

from typing import Any

from ..util.sql_guard import quote_identifier
from .base import LostRows, ParamsInvalid, number
from .declared import column_types
from .registry import Output, register

__all__ = ["GRAINS", "calendar_coverage"]

# date_trunc's name for the period, the step generate_series walks, and how the
# period is labelled. P9-D4: date_trunc returns a TIMESTAMP whatever the source
# column was, so a month printed raw reads as a day and every grain is labelled
# rather than rendered. Quarter has no strftime code of its own (Step 1, F21).
GRAINS: dict[str, tuple[str, str]] = {
    "day": ("INTERVAL 1 DAY", "strftime({p}, '%Y-%m-%d')"),
    "week": ("INTERVAL 1 WEEK", "strftime({p}, '%Y-%m-%d')"),
    "month": ("INTERVAL 1 MONTH", "strftime({p}, '%Y-%m')"),
    "quarter": ("INTERVAL 3 MONTH", "strftime({p}, '%Y-Q') || quarter({p})"),
    "year": ("INTERVAL 1 YEAR", "strftime({p}, '%Y')"),
}

DEFAULT_GRAIN = "month"

# How many absent periods are named before the list becomes a count. A reader
# needs the names to go and look; a reader given 300 names has been given a
# second table inside a sentence. The remainder is stated, never dropped.
NAMED_MISSING = 12


def _runs(flags: list[bool]) -> int:
    """The longest unbroken run of True in order.

    Six missing months in runs of three, two and one is a different story from
    six scattered ones: a run is a feed that stopped, a scatter is a business
    that was quiet. Computed from the rows already fetched rather than by a
    second query, so there is no second answer to disagree with the first.
    """
    longest = current = 0
    for flag in flags:
        current = current + 1 if flag else 0
        longest = max(longest, current)
    return longest


@register(
    "calendar_coverage",
    tier=3,
    summary="Which periods of the contract's date column hold rows and which "
            "are absent entirely, at a grain you choose, with the longest "
            "unbroken gap named.",
)
def calendar_coverage(con, gate, scope, grain: str = DEFAULT_GRAIN, **params) -> Output:
    if params:
        raise TypeError(
            f"calendar_coverage takes grain; got {', '.join(sorted(params))}."
        )
    key = str(grain).strip().lower()
    if key not in GRAINS:
        raise ParamsInvalid(
            f"grain must be one of {', '.join(sorted(GRAINS))}; got {grain!r}."
        )
    step, label_sql = GRAINS[key]

    contract = gate.contract
    date_column = getattr(contract, "date_column", None)
    if not date_column:
        raise ValueError(
            f"{contract.dataset_name} has no date_column, so there is no "
            f"calendar to check. confirm_dataset_contract with date_column set "
            f"is what fixes that -- and until it is set, no temporal analysis "
            f"can say what period a row belongs to."
        )

    table = quote_identifier(scope.dataset_name)
    col = quote_identifier(date_column)
    # The column's type is the contract's check, not this one's (P9-D10):
    # dataset_contract refuses a text date at confirm time. It is read here
    # only to decide whether the session zone is worth stating (P9-D7).
    dtype = column_types(con, scope.dataset_name).get(date_column, "")
    tz_aware = "TIME ZONE" in dtype.upper()

    window = getattr(contract, "analysis_window", None)
    if window is not None:
        lo_sql = f"CAST(DATE '{window.start.isoformat()}' AS TIMESTAMP)"
        hi_sql = f"CAST(DATE '{window.end.isoformat()}' AS TIMESTAMP)"
        bounds_text = (
            f"the declared analysis window, {window.start.isoformat()} to "
            f"{window.end.isoformat()}"
        )
    else:
        lo_sql = f"(SELECT min({col}) FROM {table} WHERE {scope.where})"
        hi_sql = f"(SELECT max({col}) FROM {table} WHERE {scope.where})"
        bounds_text = "the observed span of " + date_column

    # Nothing tz-aware is fetched into Python. DuckDB builds a TIMESTAMPTZ
    # value with pytz, which is not a dependency of this project and is absent
    # from a clean environment: a run that only fetched the bounds raised
    # InvalidInputException naming the missing module, and it raised in the
    # measurement, not in the analysis. So the bounds come back as text and
    # every comparison between them is made in SQL, where the types already
    # live. A date is not carried across a language boundary to be compared on
    # the other side.
    if window is not None:
        tests = (
            f", CAST(seen_lo AS DATE) > DATE '{window.start.isoformat()}'"
            f", CAST(seen_hi AS DATE) < DATE '{window.end.isoformat()}'"
            f", lo <> date_trunc('{key}', lo)"
        )
    else:
        tests = ", false, false, false"
    edges = con.execute(
        f"WITH e AS (SELECT {lo_sql} AS lo, {hi_sql} AS hi, "
        f"(SELECT min({col}) FROM {table} WHERE {scope.where}) AS seen_lo, "
        f"(SELECT max({col}) FROM {table} WHERE {scope.where}) AS seen_hi, "
        f"(SELECT count(*) FILTER (WHERE {col} IS NULL) FROM {table} "
        f"WHERE {scope.where}) AS undated) "
        f"SELECT CAST(lo AS VARCHAR), CAST(hi AS VARCHAR), "
        f"CAST(seen_lo AS VARCHAR), CAST(seen_hi AS VARCHAR), undated"
        f"{tests} FROM e"
    ).fetchall()[0]
    (lo, hi, seen_lo, seen_hi, undated,
     starts_late, ends_early, opens_mid_period) = edges

    headers = ["period", "rows"]
    summary = [scope.method_note(), *gate.caveats]

    if lo is None or hi is None:
        summary.append(
            f"No row in scope has a {date_column}, so there is no calendar to "
            f"cover. {undated:,} analysed row(s) are undated."
            if undated
            else f"No rows are in scope, so there is no calendar to cover."
        )
        return Output(headers=headers, rows=[], summary=summary,
                      label="calendar_coverage")

    rows_sql = (
        f"WITH b AS (SELECT date_trunc('{key}', {lo_sql}) AS lo, "
        f"date_trunc('{key}', {hi_sql}) AS hi), "
        f"s AS (SELECT x.g AS period FROM b, "
        f"generate_series(b.lo, b.hi, {step}) x(g)), "
        f"d AS (SELECT date_trunc('{key}', {col}) AS m, count(*) AS n "
        f"FROM {table} WHERE {scope.where} AND {col} IS NOT NULL GROUP BY 1) "
        f"SELECT {label_sql.format(p='s.period')}, coalesce(d.n, 0) "
        f"FROM s LEFT JOIN d ON d.m = s.period ORDER BY s.period"
    )
    fetched = con.execute(rows_sql).fetchall()

    held = sum(r[1] for r in fetched)
    if held + undated != scope.analysed:
        raise LostRows(
            f"calendar_coverage lost rows: its {len(fetched)} {key}(s) hold "
            f"{held:,} row(s) and {undated:,} are undated, against "
            f"{scope.analysed:,} analysed."
        )

    rows: list[list[Any]] = [[r[0], number(r[1])] for r in fetched]
    present = sum(1 for r in fetched if r[1])
    missing = [r[0] for r in fetched if not r[1]]
    longest = _runs([not r[1] for r in fetched])

    summary.append(
        f"{len(fetched):,} {key}(s) between {fetched[0][0]} and "
        f"{fetched[-1][0]}, generated from {bounds_text} and truncated to the "
        f"{key} -- not read off the rows, which is why an absent {key} appears "
        f"here at all."
    )
    if missing:
        named = ", ".join(missing[:NAMED_MISSING])
        rest = len(missing) - NAMED_MISSING
        summary.append(
            f"{present:,} {key}(s) hold rows and {len(missing):,} hold none: "
            f"{named}"
            + (f", and {rest:,} more." if rest > 0 else ".")
        )
        summary.append(
            f"The longest unbroken gap is {longest:,} {key}(s). A gap is not a "
            f"zero -- nothing says whether the business stopped or the feed "
            f"did, and a trend drawn across these periods interpolates over "
            f"them silently."
        )
    else:
        summary.append(
            f"Every {key} in the range holds at least one row, so a trend over "
            f"this column does not cross an absent period."
        )

    if window is not None:
        if starts_late or ends_early:
            summary.append(
                f"The window and the data do not coincide: {date_column} runs "
                f"{seen_lo} to {seen_hi}, and rows outside the window are out "
                f"of scope rather than absent from it."
            )
        if opens_mid_period:
            summary.append(
                f"The window opens on {window.start.isoformat()}, inside the "
                f"{key} beginning {fetched[0][0]}, so that {key} holds part of "
                f"its period and can read low for that reason alone -- a ramp "
                f"at the start of a chart that is not a movement in the data."
            )
    else:
        summary.append(
            f"The range runs {seen_lo} to {seen_hi}, so the first and last "
            f"{key} hold only part of their period's time. On a chart that is "
            f"a ramp at one end and a cliff at the other, and neither is a "
            f"movement in the data."
        )
    if undated:
        summary.append(
            f"{undated:,} analysed row(s) have no {date_column} and are in no "
            f"{key} above. They are not a missing period: their rows are in "
            f"scope and their period is unknown."
        )
    if tz_aware:
        zone = con.execute("SELECT current_setting('TimeZone')").fetchall()[0][0]
        summary.append(
            f"{date_column} is {dtype}, so its periods were cut at midnight in "
            f"{zone}. The same instant falls in a different {key} under a "
            f"different session zone -- measured in Step 1, a value at "
            f"2017-03-14 23:30 UTC lands on the 15th at Asia/Kolkata."
        )
    return Output(headers=headers, rows=rows, summary=summary,
                  label="calendar_coverage")
