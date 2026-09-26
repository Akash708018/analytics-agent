"""Ask: the conversation. The assistant runs the analyses; this screen shows what it said, what
it drew, and -- one click away -- every tool it called, refusals included.

While a turn runs, the status box says what it is waiting on -- a provider's rate-limit pause
names the provider and the seconds (step 2: the screen once said "Reading the data..." through
seven minutes of waits). What is still worth reading afterwards is kept on the turn as notes."""

from __future__ import annotations

import inspect
import json

import streamlit as st

from analytics_agent.webapp.contract import Artifact, Backend, ChatEvent, ChatTurn
from ui import components as ui
from ui import theme

AVATAR = ":material/insights:"


def _artifact(art: Artifact) -> None:
    be, ws = ui.backend(), ui.workspace_id()
    if art.kind == "chart":
        st.image(be.read_artifact(ws, art.path), caption=art.title)
        st.caption(art.description)  # the plotted values, in the engine's words
    else:
        st.markdown(f"**{art.title}** — {art.description} Open it on **Files**.")


def _turn(turn: ChatTurn) -> None:
    if turn.error:
        st.error(turn.error)
        # A failed turn is not a dead end: every analysis the assistant would run is on Explore,
        # which needs a contract and no model (P14-D65).
        st.caption("Every analysis the assistant runs is also on **Explore**, which needs no "
                   "model key -- the same engine, the same contract.")
    if turn.reply:
        st.markdown(turn.reply)
    if turn.verification:
        # Every figure looked for in the tool replies (webapp/verify.py); a miss is not hidden.
        if turn.verified:
            st.caption(f":material/check_circle: {turn.verification}")
        else:
            st.warning(turn.verification, icon=":material/rule:")
    for note in getattr(turn, "notes", None) or []:
        st.caption(f":material/schedule: {note}")
    for art in turn.artifacts:
        _artifact(art)
    if turn.tool_calls:
        with st.expander(f"What I did ({len(turn.tool_calls)} step"
                         f"{'s' if len(turn.tool_calls) != 1 else ''})"):
            for call in turn.tool_calls:
                mark = " · :red[refused]" if call.refused else ""
                st.markdown(f"`{call.name}`{mark}")
                st.code(json.dumps(call.arguments, indent=2), language="json")
                st.code(call.result, language=None)


def _proposals() -> None:
    """Metrics the assistant proposed, each with Approve and Reject (step 3). Nothing is computed
    with one until it is approved here."""
    be, ws = ui.backend(), ui.workspace_id()
    for p in be.pending_metrics(ws):
        with st.container(border=True):
            st.markdown(f"**Proposed metric: `{p.name}`** on {p.dataset_name} -- "
                        f"`{p.formula}`  \n{p.definition}")
            st.caption(p.measured)
            yes, no, _ = st.columns([1, 1, 4])
            if yes.button("Approve", key=f"approve_{p.id}", type="primary"):
                st.session_state["metric_result"] = be.decide_metric(ws, p.id, True).message
                st.rerun()
            if no.button("Reject", key=f"reject_{p.id}"):
                st.session_state["metric_result"] = be.decide_metric(ws, p.id, False).message
                st.rerun()
    if st.session_state.get("metric_result"):
        st.success(st.session_state.pop("metric_result"))


def _takes_progress(backend: Backend) -> bool:
    """Whether this backend's chat hears progress: one written before step 2 (the fake) takes
    three arguments and is called with three."""
    try:
        return "progress" in inspect.signature(backend.chat).parameters
    except (TypeError, ValueError):
        return False


def _ask(backend: Backend, workspace_id: str, history: list[dict], message: str) -> ChatTurn:
    """One turn, with a status box that says what the turn is waiting on while it runs."""
    with st.status("Reading the data…", expanded=False) as box:
        def progress(event: ChatEvent) -> None:
            box.update(label=event.text)
            if event.kind != "step":  # a wait, a failover, a shortened reply: kept in the box
                box.write(event.text)

        if _takes_progress(backend):
            turn = backend.chat(workspace_id, history, message, progress=progress)
        else:
            turn = backend.chat(workspace_id, history, message)
        box.update(label="Could not answer" if turn.error else "Answered",
                   state="error" if turn.error else "complete", expanded=False)
    return turn


def render() -> None:
    theme.eyebrow("05 / Ask")
    st.title("Ask in your *own words.*")
    st.caption("Ask in your own words. Every number comes from an analysis run under the "
               "dataset's contract.")
    log: list[dict] = st.session_state.setdefault("chat", [])
    for entry in log:
        with st.chat_message(entry["role"],
                             avatar=AVATAR if entry["role"] == "assistant" else ":material/person:"):
            if entry.get("turn") is not None:
                _turn(entry["turn"])
            else:
                st.markdown(entry["content"])

    message = st.chat_input("What would you like to know?")
    if message:
        history = [{"role": e["role"], "content": e["content"]} for e in log]
        log.append({"role": "user", "content": message})
        with st.chat_message("user", avatar=":material/person:"):
            st.markdown(message)
        with st.chat_message("assistant", avatar=AVATAR):
            turn = _ask(ui.backend(), ui.workspace_id(), history, message)
            _turn(turn)
        log.append({"role": "assistant", "content": turn.reply or (turn.error or ""),
                    "turn": turn})
    _proposals()
