"""
What a table looks like, counted. No judgement, no fixes.

`evidence.py` counts the four things a contract needs: rows, non-null,
distinct, range. This adds the four a person reading a table for the first time
asks for and a contract does not -- what the numbers average out to, where the
middle is, how far they spread, and how much of this is missing in ways a null
count cannot see.

It reuses `column_stats` rather than recomputing. There is exactly one
implementation of "how many nulls in region" in this codebase, and the day
there are two they will disagree inside the same chat with nothing to tell a
reader which is lying.

Three things here are worth reading before trusting the output.

**A null count is not a missing-data count.** `gaps_and_dupes.csv` opens with

    ORD-00002,4,N/A,10,Online,2829.54

That column has zero nulls and is missing a value. A profile reporting "0%
null" is technically true and practically a lie, and it is the kind of
true-and-wrong that survives into a chart. So blanks and the standard missing
tokens are counted separately and reported beside the nulls. They are never
rewritten: rewriting is cleaning, cleaning is Phase 6, and Phase 6 has an
approval gate for a reason.

**The vocabulary is not invented here.** It was, once, and the first run on a
six-row fixture reported a column as 83% missing because `unknown` was in the
list I had reasoned my way to. The defensible figure was 67%. Checking the
reference implementations instead gives a narrower list and a better model:

    pandas 3.0.2       19 strings, fixed default, overridable per read
    pyarrow 25.0.1     17 strings -- pandas' minus '<NA>' and 'None'
    Frictionless       missingValues defaults to [''], a DECLARED schema
                       property; [] disables the conversion entirely

`unknown`, `missing`, `none`, `-`, `--` and `?` are in none of them.
`MISSING_VALUES` below is the pandas/pyarrow intersection, upper-cased, with
the empty string removed because blanks are counted separately. Where those two
disagree -- `None` and `<NA>` -- the disagreement is the edge of consensus and
both are left out. `None` is also exactly the value that can be a real payment
type.

The failure modes are not symmetric, which is the whole argument. Over-
detection puts a wrong number in a headline, and headlines are what get
repeated. Under-detection leaves the value sitting in a frequency table where a
person reads it and rules on it. Tune toward the recoverable error.

Following Frictionless, the list is an argument rather than a constant: pass
`missing_values=[...]` to widen it for a source that writes `NR` or `#REF!`,
and `missing_values=[]` to switch detection off. Step 8 puts it on the contract
so the answer is declared once and read by Phase 6 and Phase 8 alike.

**Duplicate rows use `SELECT DISTINCT *`, and that is the THIRD null rule in
this codebase.** `count(DISTINCT c)` drops nulls (evidence finding 1).
`count(DISTINCT (a, b))` does not (finding 2). `DISTINCT *` also does not, and
two rows identical including their nulls collapse to one -- verified on 1.5.5:
five rows holding one exact NULL-bearing duplicate return four. Here that
behaviour is the one we want, because two identical rows ARE duplicates
whatever their nulls. It is used deliberately and said out loud, or someone
reads it as the same bug a third time.

Note on the package name: `profile` shadows a stdlib module. Every import here
is absolute, so nothing resolves to the stdlib profiler, but a bare
`import profile` anywhere in this tree would.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from analytics_agent.contract.evidence import (
    ColumnEvidence,
    _is_numeric,
    _is_text,
    _q,
    column_stats,
    suggest_role,
)

# The pandas/pyarrow intersection, upper-cased, without the empty string.
# Verified by running both rather than recalled. Matching is case-insensitive,
# which is the one deliberate widening: pandas ships 'NA', 'n/a' and 'nan' as
# separate entries, implying exact matching, so 'Null' slips through it. This
# widens case and never vocabulary.
MISSING_VALUES = (
    "#N/A", "#N/A N/A", "#NA", "-1.#IND", "-1.#QNAN", "-NAN",
    "1.#IND", "1.#QNAN", "N/A", "NA", "NAN", "NULL",
)

# Which token appeared costs one query per affected column. Capped and the
# remainder reported, the way evidence caps pair probes.
MAX_BREAKDOWN_COLUMNS = 20

# At or above this share of missing values a column is named in the summary
# rather than left for the reader to find in the table.
MOSTLY_MISSING = 0.5


def _lit(value: str) -> str:
    """A single-quoted SQL literal. Doubles any embedded quote.

    `missing_values` can arrive from a contract, which means from a person,
    which means it is not put into a query unescaped.
    """
    return "'" + value.replace("'", "''") + "'"


@dataclass(frozen=True)
class NumericSummary:
    """
    Where the middle is and how far it spreads.

    Every field is None-able, and that is not defensiveness: a column of all
    nulls has no mean and a single-row table has no sample standard deviation.
    Verified on 1.5.5 -- both return NULL rather than raising, and a zero
    written in their place would be a number nobody computed.
    """

    mean: float | None = None
    stddev: float | None = None
    q1: float | None = None
    median: float | None = None
    q3: float | None = None

    @property
    def iqr(self) -> float | None:
        """Q3 - Q1. Step 3's outlier fences are built from this."""
        if self.q1 is None or self.q3 is None:
            return None
        return self.q3 - self.q1


@dataclass(frozen=True)
class ColumnProfile:
    """One column: what evidence counted, plus what a reader asks next."""

    evidence: ColumnEvidence
    role: str
    role_reason: str
    numeric: NumericSummary | None = None
    blank_count: int = 0
    missing_token_count: int = 0
    missing_token_breakdown: dict[str, int] = field(default_factory=dict)

    @property
    def name(self) -> str:
        return self.evidence.name

    @property
    def dtype(self) -> str:
        return self.evidence.dtype

    @property
    def hidden_missing(self) -> int:
        """Missing values no null count would find."""
        return self.blank_count + self.missing_token_count

    @property
    def missing_count(self) -> int:
        return self.evidence.null_count + self.hidden_missing

    @property
    def missing_ratio(self) -> float:
        rows = self.evidence.row_count
        return self.missing_count / rows if rows else 0.0

    def sentence(self) -> str:
        """
        This column's line: evidence's sentence, plus what it cannot say.

        Built ON `evidence.sentence()` rather than beside it. When that wording
        changes this changes with it, and the two never drift into describing
        one column two ways.
        """
        out = self.evidence.sentence()
        if not self.hidden_missing:
            return out
        parts = []
        if self.blank_count:
            parts.append(f"{self.blank_count:,} blank or whitespace-only")
        if self.missing_token_count:
            named = ", ".join(
                f"{k} x{v:,}"
                for k, v in sorted(self.missing_token_breakdown.items())
            )
            parts.append(named or f"{self.missing_token_count:,} standard tokens")
        return (
            f"{out} A further {self.hidden_missing:,} value(s) read as missing "
            f"without being null: {'; '.join(parts)}."
        )


@dataclass
class TableProfile:
    """One table, counted. Stores nothing and writes nothing."""

    dataset_name: str
    row_count: int
    columns: list[ColumnProfile]
    duplicate_rows: int | None = None
    missing_values: tuple[str, ...] = MISSING_VALUES
    notes: list[str] = field(default_factory=list)

    # The first twelve are what the envelope previews inline, and the order is
    # a decision: a first look is for the missing-data story, so the numeric
    # summary sits behind it in the file rather than in front of it on screen.
    HEADERS = [
        "column", "dtype", "role", "nulls", "null_pct", "blank",
        "reads_missing", "missing_pct", "distinct", "distinct_pct",
        "min", "max",
        "mean", "median", "stddev", "q1", "q3",
    ]

    @property
    def column_count(self) -> int:
        return len(self.columns)

    def column(self, name: str) -> ColumnProfile:
        for c in self.columns:
            if c.name == name:
                return c
        raise KeyError(name)

    def to_rows(self) -> list[list[object]]:
        rows: list[list[object]] = []
        for c in self.columns:
            e, n = c.evidence, c.numeric
            rows.append([
                c.name, c.dtype, c.role,
                e.null_count, round(e.null_ratio * 100, 1),
                c.blank_count, c.missing_token_count,
                round(c.missing_ratio * 100, 1),
                e.distinct, round(e.distinct_ratio * 100, 1),
                e.min_value, e.max_value,
                None if n is None else n.mean,
                None if n is None else n.median,
                None if n is None else n.stddev,
                None if n is None else n.q1,
                None if n is None else n.q3,
            ])
        return rows

    def summary_lines(self) -> list[str]:
        """
        The findings, for the top of the envelope.

        What belongs here is what changes what someone does next. A column half
        missing changes an analysis; a column 0.2% missing does not, and
        putting both in the summary means neither gets read.
        """
        out = [f"{self.row_count:,} rows, {self.column_count} columns."]

        if self.duplicate_rows is None:
            out.append("Duplicate rows could not be counted -- see the notes.")
        elif self.duplicate_rows:
            pct = self.duplicate_rows / self.row_count * 100 if self.row_count else 0
            out.append(
                f"{self.duplicate_rows:,} row(s) are exact duplicates of another "
                f"row ({pct:.1f}%), identical including their nulls."
            )
        else:
            out.append("No exact duplicate rows.")

        hidden = [c for c in self.columns if c.hidden_missing]
        if hidden:
            named = ", ".join(f"{c.name} ({c.hidden_missing:,})" for c in hidden[:5])
            more = f", and {len(hidden) - 5} more" if len(hidden) > 5 else ""
            out.append(
                f"{len(hidden)} column(s) hold values that read as missing "
                f"without being null: {named}{more}. Nothing was rewritten."
            )

        mostly = [c for c in self.columns if c.missing_ratio >= MOSTLY_MISSING]
        if mostly:
            out.append(
                f"{len(mostly)} column(s) are at least "
                f"{int(MOSTLY_MISSING * 100)}% missing: "
                + ", ".join(
                    f"{c.name} ({c.missing_ratio * 100:.0f}%)" for c in mostly
                )
                + "."
            )

        constant = [c for c in self.columns if c.evidence.is_constant]
        if constant:
            out.append(
                f"{len(constant)} column(s) hold one value or none and cannot be "
                f"grouped by: " + ", ".join(c.name for c in constant) + "."
            )

        unique = [c for c in self.columns if c.evidence.is_unique]
        if unique:
            out.append(
                "Unique and null-free: " + ", ".join(c.name for c in unique)
                + ". Uniqueness here is a property of the rows that happen to be "
                "loaded, not a key."
            )
        return out

    def to_text(self) -> str:
        """A reading of the whole table, one line per column."""
        lines = [f"Profile of {self.dataset_name}", ""]
        lines += [f"  - {s}" for s in self.summary_lines()]
        lines += ["", "Columns:"]
        lines += [f"  - {c.sentence()}" for c in self.columns]
        if self.notes:
            lines += ["", "Notes:"] + [f"  - {n}" for n in self.notes]
        return "\n".join(lines)


def _numeric_exprs(name: str) -> list[str]:
    col = _q(name)
    return [
        f"avg({col})::DOUBLE",
        f"stddev_samp({col})::DOUBLE",
        f"quantile_cont({col}, 0.25)::DOUBLE",
        f"median({col})::DOUBLE",
        f"quantile_cont({col}, 0.75)::DOUBLE",
    ]


def _text_exprs(name: str, listed: str) -> list[str]:
    col = _q(name)
    blank = f"count(*) FILTER (WHERE trim({col}) = '')"
    if not listed:
        # Frictionless semantics: an empty vocabulary disables the conversion
        # rather than meaning "use the default". The zero here is a real count.
        return [blank, "0"]
    return [blank, f"count(*) FILTER (WHERE upper(trim({col})) IN ({listed}))"]


def _duplicate_rows(
    con, dataset_name: str, row_count: int
) -> tuple[int | None, str | None]:
    """
    Rows that are exact duplicates of another, nulls included.

    The try/except is precautionary and I could not make it fire: on 1.5.5,
    LIST, MAP and UNION columns all survive `DISTINCT *`. It stays because a
    profile that crashes on one column is worth less than one that says which
    single count it could not produce, and because the set of types is not
    fixed forever. It has never been triggered by a real type -- the test that
    covers it makes the query raise deliberately.
    """
    try:
        distinct = con.execute(
            f"SELECT count(*) FROM (SELECT DISTINCT * FROM {_q(dataset_name)})"
        ).fetchone()[0]
    except Exception as exc:  # noqa: BLE001 -- reported, not swallowed
        return None, (
            f"Exact-duplicate rows were not counted: {exc}. Every other number "
            f"here is unaffected."
        )
    return row_count - distinct, None


def _breakdown(con, dataset_name: str, name: str, listed: str) -> dict[str, int]:
    col = _q(name)
    rows = con.execute(
        f"SELECT upper(trim({col})) AS token, count(*) "
        f"FROM {_q(dataset_name)} "
        f"WHERE upper(trim({col})) IN ({listed}) "
        f"GROUP BY 1 ORDER BY 2 DESC, 1"
    ).fetchall()
    return {token: n for token, n in rows}


def profile_table(
    con,
    dataset_name: str,
    *,
    missing_values: Sequence[str] = MISSING_VALUES,
    breakdown_cap: int = MAX_BREAKDOWN_COLUMNS,
) -> TableProfile:
    """
    Count everything about one loaded table.

    Reads. Writes nothing, stores nothing, proposes nothing, changes nothing.
    A dataset that is not loaded raises `ContractRefused` from `column_stats`,
    which is the refusal this codebase already produces for that.

    Two passes plus a capped third. `column_stats` is one SELECT for the counts
    it owns; this adds one SELECT for the aggregates it does not; the duplicate
    count is its own scan because `DISTINCT *` cannot ride along with
    aggregates. Which token appeared is one small query per affected column.
    """
    stats: list[ColumnEvidence] = column_stats(con, dataset_name)
    row_count = stats[0].row_count if stats else 0

    vocabulary = tuple(
        dict.fromkeys(v.strip().upper() for v in missing_values if v.strip())
    )
    listed = ", ".join(_lit(v) for v in vocabulary)

    numeric = [c for c in stats if _is_numeric(c.dtype)]
    text = [c for c in stats if _is_text(c.dtype)]

    exprs: list[str] = []
    for c in numeric:
        exprs += _numeric_exprs(c.name)
    for c in text:
        exprs += _text_exprs(c.name, listed)

    values: tuple = ()
    if exprs:
        values = con.execute(
            f"SELECT {', '.join(exprs)} FROM {_q(dataset_name)}"
        ).fetchone()

    summaries: dict[str, NumericSummary] = {}
    for i, c in enumerate(numeric):
        mean, sd, q1, med, q3 = values[5 * i: 5 * i + 5]
        summaries[c.name] = NumericSummary(
            mean=mean, stddev=sd, q1=q1, median=med, q3=q3
        )

    offset = 5 * len(numeric)
    blanks: dict[str, int] = {}
    tokens: dict[str, int] = {}
    for i, c in enumerate(text):
        blanks[c.name], tokens[c.name] = values[offset + 2 * i: offset + 2 * i + 2]

    notes: list[str] = []
    flagged = [c.name for c in text if tokens.get(c.name)]
    breakdowns: dict[str, dict[str, int]] = {}
    for name in flagged[:breakdown_cap]:
        breakdowns[name] = _breakdown(con, dataset_name, name, listed)
    if len(flagged) > breakdown_cap:
        notes.append(
            f"{len(flagged)} column(s) hold values that read as missing; which "
            f"token appeared was looked up for the first {breakdown_cap}. The "
            f"counts themselves are complete for all of them."
        )

    columns: list[ColumnProfile] = []
    for c in stats:
        role, reason = suggest_role(c)
        columns.append(
            ColumnProfile(
                evidence=c,
                role=role,
                role_reason=reason,
                numeric=summaries.get(c.name),
                blank_count=blanks.get(c.name, 0),
                missing_token_count=tokens.get(c.name, 0),
                missing_token_breakdown=breakdowns.get(c.name, {}),
            )
        )

    dupes, dupe_note = _duplicate_rows(con, dataset_name, row_count)
    if dupe_note:
        notes.append(dupe_note)
    if flagged:
        notes.append(
            "The missing-value vocabulary is the pandas/pyarrow intersection "
            "and holds no judgement calls: 'unknown', 'none', '-' and '?' are "
            "in neither and are NOT counted here. If a source writes one of "
            "those it shows up in the column's frequency table instead, where "
            "a person decides. Nothing was rewritten either way."
        )

    return TableProfile(
        dataset_name=dataset_name,
        row_count=row_count,
        columns=columns,
        duplicate_rows=dupes,
        missing_values=vocabulary,
        notes=notes,
    )


__all__ = [
    "MAX_BREAKDOWN_COLUMNS",
    "MISSING_VALUES",
    "MOSTLY_MISSING",
    "ColumnProfile",
    "NumericSummary",
    "TableProfile",
    "profile_table",
]
