"""The three cleaning tools, as text an agent can act on.

Phase 6, Step 7b. Everything below returns a string: either a rendered result or
a `Refusal.to_text()` carrying a reason code and the exact call to make next.

**Why `propose` opens its own connection.** Step 1 measured that a genuinely
read-only handle on the workspace is reachable only through
`ATTACH ... (READ_ONLY)` from a separate connection, and only when nothing else
holds the file. `util/db.connect` cannot be that opener: it runs
`CREATE TABLE IF NOT EXISTS _agent_datasets` on every open, and a read-only
attach refuses `CREATE` by statement type, `IF NOT EXISTS` included. So
`connect_read_only` lives here for now rather than in `util/db.py`, where it
would sit beside a function it deliberately does not call. Moving it is a
one-line change if that reads better later.

**The proposal reads read-only and the plan is stored writable.** Two
connections, in that order, never open at once -- one handle per file per
process. The reading half cannot write even if it is wrong; the writing half
touches only `_agent_cleaning_plans`.

**Approval is by id and nothing else.** `apply_cleaning_plan` takes
`approved_action_ids`, resolves them against the latest stored plan, refuses on
staleness before refusing on anything else, and refuses again if the approved
set conflicts. An id that was not approved leaves no trace.

**Approved ids are applied in the order given**, not in plan order. Step 7's
live run found an agent unable to tell which it was, so it forced the order with
two calls rather than assume -- reasonable, and it should not have had to. The
docstrings say so now.

**The suggested call is one the tool would accept.** `NEXT STEP` used to slice
the first three ids, and Step 7's run watched that slice land on the one action
carrying a discard warning, one apply later, after the ids renumbered. It now
offers only actions that are neither lossy nor in conflict with each other, and
says that is what it is offering.
"""

from __future__ import annotations

import duckdb

from ..config import DEFAULT_NA_VALUES
from ..contract.dataset_contract import Binding
from ..contract.refusals import Reason, Refusal
from .. import workspace
from ..util import db
from . import apply as apply_module
from . import detect, ledger, plan
from .plan import ActionKind


def connect_read_only(workspace_id: str):
    """A handle that cannot write, whatever the code above it does.

    Measured in Step 1: CREATE, INSERT, UPDATE and DROP are all refused by the
    engine on a read-only attached database. Nothing here relies on the caller
    being careful.
    """
    con = duckdb.connect(":memory:")
    path = workspace.duckdb_path(workspace_id)
    con.execute(f"ATTACH '{path}' AS ws (READ_ONLY)")
    con.execute("USE ws")
    return con


def _table_exists(con, dataset_name: str) -> bool:
    return bool(
        con.execute(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_schema = 'main' AND table_name = ?",
            [dataset_name],
        ).fetchone()
    )


def _fingerprint(con, dataset_name: str, row_count: int) -> str:
    """Phase 4's fingerprint, computed by Phase 4's code.

    The column list is read here; the hash is not computed here. Two
    fingerprints of one table that disagree would be worse than none.

    `Binding.from_pairs` requires a row count even though the fingerprint is
    taken over the columns alone -- structure is identity, volume is not, and
    the binding records both. Passing the count we already have is cheaper than
    reading the table twice.
    """
    pairs = [
        (r[0], r[1])
        for r in con.execute(
            "SELECT column_name, data_type FROM information_schema.columns "
            "WHERE table_name = ? ORDER BY ordinal_position",
            [dataset_name],
        ).fetchall()
    ]
    return Binding.from_pairs(pairs, row_count).fingerprint


def _not_loaded(con, dataset_name: str) -> str:
    available = ", ".join(db.user_tables(con)) or "(none loaded)"
    return Refusal(
        reason=Reason.DATASET_NOT_LOADED,
        what=f"there is no dataset called '{dataset_name}' in this workspace.",
        why="cleaning rebuilds a loaded table, and nothing is read from disk here.",
        state=f"loaded: {available}",
        next_call='list_datasets() to see what is already here',
    ).to_text()


def _safe_suggestion(actions, limit: int = 3):
    """Actions worth suggesting: lossless, compatible, and in the right order.

    Three filters, and the third was missed on the first attempt.

    1. Nothing lossy. A suggestion that includes the action the same message
       just warned about is worse than no suggestion.
    2. Nothing that conflicts with what is already picked, checked with the
       same `conflicts()` that would refuse it. A suggestion the tool would
       refuse is worse than no suggestion.
    3. **No conversion on a column that also has a normalisation waiting.**
       This is the one that slipped through, because `conflicts()` only fires
       when both are in the SAME call. Suggesting the conversion alone passes
       every check and still produces the worse outcome: the declared tokens
       are disposed of by the cast rather than by a step somebody named, which
       is precisely what this module's own refusal tells you to avoid. A
       suggestion that contradicts the refusal is not a smaller bug than a
       suggestion that gets refused.

    So the normalisation is offered first and the conversion comes round on the
    next proposal, which is the order the refusal recommends.
    """
    deferred = {
        a.column for a in actions
        if a.kind is ActionKind.NORMALISE_MISSING and a.column
    }
    picked = []
    for a in actions:
        if a.is_lossy:
            continue
        if a.kind is ActionKind.CONVERT_TYPE and a.column in deferred:
            continue
        if apply_module.conflicts(picked + [a]):
            continue
        picked.append(a)
        if len(picked) == limit:
            break
    return picked


def propose_cleaning_plan(
    workspace_id: str,
    dataset_name: str,
    missing_values: list[str] | None = None,
) -> str:
    """Detect on a read-only handle, then store the plan on a writable one."""
    tokens = DEFAULT_NA_VALUES if missing_values is None else missing_values

    ro = connect_read_only(workspace_id)
    try:
        if not _table_exists(ro, dataset_name):
            return _not_loaded(ro, dataset_name)
        actions = detect.detect(
            ro, source=dataset_name, target=dataset_name, missing_tokens=tokens
        )
        rows = ro.execute(
            f'SELECT count(*) FROM "{dataset_name}"'
        ).fetchone()[0]
        fingerprint = _fingerprint(ro, dataset_name, rows)
    finally:
        ro.close()

    if not actions:
        return (
            f"Nothing to clean in {dataset_name}. {rows:,} row(s), no exact "
            f"duplicates, no declared missing tokens, no padding, no case "
            f"variants, and every column already reads as the type it holds.\n\n"
            f"NEXT STEP: call profile_dataset(dataset_name=\"{dataset_name}\") "
            f"if you want the full counts anyway."
        )

    con = db.connect(workspace_id)
    try:
        stored = plan.record(
            con,
            dataset_name=dataset_name,
            row_count=rows,
            fingerprint=fingerprint,
            actions=actions,
        )
    finally:
        con.close()

    lines = "\n\n".join(f"  {a.line()}" for a in stored.actions)
    lossy = [a.action_id for a in stored.actions if a.is_lossy]
    warning = (
        f"\n{len(lossy)} of these discard something that is not declared "
        f"missing anywhere ({', '.join(lossy)}). Read those lines before "
        f"approving them.\n"
        if lossy
        else ""
    )
    suggested = _safe_suggestion(stored.actions)
    if suggested:
        ids = ", ".join(f'"{a.action_id}"' for a in suggested)
        held = [
            a.action_id for a in stored.actions
            if a.kind is ActionKind.CONVERT_TYPE and a.column in {
                x.column for x in stored.actions
                if x.kind is ActionKind.NORMALISE_MISSING
            }
        ]
        because = (
            f" {', '.join(held)} is left for the next round on purpose: "
            f"converting that column would dispose of its declared missing "
            f"tokens as part of the cast, and doing it in two steps records "
            f"which one disposed of them."
            if held
            else ""
        )
        nudge = (
            f"NEXT STEP: call apply_cleaning_plan(dataset_name=\"{dataset_name}\", "
            f"approved_action_ids=[{ids}]) — these discard nothing and can run "
            f"together.{because} Any of the others are yours to add by id."
        )
    else:
        nudge = (
            f"NEXT STEP: read the lines above and call "
            f"apply_cleaning_plan(dataset_name=\"{dataset_name}\", "
            f"approved_action_ids=[...]) with the ids you want. Nothing here "
            f"is free of loss, so there is no set worth suggesting."
        )
    return (
        f"{len(stored.actions)} change(s) proposed for {dataset_name} "
        f"({rows:,} row(s)). Nothing has been changed.\n\n"
        f"{lines}\n{warning}\n"
        f"Approve by id, in the order you want them run. Anything you do not "
        f"name is not run.\n\n"
        f"{nudge}"
    )


def apply_cleaning_plan(
    workspace_id: str, dataset_name: str, approved_action_ids: list[str]
) -> str:
    """Run exactly the approved ids, in the order given, or change nothing."""
    con = db.connect(workspace_id)
    try:
        if not _table_exists(con, dataset_name):
            return _not_loaded(con, dataset_name)

        stored = plan.latest(con, dataset_name)
        if stored is None:
            return Refusal(
                reason=Reason.NO_CLEANING_PLAN,
                what=f"nothing has been proposed for {dataset_name}.",
                why="approval is by action id, and the ids come from a plan.",
                next_call=f'propose_cleaning_plan(dataset_name="{dataset_name}")',
            ).to_text()

        rows = con.execute(f'SELECT count(*) FROM "{dataset_name}"').fetchone()[0]
        stale = stored.staleness(rows, _fingerprint(con, dataset_name, rows))
        if stale:
            return Refusal(
                reason=Reason.CLEANING_PLAN_STALE,
                what=f"the plan for {dataset_name} is out of date.",
                why=stale,
                state=f"{stored.age_phrase()}, {len(stored.actions)} action(s)",
                next_call=f'propose_cleaning_plan(dataset_name="{dataset_name}")',
            ).to_text()

        if not approved_action_ids:
            return Refusal(
                reason=Reason.NOTHING_APPROVED,
                what="no action ids were approved.",
                why="nothing is run unless it is named. That is the whole gate.",
                state=", ".join(a.action_id for a in stored.actions),
                next_call=(
                    f'apply_cleaning_plan(dataset_name="{dataset_name}", '
                    f'approved_action_ids=["{stored.actions[0].action_id}"])'
                ),
            ).to_text()

        found, unknown = stored.resolve(approved_action_ids)
        if unknown:
            return Refusal(
                reason=Reason.ACTION_NOT_IN_PLAN,
                what=f"{', '.join(unknown)} is not in the plan for {dataset_name}.",
                why="an id that is not in the plan cannot be run, and running "
                    "the rest without saying so would be worse.",
                state="in the plan: "
                      + ", ".join(a.action_id for a in stored.actions),
                next_call=f'propose_cleaning_plan(dataset_name="{dataset_name}")',
            ).to_text()

        problems = apply_module.conflicts(found)
        if problems:
            return Refusal(
                reason=Reason.ACTIONS_CONFLICT,
                what="these actions cannot be applied together.",
                why=" ".join(problems),
                state="approved: " + ", ".join(a.action_id for a in found),
                next_call=(
                    f'apply_cleaning_plan(dataset_name="{dataset_name}", '
                    f'approved_action_ids=["{found[0].action_id}"])'
                ),
            ).to_text()

        result = apply_module.apply(
            con, dataset_name=dataset_name, actions=found,
            plan_id=stored.plan_id,
        )
        skipped = [
            a.action_id for a in stored.actions
            if a.action_id not in {x.action_id for x in found}
        ]
        applied_lines = "\n".join(
            f"  {a.action_id} {a.kind.value}"
            + (f" on {a.column}" if a.column else "")
            + (f": {a.rows_removed:,} row(s) removed"
               if a.rows_removed else ": row count unchanged")
            for a in result.applied
        )
        tail = (
            f"\n{len(skipped)} action(s) were not approved and did not run: "
            f"{', '.join(skipped)}.\n"
            if skipped
            else ""
        )
        return (
            f"{result.line()}\n\n{applied_lines}\n{tail}\n"
            f"NEXT STEP: call profile_dataset(dataset_name=\"{dataset_name}\") "
            f"to see the table as it is now."
        )
    finally:
        con.close()


def get_cleaning_ledger(workspace_id: str, dataset_name: str | None = None) -> str:
    """Every action that has actually run, newest first."""
    con = db.connect(workspace_id)
    try:
        return ledger.describe(con, dataset_name)
    finally:
        con.close()


__all__ = [
    "apply_cleaning_plan",
    "connect_read_only",
    "get_cleaning_ledger",
    "propose_cleaning_plan",
]
