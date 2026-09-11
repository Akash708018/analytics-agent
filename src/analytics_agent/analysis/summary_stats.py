"""What the contract's measures come to, over the rows the contract allows.

**Not every column.** `profile_dataset` already answers "what is in this
table", for every column, with no contract needed. If this walked every column
too there would be two profilers, gated differently and formatted differently,
and one day they would disagree about a number somebody had quoted. So this
answers a narrower question: what do the measures the contract DECLARES come
to, under its window and its exclusions. Everything it does not summarise it
names, and says why -- a reader who wanted a column back learns that declaring
it as a measure is how to ask.

**The aggregate is the contract's, not a guess.** `Measure.agg` has no default
on purpose: LookML, Cube and MetricFlow all require it, because the guess that
gets guessed is `sum` and summing a unit price or a rate produces a number
nothing downstream can detect as wrong. Two cases follow and they are not the
same case:

* `agg` unset -- nobody has said how this combines, so nothing is aggregated
  and the note says which call fixes it.
* `agg = 'none'` -- somebody decided it is non-additive. A total is WRONG here,
  not merely undeclared, and does not appear even as a convenience. Min, max
  and the counts are still true of it, so they are still reported.

**Values keep their column's type; statistics are computed in floating point.**
`min` and `max` are values out of the column, so a DECIMAL(18,2) money column
reports 10.50 with both its places. `mean`, `median` and `stddev` are derived,
and DuckDB computes `median` of a DECIMAL at the column's own scale: the median
of 10.50 and 20.25 is 15.375 and comes back as `Decimal('15.37')`. Rendered
beside a mean of 15.375 that reads as a bug in one of them. So the median is
taken as `quantile_cont(CAST(col AS DOUBLE), 0.5)` and the two agree.

**Spread is None, never zero.** P8-D9: `stddev` is `stddev_samp`, so a group of
one is NULL. `NumericSummary` said the same thing in Phase 5 -- "a single-row
table has no sample standard deviation ... a zero written in their place would
be a number nobody computed" -- and this follows it rather than inventing a
second way of saying so.
"""

from __future__ import annotations

from typing import Any

from ..util.sql_guard import quote_identifier
from .base import number
from .declared import AGG_SQL, agg_of, column_types, is_numeric
from .registry import Output, register

@register(
    "summary_stats",
    tier=1,
    summary="Each declared measure over the contract's rows: its total under "
            "the declared aggregate, plus n, nulls, min, max, mean, median and "
            "spread.",
)
def summary_stats(con, gate, scope, **params) -> Output:
    """One row per declared measure, and a note naming what was left out."""
    if params:
        raise TypeError(
            f"summary_stats takes no parameters; got {', '.join(sorted(params))}. "
            f"It summarises the measures the contract declares."
        )

    contract = gate.contract
    table = quote_identifier(scope.dataset_name)
    types = column_types(con, scope.dataset_name)
    excluded = set(contract.excluded_columns)

    headers = ["measure", "agg", "unit", "n", "nulls", "total",
               "min", "max", "mean", "median", "stddev"]
    rows: list[list[Any]] = []
    undeclared_reason: list[str] = []

    for measure in contract.measures:
        col = quote_identifier(measure.name)
        agg = agg_of(measure)
        unit = getattr(measure, "unit", None) or ""

        if measure.name in excluded:
            undeclared_reason.append(
                f"{measure.name} is in excluded_columns and was not read"
            )
            continue

        numeric = is_numeric(types.get(measure.name, ""))
        stats = ["", "", "", "", ""] if not numeric else None

        if agg is None:
            counts = con.execute(
                f"SELECT count(*), count({col}) FROM {table} WHERE {scope.where}"
            ).fetchall()[0]
            rows.append([measure.name, "(not declared)", unit,
                         number(counts[1]), number(counts[0] - counts[1]),
                         "", "", "", "", "", ""])
            undeclared_reason.append(
                f"{measure.name} has no declared aggregate, so nothing was "
                f"totalled for it -- confirm_dataset_contract with agg set is "
                f"what fixes that"
            )
            continue

        total_sql = "NULL" if agg == "none" else AGG_SQL.get(agg, "").format(col=col)
        if not total_sql:
            raise ValueError(
                f"measure {measure.name!r} declares agg={agg!r}, which this "
                f"analysis cannot compute. Known: "
                f"{', '.join(sorted(AGG_SQL))}, none."
            )

        if numeric:
            row = con.execute(
                f"SELECT count(*), count({col}), {total_sql}, min({col}), "
                f"max({col}), avg({col}), quantile_cont(CAST({col} AS DOUBLE), 0.5), "
                f"stddev({col}) "
                f"FROM {table} WHERE {scope.where}"
            ).fetchall()[0]
        else:
            # A measure on a non-numeric column: the counts and the extremes
            # are true, an average is not. Reported rather than refused,
            # because a date measure with agg=min is a legitimate thing to
            # declare and the blank cells say which parts do not apply.
            row = con.execute(
                f"SELECT count(*), count({col}), {total_sql}, min({col}), "
                f"max({col}), NULL, NULL, NULL FROM {table} WHERE {scope.where}"
            ).fetchall()[0]

        total = "not additive" if agg == "none" else number(row[2])
        rows.append([
            measure.name, agg, unit,
            number(row[1]), number(row[0] - row[1]), total,
            number(row[3]), number(row[4]),
            number(row[5]), number(row[6]), number(row[7]),
        ])

    summary = [scope.method_note()]
    summary += list(gate.caveats)
    if undeclared_reason:
        summary += undeclared_reason

    skipped = []
    if contract.primary_key:
        skipped.append(f"key column(s) {', '.join(contract.primary_key)}")
    undeclared = [
        name for name, dtype in types.items()
        if is_numeric(dtype)
        and name not in {m.name for m in contract.measures}
        and name not in contract.primary_key
        and name not in excluded
    ]
    if undeclared:
        skipped.append(f"undeclared numeric column(s) {', '.join(undeclared)}")
    if skipped:
        summary.append(
            "Not summarised: " + "; ".join(skipped)
            + ". A column is summarised here when the contract declares it as a "
              "measure; profile_dataset describes every column without one."
        )
    if any(r[10] is None or r[10] == "" for r in rows):
        summary.append(
            "A blank spread is not zero: stddev is the sample standard "
            "deviation and one row has none."
        )

    return Output(headers=headers, rows=rows, summary=summary,
                  label="summary_stats")
