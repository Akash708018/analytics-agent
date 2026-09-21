"""Pieces every screen shares: the session's workspace, refusals, and the sidebar."""

from __future__ import annotations

import html

import streamlit as st

from analytics_agent.webapp.contract import Backend, Refusal
from ui import theme
from ui.backend import get_backend


def backend() -> Backend:
    return get_backend()


def workspace_id() -> str:
    """This browser session's workspace, created on first use and kept for the session."""
    if "workspace_id" not in st.session_state:
        st.session_state["workspace_id"] = backend().new_workspace_id()
    return st.session_state["workspace_id"]


def show_refusal(refusal: Refusal) -> None:
    """A refusal as the engine meant it: what, why, and the one call that fixes it."""
    st.error(f"**{refusal.what}**\n\n{refusal.why}")
    st.markdown(f"**Next step:** `{refusal.next_step}`")
    with st.expander("Details"):
        st.code(refusal.text, language=None)


def sidebar() -> None:
    ws = workspace_id()
    be = backend()
    with st.sidebar:
        st.html('<div class="aa-title" style="font-size:1.15rem">Your workspace</div>')
        datasets = be.list_datasets(ws)
        if not datasets:
            st.caption("Nothing loaded yet. Start on **Upload & read**.")
        for d in datasets:
            st.html(
                f'<div class="aa-card" style="padding:.7rem .85rem;margin:.3rem 0">'
                f'<b>{html.escape(d.name)}</b><br>'
                f'<span class="aa-muted" style="font-size:.8rem">{d.rows:,} rows · '
                f'{d.columns} cols · {html.escape(d.loaded)}</span><br>'
                f'{theme.pill(html.escape(d.stage), theme.stage_kind(d.stage))}</div>')
            for note in d.notes:  # every note, never truncated
                st.html(f'<div class="aa-subset">{html.escape(note)}</div>')
            st.caption(f"Next: `{d.next_step}`")
        st.divider()
        confirm = st.checkbox("I want to empty this workspace", key="reset_confirm")
        if st.button("Reset workspace", disabled=not confirm, type="secondary",
                     use_container_width=True):
            result = be.reset_workspace(ws)
            st.session_state.pop("reset_confirm", None)
            for key in ("ingest", "contract_draft", "chat"):
                st.session_state.pop(key, None)
            st.toast(result.message)
            st.rerun()
        st.caption(f"workspace `{ws}`")
