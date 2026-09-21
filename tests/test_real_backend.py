"""The real backend: webapp/contract.Backend on the engine (Phase 14 Step 3).

Driven end to end on the repository's fixtures -- the bytes of a real CSV and a real merged-header
workbook go through save_upload, draft, confirm, contract and artifacts exactly as the UI sends
them. No Postgres, no network.
"""

from __future__ import annotations

import inspect
import sys
import threading
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from analytics_agent import server, workspace  # noqa: E402
from analytics_agent.config import DEFAULT_WORKSPACE_ID  # noqa: E402
from analytics_agent.webapp import contract as c  # noqa: E402
from analytics_agent.webapp.real_backend import RealBackend, refusal_from_text  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"
REPO = Path(__file__).resolve().parents[1]
ANSWERS = dict(
    grain="one row = one order", primary_key=["order_id"], date_column="order_date",
    measures=["units", "unit_price", "revenue"], dimensions=["region", "product", "channel"],
    aggregations={"units": "sum", "unit_price": "none", "revenue": "sum"},
    measure_definitions={"units": "items on the order", "unit_price": "price of one item",
                         "revenue": "units x unit_price"},
    analysis_window_start="2024-01-01", analysis_window_end="2024-12-31")


@pytest.fixture()
def be():
    return RealBackend()


@pytest.fixture()
def ws(be):
    wid = be.new_workspace_id()
    yield wid
    workspace.reset(wid)
    workspace.workspace_dir(wid).rmdir()


def _loaded(be, ws, name="clean_sales.csv"):
    path = be.save_upload(ws, name, (FIXTURES / name).read_bytes()).path
    d = be.draft_ingest(ws, path)
    assert d.refusal is None and d.unresolved == [], d.message
    assert be.confirm_ingest(ws, d.spec).ok
    return d


def test_every_protocol_method_exists_with_the_same_signature():
    want = {n: inspect.signature(f) for n, f in inspect.getmembers(c.Backend, inspect.isfunction)
            if not n.startswith("_")}
    for name, sig in want.items():
        have = inspect.signature(getattr(RealBackend, name))
        assert list(have.parameters) == list(sig.parameters), name


def test_workspace_ids_are_fresh_valid_and_never_claude_desktops(be):
    ids = {be.new_workspace_id() for _ in range(50)}
    assert len(ids) == 50 and DEFAULT_WORKSPACE_ID not in ids
    assert all(i.startswith("ws_") and len(i) == 15 for i in ids)


def test_an_upload_keeps_only_its_base_name_and_refuses_other_types(be, ws):
    ok = be.save_upload(ws, "../../etc/clean_sales.csv", b"a,b\n1,2\n")
    assert ok.verdict == "OK"
    assert Path(ok.path).parent == workspace.workspace_dir(ws) / "uploads"
    bad = be.save_upload(ws, "notes.txt", b"x")
    assert bad.verdict == "REFUSE" and bad.refusal.next_step.startswith("save_upload(")


def test_a_path_outside_the_uploads_directory_is_refused(be, ws):
    outside = str(FIXTURES / "clean_sales.csv")
    assert be.draft_ingest(ws, outside).refusal is not None
    assert not be.confirm_ingest(ws, {"path": outside}).ok


def test_the_csv_drafts_with_its_grid_and_loads(be, ws):
    d = _loaded(be, ws)
    assert d.grid.rows[0][:3] == ["order_id", "order_date", "region"]
    assert d.header_rows == [1] and d.columns[0].target_name == "order_id"
    [s] = be.list_datasets(ws)
    assert s.name == "clean_sales" and s.rows == 500 and s.stage == "loaded, no contract"
    assert s.next_step == 'propose_dataset_contract(dataset_name="clean_sales")'


def test_the_merged_header_workbook_shows_its_merges_and_loads(be, ws):
    d = _loaded(be, ws, "merged_multiheader.xlsx")
    assert d.header_rows == [1, 2] and d.grid.sheet_names == ["Sales"]
    assert d.grid.merged_ranges, "the merged header's ranges reach the editor"
    assert be.list_datasets(ws)[0].rows == 150


def test_an_unresolved_contract_field_reaches_the_form_blank(be, ws):
    """P14-D18. The engine holds the guess 'one row = one order_id' for an unresolved grain; a
    form prefilled with it would send the guess back as the person's answer."""
    _loaded(be, ws)
    d = be.draft_contract(ws, "clean_sales")
    assert "grain" in d.provisional and d.grain is None
    assert d.aggregations == {} and d.measure_definitions == {}
    assert d.analysis_window_start is None
    roles = {col.name: col.suggested_role for col in d.columns}
    assert roles["revenue"] == "measure" and roles["region"] == "dimension"


def test_a_provisional_contract_is_refused_and_an_answered_one_confirmed(be, ws):
    _loaded(be, ws)
    first = be.draft_contract(ws, "clean_sales")
    refused = be.confirm_contract(ws, first)
    assert not refused.ok and refused.refusal.next_step.startswith("draft_contract(")
    answered = be.draft_contract(ws, "clean_sales", **ANSWERS)
    assert answered.provisional == [], answered.provisional
    assert answered.grain == "one row = one order"
    result = be.confirm_contract(ws, answered)
    assert result.ok, result.message
    assert "ready" in be.list_datasets(ws)[0].stage


def test_a_web_contract_is_exported_into_the_workspace_not_the_repository(be, ws):
    """P14-D19: a browser session's export stays in its own (gitignored) workspace."""
    _loaded(be, ws)
    be.confirm_contract(ws, be.draft_contract(ws, "clean_sales", **ANSWERS))
    assert (workspace.workspace_dir(ws) / "contracts" / "clean_sales.yaml").exists()
    assert not (REPO / "docs" / "contracts" / ws).exists()


def test_artifacts_are_listed_described_and_read_and_nothing_else_is(be, ws):
    _loaded(be, ws)
    be.confirm_contract(ws, be.draft_contract(ws, "clean_sales", **ANSWERS))
    out = server.render_chart(dataset_name="clean_sales", analysis_type="frequency",
                              chart="bar", column="region", y="rows", workspace_id=ws)
    assert "Chart written" in out, out
    arts = be.list_artifacts(ws)
    chart = next(a for a in arts if a.kind == "chart")
    assert chart.path.startswith("charts/") and "row(s) analysed" in chart.description
    assert be.read_artifact(ws, chart.path)[:8] == b"\x89PNG\r\n\x1a\n"
    for bad in ("../../pyproject.toml", "session.duckdb", "uploads/clean_sales.csv",
                "charts/../session.duckdb"):
        with pytest.raises(ValueError):
            be.read_artifact(ws, bad)


def test_two_workspaces_do_not_see_each_other(be, ws):
    other = be.new_workspace_id()
    try:
        _loaded(be, ws)
        assert be.list_datasets(other) == []
        path = be.save_upload(ws, "clean_sales.csv", b"a\n1\n").path
        assert be.draft_ingest(other, path).refusal is not None  # ws's upload, not other's
    finally:
        workspace.reset(other)
        workspace.workspace_dir(other).rmdir()


def test_overlapping_calls_on_one_workspace_are_serialised_not_failed(be, ws):
    """P14-D2/D6: unlocked, a read-only attach beside an open handle raises. The lock means a
    burst of concurrent calls on one workspace all succeed."""
    _loaded(be, ws)
    errors: list[BaseException] = []
    start = threading.Barrier(6)

    def call(i: int) -> None:
        try:
            start.wait()
            if i % 3 == 0:
                be.draft_contract(ws, "clean_sales")
            elif i % 3 == 1:
                be.list_datasets(ws)
            else:
                be.list_artifacts(ws)
        except BaseException as e:  # noqa: BLE001
            errors.append(e)

    threads = [threading.Thread(target=call, args=(i,)) for i in range(6)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert errors == []


def test_reset_empties_the_workspace(be, ws):
    _loaded(be, ws)
    assert be.reset_workspace(ws).ok
    assert be.list_datasets(ws) == [] and be.list_artifacts(ws) == []


def test_merely_looking_creates_no_workspace(be):
    """P14-D21: the sidebar lists datasets on every page view; a first visit must not leave a
    directory and a database behind."""
    from analytics_agent.config import WORKSPACE_ROOT
    wid = be.new_workspace_id()
    assert be.list_datasets(wid) == [] and be.list_artifacts(wid) == []
    assert not (WORKSPACE_ROOT / wid).exists()


def test_chat_says_it_is_not_connected_yet(be, ws):
    turn = be.chat(ws, [], "hello")
    assert turn.error and "Step 4" in turn.error


def test_both_refusal_shapes_convert():
    structured = ("BLOCKED: x.\nWHY: y.\nNEXT STEP: call run_analysis(dataset_name=\"d\")\n\n"
                  "reason: NO_CONTRACT")
    r = refusal_from_text(structured)
    assert (r.reason, r.what, r.why, r.next_step) == (
        "NO_CONTRACT", "x.", "y.", 'run_analysis(dataset_name="d")')
    loose = refusal_from_text("BLOCKED: no file at p.\nNEXT STEP: check the path.")
    assert loose.reason == "LOAD_REFUSED" and loose.next_step == "check the path."
