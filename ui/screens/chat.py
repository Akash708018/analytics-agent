"""Ask: the conversation. The assistant runs the analyses; this screen shows what it said, what
it drew, and -- one click away -- every tool it called, refusals included."""

from __future__ import annotations

import json

import streamlit as st

from analytics_agent.webapp.contract import Artifact, ChatTurn
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
            with st.spinner("Reading the data…"):
                turn = ui.backend().chat(ui.workspace_id(), history, message)
            _turn(turn)
        log.append({"role": "assistant", "content": turn.reply or (turn.error or ""),
                    "turn": turn})
