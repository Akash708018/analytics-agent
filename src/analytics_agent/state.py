"""
The gate, and what a person sees when they ask where they are.

Locked decision 12: no analysis without a confirmed Dataset Contract. This is
where that is enforced, and it is one function -- `require_contract` -- that
every analysis tool calls before doing anything.

The gate is not a lookup. A stored contract answers "did somebody agree
something", and the question that matters is "is the agreement still true of
what is in front of me". So the check runs:

    1. is the table loaded at all?
    2. is there a contract in force for it?
    3. has the structure moved in a way that breaks it?           (Step 3)
    4. does the primary key still identify a row?                 (Step 3)

Steps 3 and 4 are executed, not remembered. That is the industrial pattern --
Great Expectations runs a checkpoint, dbt runs tests -- and the fingerprint is
used only as a **cache key** to skip step 4 when nothing has moved. Comparing a
stored hash answers "did something change" and never "is this still true".

What comes back is a `Gate`, which either carries the contract and any caveats
to attach to results, or has already been turned into a refusal. Every refusal
here follows 8.2 -- what was blocked, the exact next call, the current state --
and carries a reason code, so `test_phase4.py` and the Phase 13 eval can assert
on the gate rather than on its wording.

`describe_workflow_state` is the other half, and it exists because of F13. The
MCP server outlives the conversation, so a dataset loaded two hours ago in a
different chat is still sitting in the workspace. Listing every dataset with
its load time and its contract version makes that visible rather than
surprising, and gives whoever reads it the exact call to make next.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from analytics_agent.contract import ContractRefused
from analytics_agent.contract.compatibility import (
    Drift,
    DriftVerdict,
    KeyVerdict,
    binding_for,
    classify_drift,
    verify_key,
)
from analytics_agent.contract.dataset_contract import DatasetContract
from analytics_agent.contract.refusals import Reason, Refusal
from analytics_agent.contract.store import StoredContract, all_current, current
from analytics_agent.profile import runs
from analytics_agent.util import db


@dataclass
class Gate:
    """A passed gate: the contract, and what has to be said about it."""

    contract: DatasetContract
    version: int
    drift: DriftVerdict
    key: KeyVerdict | None = None
    revalidated: bool = True

    @property
    def caveats(self) -> list[str]:
        """
        Everything a result computed under this contract has to carry.

        Drift first, because it is about whether the agreement still fits;
        then the caveats a person wrote into the contract, which are about the
        data itself. A report that prints numbers without these is a report
        that has quietly dropped the reasons they might be wrong.
        """
        out = []
        drift_caveat = self.drift.caveat()
        if drift_caveat:
            out.append(drift_caveat)
        out.extend(self.contract.caveats)
        for e in self.contract.known_exclusions:
            count = f" ({e.row_count:,} rows)" if e.row_count is not None else ""
            out.append(f"Excluded: {e.rule}{count} -- {e.reason}.")
        return out

    def header(self) -> str:
        """One line naming the agreement a result was computed under."""
        return (
            f"Under contract v{self.version} for "
            f"{self.contract.dataset_name}: {self.contract.grain}."
        )


def require_contract(con, dataset_name: str) -> Gate:
    """
    The gate every analysis tool calls first.

    Raises ContractRefused with an instructional message when analysis must
    not proceed. Returns a Gate when it may -- carrying caveats, which are not
    optional decoration: a NEUTRAL verdict means the numbers were agreed
    against different data, and saying so is the difference between a result
    and a misleading result.
    """
    if dataset_name not in _loadable_tables(con):
        available = ", ".join(_loadable_tables(con)) or "(none loaded)"
        raise ContractRefused(
            Refusal(
                reason=Reason.DATASET_NOT_LOADED,
                what=f"there is no dataset called '{dataset_name}' in this workspace.",
                why="analysis runs on a loaded table, and nothing is read from disk here.",
                state=f"loaded: {available}",
                next_call=(
                    f'propose_ingest_spec(path="...") then confirm_ingest_spec, '
                    f"or list_datasets() to see what is already here"
                ),
            ).to_text()
        )

    live = current(con, dataset_name)
    if live is None:
        rows, cols = db.table_shape(con, dataset_name)
        raise ContractRefused(
            Refusal(
                reason=Reason.NO_CONTRACT,
                what=(
                    f"analysis of '{dataset_name}' requires a confirmed Dataset "
                    f"Contract. None exists."
                ),
                why=(
                    "without one there is no agreed grain, so nothing can say "
                    "whether summing a column double-counts, and no measure has "
                    "a definition any number could be traced back to."
                ),
                state=f"loaded ({rows:,} rows, {cols} columns), no contract",
                next_call=(
                    f'propose_dataset_contract(dataset_name="{dataset_name}"), '
                    f"show the draft to the user, answer its questions, then "
                    f"confirm_dataset_contract once they agree"
                ),
            ).to_text()
        )

    observed = binding_for(con, dataset_name)
    drift = classify_drift(live.contract, observed)
    if drift.blocks:
        raise ContractRefused(drift.refusal().to_text())

    # The fingerprint earns its keep here and nowhere else: identical
    # structure AND identical row count means nothing can have moved, so the
    # key re-check is skipped. Any difference at all and it is run.
    unchanged = (
        drift.drift is Drift.IDENTICAL
        and live.contract.bound_to.fingerprint == observed.fingerprint
    )
    key_verdict = None
    if live.contract.primary_key and not unchanged:
        key_verdict = verify_key(con, dataset_name, live.contract.primary_key)
        if not key_verdict.holds:
            raise ContractRefused(key_verdict.refusal().to_text())

    return Gate(
        contract=live.contract,
        version=live.version,
        drift=drift,
        key=key_verdict,
        revalidated=not unchanged,
    )


def _loadable_tables(con) -> list[str]:
    """
    Tables a person loaded, with bookkeeping filtered out here as well as in
    db.user_tables.

    Belt and braces on purpose. `_agent_contracts` did not exist when
    db.user_tables was written, so whether it is excluded depends on whether
    that filter tests for one known name or for the underscore convention.
    Listing the contract log as a dataset and then reporting that it has no
    contract would be a small absurdity in the one tool whose job is telling
    someone where they are.
    """
    return [n for n in db.user_tables(con) if not n.startswith("_")]


@dataclass
class DatasetState:
    """One dataset, as get_workflow_state reports it."""

    dataset_name: str
    row_count: int
    column_count: int
    age_phrase: str
    source: str
    contract: StoredContract | None = None
    blocked_by: str = ""
    next_call: str = ""
    notes: list[str] = field(default_factory=list)

    @property
    def stage(self) -> str:
        if self.contract is None:
            return "loaded, no contract"
        if self.blocked_by:
            return f"contract v{self.contract.version}, BLOCKED"
        return f"contract v{self.contract.version}, ready"


def dataset_states(con) -> list[DatasetState]:
    """
    Every loaded dataset, with where it is and what to call next.

    The load timestamps are the point (F13). This server is launched once when
    Claude Desktop starts and kept alive across every conversation, so a
    dataset from two hours ago and another chat is still here. Showing when
    each arrived turns a leftover from a surprise into a fact.
    """
    out: list[DatasetState] = []
    for name in _loadable_tables(con):
        rows, cols = db.table_shape(con, name)
        record = db.get_dataset(con, name)
        state = DatasetState(
            dataset_name=name,
            row_count=rows,
            column_count=cols,
            age_phrase=record.age_phrase() if record else "No load record.",
            source=(
                f"{record.source_type} - {record.source_detail}"
                if record
                else "unknown - not created by a loader"
            ),
        )
        if record is None:
            state.notes.append(
                "This table was not created by a loader, so nothing is known "
                "about where it came from."
            )

        live = current(con, name)
        state.contract = live
        if live is None:
            state.next_call = f'propose_dataset_contract(dataset_name="{name}")'
            out.append(state)
            continue

        try:
            observed = binding_for(con, name)
            drift = classify_drift(live.contract, observed)
        except ContractRefused as exc:
            state.blocked_by = str(exc)
            state.next_call = f'propose_dataset_contract(dataset_name="{name}")'
            out.append(state)
            continue

        if drift.blocks:
            state.blocked_by = f"stale: {', '.join(drift.breaking)} no longer exist"
            state.next_call = f'propose_dataset_contract(dataset_name="{name}")'
        else:
            caveat = drift.caveat()
            if caveat:
                state.notes.append(caveat)

            # The gate's own check, run here for the reason dbt will not tell
            # you to build a model whose upstream test failed: a status view
            # that recommends a call the gate refuses is worse than one that
            # recommends nothing. This mirrors require_contract exactly --
            # same function, same cache shortcut -- so the two cannot disagree
            # about a dataset. Found by a live agent reading get_workflow_state
            # and validate_dataset side by side; no acceptance fixture had a
            # key that fails.
            key = None
            if live.contract.primary_key:
                unchanged = (
                    drift.drift is Drift.IDENTICAL
                    and live.contract.bound_to.fingerprint == observed.fingerprint
                )
                if not unchanged:
                    key = verify_key(con, name, live.contract.primary_key)

            if key is not None and not key.holds:
                state.blocked_by = f"the key does not hold -- {key.sentence()}"
                state.next_call = f'validate_dataset(dataset_name="{name}")'
            else:
                state.next_call = f'run_analysis(dataset_name="{name}", ...)'
        out.append(state)
    return out


def describe_workflow_state(con) -> str:
    """What get_workflow_state returns."""
    states = dataset_states(con)
    if not states:
        return (
            "Nothing is loaded in this workspace.\n\n"
            "NEXT STEP: call propose_ingest_spec(path=\"...\") to read a file, "
            "then confirm_ingest_spec to load it."
        )

    lines = [
        f"{len(states)} dataset(s) in this workspace.",
        "",
        "| dataset | rows | columns | stage | next call |",
        "| --- | --- | --- | --- | --- |",
    ]
    for s in states:
        lines.append(
            f"| {s.dataset_name} | {s.row_count:,} | {s.column_count} | "
            f"{s.stage} | {s.next_call} |"
        )

    for s in states:
        lines += ["", f"### {s.dataset_name}", s.age_phrase, f"Source: {s.source}"]
        profile_lines = runs.state_notes(con, s.dataset_name, s.row_count)
        if profile_lines:
            lines += profile_lines
        else:
            lines.append(
                f'Not profiled. profile_dataset(dataset_name="{s.dataset_name}") '
                f"counts the nulls, duplicates and distributions before anyone "
                f"has to agree what the columns mean."
            )

        # Imported here rather than at the top: clean/ledger.py arrived two
        # phases after this file, and state.py is imported by the server at
        # startup while clean/ledger.py imports profile/runs.py. A local import
        # keeps that graph flat whatever else moves.
        from .clean import ledger as clean_ledger

        lines += clean_ledger.state_notes(con, s.dataset_name)

        # Local for the same reason, and one more: validate/runs.py imports
        # profile/runs.py, which this file already imports at the top. A local
        # import keeps the graph flat whatever else moves.
        from .validate import runs as validate_runs

        lines += validate_runs.state_notes(
            con,
            s.dataset_name,
            s.row_count,
            s.contract.version if s.contract else None,
        )
        if s.contract:
            lines.append(
                f"Contract v{s.contract.version}, confirmed "
                f"{s.contract.confirmed_at:%Y-%m-%d %H:%M}, fingerprint "
                f"{s.contract.fingerprint}."
            )
            lines.append(f"Grain: {s.contract.contract.grain}")
        else:
            lines.append("No contract. Analysis is blocked until one is confirmed.")
        for n in s.notes:
            lines.append(f"NOTE: {n}")
        if s.blocked_by:
            lines.append(f"BLOCKED: {s.blocked_by}")
        lines.append(f"NEXT STEP: call {s.next_call}")

    stale = [s for s in states if s.blocked_by]
    missing = [s for s in states if s.contract is None]
    if stale or missing:
        lines += ["", "Summary:"]
        if missing:
            lines.append(
                f"  {len(missing)} dataset(s) have no contract: "
                f"{', '.join(s.dataset_name for s in missing)}."
            )
        if stale:
            lines.append(
                f"  {len(stale)} dataset(s) have a contract that no longer "
                f"fits the table: {', '.join(s.dataset_name for s in stale)}."
            )
    return "\n".join(lines)


__all__ = [
    "DatasetState",
    "Gate",
    "dataset_states",
    "describe_workflow_state",
    "require_contract",
]
