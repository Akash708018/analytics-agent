"""One declared measure, per period, over a calendar that includes its gaps.

**A trend request on a dataset with a missing quarter must produce a gap
warning, not a clean line** -- the build guide's own words, at the Phase 13
gold questions. That is not a check bolted on at the end here: the periods come
from `temporal.per_period_sql`, so an absent period is a row in the table with
no value in it, and the warning is a description of rows that are already
there. A version of this that grouped the table would have nothing to warn
about, because the absent period would not be in its output to notice.

**The direction is two endpoints, not a fit.** The first and last periods that
hold rows, and the difference between them, stated as such. No slope, no
moving average, no percentage unless both ends are non-zero. A line fitted
across the gap this analysis exists to report would be the gap warning's own
counter-example, and `growth_decomposition` is where the arithmetic of change
belongs.

**The aggregate is the contract's.** `AGG_SQL[agg]` and nothing else. A measure
declared `agg='none'` is refused rather than averaged: a unit price summed or
averaged per month produces a number nothing downstream can detect as wrong,
which is the reason `Measure.agg` has no default.
"""

from __future__ import annotations

from typing import Any

from ..util.sql_guard import quote_identifier
from .base import LostRows, number
from .declared import AGG_SQL, agg_of, require_measure
from .registry import Output, register
from .temporal import (
    DEFAULT_GRAIN,
    calendar_for,
    edges,
    longest_run,
    per_period_sql,
    require_date_column,
)

__all__ = ["trend"]

# Absent periods named before the list becomes a count, as calendar_coverage
# names them. A reader needs enough to go and look, not a second table.
NAMED_MISSING = 12


@register(
    "trend",
    tier=3,
    summary="One declared measure per period, over a calendar that includes "
            "the periods holding no rows, with the gaps named and the "
            "direction read from the first and last periods that do.",
)
def trend(con, gate, scope, measure: str, grain: str = DEFAULT_GRAIN,
          **params) -> Output:
    if params:
        raise TypeError(
            f"trend takes measure and grain; got {', '.join(sorted(params))}."
        )

    contract = gate.contract
    m = require_measure(contract, measure)
    agg = agg_of(m)
    unit = getattr(m, "unit", None) or ""

    if agg in (None, "none"):
        raise ValueError(
            f"measure {measure!r} declares agg={agg!r}, so it does not combine "
            f"across rows and a value per period would be invented rather than "
            f"computed. Summing or averaging a non-additive measure produces a "
            f"number nothing downstream can detect as wrong. Trend a measure "
            f"that declares how it combines, or ask for frequency instead."
        )
    if agg not in AGG_SQL:
        raise ValueError(
            f"measure {measure!r} declares agg={agg!r}, which this analysis "
            f"cannot compute. Known: {', '.join(sorted(AGG_SQL))}, none."
        )

    date_column = require_date_column(contract)
    cal = calendar_for(gate, scope, date_column, grain)
    key = cal.key

    table = quote_identifier(scope.dataset_name)
    col = quote_identifier(date_column)
    value = AGG_SQL[agg].format(col=quote_identifier(measure))

    e = edges(con, cal, table, col, scope.where)
    headers = ["period", f"{measure} ({agg})" + (f" {unit}" if unit else ""),
               "rows"]
    summary = [scope.method_note(), *gate.caveats]

    if e.lo is None or e.hi is None:
        summary.append(
            f"No row in scope has a {date_column}, so there are no periods to "
            f"trend over. {e.undated:,} analysed row(s) are undated."
            if e.undated
            else "No rows are in scope, so there are no periods to trend over."
        )
        return Output(headers=headers, rows=[], summary=summary, label="trend")

    fetched = con.execute(per_period_sql(
        cal, table, col, scope.where,
        inner=[f"{value} AS v", "count(*) AS n"],
        outer=["d.v", "coalesce(d.n, 0)"],
    )).fetchall()

    held = sum(r[2] for r in fetched)
    if held + e.undated != scope.analysed:
        raise LostRows(
            f"trend lost rows: its {len(fetched)} {key}(s) hold {held:,} "
            f"row(s) and {e.undated:,} are undated, against "
            f"{scope.analysed:,} analysed."
        )

    # An absent period gets a blank, never a zero. coalesce(count, 0) is right
    # and coalesce(sum, 0) is a claim that the period happened and came to
    # nothing, which is the one thing the data does not say.
    rows: list[list[Any]] = [
        [r[0], number(r[1]) if r[1] is not None else "", number(r[2])]
        for r in fetched
    ]
    missing = [r[0] for r in fetched if not r[2]]
    present = [r for r in fetched if r[2]]

    summary.append(
        f"{len(fetched):,} {key}(s) between {fetched[0][0]} and "
        f"{fetched[-1][0]}, generated from {cal.bounds_text} and truncated to "
        f"the {key}."
    )

    if missing:
        named = ", ".join(missing[:NAMED_MISSING])
        rest = len(missing) - NAMED_MISSING
        summary.append(
            f"{len(missing):,} {key}(s) hold no rows and are blank above, not "
            f"zero: {named}" + (f", and {rest:,} more." if rest > 0 else ".")
        )
        summary.append(
            f"The longest unbroken gap is "
            f"{longest_run([not r[2] for r in fetched]):,} {key}(s). A line "
            f"drawn through these points crosses those periods without "
            f"stopping, and nothing here says whether the business paused or "
            f"the feed did."
        )

    if len(present) >= 2:
        first, last = present[0], present[-1]
        summary.append(
            f"From {number(first[1])} in {first[0]} to {number(last[1])} in "
            f"{last[0]}. That is two endpoints and the periods between them, "
            f"not a fitted line -- with {len(missing):,} {key}(s) absent, a fit "
            f"would be interpolating over them."
            if missing else
            f"From {number(first[1])} in {first[0]} to {number(last[1])} in "
            f"{last[0]}. That is two endpoints, not a fitted line."
        )
    elif len(present) == 1:
        summary.append(
            f"Only {present[0][0]} holds rows, so there is no direction to "
            f"read."
        )

    if cal.windowed and e.opens_mid_period:
        summary.append(
            f"The window opens on {cal.start}, inside the {key} beginning "
            f"{fetched[0][0]}, so that {key} covers part of its period and can "
            f"read low for that reason alone."
        )
    if e.undated:
        summary.append(
            f"{e.undated:,} analysed row(s) have no {date_column} and are in "
            f"no {key} above."
        )
    return Output(headers=headers, rows=rows, summary=summary, label="trend")
