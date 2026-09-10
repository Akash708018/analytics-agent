"""How often each value of a dimension appears, and which are the biggest.

Two analyses, one file, because they are the same problem twice: put rows into
groups, sort the groups, cut the list. Everything that is hard about them is
hard about both.

**NULL is a group.** Step 1 measured that GROUP BY keeps it as its own group
and that PIVOT silently drops it, and separately that `''` and NULL are two
distinct values. So the group is labelled `(null)` rather than left blank -- a
blank cell reads as the empty string, which is a different answer.

**A cut list is not a top.** `LIMIT n` over ties answers a different question
than the one asked: Step 1 measured 100,000 rows tied at the top of a 300,000
row table, of which `LIMIT 5` returned five, the same five on five runs, and a
tiebreak on the key changed the answer completely. Both orderings are correct
and neither is "the top 5". So the order is made deterministic with an explicit
tiebreak, AND the number of groups tied at the cut is reported. The second half
is the one that matters: determinism makes the answer repeatable, saying so
makes it honest.

**A share needs a denominator that is a total.** P8-D1 and P8-D2: `x/0` is
`inf` in DuckDB 1.5.5, not an error, and a share of a mixed-sign total is not a
proportion -- four rows summing to zero produced `inf, inf, -inf, -inf` and a
cumulative share ending in `nan`. So the denominator is computed first and the
share column is dropped, with a sentence, when it cannot mean anything.
"""

from __future__ import annotations

from typing import Any

from ..util.sql_guard import quote_identifier
from .base import label, number
from .registry import Output, register

# How many groups a frequency table shows before it stops being a table anyone
# reads. results.py previews 20 rows and pages the rest, so this is not a data
# limit -- the file has everything -- it is what the cut is set to by default.
DEFAULT_LIMIT = 20


def _dimension_names(contract) -> list[str]:
    """The declared dimensions, whether they are strings or objects.

    `dimensions` may hold names or small models; both are read the same way
    rather than one being assumed, for the reason `_agg_of` reads `agg` twice.
    """
    out = []
    for d in getattr(contract, "dimensions", []) or []:
        out.append(str(getattr(d, "name", d)))
    return out


def _require_dimension(contract, column: str) -> str:
    """P8-O1 again: the contract says which columns are dimensions.

    profile_dataset already shows the top values of every column without a
    contract. This one answers the narrower question, so a column nobody
    declared is refused with the list of the ones somebody did -- a caller who
    wanted it is one confirm_dataset_contract away.
    """
    declared = _dimension_names(contract)
    if column in declared:
        return column
    raise ValueError(
        f"{column!r} is not a declared dimension of "
        f"{contract.dataset_name}. Declared: "
        f"{', '.join(declared) if declared else '(none)'}. "
        f"profile_dataset describes any column without a contract; this "
        f"analysis reports the ones the contract names."
    )


def _tie_note(rows: list[list[Any]], value_index: int, shown: int, total_groups: int) -> str | None:
    """How many groups sit at the same value as the last one shown.

    The sentence exists because "top 5" is a claim about the data and LIMIT is
    a claim about the output, and they are only the same claim when nothing
    ties at the cut.
    """
    if shown >= total_groups or not rows:
        return None
    cut_value = rows[shown - 1][value_index]
    tied = sum(1 for r in rows if r[value_index] == cut_value)
    if tied < 2:
        return None
    return (
        f"{tied} group(s) share the value at the cut, so which of them appear "
        f"here is decided by the tiebreak on the group name, not by the data."
    )


@register(
    "frequency",
    tier=1,
    summary="How many rows carry each value of a declared dimension, with the "
            "share of the analysed rows and NULL counted as its own group.",
)
def frequency(con, gate, scope, column: str, limit: int = DEFAULT_LIMIT, **params) -> Output:
    """One row per value of `column`, most frequent first."""
    if params:
        raise TypeError(
            f"frequency takes column and limit; got {', '.join(sorted(params))}."
        )
    if limit < 1:
        raise ValueError(f"limit must be at least 1; got {limit}.")

    contract = gate.contract
    if column in set(contract.excluded_columns):
        raise ValueError(
            f"{column!r} is in excluded_columns: the contract says never to "
            f"read it."
        )
    _require_dimension(contract, column)
    col = quote_identifier(column)
    table = quote_identifier(scope.dataset_name)

    grouped = con.execute(
        f"SELECT {col}, count(*) FROM {table} WHERE {scope.where} "
        f"GROUP BY 1 ORDER BY 2 DESC, 1 ASC"
    ).fetchall()

    total = scope.analysed
    headers = ["value", "rows", "share"]
    summary = [scope.method_note()] + list(gate.caveats)

    if total == 0:
        return Output(headers=headers, rows=[], label="frequency", summary=summary + [
            "No rows are in scope, so there is nothing to count. The counts "
            "above say which rows the contract removed."
        ])

    shown = min(limit, len(grouped))
    rows = [
        [label(v), number(n), f"{n / total * 100:.1f}%"]
        for v, n in grouped[:shown]
    ]

    summary.append(
        f"{len(grouped):,} distinct value(s) of {column}; "
        f"{'all' if shown == len(grouped) else f'the {shown} most frequent'} "
        f"shown. Share is of the {total:,} analysed row(s)."
    )
    tie = _tie_note([[v, n] for v, n in grouped], 1, shown, len(grouped))
    if tie:
        summary.append(tie)
    nulls = next((n for v, n in grouped if v is None), 0)
    if nulls:
        summary.append(
            f"{nulls:,} analysed row(s) have no {column} and are the (null) "
            f"group -- not dropped, and not the empty string, which would be a "
            f"different value."
        )
    return Output(headers=headers, rows=rows, summary=summary, label="frequency")


@register(
    "top_n",
    tier=2,
    summary="The largest groups of a declared dimension by a declared measure, "
            "with the number tied at the cut stated.",
)
def top_n(con, gate, scope, dimension: str, measure: str,
          n: int = 10, **params) -> Output:
    """The `n` biggest values of `dimension`, ranked by `measure`."""
    if params:
        raise TypeError(
            f"top_n takes dimension, measure and n; got "
            f"{', '.join(sorted(params))}."
        )
    if n < 1:
        raise ValueError(f"n must be at least 1; got {n}.")

    contract = gate.contract
    _require_dimension(contract, dimension)
    declared = {m.name: m for m in contract.measures}
    if measure not in declared:
        raise ValueError(
            f"{measure!r} is not a declared measure of {contract.dataset_name}. "
            f"Declared: {', '.join(sorted(declared)) or '(none)'}."
        )
    from .summary_stats import _AGG_SQL, _agg_of  # noqa: PLC0415 -- one map, one place

    agg = _agg_of(declared[measure])
    if agg is None:
        raise ValueError(
            f"measure {measure!r} has no declared aggregate, so there is no "
            f"way to rank by it. confirm_dataset_contract with agg set is what "
            f"fixes that."
        )
    if agg == "none":
        raise ValueError(
            f"measure {measure!r} is declared non-additive, so ranking groups "
            f"by its total would produce an order built from a number the "
            f"contract says is not meaningful."
        )
    if agg not in _AGG_SQL:
        raise ValueError(f"cannot rank by agg={agg!r}.")

    dim = quote_identifier(dimension)
    total_sql = _AGG_SQL[agg].format(col=quote_identifier(measure))
    table = quote_identifier(scope.dataset_name)

    # P8-D4: the tiebreak is on the group name, so the same data gives the same
    # answer twice. It does not make the answer the only correct one, which is
    # what the tie note is for.
    grouped = con.execute(
        f"SELECT {dim}, {total_sql}, count(*) FROM {table} WHERE {scope.where} "
        f"GROUP BY 1 ORDER BY 2 DESC NULLS LAST, 1 ASC"
    ).fetchall()

    summary = [scope.method_note()] + list(gate.caveats)
    headers = ["value", f"{measure} ({agg})", "rows", "share"]

    if not grouped:
        return Output(headers=headers, rows=[], label="top_n", summary=summary + [
            "No rows are in scope, so there is nothing to rank."
        ])

    values = [g[1] for g in grouped if g[1] is not None]
    denominator = sum(values) if agg == "sum" else None
    negatives = sum(1 for v in values if v is not None and v < 0)

    share_ok = denominator is not None and denominator > 0 and negatives == 0
    shown = min(n, len(grouped))
    rows = []
    for value, total, count in grouped[:shown]:
        share = (
            f"{total / denominator * 100:.1f}%"
            if share_ok and total is not None else ""
        )
        rows.append([label(value), number(total), number(count), share])

    summary.append(
        f"{len(grouped):,} group(s) of {dimension}; the {shown} largest by "
        f"{agg} of {measure} shown."
    )
    tie = _tie_note([[g[0], g[1]] for g in grouped], 1, shown, len(grouped))
    if tie:
        summary.append(tie)

    if not share_ok:
        if negatives:
            summary.append(
                f"No share column: {negatives} group(s) total below zero, and a "
                f"share of a signed total is not a proportion -- it can exceed "
                f"100% or change sign."
            )
        elif denominator is None:
            summary.append(
                f"No share column: {agg} does not add up across groups, so "
                f"there is no total for a group to be a share of."
            )
        else:
            summary.append(
                "No share column: the totals sum to zero or less, and dividing "
                "by that gives inf rather than an error."
            )
    return Output(headers=headers, rows=rows, summary=summary, label="top_n")
