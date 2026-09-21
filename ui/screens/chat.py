"""Ask: the conversation. The assistant runs the analyses; this screen shows what it said, what
it drew, and -- one click away -- every tool it called, refusals included."""

from __future__ import annotations

import json

import streamlit as st

from analytics_agent.webapp.contract import Artifact, ChatTurn
from ui import components as ui


def _artifact(art: Artifact) -> None:
    be, ws = ui.backend(), ui.workspace_id()
    if art.kind == "chart":
        st.image(be.read_artifact(ws, art.path), caption=art.title)
        st.caption(art.description)  # the plotted values, in the engine's words
    else:
        st.markdown(f"📜 **{art.title}** — {art.description} Open it on **Files**.")


def _turn(turn: ChatTurn) -> None:
    if turn.error:
        st.error(turn.error)
    if turn.reply:
        st.markdown(turn.reply)
    for art in turn.artifacts:
        _artifact(art)
    if turn.tool_calls:
        with st.expander(f"What I did ({len(turn.tool_calls)} step"
                         f"{'s' if len(turn.tool_calls) != 1 else ''})"):
            for call in turn.tool_calls:
                mark = "🔴 refused" if call.refused else "🟢"
                st.markdown(f"**{call.name}** {mark}")
                st.code(json.dumps(call.arguments, indent=2), language="json")
                st.code(call.result, language=None)


def render() -> None:
    st.title("Ask")
    st.caption("Ask in your own words. Every number comes from an analysis run under the "
               "dataset's contract.")
    log: list[dict] = st.session_state.setdefault("chat", [])
    for entry in log:
        with st.chat_message(entry["role"], avatar="🌅" if entry["role"] == "assistant" else None):
            if entry.get("turn") is not None:
                _turn(entry["turn"])
            else:
                st.markdown(entry["content"])

    message = st.chat_input("What would you like to know?")
    if message:
        history = [{"role": e["role"], "content": e["content"]} for e in log]
        log.append({"role": "user", "content": message})
        with st.chat_message("user"):
            st.markdown(message)
        with st.chat_message("assistant", avatar="🌅"):
            with st.spinner("Reading the data…"):
                turn = ui.backend().chat(ui.workspace_id(), history, message)
            _turn(turn)
        log.append({"role": "assistant", "content": turn.reply or (turn.error or ""),
                    "turn": turn})
