"""
Evidence in, provisional contract out.

This is the join between the three layers built so far. `evidence.py` counts,
`compatibility.py` verifies, `dataset_contract.py` holds -- and this decides
what to put in front of a person, which is a different job from any of them
and the one with the most ways to go quietly wrong.

The rule it exists to enforce: **a proposal may restate what the data says,
and may never state what only a person can.** Those look identical on the page
if you are not careful, because both arrive as a filled-in field. The
difference is whether the sentence could have been derived:

    one row = one (order_id, order_item_id)      derived from the key. Fine.
    one row = one order line item                invented. Not fine.

The first is arithmetic wearing a sentence. The second is a claim about a
business, and it is worse than a blank because people nod along to it. Nobody
ever nodded along to a guessed `header_rows=[1, 2]`.

So the proposal fills in what it can derive, leaves blank what it cannot, and
puts BOTH in `unresolved`. Phase 3's shape, with one refinement it did not
need: `unresolved` holds field paths, because a missing definition is missing
per-measure.

Three things are deliberately NOT proposed.

**The analysis window.** A date column's min and max are facts, and the window
is not the same question. On olist, `shipping_limit_date` runs to 2020-04-09,
well past the end of the order data -- proposing that span as the window would
have produced a defensible-looking range that silently includes a tail nobody
wants. The span is reported as evidence and the window is asked about.

**Which date column is THE date column.** A table with `created_at`,
`approved_at` and `delivered_at` has three, and which one a trend is computed
over is a decision with an answer that changes the numbers. One temporal
column is taken; more than one is asked about.

**Known exclusions.** "status = 'cancelled' is not real revenue" cannot be
derived from a column of statuses. There is no version of this that counting
produces, so nothing is offered.

**How a measure aggregates.** Whether a column sums, averages or must not be
combined at all is a property of what it means, not of its type. `unit_price`
and `revenue` are both DOUBLE and only one of them sums. This carried a `sum`
default once; two live runs pushed back on it, and the second said why
better than the code comment did -- "the plausible-looking default is the kind
of thing that gets confirmed without being read".
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime

from analytics_agent.contract import ContractRefused
from analytics_agent.contract.compatibility import (
    KeyVerdict,
    binding_for,
    verify_key,
)
from analytics_agent.contract.dataset_contract import (
    AGGREGATIONS,
    AnalysisWindow,
    DatasetContract,
    Exclusion,
    ForeignKey,
    Measure,
)
from analytics_agent.contract.evidence import DatasetEvidence, gather, suggest_role

# There is no default aggregation, deliberately. See Measure.agg: every
# production semantic layer requires it (LookML `type:`, Cube `type`,
# MetricFlow `agg`) because the guess that gets guessed is `sum`, and summing
# a price, a rate or a balance is meaningless in a way nothing downstream can
# detect. It is asked about, in the same question as the definition.


@dataclass
class Proposal:
    """A draft contract, the evidence behind it, and what is still open."""

    contract: DatasetContract
    evidence: DatasetEvidence
    key_verdict: KeyVerdict | None = None
    notes: list[str] = field(default_factory=list)

    @property
    def needs_answer(self) -> bool:
        return not self.contract.is_confirmable

    def to_text(self) -> str:
        """
        The draft as the user reads it.

        Ordered so the questions come last: whatever sits at the bottom of a
        tool result is what gets answered. Phase 3 learned this the hard way,
        and then learned the second half of it -- print what is outstanding
        NOW, not what the data could never settle, or you ask someone the
        question they just answered.
        """
        out = [self.contract.to_text()]

        if self.notes:
            out += ["", "What the data showed:"]
            out += [f"  - {n}" for n in self.notes]

        if self.contract.unresolved:
            out += [
                "",
                "THIS CONTRACT CANNOT BE CONFIRMED AS IT STANDS.",
                f"{', '.join(self.contract.unresolved)} "
                f"{'is' if len(self.contract.unresolved) == 1 else 'are'} a "
                f"guess or a blank, not something anyone has stated.",
                "",
                "Put these to the user:",
            ]
            out += [f"  - {q}" for q in self.contract.questions]
            out += [
                "",
                "Then call propose_dataset_contract again with their answers "
                "-- grain=..., measure_definitions={...}, analysis_window=... "
                "-- and confirm the contract it returns. Do not delete the "
                "unresolved entries: a blank definition is invalid on its own, "
                "so that edit fails rather than confirming a guess.",
            ]
            return "\n".join(out)

        out += [
            "",
            "Nothing is stored yet. To store exactly this, pass the JSON below "
            "back to confirm_dataset_contract.",
            "",
            "```json",
            self.contract.model_dump_json(indent=2),
            "```",
        ]
        return "\n".join(out)


def _grain_sentence(key: list[str]) -> str:
    """
    A grain derived from the key, in the table's own column names.

    Deliberately not English. "one row = one order line item" is the same
    sentence with a business meaning invented, and it reads as knowledge.
    """
    if not key:
        return ""
    if len(key) == 1:
        return f"one row = one {key[0]}"
    return f"one row = one ({', '.join(key)})"


def _rank_candidates(usable, roles: dict[str, str]):
    """
    Candidates whose columns all read as identifiers, first.

    Evidence returns unique single columns before pairs, in column order, and
    that ordering picks the wrong key the moment a column is unique by
    accident. On a 300-row fixture where `order_date` held 300 distinct dates,
    taking the first candidate produced `one row = one order_date` and buried
    `order_id + order_item_id` -- a grain that is arithmetically true and
    means nothing.

    Shorter wins among equals, which costs nothing: evidence has already
    dropped any candidate containing a column that is unique on its own.
    """
    def sort_key(candidate):
        all_ident = all(
            roles.get(col) == "identifier" for col in candidate.columns
        )
        return (0 if all_ident else 1, len(candidate.columns))

    return sorted(usable, key=sort_key)


def _resolve_key(
    con,
    dataset_name: str,
    stated: list[str] | None,
    ev: DatasetEvidence,
    roles: dict[str, str],
) -> tuple[list[str], KeyVerdict | None, list[str]]:
    """
    The primary key: verified when stated, taken from evidence when not.

    A stated key that does not hold is refused HERE, at proposal time, rather
    than being written into a contract that fails at the gate three steps
    later. The refusal is the one KeyVerdict already produces.
    """
    notes: list[str] = []
    if stated:
        verdict = verify_key(con, dataset_name, stated)
        if not verdict.holds:
            raise ContractRefused(verdict.refusal().to_text())
        notes.append(f"Key as stated: {verdict.sentence()}")
        return list(stated), verdict, notes

    usable = ev.usable_keys()
    if not usable:
        notes.append(
            "No column or pair identifies a row uniquely, so no primary key "
            "was proposed. That is either a coarser grain than one row, or a "
            "key of three or more columns, which is not searched for. State "
            "it with primary_key=[...] and it will be checked."
        )
        return [], None, notes

    ranked = _rank_candidates(usable, roles)
    best = ranked[0]
    notes.append(f"Key from evidence: {best.sentence()}")
    if len(ranked) > 1:
        others = ", ".join(k.label() for k in ranked[1:4])
        notes.append(
            f"Also unique in this data: {others}. Uniqueness is a property of "
            f"the rows that happen to be here; state primary_key=[...] to use "
            f"one of them instead."
        )
    return list(best.columns), None, notes


def _resolve_date_column(
    stated: str | None, ev: DatasetEvidence
) -> tuple[str | None, bool, list[str]]:
    """
    Returns (column, is_a_guess, notes).

    One temporal column is taken. Several is a decision -- which date a trend
    is computed over changes the numbers -- so the widest is offered and
    marked as a guess.
    """
    notes: list[str] = []
    if stated:
        return stated, False, notes

    dates = ev.date_columns()
    if not dates:
        notes.append(
            "No DATE or TIMESTAMP column, so nothing here can be trended over "
            "time and no analysis window applies."
        )
        return None, False, notes

    if len(dates) == 1:
        c = dates[0]
        notes.append(
            f"{c.name} is the only date column, spanning {c.min_value} to "
            f"{c.max_value}."
        )
        return c.name, False, notes

    names = ", ".join(c.name for c in dates)
    notes.append(
        f"{len(dates)} date columns: {names}. The widest was offered, but "
        f"which one a trend is computed over changes the answer."
    )
    return dates[0].name, True, notes


# The point past which a column stops looking like a controlled vocabulary.
# The same twelve the dimension heuristic uses, for the same reason: a set a
# person can read in one line is a set they can confirm or correct.
VOCABULARY_LIMIT = 12


# What a controlled vocabulary is stored as, in this project and in every
# warehouse it will read from. A numeric column of 1-5 could be a rating to
# average or a bucket to group by, and evidence.suggest_role already says only
# a person knows which -- so numbers are left out rather than guessed at.
_VOCABULARY_TYPES = ("VARCHAR", "CHAR", "TEXT", "STRING")


def _domain_notes(con, dataset_name, ev, declared) -> list[str]:
    """What a low-cardinality column holds -- reported, never proposed.

    `analysis_window`'s rule, applied to a second field. The distinct values in
    a column are what IS there; a domain is what is ALLOWED, and the difference
    is whether another value would be a mistake or a Tuesday. Reading the
    set off the data would produce a check that validates the column against
    itself and passes by construction, which is worse than no check because it
    looks like one.

    So this states the values and stops. Nothing is written into `domains`,
    nothing goes in `unresolved`, and no question is asked -- a dataset with no
    controlled vocabulary is complete, not unfinished.
    """
    notes = []
    for col in ev.columns:
        if col.name in declared:
            continue
        # Not `role == "dimension"`: on a small table every repeated-in-life
        # column can look unique, and suggest_role reads a five-row fixture's
        # region as an identifier. The shape of a vocabulary is simpler than
        # the role heuristic -- text, repeating, and few enough to read.
        if not col.dtype.upper().startswith(_VOCABULARY_TYPES):
            continue
        if col.is_unique or col.is_constant or not col.non_null:
            continue
        if col.distinct > VOCABULARY_LIMIT:
            continue
        values = [
            r[0] for r in con.execute(
                f'SELECT DISTINCT "{col.name}" FROM "{dataset_name}" '
                f'WHERE "{col.name}" IS NOT NULL ORDER BY 1'
            ).fetchall()
        ]
        notes.append(
            f"{col.name} holds {col.distinct:,} distinct value(s): "
            f"{', '.join(str(v) for v in values)}. Declare "
            f'domains={{"{col.name}": [...]}} if that is the complete set -- '
            f"the data cannot tell you whether another value is legal and "
            f"merely absent."
        )
    return notes

def propose_contract(
    con,
    dataset_name: str,
    *,
    grain: str | None = None,
    primary_key: list[str] | None = None,
    date_column: str | None = None,
    measures: list[str] | None = None,
    dimensions: list[str] | None = None,
    measure_definitions: dict[str, str] | None = None,
    aggregations: dict[str, str] | None = None,
    analysis_window: tuple[date, date] | None = None,
    known_exclusions: list[Exclusion] | None = None,
    caveats: list[str] | None = None,
    foreign_keys: list[ForeignKey] | None = None,
    domains: dict[str, list[str]] | None = None,
    loaded_at: datetime | None = None,
) -> Proposal:
    """
    Draft a contract for one loaded table.

    Everything after `dataset_name` is an answer coming back. Supplying one
    settles the field it names and removes it from `unresolved` -- the Phase 3
    mechanism, for the Phase 3 reason: a contract's questions are ABOUT its
    fields, so an answer edited into the JSON would leave the rest of the
    document disagreeing with it. The answer comes back the way the question
    went out.

    Stores nothing. `confirm_dataset_contract` does that, in Step 5.
    """
    ev = gather(con, dataset_name)
    binding = binding_for(con, dataset_name, loaded_at)
    roles = {c.name: suggest_role(c)[0] for c in ev.columns}

    notes: list[str] = []
    unresolved: list[str] = []
    questions: list[str] = []

    key, key_verdict, key_notes = _resolve_key(
        con, dataset_name, primary_key, ev, roles
    )
    notes += key_notes

    date_col, date_is_guess, date_notes = _resolve_date_column(date_column, ev)
    notes += date_notes
    if date_is_guess:
        unresolved.append("date_column")
        questions.append(
            f"Which date should analysis be based on? {date_col} was assumed. "
            f"Others present: "
            f"{', '.join(c.name for c in ev.date_columns() if c.name != date_col)}."
        )

    # ---- grain: derived, and still unresolved
    if grain is not None and grain.strip():
        final_grain = grain.strip()
    else:
        final_grain = _grain_sentence(key)
        unresolved.append("grain")
        if key:
            questions.append(
                f"Is '{final_grain}' what one row MEANS, in your words? The "
                f"column names are all the data can offer; what the row "
                f"represents is yours."
            )
        else:
            questions.append(
                "What is one row of this table? Nothing in the data identifies "
                "a row uniquely, so there is not even a candidate to correct."
            )

    # ---- measures and dimensions from roles, unless stated
    measure_names = (
        list(measures)
        if measures is not None
        else [c.name for c in ev.columns if roles[c.name] == "measure"]
    )
    # A repeating identifier is exactly what people group by -- seller_id,
    # customer_id, product_id. Excluding every identifier from the dimensions
    # left `status` as the only thing this table could be broken down by,
    # which is not a description of the table anyone would recognise. The
    # columns that ARE the key are excluded, because grouping by the key
    # returns the table.
    dimension_names = (
        list(dimensions)
        if dimensions is not None
        else [
            c.name
            for c in ev.columns
            if roles[c.name] == "dimension"
            or (
                roles[c.name] == "identifier"
                and not c.is_unique
                and c.name not in key
            )
        ]
    )
    dimension_names = [d for d in dimension_names if d not in measure_names]

    definitions = dict(measure_definitions or {})
    aggs = dict(aggregations or {})
    built: list[Measure] = []
    for name in measure_names:
        definition = definitions.get(name, "").strip()
        agg = aggs.get(name)
        m = Measure(name=name, agg=agg, definition=definition)
        built.append(m)
        if not definition:
            unresolved.append(m.definition_path)
        if agg is None:
            unresolved.append(m.agg_path)
        if not definition or agg is None:
            wanted = []
            if not definition:
                wanted.append("what is included and excluded")
            if agg is None:
                wanted.append(
                    f"how it combines across rows ({', '.join(AGGREGATIONS)} "
                    f"-- 'none' if it must not be combined, which is the "
                    f"answer for a price or a rate)"
                )
            questions.append(
                f"What does {name} mean: {', and '.join(wanted)}?"
            )

    if not built:
        notes.append(
            "No column reads as a measure, so there is nothing to aggregate. "
            "State one with measures=[...] if a column here is a number worth "
            "adding up."
        )

    # ---- analysis window: reported, never proposed
    window = None
    if analysis_window is not None:
        window = AnalysisWindow(start=analysis_window[0], end=analysis_window[1])
    elif date_col:
        unresolved.append("analysis_window")
        span = next(
            (c for c in ev.date_columns() if c.name == date_col), None
        )
        seen = (
            f"{date_col} runs from {span.min_value} to {span.max_value}"
            if span
            else f"{date_col} is the date column"
        )
        questions.append(
            f"What period should the analysis cover? {seen}, but the span of a "
            f"column is not the same as the window you want -- a feed that "
            f"kept writing after the data stopped will stretch it."
        )

    contract = DatasetContract(
        dataset_name=dataset_name,
        grain=final_grain,
        primary_key=key,
        date_column=date_col,
        analysis_window=window,
        measures=built,
        dimensions=dimension_names,
        known_exclusions=list(known_exclusions or []),
        caveats=list(caveats or []),
        # Neither is asked about and neither goes in `unresolved`. dbt does not
        # nag you for a relationships test; empty is a default, not a gap, and
        # a question about a field most datasets leave empty would be noise in
        # the one place this project cannot afford it.
        foreign_keys=list(foreign_keys or []),
        domains=dict(domains or {}),
        bound_to=binding,
        questions=questions,
        unresolved=unresolved,
    )

    notes += _domain_notes(con, dataset_name, ev, contract.domains)
    notes += ev.notes
    return Proposal(
        contract=contract,
        evidence=ev,
        key_verdict=key_verdict,
        notes=notes,
    )


__all__ = ["Proposal", "propose_contract"]
