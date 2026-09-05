"""What was actually applied, in the transaction that applied it.

Phase 6, Step 7.

**P6-D6, both halves.**

*Append-only, and a table rather than a JSONL file.* The build guide asks for
JSONL. The reason to overrule it is the one thing a file cannot do: **the ledger
must be written inside the same transaction as the apply.** Step 6 measured that
DuckDB rolls DDL back, so a clean either happens entirely or not at all -- and a
ledger written after the commit can still fail after it, leaving a clean nobody
recorded, or be written before a rollback, leaving a record of a clean that
never happened. A row in the same transaction cannot disagree with the tables it
describes. Durability across a `workspace.reset` is not a counter-argument:
reset is meant to clear the workspace, and a ledger that outlived it would
describe tables that no longer exist.

*No envelope.* `util/results.py` exists for results too big to say -- a profile
of sixty columns, a query returning fifty thousand rows. A ledger is bounded by
the number of times somebody approved a clean, not by the size of the data, and
filtering it by dataset is one `WHERE`. So `describe()` returns inline, newest
first, **capped with the remainder counted** -- the principle P5-D3 settled for
a different problem: a cap with the remainder reported, never a sample with the
shortfall unstated.

**One row per action, not per apply.** "Approve 3 of 6, and the ledger shows
exactly those 3 with correct counts" is the Done-When, and it is a statement
about actions. An apply-level row would have to summarise, and summarising is
where a count stops being checkable.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ..profile.runs import BOOKKEEPING_PREFIX

LEDGER_TABLE = f"{BOOKKEEPING_PREFIX}cleaning_ledger"

# What describe() shows before it starts counting instead of listing.
INLINE_ENTRIES = 20


@dataclass(frozen=True)
class LedgerEntry:
    applied_at: datetime
    dataset_name: str
    plan_id: str
    action_id: str
    kind: str
    column: str | None
    rows_before: int
    rows_after: int
    history_table: str
    statement: str

    @property
    def rows_removed(self) -> int:
        return self.rows_before - self.rows_after

    def line(self) -> str:
        """One entry, with the plan its id belongs to.

        Action ids are per-plan by design -- C001 is meant to be read off a
        screen and typed back, which rules out a uuid -- and that is right for
        approval and wrong for a permanent record. Step 7's live run found C002
        and C004 each appearing twice in one ledger meaning different actions,
        disambiguated only by the history table name. The plan id was already
        stored; it just was not printed.
        """
        where = f" on {self.column}" if self.column else ""
        stamp = self.applied_at.strftime("%Y-%m-%d %H:%M")
        change = (
            f"{self.rows_removed:,} row(s) removed"
            if self.rows_removed
            else f"{self.rows_after:,} row(s), unchanged in count"
        )
        return (
            f"{stamp}  {self.dataset_name}  {self.action_id}/{self.plan_id[:6]} "
            f"{self.kind}{where}: {change}. Before: {self.history_table}"
        )


def ensure_table(con) -> None:
    """Lazily, for the reason contract/store.py and profile/runs.py record.

    Called by apply() on the writable connection before the transaction opens,
    never from the read-only proposal path -- a read-only ATTACH refuses CREATE
    by statement type, IF NOT EXISTS included. Step 1 measured that.
    """
    con.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {LEDGER_TABLE} (
            applied_at     TIMESTAMP NOT NULL,
            dataset_name   VARCHAR NOT NULL,
            plan_id        VARCHAR NOT NULL,
            action_id      VARCHAR NOT NULL,
            kind           VARCHAR NOT NULL,
            column_name    VARCHAR,
            rows_before    BIGINT NOT NULL,
            rows_after     BIGINT NOT NULL,
            history_table  VARCHAR NOT NULL,
            statement      VARCHAR NOT NULL
        )
        """
    )


def record_action(
    con,
    *,
    applied_at: datetime,
    dataset_name: str,
    plan_id: str,
    action_id: str,
    kind: str,
    column: str | None,
    rows_before: int,
    rows_after: int,
    history_table: str,
    statement: str,
) -> None:
    """Append one action. Called from inside apply()'s transaction.

    Primitives rather than an ApplyResult, so this module imports nothing from
    apply and apply can import this one.
    """
    con.execute(
        f"INSERT INTO {LEDGER_TABLE} VALUES (?,?,?,?,?,?,?,?,?,?)",
        [
            applied_at, dataset_name, plan_id, action_id, kind, column,
            rows_before, rows_after, history_table, statement,
        ],
    )


def entries(
    con, dataset_name: str | None = None, limit: int | None = None
) -> list[LedgerEntry]:
    """Newest first. Everything, or one dataset's."""
    ensure_table(con)
    where, args = "", []
    if dataset_name:
        where, args = "WHERE dataset_name = ?", [dataset_name]
    cap = f"LIMIT {int(limit)}" if limit else ""
    rows = con.execute(
        f"SELECT * FROM {LEDGER_TABLE} {where} "
        f"ORDER BY applied_at DESC, action_id DESC {cap}",
        args,
    ).fetchall()
    return [LedgerEntry(*r) for r in rows]


def count(con, dataset_name: str | None = None) -> int:
    ensure_table(con)
    where, args = "", []
    if dataset_name:
        where, args = "WHERE dataset_name = ?", [dataset_name]
    return con.execute(
        f"SELECT count(*) FROM {LEDGER_TABLE} {where}", args
    ).fetchone()[0]


def describe(con, dataset_name: str | None = None) -> str:
    """The ledger as text. Inline, capped, with the remainder counted."""
    total = count(con, dataset_name)
    scope = f" for {dataset_name}" if dataset_name else ""
    if not total:
        return (
            f"Nothing has been cleaned{scope}. Every table is as it was "
            f"loaded.\n\n"
            f"NEXT STEP: call propose_cleaning_plan(dataset_name=\"...\") to "
            f"see what could be changed."
        )

    shown = entries(con, dataset_name, limit=INLINE_ENTRIES)
    head = (
        f"{total:,} cleaning action(s) applied{scope}, newest first."
        if total <= INLINE_ENTRIES
        else f"{total:,} cleaning action(s) applied{scope}. "
        f"Showing the {len(shown)} most recent; {total - len(shown):,} older "
        f"one(s) are not shown."
    )
    body = "\n".join(f"  {e.line()}" for e in shown)
    return (
        f"{head}\n\n{body}\n\n"
        f"Each line names the table holding the data as it was before that "
        f"action. Nothing here was applied without an action id being "
        f"approved by name."
    )


__all__ = [
    "INLINE_ENTRIES",
    "LEDGER_TABLE",
    "LedgerEntry",
    "count",
    "describe",
    "ensure_table",
    "entries",
    "record_action",
]
