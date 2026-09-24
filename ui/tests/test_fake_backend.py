"""FakeBackend keeps the contract: every method, every return type, and the behaviours the
screens depend on (provisional until answered, refusals with a next step, isolation)."""

from __future__ import annotations

import inspect
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from analytics_agent.webapp import contract as c  # noqa: E402
from ui.fake_backend import SUBSET_NOTE, FakeBackend  # noqa: E402


def _methods(cls) -> dict[str, inspect.Signature]:
    return {n: inspect.signature(f) for n, f in inspect.getmembers(cls, inspect.isfunction)
            if not n.startswith("_")}


def test_every_protocol_method_exists_with_the_same_signature():
    want, have = _methods(c.Backend), _methods(FakeBackend)
    assert set(want) <= set(have), set(want) - set(have)
    for name, sig in want.items():
        assert list(have[name].parameters) == list(sig.parameters), name


def test_workspace_ids_are_distinct_and_valid():
    be = FakeBackend()
    a, b = be.new_workspace_id(), be.new_workspace_id()
    assert a != b
    from analytics_agent.config import DEFAULT_WORKSPACE_ID, validate_workspace_id
    assert validate_workspace_id(a) == a and a != DEFAULT_WORKSPACE_ID


def test_upload_refuses_other_formats_and_oversize():
    be = FakeBackend()
    ws = be.new_workspace_id()
    bad = be.save_upload(ws, "notes.txt", b"x")
    assert bad.verdict == "REFUSE" and isinstance(bad.refusal, c.Refusal) and bad.path is None
    ok = be.save_upload(ws, "sales.csv", b"a,b\n1,2\n")
    assert ok.verdict == "OK" and ok.path == "uploads/sales.csv"


def test_ingest_is_provisional_until_the_header_is_answered_then_loads():
    be = FakeBackend()
    ws = be.new_workspace_id()
    path = be.save_upload(ws, "sales.csv", b"x").path
    first = be.draft_ingest(ws, path)
    assert isinstance(first, c.IngestDraft) and first.unresolved and first.questions
    refused = be.confirm_ingest(ws, first.spec)
    assert not refused.ok and refused.refusal.next_step
    second = be.draft_ingest(ws, path, header_rows=[1, 2])
    assert second.unresolved == [] and second.header_rows == [1, 2]
    assert [col.target_name for col in second.columns][1] == "c_2024_sales_units"
    loaded = be.confirm_ingest(ws, second.spec)
    assert loaded.ok
    assert any(d.name == "sales" and d.stage == "loaded, no contract"
               for d in be.list_datasets(ws))


def test_a_draft_for_an_unknown_path_is_refused():
    be = FakeBackend()
    draft = be.draft_ingest(be.new_workspace_id(), "uploads/nothing.csv")
    assert draft.refusal is not None


def test_contract_is_provisional_until_grain_window_and_measures_are_settled():
    be = FakeBackend()
    ws = be.new_workspace_id()
    d = be.draft_contract(ws, "geolocation")
    assert "grain" in d.provisional and "analysis window" in d.provisional
    assert not be.confirm_contract(ws, d).ok
    settled = be.draft_contract(
        ws, "geolocation", grain="one row = one location sample",
        measures=["geolocation_lat"], dimensions=["geolocation_state"],
        aggregations={"geolocation_lat": "none"},
        measure_definitions={"geolocation_lat": "latitude"},
        analysis_window_start="2016-01-01", analysis_window_end="2018-12-31")
    assert settled.provisional == []
    result = be.confirm_contract(ws, settled)
    assert result.ok and "v2" in result.message


def test_the_seeded_subset_dataset_carries_its_warning():
    be = FakeBackend()
    geo = [d for d in be.list_datasets(be.new_workspace_id()) if d.name == "geolocation"][0]
    assert SUBSET_NOTE in geo.notes and "1,000 of 1,000,163" in SUBSET_NOTE


def test_chat_chart_is_a_real_png_with_a_description_and_fail_sets_error():
    be = FakeBackend()
    ws = be.new_workspace_id()
    turn = be.chat(ws, [], "show me a chart")
    assert isinstance(turn, c.ChatTurn) and turn.artifacts[0].kind == "chart"
    data = be.read_artifact(ws, turn.artifacts[0].path)
    assert data[:8] == b"\x89PNG\r\n\x1a\n" and "highest" in turn.artifacts[0].description
    assert any(t.refused for t in be.chat(ws, [], "what's the trend?").tool_calls)
    assert be.chat(ws, [], "fail").error


def test_workspaces_are_isolated_and_foreign_paths_are_refused():
    be = FakeBackend()
    a, b = be.new_workspace_id(), be.new_workspace_id()
    art = be.chat(a, [], "chart").artifacts[0]
    assert be.list_artifacts(b) == []
    try:
        be.read_artifact(b, art.path)
    except ValueError:
        pass
    else:
        raise AssertionError("read_artifact served another workspace's file")


def test_reset_empties_everything_including_the_seed():
    be = FakeBackend()
    ws = be.new_workspace_id()
    be.chat(ws, [], "chart")
    assert be.reset_workspace(ws).ok
    assert be.list_datasets(ws) == [] and be.list_artifacts(ws) == []


def test_cleaning_proposes_one_free_and_one_lossy_step_and_applies_by_id():
    be = FakeBackend()
    ws = be.new_workspace_id()
    p = be.propose_cleaning(ws, "geolocation")
    assert [(s.action_id, s.suggested, s.lossy) for s in p.steps] == [
        ("C001", True, False), ("C002", False, True)]
    assert not be.apply_cleaning(ws, "geolocation", []).ok
    assert be.apply_cleaning(ws, "geolocation", ["C999"]).refusal.reason == "ACTION_NOT_IN_PLAN"
    assert be.apply_cleaning(ws, "geolocation", ["C001"]).ok
    assert [s.action_id for s in be.propose_cleaning(ws, "geolocation").steps] == ["C002"]
    assert be.propose_cleaning(ws, "nope").refusal.reason == "DATASET_NOT_LOADED"
