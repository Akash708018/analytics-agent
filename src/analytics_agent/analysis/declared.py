"""What a contract declares, and how its aggregates are spelled in SQL.

These helpers inspect declarations and column types. They do not select a
scope, write results, or translate engine errors.
"""

from __future__ import annotations

__all__ = [
    "AGG_SQL", "agg_of", "column_types", "is_numeric", "is_integer",
    "dimension_names", "require_dimension", "require_measure",
]

# What a declared aggregate becomes in SQL. `none` is deliberately absent: it
# is not an aggregate that produces nothing, it is a statement that no total is
# meaningful, and mapping it to anything at all would produce that total.
# An absent aggregate has no default: the contract must say how rows combine.
AGG_SQL: dict[str, str] = {
    "sum": "sum({col})",
    "mean": "avg({col})",
    "min": "min({col})",
    "max": "max({col})",
    "count": "count({col})",
    "count_distinct": "count(DISTINCT {col})",
    "median": "quantile_cont(CAST({col} AS DOUBLE), 0.5)",
}


def agg_of(measure) -> str | None:
    """Read the aggregate declared by a measure.

    Aggregation is the Literal at dataset_contract.py:60. A contract can only
    produce a lowercase string or None; no enum value needs unwrapping.
    """
    agg = getattr(measure, "agg", None)
    if agg is None:
        return None
    return str(agg).strip().lower()


def column_types(con, dataset_name: str) -> dict[str, str]:
    rows = con.execute(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_name = ? ORDER BY ordinal_position",
        [dataset_name],
    ).fetchall()
    return {r[0]: r[1] for r in rows}


NUMERIC_TYPES = ("TINYINT", "SMALLINT", "INTEGER", "BIGINT", "HUGEINT", "UTINYINT",
            "USMALLINT", "UINTEGER", "UBIGINT", "FLOAT", "DOUBLE", "DECIMAL", "REAL")


def is_numeric(dtype: str) -> bool:
    return dtype.upper().startswith(NUMERIC_TYPES)


INTEGER_TYPES = (
    "TINYINT", "SMALLINT", "INTEGER", "BIGINT", "HUGEINT",
    "UTINYINT", "USMALLINT", "UINTEGER", "UBIGINT", "UHUGEINT",
)


def is_integer(dtype: str) -> bool:
    """Whether this is a scalar integer type, including unsigned HUGEINT."""
    return dtype.strip().upper() in INTEGER_TYPES


def dimension_names(contract) -> list[str]:
    """The declared dimensions, whether they are strings or objects.

    `dimensions` may hold names or small models; both are read the same way
    rather than one being assumed.
    """
    out = []
    for d in getattr(contract, "dimensions", []) or []:
        out.append(str(getattr(d, "name", d)))
    return out


def require_dimension(contract, column: str) -> str:
    """P8-O1 again: the contract says which columns are dimensions.

    profile_dataset already shows the top values of every column without a
    contract. This one answers the narrower question, so a column nobody
    declared is refused with the list of the ones somebody did -- a caller who
    wanted it is one confirm_dataset_contract away.
    """
    if column in set(getattr(contract, "excluded_columns", None) or []):
        raise ValueError(
            f"{column!r} is in excluded_columns: the contract says never to "
            f"read it."
        )
    declared = dimension_names(contract)
    if column in declared:
        return column
    raise ValueError(
        f"{column!r} is not a declared dimension of "
        f"{contract.dataset_name}. Declared: "
        f"{', '.join(declared) if declared else '(none)'}. "
        f"profile_dataset describes any column without a contract; this "
        f"analysis reports the ones the contract names."
    )


def require_measure(contract, name: str):
    """Return the declared measure itself, refusing excluded columns first."""
    if name in set(getattr(contract, "excluded_columns", None) or []):
        raise ValueError(
            f"{name!r} is in excluded_columns: the contract says never to "
            f"read it."
        )
    declared = {m.name: m for m in contract.measures}
    if name not in declared:
        raise ValueError(
            f"{name!r} is not a declared measure of {contract.dataset_name}. "
            f"Declared: {', '.join(sorted(declared)) or '(none)'}."
        )
    return declared[name]
