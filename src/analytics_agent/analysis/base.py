"""Which rows an analysis may see, and the sentence that says so.

Nine analyses arrive in Steps 5-8 and none of them decides what "the data"
means. `analysis_window`, `known_exclusions` and `excluded_columns` are the
contract's, so one module reads them and the nine read this. Nine
implementations of a WHERE clause would disagree eventually, which is P7-D6's
shape with nine copies instead of two.

**The counts are the reason this is a module and not a helper.** P8-D6 asked
for four numbers that sum to the row count, and the obvious way to write them
double-counts. A row with no date, kept by an exclusion that could not judge
it, lands in `outside_window` AND in `no_date` if the window count is written
`NOT coalesce((window), false)` -- the coalesce turns "cannot tell" into
"outside". `NOT (window)` leaves it NULL, FILTER does not count a NULL
predicate, and the row appears once, in the bucket named after why it could not
be judged. Measured on a seven-row fixture before this file existed: 8, then 7.

So a null-safe predicate and a null-safe count want opposite treatments of
NULL. The predicate has to decide; the count has to refuse to.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..util.sql_guard import bind_predicate, negate, quote_identifier

__all__ = ["Scope", "ScopeError", "window_clause", "scope_for"]


class ScopeError(ValueError):
    """The contract describes rows that cannot be selected."""


def window_clause(column: str, start, end) -> str:
    """The inclusive window, as SQL, with the dates written in.

    P7-D2, which validate/rules.py already applies to its date checks: the
    window is inclusive at both ends and the column may be a TIMESTAMP, so the
    upper bound is `< end + INTERVAL 1 DAY`. Written `<= end` the bound casts to
    midnight and every window on a timestamp column silently loses its last day.

    The dates are interpolated rather than parameterised. `rules.py` passes them
    as `?` and is right to -- it builds and runs one query. This returns a
    fragment that nine analyses will paste into queries of their own, and a
    fragment carrying placeholders makes every one of them responsible for
    passing two parameters in the right order. A `date` cannot carry SQL: these
    come off a validated `AnalysisWindow`, and `isoformat()` of a `date` is
    three integers and two hyphens. The exclusion rules, which ARE caller text,
    go through sql_guard instead.
    """
    col = quote_identifier(column)
    return (
        f"{col} >= DATE '{start.isoformat()}' "
        f"AND {col} < DATE '{end.isoformat()}' + INTERVAL 1 DAY"
    )


@dataclass(frozen=True)
class Scope:
    """The rows an analysis may see, and why the others were left out."""

    dataset_name: str
    where: str
    rows: int
    excluded: int
    outside_window: int
    no_date: int
    analysed: int
    rule_unknown: int = 0
    skipped_columns: list[str] = field(default_factory=list)
    window_text: str = ""

    def __post_init__(self):
        """Four numbers that sum to the row count, refused if they do not.

        CheckResult's constructor will not let a check under-report; this will
        not let a scope lose a row. An analysis that quietly analysed 900 of
        1,000 rows and said nothing is the failure this whole phase is
        arranged against, and it would arrive as arithmetic rather than as an
        error.
        """
        total = self.excluded + self.outside_window + self.no_date + self.analysed
        if total != self.rows:
            raise ScopeError(
                f"the scope of {self.dataset_name} loses rows: "
                f"{self.excluded} excluded + {self.outside_window} outside the "
                f"window + {self.no_date} undated + {self.analysed} analysed = "
                f"{total}, against {self.rows} row(s) in the table."
            )
        if self.rule_unknown > self.analysed + self.outside_window + self.no_date:
            raise ScopeError(
                f"{self.rule_unknown} row(s) could not be judged by an "
                f"exclusion, which is more than the {self.rows - self.excluded} "
                f"row(s) the exclusions kept."
            )

    def method_note(self) -> str:
        """What was computed over, in one paragraph a reader can check.

        Every line is a number from this object rather than a description of
        the intent, so a scope that dropped rows unexpectedly says so here
        before anybody reads the result.
        """
        parts = [
            f"{self.analysed:,} of {self.rows:,} row(s) analysed."
        ]
        if self.excluded:
            parts.append(f"{self.excluded:,} excluded by the contract.")
        if self.outside_window:
            parts.append(
                f"{self.outside_window:,} outside {self.window_text}."
                if self.window_text
                else f"{self.outside_window:,} outside the analysis window."
            )
        if self.no_date:
            parts.append(
                f"{self.no_date:,} undated and so not placed in the window."
            )
        if self.rule_unknown:
            parts.append(
                f"{self.rule_unknown:,} kept although an exclusion rule could "
                f"not judge them."
            )
        if self.skipped_columns:
            parts.append(
                "Skipped, as the contract excludes them: "
                + ", ".join(sorted(self.skipped_columns))
                + "."
            )
        return " ".join(parts)


def scope_for(con, gate) -> Scope:
    """The Scope for a gate, measured against the table it names.

    Takes a Gate, never a dataset name. Locked decision 12 says no analysis
    without a confirmed contract, and a builder that accepts a string is a way
    around the gate -- the type is the enforcement.
    """
    contract = gate.contract
    name = contract.dataset_name
    ident = quote_identifier(name)

    keep_terms = []
    excluded_terms = []
    unknown_terms = []
    for exclusion in contract.known_exclusions:
        rule = bind_predicate(con, name, exclusion.rule)
        keep_terms.append(negate(rule))
        excluded_terms.append(f"coalesce(({rule}), false)")
        unknown_terms.append(f"(({rule}) IS NULL)")

    keep = " AND ".join(keep_terms) if keep_terms else "true"
    excluded_any = " OR ".join(excluded_terms) if excluded_terms else "false"
    unknown_any = " OR ".join(unknown_terms) if unknown_terms else "false"

    window = contract.analysis_window
    date_column = contract.date_column
    if window is not None and date_column:
        in_window = window_clause(date_column, window.start, window.end)
        window_text = f"{window.start.isoformat()} to {window.end.isoformat()}"
        where = f"({keep}) AND ({in_window})"
    else:
        # A contract with no window analyses everything it kept, and says so by
        # reporting zero in both window buckets rather than by omitting them.
        in_window = None
        window_text = ""
        where = f"({keep})"

    counts = con.execute(
        f"""
        SELECT
          count(*),
          count(*) FILTER (WHERE {excluded_any}),
          count(*) FILTER (WHERE NOT ({excluded_any}) AND {
              f"NOT ({in_window})" if in_window else "false"}),
          count(*) FILTER (WHERE NOT ({excluded_any}) AND {
              f"({in_window}) IS NULL" if in_window else "false"}),
          count(*) FILTER (WHERE {where}),
          count(*) FILTER (WHERE NOT ({excluded_any}) AND ({unknown_any}))
        FROM {ident}
        """
    ).fetchall()[0]

    return Scope(
        dataset_name=name,
        where=where,
        rows=counts[0],
        excluded=counts[1],
        outside_window=counts[2],
        no_date=counts[3],
        analysed=counts[4],
        rule_unknown=counts[5],
        skipped_columns=list(contract.excluded_columns),
        window_text=window_text,
    )
