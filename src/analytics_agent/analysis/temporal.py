"""The calendar every temporal analysis reads its periods off.

Section 9: **calendar_coverage runs mandatorily before any other temporal
analysis.** Read as a call order that rule is unenforceable -- nothing checks,
and the case it exists for is a model answering a trend question directly. Read
as a query shape it enforces itself: every Tier 3 analysis takes its periods
from a generated series and LEFT JOINs the table onto it, so an absent period
is in the result whether or not anybody remembered to look for one. That is
P9-D12, and this module is where it lives once instead of five times.

The rulings carried here, all measured in Step 1 and listed in decisions.md:

  P9-D2   bounds are truncated to the grain before the series is built. A
          series started at an observed minimum of 2017-01-31 walks Feb 28,
          Mar 28, Apr 28 -- February's clamp sticks -- and none of those is a
          value date_trunc will ever produce.
  P9-D3   generate_series includes its upper bound and range does not. On
          Olist that difference is October 2018, the last month in the window.
  P9-D4   date_trunc returns TIMESTAMP whatever the column was, so a period is
          labelled by strftime rather than rendered raw.
  P9-D13  bounds come from analysis_window when there is one and from the
          observed span when there is not, and the caller says which.
  P9-D15  five grains, each with its own step and label. Quarter has no
          strftime code of its own.
  P9-D18  no tz-aware value is fetched into Python. DuckDB builds a TIMESTAMPTZ
          with pytz, which this project does not depend on.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import NamedTuple

from ..util.sql_guard import quote_identifier
from .base import ParamsInvalid

__all__ = [
    "DEFAULT_GRAIN",
    "GRAINS",
    "Calendar",
    "Edges",
    "calendar_for",
    "edges",
    "longest_run",
    "per_period_sql",
    "require_date_column",
]

# date_trunc's name for the period, the step generate_series walks, and how the
# period is labelled.
GRAINS: dict[str, tuple[str, str]] = {
    "day": ("INTERVAL 1 DAY", "strftime({p}, '%Y-%m-%d')"),
    "week": ("INTERVAL 1 WEEK", "strftime({p}, '%Y-%m-%d')"),
    "month": ("INTERVAL 1 MONTH", "strftime({p}, '%Y-%m')"),
    "quarter": ("INTERVAL 3 MONTH", "strftime({p}, '%Y-Q') || quarter({p})"),
    "year": ("INTERVAL 1 YEAR", "strftime({p}, '%Y')"),
}

DEFAULT_GRAIN = "month"


@dataclass(frozen=True)
class Calendar:
    """Everything a temporal query needs about the periods it will report."""

    key: str            # date_trunc's name for the grain
    step: str           # the interval generate_series walks
    label_sql: str      # a format string taking {p}, the period expression
    lo_sql: str         # the lower bound, untruncated, as SQL
    hi_sql: str         # the upper bound, untruncated, as SQL
    bounds_text: str    # what the summary calls the source of the bounds
    windowed: bool      # whether those bounds came from the contract
    start: str = ""     # the window's first day, ISO, when there is a window
    end: str = ""       # the window's last day, ISO, when there is a window

    def label(self, period_expr: str) -> str:
        return self.label_sql.format(p=period_expr)


def require_date_column(contract) -> str:
    """The contract's date column, or the refusal that names what to do.

    P9-D10: the column's TYPE is the contract's check, made at confirm time.
    This asks only whether one was named.
    """
    date_column = getattr(contract, "date_column", None)
    if not date_column:
        raise ValueError(
            f"{contract.dataset_name} has no date_column, so there is no "
            f"calendar to check. confirm_dataset_contract with date_column set "
            f"is what fixes that -- and until it is set, no temporal analysis "
            f"can say what period a row belongs to."
        )
    return date_column


def calendar_for(gate, scope, date_column: str, grain: str) -> Calendar:
    """Resolve the grain and the bounds. No query runs here."""
    key = str(grain).strip().lower()
    if key not in GRAINS:
        raise ParamsInvalid(
            f"grain must be one of {', '.join(sorted(GRAINS))}; got {grain!r}."
        )
    step, label_sql = GRAINS[key]

    table = quote_identifier(scope.dataset_name)
    col = quote_identifier(date_column)
    window = getattr(gate.contract, "analysis_window", None)
    if window is not None:
        return Calendar(
            key=key, step=step, label_sql=label_sql,
            lo_sql=f"CAST(DATE '{window.start.isoformat()}' AS TIMESTAMP)",
            hi_sql=f"CAST(DATE '{window.end.isoformat()}' AS TIMESTAMP)",
            bounds_text=(
                f"the declared analysis window, {window.start.isoformat()} to "
                f"{window.end.isoformat()}"
            ),
            windowed=True,
            start=window.start.isoformat(),
            end=window.end.isoformat(),
        )
    return Calendar(
        key=key, step=step, label_sql=label_sql,
        lo_sql=f"(SELECT min({col}) FROM {table} WHERE {scope.where})",
        hi_sql=f"(SELECT max({col}) FROM {table} WHERE {scope.where})",
        bounds_text="the observed span of " + date_column,
        windowed=False,
    )


def per_period_sql(
    cal: Calendar,
    table: str,
    col: str,
    where: str,
    inner: list[str],
    outer: list[str],
) -> str:
    """One row per period in the calendar, whether or not the table has rows.

    `inner` are the aggregates computed per period inside the GROUP BY, each
    already aliased. `outer` are the expressions selected against the joined
    row -- that is where a caller decides what an absent period looks like,
    because coalesce(count, 0) is right and coalesce(avg, 0) is a lie.
    """
    aggregates = ", ".join(inner)
    selected = ", ".join(outer)
    return (
        f"WITH b AS (SELECT date_trunc('{cal.key}', {cal.lo_sql}) AS lo, "
        f"date_trunc('{cal.key}', {cal.hi_sql}) AS hi), "
        f"s AS (SELECT x.g AS period FROM b, "
        f"generate_series(b.lo, b.hi, {cal.step}) x(g)), "
        f"d AS (SELECT date_trunc('{cal.key}', {col}) AS m, {aggregates} "
        f"FROM {table} WHERE {where} AND {col} IS NOT NULL GROUP BY 1) "
        f"SELECT {cal.label('s.period')}, {selected} "
        f"FROM s LEFT JOIN d ON d.m = s.period ORDER BY s.period"
    )


def longest_run(flags: list[bool]) -> int:
    """The longest unbroken run of True, in order.

    Six missing months in runs of three, two and one is a different story from
    six scattered ones: a run is a feed that stopped, a scatter is a business
    that was quiet. Computed from rows already fetched rather than by a second
    query, so there is no second answer to disagree with the first.
    """
    longest = current = 0
    for flag in flags:
        current = current + 1 if flag else 0
        longest = max(longest, current)
    return longest


class Edges(NamedTuple):
    """What the bounds and the data have to say about each other.

    Every value here is text or a boolean because none of it is fetched as a
    datetime: DuckDB builds a TIMESTAMPTZ with pytz, which this project does
    not depend on, so the comparisons happen in SQL where the types live
    (P9-D18). `lo` and `hi` are the untruncated bounds; `seen_lo` and `seen_hi`
    are what the column actually holds inside the scope.
    """

    lo: str | None
    hi: str | None
    seen_lo: str | None
    seen_hi: str | None
    undated: int
    starts_late: bool
    ends_early: bool
    opens_mid_period: bool


def edges(con, cal: Calendar, table: str, col: str, where: str) -> Edges:
    """The bounds, the observed span, the undated count, and three verdicts.

    The undated count is here because `scope_for` cannot supply it: it fills
    `no_date` only when a window exists, since with no window there is nothing
    to be outside of, so a NULL-dated row sits in `analysed` and would vanish
    between the periods (P9-D14).
    """
    if cal.windowed:
        tests = (
            f", CAST(seen_lo AS DATE) > DATE '{cal.start}'"
            f", CAST(seen_hi AS DATE) < DATE '{cal.end}'"
            f", lo <> date_trunc('{cal.key}', lo)"
        )
    else:
        tests = ", false, false, false"
    row = con.execute(
        f"WITH e AS (SELECT {cal.lo_sql} AS lo, {cal.hi_sql} AS hi, "
        f"(SELECT min({col}) FROM {table} WHERE {where}) AS seen_lo, "
        f"(SELECT max({col}) FROM {table} WHERE {where}) AS seen_hi, "
        f"(SELECT count(*) FILTER (WHERE {col} IS NULL) FROM {table} "
        f"WHERE {where}) AS undated) "
        f"SELECT CAST(lo AS VARCHAR), CAST(hi AS VARCHAR), "
        f"CAST(seen_lo AS VARCHAR), CAST(seen_hi AS VARCHAR), undated"
        f"{tests} FROM e"
    ).fetchall()[0]
    return Edges(*row)
