"""Files: every chart, report and result table the engine wrote in this workspace."""

from __future__ import annotations

import streamlit as st

from ui import components as ui
from ui import theme

_KINDS = {"chart": "Charts", "report": "Reports", "result": "Result tables"}


def render() -> None:
    theme.eyebrow("05 / Keep")
    st.title("What was *written.*")
    st.caption("Everything the engine wrote, newest first. Each comes with its own account of "
               "what it holds.")
    be, ws = ui.backend(), ui.workspace_id()
    artifacts = be.list_artifacts(ws)
    if not artifacts:
        st.info("Nothing written yet. Ask for a chart or a report on **Ask**.")
        return
    kinds = st.pills("Show", list(_KINDS), default=list(_KINDS), selection_mode="multi",
                     format_func=_KINDS.get)
    for art in (a for a in artifacts if a.kind in (kinds or [])):
        data = be.read_artifact(ws, art.path)
        with st.container(border=True):
            st.markdown(f"**{art.title}** · <span class='aa-muted'>{art.created[:16]}</span>",
                        unsafe_allow_html=True)
            if art.kind == "chart":
                st.image(data)
            elif art.kind == "report":
                with st.expander("Read the report"):
                    st.markdown(data.decode("utf-8", errors="replace"))
            else:
                st.code(data.decode("utf-8", errors="replace")[:2000], language=None)
            if art.description:
                st.caption(art.description)
            st.download_button("Download", data, file_name=art.path.rsplit("/", 1)[-1],
                               key=f"dl_{art.path}")
