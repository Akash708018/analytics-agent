"""The agent loop behind the Ask screen (Phase 14 Step 4).

A model reads the question, calls the engine's tools, reads their replies, and answers. The tools
are server.py's own functions -- what Claude Desktop calls -- restricted to an allowlist, with the
workspace injected by this module and never chosen by the model.
"""

from __future__ import annotations

import asyncio
import functools
import re
from collections.abc import Callable
from contextlib import AbstractContextManager

from analytics_agent import server
from analytics_agent.contract.refusals import reason_of

from .contract import Artifact, ChatTurn, ToolCall
from .llm import Call, Provider, ProviderError, ToolSpec, configured, convert_schema

#: Reading and analysis only. Excluded on purpose: tools taking a filesystem path (the server's
#: disk, on a public host), SQL against configured databases, and every step a person must agree
#: to on a screen -- loading, confirming, cleaning, resetting (Step 4 decision 1).
ALLOWED: tuple[str, ...] = (
    "list_datasets", "describe_dataset", "get_workflow_state", "run_analysis",
    "compute_analysis", "render_chart", "read_result_file", "profile_dataset", "profile_column",
    "validate_dataset", "get_cleaning_ledger", "build_report",
)

MAX_ROUNDS = 8
RESULT_CHARS = 8_000     # what the model reads of one tool reply
HISTORY_MESSAGES = 12

SYSTEM = """You are the analyst inside a data-analysis engine. The person is looking at a web app \
with their datasets in a sidebar.

Rules you do not break:
- Every number you state comes from a tool reply in this conversation. Never estimate, recall or \
round a figure into something the tool did not say.
- No analysis runs without a confirmed Dataset Contract. If a tool refuses, read its NEXT STEP. \
If the step is something only the person can do (load a file, confirm a contract, approve \
cleaning), tell them where: the Upload & read screen, the Clean screen, the Contract screen. You \
cannot do those.
- Start with get_workflow_state or list_datasets if you do not know what is loaded.
- Charts appear to the person automatically under your answer. You cannot see them: describe a \
chart only from the numbers its reply gives.
- Carry every caveat a result prints -- a subset warning, a gap, excluded rows -- into your answer.
- Add no unit or currency the contract does not state: a measure defined as "units x unit_price" \
is a number, not dollars.
- Answer in plain language, briefly, and name the analysis you ran."""


@functools.lru_cache(maxsize=1)
def tool_specs() -> tuple[ToolSpec, ...]:
    """The allowlisted tools, their schemas converted and workspace_id removed."""
    tools = {t.name: t for t in asyncio.run(server.mcp.list_tools())}
    missing = [n for n in ALLOWED if n not in tools]
    if missing:
        raise RuntimeError(f"allowlisted tools not registered: {missing}")
    return tuple(ToolSpec(n, tools[n].description or "", convert_schema(tools[n].parameters))
                 for n in ALLOWED)


def run_tool(call: Call, workspace_id: str) -> str:
    """One tool call, with this workspace forced in. A tool outside the allowlist is refused in
    the engine's own shape, so the model can read why."""
    if call.name not in ALLOWED:
        return (f"BLOCKED: {call.name} is not available here.\n"
                f"WHY: this assistant reads and analyses; loading, contracts and cleaning are "
                f"done by the person on their screens.\n"
                f"NEXT STEP: call get_workflow_state()\n\nreason: ANALYSIS_NOT_POSSIBLE")
    args = {k: v for k, v in call.args.items() if v is not None}
    args["workspace_id"] = workspace_id  # overwrite anything the model sent
    try:
        return getattr(server, call.name)(**args)
    except TypeError as exc:
        return (f"BLOCKED: {call.name} was called with arguments it does not take.\n"
                f"WHY: {exc}\nNEXT STEP: call {call.name}(...) with the arguments its description "
                f"lists\n\nreason: ANALYSIS_NOT_POSSIBLE")


#: Where the person does what the engine's NEXT STEP asks, when the tool is not the assistant's.
SCREEN_FOR: dict[str, str] = {
    "propose_dataset_contract": "the Contract screen", "confirm_dataset_contract": "the Contract screen",
    "propose_ingest_spec": "the Upload & read screen", "confirm_ingest_spec": "the Upload & read screen",
    "load_csv": "the Upload & read screen", "load_excel": "the Upload & read screen",
    "check_file": "the Upload & read screen", "preview_file": "the Upload & read screen",
    "reset_workspace": "the sidebar's Reset",
    "propose_cleaning_plan": "the Clean screen", "apply_cleaning_plan": "the Clean screen",
    "load_postgres_table": "no screen -- databases are not connected to the web app",
    "query_source": "no screen -- databases are not connected to the web app",
    "describe_source": "no screen -- databases are not connected to the web app",
}
_NAMED_CALL = re.compile(r"\b([a-z_]+)\(")


def _with_screen_notes(text: str) -> str:
    """A tool reply whose NEXT STEP names a tool the assistant lacks, with a note saying where the
    person does it. Seen live: gpt-oss copied "NEXT STEP: call propose_dataset_contract(...)" into
    a tool call Groq refused, failing the turn (P14-D33)."""
    named = [n for n in dict.fromkeys(_NAMED_CALL.findall(text)) if n in SCREEN_FOR]
    if not named:
        return text
    notes = "\n".join(f"- {n}: not one of your tools; the person does it on {SCREEN_FOR[n]}."
                       for n in named)
    return f"{text}\n\n[Note for the assistant]\n{notes}"


def _trim(text: str) -> str:
    if len(text) <= RESULT_CHARS:
        return text
    return text[:RESULT_CHARS] + (f"\n[... {len(text) - RESULT_CHARS:,} more characters not shown. "
                                  f"Page a written result with read_result_file.]")


def answer(workspace_id: str, history: list[dict], message: str, *,
           lock: Callable[[], AbstractContextManager],
           list_artifacts: Callable[[], list[Artifact]],
           providers: list[Provider] | None = None) -> ChatTurn:
    """One turn: the providers in order, failing over on a retryable error."""
    providers = configured() if providers is None else providers
    if not providers:
        return ChatTurn(reply="", error=(
            "No model is configured. Add GEMINI_API_KEY (or GROQ_API_KEY) to the .env file at "
            "the repository root and restart the app."))
    failures: list[str] = []
    calls: list[ToolCall] = []
    for provider in providers:
        # A spent daily quota is per model: Gemini tries its next model before the next
        # provider (P14-D32). Bounded by the ladder's length.
        for _attempt in range(6):
            # Per attempt: an abandoned attempt may have drawn a chart the final answer never
            # mentions. It stays in Files, not under this answer (P14-D28).
            before = {a.path for a in list_artifacts()}
            calls = []
            try:
                text = _turn(provider, workspace_id, history, message, lock, calls)
            except ProviderError as exc:
                failures.append(exc.summary)
                more = getattr(provider, "has_another_model", lambda: False)()
                if exc.kind == "daily_quota" and more:
                    continue
                if exc.retryable:
                    break
                # Every failure, not the last (P14-D25), each as one readable sentence.
                return ChatTurn(reply="", tool_calls=calls, error=_failed(failures))
            new = [a for a in list_artifacts() if a.path not in before]
            return ChatTurn(reply=text, tool_calls=calls, artifacts=new)
    return ChatTurn(reply="", tool_calls=calls, error=_failed(failures))


def _failed(failures: list[str]) -> str:
    return ("The assistant could not answer this time.\n\n"
            + "\n".join(f"- {f}" for f in failures)
            + "\n\nNothing in your workspace changed. Try again shortly.")


def _turn(provider: Provider, workspace_id: str, history: list[dict], message: str,
          lock: Callable[[], AbstractContextManager], calls: list[ToolCall]) -> str:
    session = provider.start(SYSTEM, history[-HISTORY_MESSAGES:], message, list(tool_specs()))
    for _ in range(MAX_ROUNDS):
        reply = session.step()
        if not reply.calls:
            return reply.text
        results = []
        for call in reply.calls:
            with lock():  # one tool at a time holds the workspace; the model's thinking does not
                result = run_tool(call, workspace_id)
            calls.append(ToolCall(call.name, dict(call.args), result,
                                  refused=reason_of(result) is not None
                                  or result.lstrip().startswith("BLOCKED")))
            results.append((call, _trim(_with_screen_notes(result))))
        session.add_results(results)
    return (reply.text + "\n\n" if reply.text else "") + (
        f"I stopped after {MAX_ROUNDS} rounds of tool calls without a final answer. What I ran is "
        f"listed below; ask again more narrowly.")


__all__ = ["ALLOWED", "MAX_ROUNDS", "SYSTEM", "answer", "run_tool", "tool_specs"]
