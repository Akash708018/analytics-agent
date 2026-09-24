"""Pieces every screen shares: the session's workspace, refusals, and the sidebar."""

from __future__ import annotations

import html
import re

import streamlit as st

from analytics_agent.webapp.contract import Backend, Refusal
from ui import theme
from ui.backend import get_backend


def backend() -> Backend:
    return get_backend()


# The only shape new_workspace_id() produces. A URL can therefore name a session's workspace but
# never "local" (Claude Desktop's, P14-D4) nor anything path-like.
_WS_IN_URL = re.compile(r"^ws_[0-9a-f]{12}$")


def workspace_id() -> str:
    """This browser session's workspace, kept in the URL so a reload finds it again.

    Session state alone died with every refresh: a reload is a new Streamlit session, so it
    made a new, empty workspace and orphaned the old one (P14-D20, seen in the browser). The id
    is 48 random bits -- whoever holds the URL holds the workspace, like any share link.
    """
    if "workspace_id" not in st.session_state:
        from_url = st.query_params.get("ws", "")
        st.session_state["workspace_id"] = (
            from_url if _WS_IN_URL.match(from_url) else backend().new_workspace_id())
    wid = st.session_state["workspace_id"]
    if st.query_params.get("ws") != wid:
        st.query_params["ws"] = wid
    return wid


# The engine names its next step as a call; the sidebar says where a person takes it (display
# only -- the step itself is still the engine's). An unknown call is shown as the call.
_SCREEN_FOR = (
    (("propose_cleaning_plan", "apply_cleaning_plan"), "review the proposed fixes on **Clean**"),
    (("propose_dataset_contract", "confirm_dataset_contract"),
     "agree what the columns mean on **Contract**"),
    (("run_analysis", "compute_analysis", "render_chart"),
     "run an analysis on **Explore**, or ask on **Ask**"),
    (("propose_ingest_spec", "confirm_ingest_spec", "load_csv", "load_excel"),
     "load it on **Upload & read**"),
)


def next_step_words(call: str) -> str:
    for names, words in _SCREEN_FOR:
        if call.split("(", 1)[0].strip() in names:
            return words
    return f"`{call}`"


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
        st.html('<div class="aa-eyebrow">Your workspace</div>')
        datasets = be.list_datasets(ws)
        if not datasets:
            st.caption("Nothing loaded yet. Start on **Upload & read**.")
        for d in datasets:
            st.html(
                f'<div class="aa-card" style="padding:.7rem .85rem;margin:.3rem 0">'
                f'{theme.icon("database")}<b>{html.escape(d.name)}</b><br>'
                f'<span class="aa-muted" style="font-size:.8rem">{d.rows:,} rows · '
                f'{d.columns} cols · {html.escape(d.loaded)}</span><br>'
                f'{theme.pill(html.escape(d.stage), theme.stage_kind(d.stage))}</div>')
            for note in d.notes:  # every note, never truncated
                st.html(f'<div class="aa-subset">{html.escape(note)}</div>')
            st.caption(f"Next: {next_step_words(d.next_step)}")
        st.divider()
        # The portfolio's "Pause motion": stops every animation, keeps two faint marks.
        st.toggle("Motion", value=theme.motion_on(), key="motion",
                  help="Turn off to stop the ink and every other animation.")
        confirm = st.checkbox("I want to empty this workspace", key="reset_confirm")
        if st.button("Reset workspace", disabled=not confirm, type="secondary",
                     width="stretch"):
            result = be.reset_workspace(ws)
            st.session_state.pop("reset_confirm", None)
            for key in [k for k in st.session_state
                        if k in ("ingest", "contract_draft", "contract_result", "chat",
                                 "clean_proposal", "clean_result", "clean_dataset",
                                 "explore_runs", "explore_dataset")
                        or k.startswith(("clean_", "x_", "explore_", "c_grain_", "c_from_",
                                         "c_to_", "c_rows_", "c_caveats_", "c_agg_", "c_def_",
                                         "contract_cols_"))]:
                st.session_state.pop(key, None)
            st.toast(result.message)
            st.rerun()
        st.caption(f"workspace `{ws}`")
