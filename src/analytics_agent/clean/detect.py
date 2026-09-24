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

    if share("DOUBLE") >= CONVERT_MIN_SHARE:
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


NUMERIC_TYPES = ("BIGINT", "DOUBLE", "DECIMAL(18,2)")

# Numbers written for people rather than parsers (P14-O10, B8/B9). RE2, full-match. A value like
# '1,234' fits both conventions -- a thousand and twenty-four in one, one point two in the other --
# so a convention is chosen only by values that fit it and not the other.
_US_NUMBER = r"[-+]?[$€£¥]?\s?[-+]?(\d{1,3}(,\d{3})+|\d+)(\.\d+)?"
_EU_NUMBER = r"[-+]?[$€£¥]?\s?[-+]?(\d{1,3}(\.\d{3})+|\d+)(,\d+)?"
_PERCENT = r"[-+]?\d+([.,]\d+)?\s?%"
_CURRENCY_AND_SPACE = "[$€£¥\\s]"

# Date formats tried in order for a text column no single cast reads (P14-O10, B12). The numeric
# day/month orders are added only when a value settles which comes first (a part above 12).
_DATE_FORMATS = ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y/%m/%d",
                 "%b %d, %Y", "%B %d, %Y", "%d %b %Y", "%d %B %Y", "%d-%b-%Y", "%Y%m%d")
_DAY_FIRST = ("%d/%m/%Y", "%d.%m.%Y", "%d-%m-%Y")
_MONTH_FIRST = ("%m/%d/%Y", "%m.%d.%Y", "%m-%d-%Y")
_NUMERIC_DATE = r"(\d{1,2})[/.-](\d{1,2})[/.-]\d{4}"


def _share_where(con, table: str, column: str, condition: str) -> float:
    total = _non_null(con, table, column)
    if not total:
        return 0.0
    t, c = sql.ident(table), sql.ident(column)
    n = _scalar(con, f"SELECT count(*) FROM {t} WHERE {c} IS NOT NULL AND ({condition})")
    return n / total


def _numeric_type_of(con, table: str, text: str) -> str:
    """BIGINT, DECIMAL(18,2) or DOUBLE for a cleaned text expression, by the same rules as
    proposed_type: never round a fraction away, keep cents exact."""
    t = sql.ident(table)
    as_double = f"TRY_CAST({text} AS DOUBLE)"
    fractional = _scalar(con, f"SELECT count(*) FROM {t} WHERE {as_double} IS NOT NULL "
                              f"AND {as_double} <> round({as_double})")
    if not fractional:
        return "BIGINT"
    off_cents = _scalar(con, f"SELECT count(*) FROM {t} WHERE {as_double} IS NOT NULL "
                             f"AND round({as_double}, 2) <> {as_double}")
    return "DOUBLE" if off_cents else "DECIMAL(18,2)"


def alternative_conversion(con, table: str, column: str) -> tuple[str, str, str] | None:
    """(to_type, expression, how) for text a plain cast cannot read, or None.

    Tried only after proposed_type found nothing. Each candidate must read CONVERT_MIN_SHARE of
    the column, like any conversion, and what it cannot read is counted as lost from the same
    expression when the action is built.
    """
    c = sql.ident(column)
    trimmed = f"trim({c})"

    def full(pattern: str) -> str:
        return f"regexp_full_match({trimmed}, {sql.literal(pattern)})"

    if _share_where(con, table, column, full(_PERCENT)) >= CONVERT_MIN_SHARE:
        text = f"replace(rtrim({trimmed}, '%'), ',', '.')"
        to_type = _numeric_type_of(con, table, text)
        return (to_type, f"TRY_CAST({text} AS {to_type})",
                "the number before its % sign, so '12.5%' becomes 12.5")

    us = _share_where(con, table, column, full(_US_NUMBER))
    eu = _share_where(con, table, column, full(_EU_NUMBER))
    if max(us, eu) >= CONVERT_MIN_SHARE:
        only_us = _share_where(con, table, column,
                               f"{full(_US_NUMBER)} AND NOT {full(_EU_NUMBER)}")
        only_eu = _share_where(con, table, column,
                               f"{full(_EU_NUMBER)} AND NOT {full(_US_NUMBER)}")
        bare = f"regexp_replace({trimmed}, {sql.literal(_CURRENCY_AND_SPACE)}, '', 'g')"
        if us >= CONVERT_MIN_SHARE and only_us and not only_eu:
            text = f"replace({bare}, ',', '')"
            how = "with its currency signs and thousands separators removed ('$1,234.56' is 1234.56)"
        elif eu >= CONVERT_MIN_SHARE and only_eu and not only_us:
            text = f"replace(replace({bare}, '.', ''), ',', '.')"
            how = "with a decimal comma ('1.234,56' is 1234.56)"
        else:
            return None  # every value reads both ways: which one is the person's to say
        to_type = _numeric_type_of(con, table, text)
        return to_type, f"TRY_CAST({text} AS {to_type})", how

    return _date_conversion(con, table, column)


def _date_conversion(con, table: str, column: str) -> tuple[str, str, str] | None:
    t, c = sql.ident(table), sql.ident(column)
    trimmed = f"trim({c})"
    # A column of plain digits is ids or amounts, however many of them look like 20240131.
    if _share_where(con, table, column,
                    f"regexp_full_match({trimmed}, '\\d+')") >= CONVERT_MIN_SHARE:
        return None
    first = f"TRY_CAST(regexp_extract({trimmed}, {sql.literal(_NUMERIC_DATE)}, 1) AS INTEGER)"
    second = f"TRY_CAST(regexp_extract({trimmed}, {sql.literal(_NUMERIC_DATE)}, 2) AS INTEGER)"
    day_first = _scalar(con, f"SELECT count(*) FROM {t} WHERE {first} > 12")
    month_first = _scalar(con, f"SELECT count(*) FROM {t} WHERE {second} > 12")
    formats = list(_DATE_FORMATS)
    order = ""
    if day_first and not month_first:
        formats += _DAY_FIRST
        order = "; numeric dates read day first, as values such as 31/01 show"
    elif month_first and not day_first:
        formats += _MONTH_FIRST
        order = "; numeric dates read month first, as values such as 01/31 show"
    parsed = "COALESCE(" + ", ".join(
        f"TRY_STRPTIME({trimmed}, {sql.literal(f)})" for f in formats) + ")"
    if _share_where(con, table, column, f"{parsed} IS NOT NULL") < CONVERT_MIN_SHARE:
        return None
    with_time = _scalar(con, f"SELECT count(*) FROM {t} WHERE {parsed} IS NOT NULL "
                             f"AND {parsed} <> date_trunc('day', {parsed})")
    to_type = "TIMESTAMP" if with_time else "DATE"
    expression = parsed if with_time else f"CAST({parsed} AS DATE)"
    return to_type, expression, f"from the date formats it is written in{order}"


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

    columns = [r[0] for r in con.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_name = ? "
        "ORDER BY ordinal_position", [source]).fetchall()]
    if len(columns) >= 2:
        need = max(2, (len(columns) + 1) // 2)
        copies = _scalar(con, f"SELECT count(*) FROM {sql.ident(source)} "
                              f"WHERE {sql.header_match(columns, need)}")
        if copies:
            add(
                ActionKind.DROP_HEADER_ROWS,
                sql.drop_header_rows(source=source, target=target, columns=columns,
                                     min_match=need),
                f"remove the {copies:,} row(s) that repeat the column names -- a header "
                f"pasted into the data, which is what keeps numeric columns as text",
                None,
                loss_unit="row",
            )

    for column in text_columns(con, source):
        t, c = sql.ident(source), sql.ident(column)

        to_type = proposed_type(con, source, column)
        if to_type:
            numeric = to_type in NUMERIC_TYPES
            lead = numeric and _scalar(
                con, f"SELECT count(*) FROM {t} WHERE "
                     f"{sql.LEADING_ZERO.format(col=c)}")
            add(
                ActionKind.CONVERT_TYPE,
                sql.convert_type(source=source, target=target, column=column,
                                 to_type=to_type, missing_tokens=missing_tokens,
                                 numeric=numeric),
                f"read {column} as {to_type}"
                + (f" -- {lead:,} value(s) begin with a zero that a number cannot keep, "
                   f"as a zip code or an account number would" if lead else ""),
                column,
            )
        else:
            alt = alternative_conversion(con, source, column)
            if alt:
                alt_type, expression, how = alt
                add(
                    ActionKind.CONVERT_TYPE,
                    sql.convert_type(source=source, target=target, column=column,
                                     to_type=alt_type, missing_tokens=missing_tokens,
                                     expression=expression,
                                     numeric=alt_type in NUMERIC_TYPES),
                    f"read {column} as {alt_type}, {how}",
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

    for column in _float_columns(con, source):
        c = sql.ident(column)
        bad = _scalar(con, f"SELECT count(*) FROM {sql.ident(source)} "
                           f"WHERE {c} IS NOT NULL AND NOT isfinite({c})")
        if bad:
            add(
                ActionKind.NULL_NON_FINITE,
                sql.null_non_finite(source=source, target=target, column=column),
                f"turn the {bad:,} NaN / Infinity value(s) in {column} into nulls -- they "
                f"make every mean and spread over the column meaningless",
                column,
            )

    return actions


def _float_columns(con, table: str) -> list[str]:
    return [r[0] for r in con.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_name = ? "
        "AND data_type IN ('DOUBLE', 'FLOAT', 'REAL') ORDER BY ordinal_position",
        [table]).fetchall()]


__all__ = [
    "alternative_conversion",
    "BOOLEAN_WORDS",
    "CONVERT_MIN_SHARE",
    "detect",
    "proposed_type",
    "text_columns",
]
