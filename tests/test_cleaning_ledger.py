"""clean/ledger.py and clean/tools.py: what ran, and the gate in front of it.

Phase 6, Step 7. Run from the repo root:

    uv run pytest tests/test_cleaning_ledger.py -q

The ledger tests use a plain in-memory connection. The tool tests need a real
workspace, because the whole point of propose_cleaning_plan is that it opens the
workspace file read-only and cannot write to it.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

import duckdb
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from analytics_agent import workspace  # noqa: E402
from analytics_agent.clean import apply as ap  # noqa: E402
from analytics_agent.clean import detect, ledger, tools  # noqa: E402
from analytics_agent.clean.plan import ActionKind  # noqa: E402
from analytics_agent.contract.refusals import Reason, reason_of  # noqa: E402
from analytics_agent.profile.runs import is_bookkeeping  # noqa: E402
from analytics_agent.util import db  # noqa: E402

WORKSPACE = "cleaning_tools_test"
TOKENS = ["", "NA", "N/A", "-", "--", "null", "NULL", "None"]

ROWS = """
  ('ORD-01', 'North',  '10',  '9.50'),
  ('ORD-02', 'North ', '20',  '10.00'),
  ('ORD-03', 'north',  'n/a', '11.00'),
  ('ORD-04', 'South',  '40',  '12.25'),
  ('ORD-05', 'N/A',    '50',  '13.00'),
  ('ORD-06', 'South',  '60',  '14.00'),
  ('ORD-07', 'East',   '70',  '15.75'),
  ('ORD-08', 'East',   '80',  '16.00'),
  ('ORD-09', 'West',   '90',  '17.50'),
  ('ORD-10', 'West',   '11',  '18.00')
"""
CREATE = (
    f"CREATE OR REPLACE TABLE mixed AS SELECT * FROM (VALUES {ROWS}) "
    f"t(order_id, region, units, unit_price)"
)


@pytest.fixture()
def con():
    c = duckdb.connect(":memory:")
    c.execute(CREATE)
    yield c
    c.close()


@pytest.fixture()
def ws():
    workspace.reset(WORKSPACE)
    c = db.connect(WORKSPACE)
    c.execute(CREATE)
    c.close()
    yield WORKSPACE
    workspace.reset(WORKSPACE)


def proposals(con):
    return detect.detect(con, source="mixed", target="mixed",
                         missing_tokens=TOKENS)


def pick(actions, kind, column=None):
    return next(a for a in actions if a.kind is kind and a.column == column)


# --------------------------------------------------------------------------
# the ledger
# --------------------------------------------------------------------------


def test_the_ledger_table_is_bookkeeping():
    assert ledger.LEDGER_TABLE == "_agent_cleaning_ledger"
    assert is_bookkeeping(ledger.LEDGER_TABLE)


def test_an_empty_ledger_says_nothing_has_been_cleaned(con):
    text = ledger.describe(con)
    assert "Nothing has been cleaned" in text
    assert "propose_cleaning_plan" in text


def test_one_row_per_action_not_per_apply(con):
    """The Done-When is "the ledger shows exactly those 3", which is a
    statement about actions. An apply-level row would have to summarise."""
    actions = proposals(con)
    pair = [
        pick(actions, ActionKind.TRIM_WHITESPACE, "region"),
        pick(actions, ActionKind.NORMALISE_CASE, "region"),
    ]
    ap.apply(con, dataset_name="mixed", actions=pair, plan_id="p1")
    assert ledger.count(con) == 2
    assert {e.action_id for e in ledger.entries(con)} == {
        a.action_id for a in pair
    }


def test_the_ledger_names_the_snapshot_for_each_action(con):
    ap.apply(con, dataset_name="mixed",
             actions=[pick(proposals(con), ActionKind.CONVERT_TYPE, "units")],
             plan_id="p1")
    entry = ledger.entries(con)[0]
    assert entry.history_table == "_agent_history_mixed_v1"
    assert "_agent_history_mixed_v1" in entry.line()


def test_the_ledger_carries_the_statement_that_ran(con):
    action = pick(proposals(con), ActionKind.CONVERT_TYPE, "units")
    ap.apply(con, dataset_name="mixed", actions=[action], plan_id="p1")
    assert ledger.entries(con)[0].statement == action.sql


def test_a_rolled_back_apply_leaves_no_ledger_entry(con):
    """The reason this is a table and not a JSONL file. A ledger written after
    the commit can fail after it; one written before a rollback records a clean
    that never happened. A row in the same transaction cannot disagree."""
    good = pick(proposals(con), ActionKind.CONVERT_TYPE, "units")
    from analytics_agent.clean.plan import CleaningAction
    broken = CleaningAction(
        action_id="C099", kind=ActionKind.TRIM_WHITESPACE, column="unit_price",
        intent="cannot run",
        sql='CREATE OR REPLACE TABLE "mixed" AS SELECT * REPLACE '
            '(no_such_function("unit_price") AS "unit_price") FROM "mixed"',
    )
    with pytest.raises(Exception):
        ap.apply(con, dataset_name="mixed", actions=[good, broken], plan_id="p1")
    assert ledger.count(con) == 0


def test_the_ledger_filters_by_dataset(con):
    con.execute("CREATE TABLE other AS SELECT ' x ' AS c")
    ap.apply(con, dataset_name="mixed",
             actions=[pick(proposals(con), ActionKind.CONVERT_TYPE, "units")],
             plan_id="p1")
    ap.apply(
        con, dataset_name="other",
        actions=detect.detect(con, source="other", target="other",
                              missing_tokens=TOKENS),
        plan_id="p2",
    )
    assert ledger.count(con, "mixed") == 1
    assert {e.dataset_name for e in ledger.entries(con, "other")} == {"other"}


def test_a_long_ledger_is_capped_with_the_remainder_counted(con):
    """P5-D3's principle on a different problem: a cap with the remainder
    reported, never a sample with the shortfall unstated."""
    now = datetime.now()
    ledger.ensure_table(con)
    for i in range(ledger.INLINE_ENTRIES + 5):
        ledger.record_action(
            con, applied_at=now - timedelta(minutes=i), dataset_name="mixed",
            plan_id="p", action_id=f"C{i:03d}", kind="CONVERT_TYPE",
            column="units", rows_before=10, rows_after=10,
            history_table="_agent_history_mixed_v1", statement="SELECT 1",
        )
    text = ledger.describe(con, "mixed")
    assert "25 cleaning action(s) applied" in text
    assert "5 older one(s) are not shown" in text
    assert text.count("CONVERT_TYPE") == ledger.INLINE_ENTRIES


# --------------------------------------------------------------------------
# the tools
# --------------------------------------------------------------------------


def test_the_proposal_connection_cannot_write(ws):
    """Step 1 measured the guard; this asserts the tool actually uses it."""
    ro = tools.connect_read_only(ws)
    try:
        with pytest.raises(duckdb.InvalidInputException):
            ro.execute("CREATE TABLE evil AS SELECT 1")
        assert ro.execute("SELECT count(*) FROM mixed").fetchone()[0] == 10
    finally:
        ro.close()


def test_proposing_lists_the_actions_and_changes_nothing(ws):
    text = tools.propose_cleaning_plan(ws, "mixed", missing_values=TOKENS)
    assert "Nothing has been changed" in text
    assert "C001" in text
    assert "apply_cleaning_plan" in text
    con = db.connect(ws)
    try:
        assert con.execute(
            "SELECT units FROM mixed WHERE order_id = 'ORD-03'"
        ).fetchone()[0] == "n/a"
    finally:
        con.close()


def test_proposing_a_missing_dataset_refuses_with_a_reason(ws):
    text = tools.propose_cleaning_plan(ws, "nope")
    assert reason_of(text) is Reason.DATASET_NOT_LOADED
    assert "list_datasets()" in text


def test_applying_without_a_plan_refuses(ws):
    text = tools.apply_cleaning_plan(ws, "mixed", ["C001"])
    assert reason_of(text) is Reason.NO_CLEANING_PLAN
    assert "propose_cleaning_plan" in text


def test_approving_nothing_refuses_and_says_why(ws):
    tools.propose_cleaning_plan(ws, "mixed", missing_values=TOKENS)
    text = tools.apply_cleaning_plan(ws, "mixed", [])
    assert reason_of(text) is Reason.NOTHING_APPROVED
    assert "nothing is run unless it is named" in text


def test_an_unknown_id_refuses_rather_than_running_the_rest(ws):
    """Running the known ids and silently skipping the unknown one is the worst
    failure this tool has available."""
    tools.propose_cleaning_plan(ws, "mixed", missing_values=TOKENS)
    text = tools.apply_cleaning_plan(ws, "mixed", ["C001", "C099"])
    assert reason_of(text) is Reason.ACTION_NOT_IN_PLAN
    assert "C099" in text
    con = db.connect(ws)
    try:
        assert ledger.count(con, "mixed") == 0
    finally:
        con.close()


def test_conflicting_ids_refuse_and_name_one_to_drop(ws):
    tools.propose_cleaning_plan(ws, "mixed", missing_values=TOKENS)
    con = db.connect(ws)
    try:
        from analytics_agent.clean.plan import latest
        units = [a.action_id for a in latest(con, "mixed").actions
                 if a.column == "units"]
    finally:
        con.close()
    text = tools.apply_cleaning_plan(ws, "mixed", units)
    assert reason_of(text) is Reason.ACTIONS_CONFLICT
    assert "both change units" in text


def test_a_stale_plan_refuses_and_says_old_rather_than_wrong(ws):
    tools.propose_cleaning_plan(ws, "mixed", missing_values=TOKENS)
    con = db.connect(ws)
    try:
        con.execute("INSERT INTO mixed SELECT * FROM mixed LIMIT 2")
    finally:
        con.close()
    text = tools.apply_cleaning_plan(ws, "mixed", ["C001"])
    assert reason_of(text) is Reason.CLEANING_PLAN_STALE
    assert "wrong" not in text.lower()


def test_applying_runs_only_what_was_approved_and_says_what_it_skipped(ws):
    tools.propose_cleaning_plan(ws, "mixed", missing_values=TOKENS)
    con = db.connect(ws)
    try:
        from analytics_agent.clean.plan import latest
        stored = latest(con, "mixed")
        price = next(a.action_id for a in stored.actions
                     if a.column == "unit_price")
        total = len(stored.actions)
    finally:
        con.close()

    text = tools.apply_cleaning_plan(ws, "mixed", [price])
    assert "1 action(s) applied to mixed" in text
    assert f"{total - 1} action(s) were not approved" in text

    con = db.connect(ws)
    try:
        types = dict(con.execute(
            "SELECT column_name, data_type FROM information_schema.columns "
            "WHERE table_name = 'mixed'").fetchall())
        assert types["unit_price"] != "VARCHAR"
        assert types["units"] == "VARCHAR"  # not approved, no trace
        assert ledger.count(con, "mixed") == 1
    finally:
        con.close()


def test_the_ledger_tool_reports_what_ran(ws):
    tools.propose_cleaning_plan(ws, "mixed", missing_values=TOKENS)
    con = db.connect(ws)
    try:
        from analytics_agent.clean.plan import latest
        price = next(a.action_id for a in latest(con, "mixed").actions
                     if a.column == "unit_price")
    finally:
        con.close()
    tools.apply_cleaning_plan(ws, "mixed", [price])
    text = tools.get_cleaning_ledger(ws, "mixed")
    assert "1 cleaning action(s) applied for mixed" in text
    assert "_agent_history_mixed_v1" in text


def test_a_clean_table_proposes_nothing_and_says_so(ws):
    con = db.connect(ws)
    try:
        con.execute("CREATE TABLE tidy AS SELECT 'a' AS k, 1 AS n")
    finally:
        con.close()
    text = tools.propose_cleaning_plan(ws, "tidy", missing_values=TOKENS)
    assert "Nothing to clean in tidy" in text
    assert reason_of(text) is None
