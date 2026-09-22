"""What a table needs, found without touching it.

Phase 6, Step 5. Turns a loaded table into a list of `CleaningAction`s, each
already carrying the SQL that will run and the counts that justify it.

**P6-D5, resolved by P6-D2 rather than by preference.** The open question was
whether detection should read a `TableProfile` or compute its own counts. It
cannot read one: `profile_dataset` records a run in `_agent_profiles`, and the
proposal path holds the workspace through `ATTACH ... (READ_ONLY)`, which
refuses `INSERT` and `CREATE` by statement type. A read-only path cannot invoke
a tool that writes. So detection does its own reading, and everything it reads
is a `SELECT`.

That turns out to be the better answer anyway. A profile taken forty minutes ago
describes the table as it was; a proposal has to describe the table as it is,
and the numbers it prints are the numbers its own statement will produce because
both come from the same expression in `clean/sql.py`.

**Detection proposes. It never decides.** Every action here goes into a plan and
waits for an id to be approved. Nothing in this module writes.

**EXCLUDE_COLUMN is not detected.** Dropping a column is not something a table's
contents can suggest -- a column that is 100% null may be the one column that
matters and the feed is broken. It arrives from the contract (P6-D8) or from a
person, and `clean/sql.py` renders it when asked.
"""

from __future__ import annotations

from .plan import ActionKind, CleaningAction, next_action_id
from . import sql

# A column is only offered as a type conversion when nearly all of it already
# parses. Below this it is not a column of the wrong type, it is a mixed
# column, and merging two meanings into one is a decision no threshold should
# make. Measured against the fixture: mixed_types' units parses 5,993/6,000
# (0.9988) and unit_price 5,997/6,000 (0.9995), so the fixture sits far above
# this and the number is not tuned to pass it.
CONVERT_MIN_SHARE = 0.90

# Values that mean true/false and nothing else. Deliberately NOT {'1','0'}:
# TRY_CAST('1' AS BOOLEAN) is TRUE in DuckDB, so an integer column of ones and
# zeroes parses perfectly as boolean, and proposing that would silently turn
# counts into flags.
BOOLEAN_WORDS = ("TRUE", "FALSE")


def _scalar(con, query: str):
    return con.execute(query).fetchone()[0]


def text_columns(con, table: str) -> list[str]:
    return [
        r[0]
        for r in con.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = ? AND data_type = 'VARCHAR' "
            "ORDER BY ordinal_position",
            [table],
        ).fetchall()
    ]


def _non_null(con, table: str, column: str) -> int:
    c, t = sql.ident(column), sql.ident(table)
    return _scalar(con, f"SELECT count(*) FROM {t} WHERE {c} IS NOT NULL")


def proposed_type(con, table: str, column: str) -> str | None:
    """The narrowest type this column can be read as without losing anything.

    Order and guards both matter, and both are measured rather than assumed:

    - `TRY_CAST('9.50' AS BIGINT)` is **10**. A column of prices parses 100%
      as BIGINT and rounds every value. So "does it parse" is not a signal;
      BIGINT is only proposed when no value loses a fractional part, which is
      asked directly rather than inferred from the text.
    - `TRY_CAST('1' AS BOOLEAN)` is **TRUE**. So BOOLEAN is only proposed when
      every value is literally true or false.
    - `TRY_CAST` on a timestamp string will happily produce a DATE and drop the
      time. TIMESTAMP is proposed; DATE only when every value is midnight.
    """
    t, c = sql.ident(table), sql.ident(column)
    total = _non_null(con, table, column)
    if total == 0:
        return None
    # A value with a zero before another digit is a code: '000435' becomes 435, and SKUs that
    # were six characters stop being what anybody wrote. Retail C003 offered exactly that as
    # discarding nothing and recommended it (Cleanup Step 12, RF-O5).
    padded = _scalar(con, f"SELECT count(*) FROM {t} WHERE regexp_matches({c}, '^[+-]?0[0-9]')")

    def share(to_type: str) -> float:
        n = _scalar(
            con,
            f"SELECT count(*) FROM {t} WHERE {c} IS NOT NULL "
            f"AND TRY_CAST({c} AS {to_type}) IS NOT NULL",
        )
        return n / total

    if share("BOOLEAN") >= CONVERT_MIN_SHARE:
        words = ", ".join(sql.literal(w) for w in BOOLEAN_WORDS)
        odd = _scalar(
            con,
            f"SELECT count(*) FROM {t} WHERE {c} IS NOT NULL "
            f"AND upper(trim({c})) NOT IN ({words})",
        )
        if odd == 0:
            return "BOOLEAN"

    if not padded and share("DOUBLE") >= CONVERT_MIN_SHARE:
        rounded = _scalar(
            con,
            f"SELECT count(*) FROM {t} WHERE TRY_CAST({c} AS DOUBLE) IS NOT NULL "
            f"AND TRY_CAST({c} AS DOUBLE) <> TRY_CAST({c} AS BIGINT)",
        )
        if rounded == 0 and share("BIGINT") >= CONVERT_MIN_SHARE:
            return "BIGINT"
        return "DECIMAL(18,2)" if _fits_two_places(con, table, column) else "DOUBLE"

    if share("TIMESTAMP") >= CONVERT_MIN_SHARE:
        with_time = _scalar(
            con,
            f"SELECT count(*) FROM {t} WHERE TRY_CAST({c} AS TIMESTAMP) IS NOT NULL "
            f"AND TRY_CAST({c} AS TIMESTAMP) <> "
            f"date_trunc('day', TRY_CAST({c} AS TIMESTAMP))",
        )
        return "TIMESTAMP" if with_time else "DATE"

    return None


def currency_type(con, table: str, column: str) -> str | None:
    """The number type a column of currency text reads as, or None (Cleanup Step 12, A3).

    Offered only where the plain cast fails and most values parse once the currency sign, the
    thousands separators and spaces are removed -- and at least one value holds such a character,
    so a column of plain numbers is never routed here.
    """
    t, c = sql.ident(table), sql.ident(column)
    total = _non_null(con, table, column)
    if total == 0:
        return None
    stripped = f"regexp_replace({c}, '{sql.CURRENCY_CHARS}', '', 'g')"
    marked = _scalar(con, f"SELECT count(*) FROM {t} WHERE regexp_matches({c}, '[₹$€£¥,]')")
    parsed = _scalar(con, f"SELECT count(*) FROM {t} WHERE {c} IS NOT NULL "
                          f"AND TRY_CAST({stripped} AS DOUBLE) IS NOT NULL")
    if not marked or parsed / total < CONVERT_MIN_SHARE:
        return None
    lost = _scalar(con, f"SELECT count(*) FROM {t} WHERE TRY_CAST({stripped} AS DOUBLE) IS NOT NULL "
                        f"AND (TRY_CAST({stripped} AS DECIMAL(18,2)) IS NULL OR "
                        f"TRY_CAST({stripped} AS DECIMAL(18,2)) <> TRY_CAST({stripped} AS DOUBLE))")
    return "DECIMAL(18,2)" if lost == 0 else "DOUBLE"


def _fits_two_places(con, table: str, column: str) -> bool:
    """DECIMAL(18,2) over DOUBLE where it fits.

    Money in a DOUBLE is how a total ends in .9999999999998, and the Olist
    revenue figure this project verified to the cent is the reason to care.
    """
    t, c = sql.ident(table), sql.ident(column)
    lost = _scalar(
        con,
        f"SELECT count(*) FROM {t} WHERE TRY_CAST({c} AS DOUBLE) IS NOT NULL "
        f"AND (TRY_CAST({c} AS DECIMAL(18,2)) IS NULL "
        f"     OR TRY_CAST({c} AS DECIMAL(18,2)) <> TRY_CAST({c} AS DOUBLE))",
    )
    return lost == 0


def _action(
    con, *, action_id: str, kind: ActionKind, rendering: sql.Rendering,
    intent: str, column: str | None, loss_unit: str,
) -> CleaningAction:
    """Take the counts from the rendering's own queries. Never from anywhere
    else -- that is the whole argument of clean/sql.py."""
    lost, sample = 0, ()
    if rendering.lost_sql:
        lost = _scalar(con, rendering.lost_sql) or 0
        if lost and rendering.sample_sql:
            sample = tuple(
                str(r[0]) for r in con.execute(rendering.sample_sql).fetchall()
            )
    return CleaningAction(
        action_id=action_id,
        kind=kind,
        column=column,
        intent=intent,
        sql=rendering.statement,
        rows_affected=_scalar(con, rendering.affected_sql) or 0,
        values_lost=lost,
        loss_unit=loss_unit,
        sample=sample,
    )


def detect(
    con, *, source: str, target: str, missing_tokens: list[str]
) -> list[CleaningAction]:
    """Every action this table supports, in a stable order.

    Table-level first, then per column in ordinal order, so two runs against an
    unchanged table produce the same ids. An id that moves between proposals is
    an id nobody can approve.
    """
    actions: list[CleaningAction] = []

    def add(kind, rendering, intent, column, loss_unit="value"):
        actions.append(
            _action(
                con, action_id=next_action_id(len(actions)), kind=kind,
                rendering=rendering, intent=intent, column=column,
                loss_unit=loss_unit,
            )
        )

    dupes = _scalar(
        con,
        f"SELECT count(*) - (SELECT count(*) FROM "
        f"(SELECT DISTINCT * FROM {sql.ident(source)})) "
        f"FROM {sql.ident(source)}",
    )
    if dupes:
        add(
            ActionKind.DROP_DUPLICATE_ROWS,
            sql.drop_duplicate_rows(source=source, target=target),
            f"keep one of each of the {dupes:,} exactly duplicated row(s)",
            None,
            loss_unit="row",
        )

    for column in text_columns(con, source):
        t, c = sql.ident(source), sql.ident(column)

        to_type = proposed_type(con, source, column)
        if to_type:
            add(
                ActionKind.CONVERT_TYPE,
                sql.convert_type(source=source, target=target, column=column,
                                 to_type=to_type, missing_tokens=missing_tokens),
                f"read {column} as {to_type}",
                column,
            )
        else:
            money = currency_type(con, source, column)
            if money:
                add(
                    ActionKind.CONVERT_TYPE,
                    sql.convert_type(source=source, target=target, column=column,
                                     to_type=money, missing_tokens=missing_tokens,
                                     strip_currency=True),
                    f"read {column} as {money}, removing the currency sign and thousands "
                    f"separators first (currency text)",
                    column,
                )

        if missing_tokens:
            words = sql.token_list(missing_tokens)
            hits = _scalar(
                con,
                f"SELECT count(*) FROM {t} WHERE upper(trim({c})) IN ({words})",
            )
            if hits:
                add(
                    ActionKind.NORMALISE_MISSING,
                    sql.normalise_missing(source=source, target=target,
                                          column=column, tokens=missing_tokens),
                    f"turn the {hits:,} declared missing token(s) in {column} "
                    f"into real nulls",
                    column,
                )

        padded = _scalar(
            con,
            f"SELECT count(*) FROM {t} WHERE {c} IS NOT NULL "
            f"AND {c} <> trim({c})",
        )
        if padded:
            add(
                ActionKind.TRIM_WHITESPACE,
                sql.trim_whitespace(source=source, target=target, column=column),
                f"strip padding from {padded:,} value(s) in {column}",
                column,
            )

        merged = _scalar(
            con,
            f"SELECT count(DISTINCT {c}) - count(DISTINCT upper({c})) FROM {t}",
        )
        if merged:
            add(
                ActionKind.NORMALISE_CASE,
                sql.normalise_case(source=source, target=target, column=column),
                f"fold {column} to one case, merging {merged:,} distinct "
                f"value(s) into others",
                column,
                loss_unit="distinct value",
            )

    return actions


__all__ = [
    "BOOLEAN_WORDS",
    "CONVERT_MIN_SHARE",
    "detect",
    "proposed_type",
    "text_columns",
]
