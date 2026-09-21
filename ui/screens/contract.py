"""Contract: agree what a dataset's columns mean before any number is computed from them.

Each column gets a role; each measure an aggregation (deliberately no default -- summing a unit
price means nothing, and only a person knows) and a one-line definition. The choices go back to
the engine, which says what is still missing. Confirm stays disabled until nothing is.
"""

from __future__ import annotations

import datetime as _dt

import streamlit as st

from analytics_agent.webapp.contract import AGGREGATIONS, ROLES, ContractDraft
from ui import components as ui
from ui import theme


def _role_of(draft: ContractDraft, name: str, suggested: str) -> str:
    if name in draft.primary_key:
        return "key"
    if name == draft.date_column:
        return "date"
    if name in draft.measures:
        return "measure"
    if name in draft.dimensions:
        return "dimension"
    return suggested if suggested in ROLES else "ignore"


def _iso(value) -> str | None:
    return value.isoformat() if isinstance(value, _dt.date) else None


def render() -> None:
    theme.eyebrow("02 / Agree")
    st.title("The *contract.*")
    st.caption("No analysis runs without an agreement on what one row is and what each number "
               "means. The engine drafts it from the data; you settle what the data cannot say.")
    be, ws = ui.backend(), ui.workspace_id()
    datasets = be.list_datasets(ws)
    if not datasets:
        st.info("Load a file on **Upload & read** first.")
        return

    names = [d.name for d in datasets]
    name = st.selectbox("Dataset", names)
    drafts = st.session_state.setdefault("contract_draft", {})
    if name not in drafts:
        drafts[name] = be.draft_contract(ws, name)
    draft: ContractDraft = drafts[name]
    if draft.refusal:
        ui.show_refusal(draft.refusal)
        return

    st.subheader("What one row is")
    grain = st.text_input("Grain", value=draft.grain or "",
                          placeholder="one row = one order")
    c1, c2 = st.columns(2)
    start = c1.date_input("Analysis window from", value=(
        _dt.date.fromisoformat(draft.analysis_window_start)
        if draft.analysis_window_start else None))
    end = c2.date_input("to", value=(
        _dt.date.fromisoformat(draft.analysis_window_end) if draft.analysis_window_end else None))

    st.subheader("What each column is")
    rows = [{
        "column": c.name, "type": c.dtype,
        "distinct": c.distinct_count, "nulls": c.null_count,
        "examples": ", ".join(c.sample_values[:3]),
        "role": _role_of(draft, c.name, c.suggested_role),
        "aggregation": draft.aggregations.get(c.name),
        "definition": draft.measure_definitions.get(c.name, ""),
    } for c in draft.columns]
    edited = st.data_editor(
        rows, hide_index=True, width="stretch", key=f"contract_cols_{name}",
        column_config={
            "column": st.column_config.TextColumn(disabled=True),
            "type": st.column_config.TextColumn(disabled=True),
            "distinct": st.column_config.NumberColumn(disabled=True),
            "nulls": st.column_config.NumberColumn(disabled=True),
            "examples": st.column_config.TextColumn(disabled=True),
            "role": st.column_config.SelectboxColumn(options=list(ROLES), required=True),
            "aggregation": st.column_config.SelectboxColumn(
                options=list(AGGREGATIONS), help="Measures only. 'none' = per-row only."),
            "definition": st.column_config.TextColumn(help="Measures only: one line."),
        })
    caveats = st.text_area("Caveats (one per line)", value="\n".join(draft.caveats))

    if st.button("Update draft", type="secondary"):
        measures = [r["column"] for r in edited if r["role"] == "measure"]
        drafts[name] = be.draft_contract(
            ws, name, grain=grain or None,
            primary_key=[r["column"] for r in edited if r["role"] == "key"],
            date_column=next((r["column"] for r in edited if r["role"] == "date"), None),
            measures=measures,
            dimensions=[r["column"] for r in edited if r["role"] == "dimension"],
            aggregations={r["column"]: r["aggregation"] for r in edited
                          if r["role"] == "measure" and r["aggregation"]},
            measure_definitions={r["column"]: r["definition"] for r in edited
                                 if r["role"] == "measure" and r["definition"]},
            analysis_window_start=_iso(start), analysis_window_end=_iso(end),
            caveats=[c.strip() for c in caveats.splitlines() if c.strip()])
        st.rerun()

    if draft.evidence:
        with st.expander("What the data showed"):
            for e in draft.evidence:
                st.markdown(f"- {e}")
    for q in draft.questions:
        st.markdown(f"> {q}")
    if draft.provisional:
        st.warning("**Still needed before this can be confirmed:** "
                   + ", ".join(draft.provisional))
    st.caption(draft.message)

    if st.button("Confirm contract", disabled=bool(draft.provisional),
                 help="Settle what is listed above, then Update draft." if draft.provisional
                 else None):
        st.session_state["contract_result"] = (name, be.confirm_contract(ws, draft))
        drafts.pop(name, None)
        st.rerun()  # redraw the sidebar, which shows the dataset's new stage
    shown = st.session_state.get("contract_result")
    if shown and shown[0] == name:
        if shown[1].refusal:
            ui.show_refusal(shown[1].refusal)
        else:
            st.success(shown[1].message)
            st.caption("Next: ask a question on **Ask**.")
