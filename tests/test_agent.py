"""The agent loop (Phase 14 Step 4), with no network.

A scripted provider stands in for the model so the loop is tested exactly: which tools run, with
which workspace, what is refused, when it stops, when it fails over. The two real providers' wire
formats are tested by translating canned responses in the shapes their APIs document.
"""

from __future__ import annotations

import contextlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from analytics_agent import workspace  # noqa: E402
from analytics_agent.webapp import agent, llm  # noqa: E402
from analytics_agent.webapp.llm import Call, ProviderError, Reply  # noqa: E402
from analytics_agent.webapp.real_backend import RealBackend  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"
ANSWERS = dict(
    grain="one row = one order", primary_key=["order_id"], date_column="order_date",
    measures=["units", "unit_price", "revenue"], dimensions=["region", "product", "channel"],
    aggregations={"units": "sum", "unit_price": "none", "revenue": "sum"},
    measure_definitions={"units": "items", "unit_price": "price of one", "revenue": "u x p"},
    analysis_window_start="2024-01-01", analysis_window_end="2024-12-31")


class Scripted:
    """A provider whose model replies are a list, consumed one per step."""

    name = "scripted"

    def __init__(self, replies, fail: ProviderError | None = None):
        self.replies, self.fail, self.seen = list(replies), fail, []

    def available(self):
        return True

    def start(self, system, history, message, tools):
        self.tools = tools
        outer = self

        class S:
            def step(self_inner):
                if outer.fail:
                    raise outer.fail
                return outer.replies.pop(0)

            def add_results(self_inner, results):
                outer.seen.extend(results)
        return S()


@pytest.fixture()
def contracted():
    be = RealBackend()
    ws = be.new_workspace_id()
    path = be.save_upload(ws, "clean_sales.csv", (FIXTURES / "clean_sales.csv").read_bytes()).path
    assert be.confirm_ingest(ws, be.draft_ingest(ws, path).spec).ok
    assert be.confirm_contract(ws, be.draft_contract(ws, "clean_sales", **ANSWERS)).ok
    yield be, ws
    workspace.reset(ws)
    workspace.workspace_dir(ws).rmdir()


def _answer(be, ws, provider, message="how many orders by region?"):
    return agent.answer(ws, [], message, lock=lambda: be._workspace(ws),
                        list_artifacts=lambda: be.list_artifacts(ws), providers=[provider])


# --- schemas ---------------------------------------------------------------------------------

def _schema_keys(schema, out):
    """Keywords of the schema itself, not property NAMES (render_chart has a parameter 'title')."""
    if isinstance(schema, dict):
        for k, v in schema.items():
            out.add(k)
            if k == "properties":
                for sub in v.values():
                    _schema_keys(sub, out)
            elif isinstance(v, (dict, list)):
                _schema_keys(v, out)
    elif isinstance(schema, list):
        for v in schema:
            _schema_keys(v, out)
    return out


def test_every_allowlisted_tool_converts_to_the_openapi_subset():
    specs = agent.tool_specs()
    assert [s.name for s in specs] == list(agent.ALLOWED)
    for s in specs:
        keys = _schema_keys(s.parameters, set())
        assert not keys & {"anyOf", "default", "title", "additionalProperties", "$schema"}, s.name
        assert "workspace_id" not in s.parameters.get("properties", {}), s.name
    ca = next(s for s in specs if s.name == "compute_analysis").parameters
    assert ca["required"] == ["dataset_name", "analysis_type"]
    assert ca["properties"]["column"] == {"type": "string", "nullable": True}
    assert "title" in next(s for s in specs if s.name == "render_chart").parameters["properties"]


def test_no_path_sql_or_consent_tool_is_offered():
    for name in ("preview_file", "check_file", "propose_ingest_spec", "load_csv", "load_excel",
                 "query_source", "describe_source", "load_postgres_table", "confirm_ingest_spec",
                 "confirm_dataset_contract", "propose_dataset_contract", "apply_cleaning_plan",
                 "reset_workspace"):
        assert name not in agent.ALLOWED


def test_a_parameterless_tool_omits_parameters_for_gemini():
    specs = {s.name: s for s in agent.tool_specs()}
    assert "parameters" not in llm._declaration(specs["list_datasets"])
    assert "parameters" in llm._declaration(specs["compute_analysis"])


# --- the loop ----------------------------------------------------------------------------------

def test_a_tool_runs_in_this_workspace_and_the_answer_comes_back(contracted):
    be, ws = contracted
    p = Scripted([
        Reply(calls=[Call("1", "compute_analysis", {"dataset_name": "clean_sales",
                                                    "analysis_type": "frequency",
                                                    "column": "region"})]),
        Reply(text="North leads.")])
    turn = _answer(be, ws, p)
    assert turn.error is None and turn.reply == "North leads."
    [call] = turn.tool_calls
    assert not call.refused and "500 of 500 row(s) analysed" in call.result
    assert "workspace_id" not in call.arguments


def test_a_model_supplied_workspace_is_overwritten(contracted):
    be, ws = contracted
    p = Scripted([Reply(calls=[Call("1", "list_datasets", {"workspace_id": "local"})]),
                  Reply(text="ok")])
    turn = _answer(be, ws, p)
    # By the workspace's own name: "local" (Claude Desktop's) may hold a clean_sales too, so
    # finding the dataset would not prove which workspace answered.
    result = turn.tool_calls[0].result
    assert f"'{ws}'" in result and "'local'" not in result


def test_a_tool_outside_the_allowlist_is_refused_in_the_engines_shape(contracted):
    be, ws = contracted
    p = Scripted([Reply(calls=[Call("1", "reset_workspace", {"confirm": True})]),
                  Reply(text="I can't do that.")])
    turn = _answer(be, ws, p)
    assert turn.tool_calls[0].refused and "not available here" in turn.tool_calls[0].result
    assert be.list_datasets(ws), "nothing was reset"


def test_a_refused_analysis_is_marked_and_its_text_reaches_the_model(contracted):
    be, ws = contracted
    p = Scripted([Reply(calls=[Call("1", "compute_analysis", {"dataset_name": "nope",
                                                              "analysis_type": "frequency"})]),
                  Reply(text="That dataset is not loaded.")])
    turn = _answer(be, ws, p)
    assert turn.tool_calls[0].refused
    assert "NEXT STEP" in p.seen[0][1]


def test_the_loop_stops_after_the_round_limit(contracted):
    be, ws = contracted
    p = Scripted([Reply(calls=[Call(str(i), "list_datasets", {})])
                  for i in range(agent.MAX_ROUNDS + 2)])
    turn = _answer(be, ws, p)
    assert len(turn.tool_calls) == agent.MAX_ROUNDS
    assert f"stopped after {agent.MAX_ROUNDS} rounds" in turn.reply


def test_a_chart_drawn_this_turn_is_returned_as_an_artifact(contracted):
    be, ws = contracted
    p = Scripted([Reply(calls=[Call("1", "render_chart", {
        "dataset_name": "clean_sales", "analysis_type": "frequency", "chart": "bar",
        "column": "region", "y": "rows"})]), Reply(text="Here it is.")])
    turn = _answer(be, ws, p)
    assert [a.kind for a in turn.artifacts] == ["chart"]
    assert be.read_artifact(ws, turn.artifacts[0].path)[:4] == b"\x89PNG"


def test_a_long_tool_reply_is_trimmed_for_the_model_but_kept_whole_for_the_person():
    long = "x" * (agent.RESULT_CHARS + 500)
    trimmed = agent._trim(long)
    assert len(trimmed) < len(long) and "500 more characters" in trimmed


def test_a_retryable_failure_fails_over_to_the_next_provider(contracted):
    be, ws = contracted
    down = Scripted([], fail=ProviderError("gemini", "HTTP 429", retryable=True))
    up = Scripted([Reply(text="from the second provider")])
    turn = agent.answer(ws, [], "hi", lock=lambda: be._workspace(ws),
                        list_artifacts=lambda: be.list_artifacts(ws), providers=[down, up])
    assert turn.reply == "from the second provider" and turn.error is None


def test_a_fatal_failure_is_reported_not_retried(contracted):
    be, ws = contracted
    bad = Scripted([], fail=ProviderError("gemini", "HTTP 400: bad key", retryable=False))
    never = Scripted([Reply(text="should not run")])
    turn = agent.answer(ws, [], "hi", lock=lambda: be._workspace(ws),
                        list_artifacts=lambda: be.list_artifacts(ws), providers=[bad, never])
    assert turn.error and "bad key" in turn.error and never.replies


def test_no_configured_provider_says_how_to_configure_one():
    turn = agent.answer("ws_000000000abc", [], "hi", lock=contextlib.nullcontext,
                        list_artifacts=list, providers=[])
    assert "GEMINI_API_KEY" in turn.error and ".env" in turn.error


# --- wire formats, from canned responses ---------------------------------------------------------

def test_gemini_calls_are_read_and_the_models_content_echoed_verbatim(monkeypatch):
    g = llm.Gemini()
    monkeypatch.setattr(g, "model", lambda: "m")
    content = {"role": "model", "parts": [
        {"functionCall": {"name": "list_datasets", "args": {}}, "thoughtSignature": "sig=="},
        {"text": "checking"}]}
    replies = iter([{"candidates": [{"content": content}]},
                    {"candidates": [{"content": {"role": "model", "parts": [{"text": "done"}]}}]}])
    sent = []
    monkeypatch.setattr(g, "post", lambda body: (sent.append(body), next(replies))[1])
    s = g.start("sys", [{"role": "assistant", "content": "earlier"}], "q", [])
    r = s.step()
    assert r.calls[0].name == "list_datasets" and r.text == "checking"
    s.add_results([(r.calls[0], "result text")])
    assert s.step().text == "done"
    contents = sent[-1]["contents"]
    assert contents[0]["role"] == "model"                       # history mapped
    assert contents[2] == content                                # echoed verbatim, signature kept
    assert contents[3]["parts"][0]["functionResponse"]["response"] == {"result": "result text"}


def test_gemini_with_no_candidate_is_a_fatal_error(monkeypatch):
    g = llm.Gemini()
    monkeypatch.setattr(g, "model", lambda: "m")
    monkeypatch.setattr(g, "post", lambda body: {"promptFeedback": {"blockReason": "SAFETY"}})
    with pytest.raises(ProviderError) as exc:
        g.start("s", [], "q", []).step()
    assert not exc.value.retryable and "SAFETY" in str(exc.value)


def test_groq_tool_calls_round_trip(monkeypatch):
    q = llm.Groq()
    monkeypatch.setattr(q, "model", lambda: "m")
    replies = iter([
        {"choices": [{"message": {"role": "assistant", "content": None, "tool_calls": [
            {"id": "c1", "type": "function",
             "function": {"name": "run_analysis", "arguments": '{"dataset_name": "d"}'}}]}}]},
        {"choices": [{"message": {"role": "assistant", "content": "done"}}]}])
    sent = []
    monkeypatch.setattr(q, "post", lambda body: (sent.append(body), next(replies))[1])
    s = q.start("sys", [], "q", [llm.ToolSpec("run_analysis", "d", {"type": "object",
                                                                    "properties": {}})])
    r = s.step()
    assert r.calls == [Call("c1", "run_analysis", {"dataset_name": "d"})]
    s.add_results([(r.calls[0], "text")])
    assert s.step().text == "done"
    # The session appends to one list, so the last request's messages end with the model's
    # final reply; the tool result is the one before it.
    assert sent[-1]["messages"][-2] == {"role": "tool", "tool_call_id": "c1", "content": "text"}
    assert sent[0]["tools"][0]["function"]["name"] == "run_analysis"


def test_http_errors_are_classified_and_never_carry_the_key(monkeypatch):
    import io
    import urllib.error

    def raise_(code):
        def f(req, timeout):
            raise urllib.error.HTTPError(req.full_url, code, "x", {}, io.BytesIO(b"{}"))
        return f
    monkeypatch.setenv("GEMINI_API_KEY", "SECRET-KEY-123")
    for code, retry in ((429, True), (503, True), (400, False), (403, False)):
        monkeypatch.setattr(llm.urllib.request, "urlopen", raise_(code))
        with pytest.raises(ProviderError) as exc:
            llm._request("gemini", "https://example.invalid", {"x-goog-api-key": "SECRET-KEY-123"})
        assert exc.value.retryable is retry and "SECRET-KEY-123" not in str(exc.value)


def test_env_file_loads_names_without_overwriting(tmp_path, monkeypatch):
    """On a private copy of the environment. The first version used delenv(raising=False) on an
    absent variable, which registers nothing to undo, so the key load_env wrote outlived the test
    and a later test called Gemini for real with it (P14-D24)."""
    import os
    env = tmp_path / ".env"
    env.write_text('# comment\nexport GEMINI_API_KEY="abc"\nGROQ_API_KEY=already\n')
    private = {k: v for k, v in os.environ.items() if not k.endswith("_API_KEY")}
    private["GROQ_API_KEY"] = "kept"
    monkeypatch.setattr(os, "environ", private)
    assert llm.load_env(env) == ["GEMINI_API_KEY"]
    assert private["GEMINI_API_KEY"] == "abc" and private["GROQ_API_KEY"] == "kept"
