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
    monkeypatch.setattr(g, "post", lambda body, model=None: (sent.append(body), next(replies))[1])
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
    monkeypatch.setattr(g, "post",
                        lambda body, model=None: {"promptFeedback": {"blockReason": "SAFETY"}})
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
    monkeypatch.setattr(llm, "_sleep", lambda s: None)
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


def test_gemini_model_choice_prefers_the_alias_then_the_highest_number():
    """P14-D25: string sorting chose gemini-omni-1.1-flash, whose free tier refused at once."""
    listed = ["gemini-2.5-flash", "gemini-3.8-flash", "gemini-omni-1.1-flash", "gemini-3.5-flash",
              "gemini-3.1-flash-lite", "gemini-3-flash-preview", "gemini-flash-latest"]
    assert llm.choose_gemini_model(listed) == "gemini-flash-latest"
    no_alias = [n for n in listed if n != "gemini-flash-latest"]
    assert llm.choose_gemini_model(no_alias) == "gemini-3.8-flash"
    assert llm.choose_gemini_model(["gemini-3.8-flash", "gemini-3.10-flash"]) == "gemini-3.10-flash"


def test_every_request_names_its_user_agent(monkeypatch):
    """Groq's edge refuses Python's default agent with 403 / 1010 (P14-D25)."""
    seen = {}

    class Resp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return b"{}"

    def capture(req, timeout):
        seen.update({k.lower(): v for k, v in req.header_items()})
        return Resp()
    monkeypatch.setattr(llm.urllib.request, "urlopen", capture)
    llm._request("groq", "https://example.invalid", {"Authorization": "Bearer x"})
    assert seen["user-agent"] == llm.USER_AGENT and "urllib" not in seen["user-agent"].lower()


def test_a_fatal_failure_after_a_retryable_one_reports_both(contracted):
    be, ws = contracted
    limited = Scripted([], fail=ProviderError("gemini", "HTTP 429: quota", retryable=True))
    blocked = Scripted([], fail=ProviderError("groq", "HTTP 403: 1010", retryable=False))
    turn = agent.answer(ws, [], "hi", lock=lambda: be._workspace(ws),
                        list_artifacts=lambda: be.list_artifacts(ws), providers=[limited, blocked])
    assert "gemini: HTTP 429" in turn.error and "groq: HTTP 403" in turn.error


def _http_error(code, body=b"{}", headers=None):
    import io
    import urllib.error
    return urllib.error.HTTPError("https://x", code, "x", headers or {}, io.BytesIO(body))


def test_a_busy_provider_is_waited_on_as_it_asks_then_succeeds(monkeypatch):
    """P14-D26: Groq's own "try again in 3.9675s" is honoured, then the call goes through."""
    waits, calls = [], []

    class Ok:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return b'{"ok": true}'

    def urlopen(req, timeout):
        calls.append(1)
        if len(calls) == 1:
            raise _http_error(429, b'{"error":{"message":"Please try again in 3.9675s."}}')
        return Ok()
    monkeypatch.setattr(llm.urllib.request, "urlopen", urlopen)
    monkeypatch.setattr(llm, "_sleep", waits.append)
    assert llm._request("groq", "https://x", {}) == {"ok": True}
    assert len(calls) == 2 and abs(waits[0] - (3.9675 + 0.25)) < 1e-6


def test_a_long_wait_fails_over_instead_of_stalling(monkeypatch):
    """A spent daily quota asks for longer than MAX_WAIT_S: no sleep, straight to the next
    provider."""
    waits = []
    body = b'{"error":{"details":[{"retryDelay": "3600s"}]}}'

    def urlopen(req, timeout):
        raise _http_error(429, body)
    monkeypatch.setattr(llm.urllib.request, "urlopen", urlopen)
    monkeypatch.setattr(llm, "_sleep", waits.append)
    with pytest.raises(ProviderError) as exc:
        llm._request("gemini", "https://x", {})
    assert exc.value.retryable and waits == []


def test_a_503_is_retried_with_backoff_then_reported(monkeypatch):
    waits = []
    monkeypatch.setattr(llm.urllib.request, "urlopen",
                        lambda req, timeout: (_ for _ in ()).throw(_http_error(503)))
    monkeypatch.setattr(llm, "_sleep", waits.append)
    with pytest.raises(ProviderError) as exc:
        llm._request("gemini", "https://x", {})
    assert exc.value.retryable and len(waits) == llm.ATTEMPTS - 1


def test_groq_gets_json_schema_nullables_and_gemini_keeps_openapi():
    """P14-D27: Groq refused gpt-oss's `question: null` because `nullable` is not JSON Schema.
    run_analysis carried that argument and left the allowlist in Cleanup Step 10; compute_analysis's
    `dimension` is the same shape, a string that may be null."""
    ca = next(s for s in agent.tool_specs() if s.name == "compute_analysis")
    assert ca.parameters["properties"]["dimension"] == {"type": "string", "nullable": True}
    js = llm.to_json_schema(ca.parameters)
    assert js["properties"]["dimension"] == {"type": ["string", "null"]}
    assert js["properties"]["dataset_name"] == {"type": "string"}
    q = llm.Groq()
    session = q.start("s", [], "m", [ca])
    sent = session._tools[0]["function"]["parameters"]["properties"]["dimension"]
    assert sent == {"type": ["string", "null"]}


def test_only_the_successful_attempts_artifacts_come_back(contracted):
    """P14-D28: an attempt that drew a chart and then failed over leaves the chart in Files, not
    under an answer that never mentions it."""
    be, ws = contracted

    class DrawsThenFails(Scripted):
        def start(self, system, history, message, tools):
            session = super().start(system, history, message, tools)
            outer, step = self, session.step

            def failing_step():
                if not outer.replies:
                    raise ProviderError("gemini", "HTTP 429", retryable=True)
                return step()
            session.step = failing_step
            return session
    first = DrawsThenFails([Reply(calls=[Call("1", "render_chart", {
        "dataset_name": "clean_sales", "analysis_type": "frequency", "chart": "bar",
        "column": "region", "y": "rows"})])])
    second = Scripted([Reply(text="answered without a chart")])
    turn = agent.answer(ws, [], "q", lock=lambda: be._workspace(ws),
                        list_artifacts=lambda: be.list_artifacts(ws), providers=[first, second])
    assert turn.reply == "answered without a chart" and turn.artifacts == []
    assert any(a.kind == "chart" for a in be.list_artifacts(ws))  # still in Files


def test_the_rules_forbid_inventing_units():
    assert "no unit or currency" in agent.SYSTEM


DAILY = (b'{"error":{"code":429,"message":"You exceeded your current quota. Quota exceeded for '
         b'metric: generate_content_free_tier_requests, limit: 20, model: gemini-3.8-flash. '
         b'Please retry in 59.2s.","details":[{"violations":[{"quotaId":'
         b'"GenerateRequestsPerDayPerProjectPerModel-FreeTier"}]}]}}')


def test_a_spent_daily_quota_is_never_waited_on(monkeypatch):
    """P14-D32: the 59 s "retry" on a daily quota was waited twice before failing over."""
    waits = []
    monkeypatch.setattr(llm.urllib.request, "urlopen",
                        lambda req, timeout: (_ for _ in ()).throw(_http_error(429, DAILY)))
    monkeypatch.setattr(llm, "_sleep", waits.append)
    with pytest.raises(ProviderError) as exc:
        llm._request("gemini", "https://x", {})
    assert exc.value.kind == "daily_quota" and exc.value.model == "gemini-3.8-flash"
    assert waits == [] and "daily quota for gemini-3.8-flash is used up" in exc.value.summary


def test_gemini_climbs_its_ladder_when_a_models_day_is_spent(monkeypatch):
    g = llm.Gemini()
    monkeypatch.setattr(g, "_discover", lambda: ["gemini-flash-latest", "gemini-3.8-flash",
                                                 "gemini-3.7-flash"])
    tried = []

    def request(provider, url, headers, body=None):
        model = url.split("/models/")[1].split(":")[0]
        tried.append(model)
        if model in ("gemini-flash-latest", "gemini-3.8-flash"):
            raise llm._classify("gemini", 429, DAILY.decode())
        return {"candidates": [{"content": {"role": "model", "parts": [{"text": "ok"}]}}]}
    monkeypatch.setattr(llm, "_request", request)
    with pytest.raises(ProviderError):
        g.start("s", [], "q", []).step()             # the alias is spent, and names 3.8
    assert g.model() == "gemini-3.7-flash"           # 3.8 skipped: the alias's error named it
    assert g.start("s", [], "q", []).step().text == "ok"
    assert tried == ["gemini-flash-latest", "gemini-3.7-flash"]


def test_the_loop_retries_gemini_on_its_next_model_before_groq(contracted):
    be, ws = contracted

    class Laddered(Scripted):
        name = "gemini"

        def __init__(self):
            super().__init__([Reply(text="from the second model")])
            self.left = 1

        def has_another_model(self):
            return True

        def start(self, *a):
            if self.left:
                self.left -= 1
                raise llm._classify("gemini", 429, DAILY.decode())
            return super().start(*a)
    groq = Scripted([Reply(text="should not be reached")])
    turn = agent.answer(ws, [], "q", lock=lambda: be._workspace(ws),
                        list_artifacts=lambda: be.list_artifacts(ws), providers=[Laddered(), groq])
    assert turn.reply == "from the second model" and groq.replies


def test_groq_recovers_when_its_model_calls_a_tool_it_was_not_given(monkeypatch):
    """P14-D33: gpt-oss copied a NEXT STEP into a call to propose_dataset_contract; Groq
    refused it with 400 tool_use_failed and the whole turn failed."""
    q = llm.Groq()
    monkeypatch.setattr(q, "model", lambda: "m")
    refusal = ('{"error":{"message":"Tool call validation failed: attempted to call tool '
               "'propose_dataset_contract' which was not in request.tools\","
               '"code":"tool_use_failed"}}')
    replies = iter([llm._classify("groq", 400, refusal),
                    {"choices": [{"message": {"role": "assistant",
                                              "content": "Confirm it on the Contract screen."}}]}])
    sent = []

    def post(body):
        sent.append([dict(m) for m in body["messages"]])
        r = next(replies)
        if isinstance(r, Exception):
            raise r
        return r
    monkeypatch.setattr(q, "post", post)
    reply = q.start("sys", [], "q", []).step()
    assert reply.text == "Confirm it on the Contract screen."
    note = sent[1][-1]
    assert note["role"] == "user" and "propose_dataset_contract is not one of your tools" in (
        note["content"])


def test_a_next_step_naming_a_screen_tool_is_annotated():
    text = 'NEXT STEP: call propose_dataset_contract(dataset_name="t")'
    out = agent._with_screen_notes(text)
    assert "propose_dataset_contract: not one of your tools" in out and "Contract screen" in out
    plain = 'NEXT STEP: call compute_analysis(dataset_name="t", analysis_type="trend")'
    assert agent._with_screen_notes(plain) == plain


def test_a_failed_turn_reads_as_sentences_not_json(contracted):
    be, ws = contracted
    daily = Scripted([], fail=llm._classify("gemini", 429, DAILY.decode()))
    turn = agent.answer(ws, [], "q", lock=lambda: be._workspace(ws),
                        list_artifacts=lambda: be.list_artifacts(ws), providers=[daily])
    assert turn.error.startswith("The assistant could not answer this time.")
    assert "daily quota for gemini-3.8-flash is used up" in turn.error and "{" not in turn.error


def test_the_screen_note_reaches_the_model_through_the_loop(contracted):
    """Wiring, not just the function: the first test of the note passed with it unwired."""
    be, ws = contracted
    p = Scripted([Reply(calls=[Call("1", "compute_analysis", {"dataset_name": "not_loaded",
                                                              "analysis_type": "frequency"})]),
                  Reply(text="Load it first.")])
    _answer(be, ws, p)
    to_model = p.seen[0][1]
    assert "[Note for the assistant]" in to_model and "Upload & read screen" in to_model


# --- the rules the graded answer of 22/09/2026 12:21 broke (Cleanup Step 9) -------------------

def test_the_screens_the_rules_name_are_the_screens_the_app_has():
    """It sent the person to a Cleaning screen that does not exist."""
    import re
    from pathlib import Path
    app = (Path(__file__).resolve().parents[1] / "ui" / "app.py").read_text()
    assert list(agent.SCREENS) == re.findall(r'st\.Page\([^)]*title="([^"]+)"', app)
    assert all(name in agent.SYSTEM for name in agent.SCREENS)


def test_the_rules_forbid_handing_the_person_a_tool_call():
    assert "never give the person a tool call" in agent.SYSTEM.lower()


def test_the_rules_say_to_run_what_the_question_needs_rather_than_suggest_it():
    text = agent.SYSTEM.lower()
    assert "run it yourself" in text and "render_chart" in text and "period=" in text


def test_the_rules_forbid_a_cause_no_result_states():
    assert "cause" in agent.SYSTEM.lower()


def test_no_rule_lists_cleaning_among_what_a_screen_does():
    """The old rule read 'approve cleaning ... tell them where: the Upload & read screen, the
    Contract screen', beside the rule that cleaning has no screen."""
    assert "approve cleaning" not in agent.SYSTEM


# --- the request fits the providers (Cleanup Step 10, CL9-O1) ---------------------------------
#
# Groq refused every graded question with 413: 8,000 tokens a minute, and the twelve tool specs
# alone were 19,616 characters (~4,900 tokens) before a word of the conversation.

SPEC_BUDGET = 8_000


def _spec_chars() -> int:
    import json
    return sum(len(s.description) + len(json.dumps(s.parameters)) for s in agent.tool_specs())


def test_the_tool_specs_fit_their_budget():
    assert _spec_chars() <= SPEC_BUDGET, _spec_chars()


def test_the_analysis_roster_is_derived_from_the_registry():
    from analytics_agent.analysis.registry import REGISTRY
    desc = next(s.description for s in agent.tool_specs() if s.name == "compute_analysis")
    for name in REGISTRY:
        assert f"{name}(" in desc, name
    assert "top_n(dimension, measure, n, period, grain)" in desc


def test_run_analysis_is_not_offered_to_the_model():
    """compute_analysis passes the same gate; run_analysis's reply was 7,431 characters of a
    catalogue the roster above already carries."""
    assert "run_analysis" not in agent.ALLOWED


def test_a_reply_naming_run_analysis_says_compute_analysis_does_the_same():
    text = agent._with_screen_notes('NEXT STEP: call run_analysis(dataset_name="x", ...)')
    assert "run_analysis: not one of your tools" in text and "compute_analysis" in text


# --- the live run of Cleanup Step 10: a malformed generation, and a false "nothing changed" ---

PARSE_FAILED = ('{"error":{"message":"Parsing failed. The model generated output that could not be '
                'parsed. Please adjust your prompt. See \'failed_generation\' for more details.",'
                '"type":"invalid_request_error","failed_generation":"{\\"name\\": ..."}}')


def test_a_generation_groq_could_not_parse_is_classified():
    assert llm._classify("groq", 400, PARSE_FAILED).kind == "generation_failed"


def test_groq_retries_a_generation_it_could_not_parse(monkeypatch):
    """Seen live: six tool calls made, a chart drawn, then 400 'Parsing failed' ended the turn."""
    q = llm.Groq()
    monkeypatch.setattr(q, "model", lambda: "m")
    replies = iter([llm._classify("groq", 400, PARSE_FAILED),
                    {"choices": [{"message": {"role": "assistant", "content": "November."}}]}])

    def post(body):
        r = next(replies)
        if isinstance(r, Exception):
            raise r
        return r
    monkeypatch.setattr(q, "post", post)
    assert q.start("sys", [], "q", []).step().text == "November."


def test_a_failed_turn_does_not_say_nothing_changed_when_a_file_was_written():
    """The same run wrote a chart before failing; the message said nothing had changed."""
    text = agent._failed(["groq: could not parse"], written=1)
    assert "Nothing in your workspace changed" not in text and "Files" in text
    assert "Nothing in your workspace changed" in agent._failed(["x"], written=0)
