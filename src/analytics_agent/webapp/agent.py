"""The agent loop behind the Ask screen (Phase 14 Step 4).

A model reads the question, calls the engine's tools, reads their replies, and answers. The tools
are server.py's own functions -- what Claude Desktop calls -- restricted to an allowlist, with the
workspace injected by this module and never chosen by the model.
"""

from __future__ import annotations

import asyncio
import functools
import inspect
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
#: run_analysis is left out too (Cleanup Step 10): compute_analysis passes the same gate and
#: carries the same caveats, and run_analysis's reply was 7,431 characters of a catalogue the
#: roster below already carries.
ALLOWED: tuple[str, ...] = (
    "list_datasets", "describe_dataset", "get_workflow_state",
    "compute_analysis", "render_chart", "read_result_file", "profile_dataset", "profile_column",
    "validate_dataset", "get_cleaning_ledger", "build_report",
)

MAX_ROUNDS = 8
#: The web app's screens, in ui/app.py's order -- a test holds the two equal. The graded answer
#: of 22/09/2026 12:21 sent the person to a "Cleaning screen" that does not exist (Cleanup Step 9).
SCREENS: tuple[str, ...] = ("Journey", "Upload & read", "Contract", "Ask", "Files")
RESULT_CHARS = 8_000     # what the model reads of one tool reply
HISTORY_MESSAGES = 12

SYSTEM = """You are the analyst inside a data-analysis engine. The person is looking at a web app \
with their datasets in a sidebar.

Rules you do not break:
- Every number you state comes from a tool reply in this conversation. Never estimate, recall or \
round a figure into something the tool did not say.
- No analysis runs without a confirmed Dataset Contract. If a tool refuses, read its NEXT STEP. \
If the step is something only the person can do (load a file, confirm a contract), tell them \
where: the Upload & read screen, the Contract screen. You cannot do those.
- Start with get_workflow_state or list_datasets if you do not know what is loaded. When it says a \
contract is ready, go straight to the analyses the question needs: profile, describe or validate \
only when the question asks about the data's quality or shape.
- Charts appear to the person automatically under your answer. You cannot see them: describe a \
chart only from the numbers its reply gives.
- Carry every caveat a result prints -- a subset warning, a gap, excluded rows -- into your answer.
- Add no unit or currency the contract does not state: a measure defined as "units x unit_price" \
is a number, not dollars.
- The app's screens are exactly: {screens}, and the sidebar's Reset. Name no other. Cleaning \
and databases have no screen: say so plainly rather than inventing one.
- Never give the person a tool call, JSON or parameters to run -- they cannot call tools. If the \
question needs an analysis you have, run it yourself; if it needs a step you do not have, say \
what cannot be done here and why.
- Do the work the question asks for while you have rounds left, rather than suggesting it as a \
next step: a chart asked for is drawn with render_chart; "which items drive this month" is \
top_n (or concentration) with period= set to that period, e.g. period="2025-11".
- Give a cause for a gap, a peak or a change only if a tool reply states it. An empty period \
says no rows were loaded for it, not why.
- If the question asks for cleaned or deduplicated data and a reply says rows are copies, \
answer on the data as it is, say plainly that the figures include those rows, and that \
cleaning is not available in the web app.
- Answer in plain language, briefly, and name the analysis you ran.""".format(
    screens=", ".join(SCREENS))


def _roster() -> str:
    """Every analysis with the parameters its function takes, read from the registry.

    Replaces, for the model, compute_analysis's hand-written 7,051-character table: derived, it
    cannot name a parameter the code lacks, and it is a sixth of the size (Cleanup Step 10).
    """
    from analytics_agent.analysis.registry import REGISTRY

    lines = []
    for a in sorted(REGISTRY.values(), key=lambda a: (a.tier, a.name)):
        names = [n for n, prm in inspect.signature(a.run).parameters.items()
                 if n not in ("con", "gate", "scope") and prm.kind is not prm.VAR_KEYWORD]
        if a.narrows:
            names += ["period", "grain"]
        if a.selects:
            names += ["groups"]
        lines.append(f"{a.name}({', '.join(names)})")
    return "; ".join(lines)


#: What the model is told beyond each docstring's first paragraph, for the two tools whose full
#: docstrings are most of the request. Claude Desktop still reads the full docstrings.
_EXTRA = {
    "compute_analysis": lambda: (
        "analysis_type and its parameters: " + _roster() + ". measure and dimension must be "
        "declared in the contract. grain is day, week, month, quarter or year (default month); "
        'period names one, e.g. "2025-11" or "2025-Q4" with grain="quarter".'),
    "render_chart": lambda: (
        "Same analysis parameters as compute_analysis, plus chart: line, bar, grouped_bar, "
        "scatter, histogram, box, heatmap or waterfall. line, bar, histogram and waterfall draw "
        "one measure: the measure passed is drawn; otherwise name it with y. grouped_bar draws "
        "several, e.g. trend with a dimension."),
}


def _compact(name: str, doc: str) -> str:
    first = doc.strip().split("\n\n", 1)[0]
    extra = _EXTRA.get(name)
    return " ".join(first.split()) + (f" {extra()}" if extra else "")


@functools.lru_cache(maxsize=1)
def tool_specs() -> tuple[ToolSpec, ...]:
    """The allowlisted tools, their schemas converted and workspace_id removed, each described by
    its docstring's first paragraph (Cleanup Step 10: the full docstrings were 19,616 characters
    with the schemas, and Groq's limit is 8,000 tokens a minute for the whole conversation)."""
    tools = {t.name: t for t in asyncio.run(server.mcp.list_tools())}
    missing = [n for n in ALLOWED if n not in tools]
    if missing:
        raise RuntimeError(f"allowlisted tools not registered: {missing}")
    return tuple(ToolSpec(n, _compact(n, tools[n].description or ""),
                          convert_schema(tools[n].parameters))
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
    "propose_cleaning_plan": "no screen yet -- cleaning is not in the web app",
    "apply_cleaning_plan": "no screen yet -- cleaning is not in the web app",
    "load_postgres_table": "no screen -- databases are not connected to the web app",
    "query_source": "no screen -- databases are not connected to the web app",
    "describe_source": "no screen -- databases are not connected to the web app",
}
#: Tools left out of the allowlist whose work another allowlisted tool does.
INSTEAD: dict[str, str] = {
    "run_analysis": "call compute_analysis directly -- it checks the same contract and computes.",
}
_NAMED_CALL = re.compile(r"\b([a-z_]+)\(")


def _with_screen_notes(text: str) -> str:
    """A tool reply whose NEXT STEP names a tool the assistant lacks, with a note saying where the
    person does it. Seen live: gpt-oss copied "NEXT STEP: call propose_dataset_contract(...)" into
    a tool call Groq refused, failing the turn (P14-D33)."""
    found = list(dict.fromkeys(_NAMED_CALL.findall(text)))
    named = [n for n in found if n in SCREEN_FOR]
    instead = [n for n in found if n in INSTEAD]
    if not named and not instead:
        return text
    notes = "\n".join(
        [f"- {n}: not one of your tools; the person does it on {SCREEN_FOR[n]}." for n in named]
        + [f"- {n}: not one of your tools; {INSTEAD[n]}" for n in instead])
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
    at_start = {a.path for a in list_artifacts()}
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
                return ChatTurn(reply="", tool_calls=calls,
                                error=_failed(failures, _written(list_artifacts, at_start)))
            new = [a for a in list_artifacts() if a.path not in before]
            return ChatTurn(reply=text, tool_calls=calls, artifacts=new)
    return ChatTurn(reply="", tool_calls=calls,
                    error=_failed(failures, _written(list_artifacts, at_start)))


def _written(list_artifacts: Callable[[], list[Artifact]], at_start: set) -> int:
    return len([a for a in list_artifacts() if a.path not in at_start])


def _failed(failures: list[str], written: int = 0) -> str:
    """Seen live (Cleanup Step 10): a turn drew a chart, then failed, and this said nothing had
    changed. A result or chart written before the failure stays in Files (P14-D28)."""
    after = (f"{written:,} file(s) written before the failure are in Files; nothing else "
             f"changed." if written else "Nothing in your workspace changed.")
    return ("The assistant could not answer this time.\n\n"
            + "\n".join(f"- {f}" for f in failures)
            + f"\n\n{after} Try again shortly.")


def _turn(provider: Provider, workspace_id: str, history: list[dict], message: str,
          lock: Callable[[], AbstractContextManager], calls: list[ToolCall]) -> str:
    session = provider.start(SYSTEM, history[-HISTORY_MESSAGES:], message, list(tool_specs()))
    for i in range(MAX_ROUNDS):
        # The last round offers no tools, so what was fetched is answered rather than dropped
        # (Cleanup Step 11: seven rounds held every figure, the eighth was a call, and the turn
        # returned only the stop message).
        final = i == MAX_ROUNDS - 1
        reply = session.step(final=final)
        if not reply.calls or (final and reply.text):
            return reply.text
        if final:
            break
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


__all__ = ["ALLOWED", "MAX_ROUNDS", "SCREENS", "SYSTEM", "answer", "run_tool", "tool_specs"]
