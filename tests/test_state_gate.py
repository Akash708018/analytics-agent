"""get_workflow_state must not recommend a call the gate will refuse.

Phase 7, Step 10b. Run from the repo root:

    uv run pytest tests/test_state_gate.py -q

The defect these pin was found by a live agent reading get_workflow_state and
validate_dataset side by side: the state said `contract v1, ready` with
`NEXT STEP: call run_analysis(...)` on a dataset require_contract refuses with
KEY_NOT_UNIQUE. No acceptance fixture could catch it -- Phase 4's clause 2 uses
clean_sales, whose key holds.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from analytics_agent import workspace  # noqa: E402
from analytics_agent.contract import ContractRefused, store  # noqa: E402
from analytics_agent.contract.dataset_contract import (  # noqa: E402
    AnalysisWindow, Binding, DatasetContract, Measure)
from analytics_agent.state import dataset_states, require_contract  # noqa: E402
from analytics_agent.util import db  # noqa: E402

WORKSPACE = "state_gate_test"
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def build(dataset_name: str, sql: str, primary_key: list[str]):
    workspace.reset(WORKSPACE)
    con = db.connect(WORKSPACE)
    try:
        con.execute(f'CREATE TABLE "{dataset_name}" AS {sql}')
        pairs = [
            (r[0], r[1]) for r in con.execute(
                "SELECT column_name, data_type FROM information_schema.columns "
                "WHERE table_name = ? ORDER BY ordinal_position",
                [dataset_name]).fetchall()
        ]
        rows = con.execute(f'SELECT count(*) FROM "{dataset_name}"').fetchone()[0]
        store.confirm(con, DatasetContract(
            dataset_name=dataset_name,
            grain=f"one row = one {dataset_name}",
            primary_key=primary_key,
            date_column="ts",
            analysis_window=AnalysisWindow(start=date(2024, 1, 1),
                                           end=date(2024, 12, 31)),
            measures=[Measure(name="amount", agg="sum",
                              definition="what was charged", unit="GBP")],
            bound_to=Binding.from_pairs(pairs, rows),
        ))
    finally:
        con.close()


def state_of(dataset_name: str):
    con = db.connect(WORKSPACE)
    try:
        return next(s for s in dataset_states(con) if s.dataset_name == dataset_name)
    finally:
        con.close()


def gate_refuses(dataset_name: str) -> bool:
    con = db.connect(WORKSPACE)
    try:
        require_contract(con, dataset_name)
        return False
    except ContractRefused:
        return True
    finally:
        con.close()


GOOD = """SELECT * FROM (VALUES
    ('A', TIMESTAMP '2024-03-01 09:00:00', 10),
    ('B', TIMESTAMP '2024-04-01 09:00:00', 20)) v(k, ts, amount)"""
DUPES = """SELECT * FROM (VALUES
    ('A', TIMESTAMP '2024-03-01 09:00:00', 10),
    ('A', TIMESTAMP '2024-04-01 09:00:00', 20)) v(k, ts, amount)"""
NULLS = """SELECT * FROM (VALUES
    ('A', TIMESTAMP '2024-03-01 09:00:00', 10),
    (NULL, TIMESTAMP '2024-04-01 09:00:00', 20)) v(k, ts, amount)"""


@pytest.fixture(autouse=True)
def clean_up():
    yield
    workspace.reset(WORKSPACE)


def test_a_key_that_holds_still_points_at_analysis():
    build("sales", GOOD, ["k"])
    state = state_of("sales")
    assert not gate_refuses("sales")
    assert state.stage.endswith("ready")
    assert state.next_call.startswith("run_analysis")


def test_a_repeated_key_is_reported_as_blocked_not_as_ready():
    """The defect, in the shape a live agent found it."""
    build("sales", GOOD, ["k"])
    con = db.connect(WORKSPACE)
    try:
        con.execute("INSERT INTO sales VALUES ('A', TIMESTAMP '2024-05-01', 30)")
    finally:
        con.close()
    state = state_of("sales")
    assert gate_refuses("sales"), "the gate must refuse for this test to mean anything"
    assert "BLOCKED" in state.stage
    assert state.next_call == 'validate_dataset(dataset_name="sales")'
    assert "run_analysis" not in state.next_call


def test_the_state_and_the_gate_cannot_disagree():
    """Both call verify_key with the same shortcut, so a dataset the gate
    refuses can never read as ready."""
    for name, sql, key in (("ok", GOOD, ["k"]), ("dupes", DUPES, ["k"]),
                           ("nulls", NULLS, ["k"])):
        build(name, sql, key)
        refused = gate_refuses(name)
        state = state_of(name)
        assert refused == ("BLOCKED" in state.stage), name
        assert refused != state.next_call.startswith("run_analysis"), name


def test_the_block_says_what_is_wrong_with_the_key():
    build("sales", GOOD, ["k"])
    con = db.connect(WORKSPACE)
    try:
        con.execute("INSERT INTO sales VALUES (NULL, TIMESTAMP '2024-05-01', 30)")
    finally:
        con.close()
    state = state_of("sales")
    assert "the key does not hold" in state.blocked_by
    assert "null in 1 row(s)" in state.blocked_by
    assert "repeat" not in state.blocked_by, "P7-D6: a null key is not a duplicate"


def test_a_contract_with_no_key_declared_is_not_blocked_by_one():
    """Nothing to verify is not the same as a verification that failed."""
    build("sales", DUPES, [])
    state = state_of("sales")
    assert "BLOCKED" not in state.stage
    assert state.next_call.startswith("run_analysis")


def test_a_key_that_never_held_is_not_re_checked_and_both_agree_about_it():
    """A known limitation, pinned so it is a decision rather than a surprise.

    require_contract skips verify_key when the structure and row count are
    identical to what the contract was bound to -- a cache keyed on "nothing
    moved". Nothing establishes that the key held when the contract was
    confirmed: store.confirm does not look at the data, deliberately, because
    a contract is an agreement about intent and testing it is a separate act.
    So a contract confirmed against a table whose key ALREADY failed is never
    re-checked, and neither the gate nor this report notices.

    dataset_states mirrors the shortcut rather than fixing it here, because a
    state view that blocked what the gate allows is the same disagreement in
    the other direction. validate_dataset uses no shortcut and catches it every
    time, which is the answer available today.
    """
    build("sales", DUPES, ["k"])
    assert not gate_refuses("sales"), "the shortcut is what this pins"
    state = state_of("sales")
    assert "BLOCKED" not in state.stage
    assert state.next_call.startswith("run_analysis")
