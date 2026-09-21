"""Contract: agree what a dataset's columns mean before any number is computed from them.

Each column gets a role; each measure an aggregation (deliberately no default -- summing a unit
price means nothing, and only a person knows) and a one-line definition. The choices go back to
the engine, which says what is still missing. Confirm stays disabled until nothing is.
"""

from __future__ import annotations

import datetime as _dt
import re

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


DATE_MIN = _dt.date(1900, 1, 1)
DATE_MAX = _dt.date(2100, 12, 31)


def _seed(key: str, value) -> str:
    """A widget key whose first value is `value` and whose later values are the person's."""
    if key not in st.session_state:
        st.session_state[key] = value
    return key


def _iso(value) -> str | None:
    return value.isoformat() if isinstance(value, _dt.date) else None


def form_answers(rows: list[dict], grain: str, start, end, caveats: str) -> dict:
    """The form as the engine's draft_contract takes it. Reading, not deciding: which of these
    is enough is the engine's call."""
    return dict(
        grain=grain.strip() or None,
        primary_key=[r["column"] for r in rows if r["role"] == "key"],
        date_column=next((r["column"] for r in rows if r["role"] == "date"), None),
        measures=[r["column"] for r in rows if r["role"] == "measure"],
        dimensions=[r["column"] for r in rows if r["role"] == "dimension"],
        aggregations={r["column"]: r["aggregation"] for r in rows
                      if r["role"] == "measure" and r["aggregation"]},
        measure_definitions={r["column"]: r["definition"].strip() for r in rows
                             if r["role"] == "measure" and (r["definition"] or "").strip()},
        analysis_window_start=_iso(start), analysis_window_end=_iso(end),
        caveats=[c.strip() for c in caveats.splitlines() if c.strip()])


def submit(be, ws: str, name: str, answers: dict, *, confirm: bool):
    """Check -- and, if asked and nothing is missing, store -- the form AS IT IS NOW.

    Confirm used to send the stored draft instead: disabled until "Update draft" was clicked,
    and blind to any edit made after it, so the contract stored could differ from the one on
    screen (P14-D30). Returns (the fresh draft, the confirm result or None).
    """
    fresh = be.draft_contract(ws, name, **answers)
    if confirm and not fresh.provisional and fresh.refusal is None:
        return fresh, be.confirm_contract(ws, fresh)
    return fresh, None


_PATH = re.compile(r"^measures\[(.+)\]\.(agg|definition)$")
_WORDS = {"grain": "Grain (what one row is)", "analysis_window": "Analysis window (from and to)",
          "primary_key": "a key column", "date_column": "a date column"}


def plain(path: str) -> str:
    """An engine field path in words, for display only: measures[units].agg -> units: aggregation."""
    m = _PATH.match(path)
    if m:
        return f"{m.group(1)}: {'aggregation' if m.group(2) == 'agg' else 'definition'}"
    return _WORDS.get(path, path)


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

    # Every field is keyed per dataset and seeded from the draft ONCE, so the form holds what the
    # person entered rather than whatever the latest draft echoes. For text and dates the engine
    # echoes what was typed, so this changes nothing visible today; for a column marked "ignore"
    # it does not -- the engine leaves the column out, and an unseeded table would reset its role
    # on the next check. Reasoned, not measured: AppTest cannot edit a data_editor (C99).
    st.subheader("What one row is")
    grain = st.text_input("Grain", key=_seed(f"c_grain_{name}", draft.grain or ""),
                          placeholder="one row = one order")
    c1, c2 = st.columns(2)
    # Any date. Streamlit's default range is ten years before today, so on 22/09/2026 nothing
    # before 22/09/2016 could be picked and an older start was dropped silently -- Olist's own
    # data begins in 2016 (measured: 2016-01-01 set, value None; 2018-12-31 kept; P14-D31).
    start = c1.date_input("Analysis window from", min_value=DATE_MIN, max_value=DATE_MAX,
                          key=_seed(f"c_from_{name}", (
                              _dt.date.fromisoformat(draft.analysis_window_start)
                              if draft.analysis_window_start else None)))
    end = c2.date_input("to", min_value=DATE_MIN, max_value=DATE_MAX,
                        key=_seed(f"c_to_{name}", (
                            _dt.date.fromisoformat(draft.analysis_window_end)
                            if draft.analysis_window_end else None)))

    st.subheader("What each column is")
    # Seeded once too: the editor rebuilds when its data changes.
    rows = st.session_state.setdefault(f"c_rows_{name}", [{
        "column": c.name, "type": c.dtype,
        "distinct": c.distinct_count, "nulls": c.null_count,
        "examples": ", ".join(c.sample_values[:3]),
        "role": _role_of(draft, c.name, c.suggested_role),
        "aggregation": draft.aggregations.get(c.name),
        "definition": draft.measure_definitions.get(c.name, ""),
    } for c in draft.columns])
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
    caveats = st.text_area("Caveats (one per line)",
                           key=_seed(f"c_caveats_{name}", "\n".join(draft.caveats)))

    answers = form_answers(edited, grain, start, end, caveats)
    left, right = st.columns([1, 1])
    check = left.button("Check what's missing", type="secondary", width="stretch")
    confirm = right.button("Confirm contract", width="stretch")
    if check or confirm:
        fresh, result = submit(be, ws, name, answers, confirm=confirm)
        drafts[name] = fresh
        if result is not None:
            st.session_state["contract_result"] = (name, result)
            if result.ok:
                drafts.pop(name, None)
        else:
            st.session_state.pop("contract_result", None)
        st.rerun()  # redraw: the sidebar shows the new stage, the list below the fresh check

    if draft.evidence:
        with st.expander("What the data showed"):
            for e in draft.evidence:
                st.markdown(f"- {e}")
    for q in draft.questions:
        st.markdown(f"> {q}")
    if draft.provisional:
        st.warning("**Still needed before this can be confirmed:** "
                   + "; ".join(plain(item) for item in draft.provisional))
    st.caption(draft.message)

    shown = st.session_state.get("contract_result")
    if shown and shown[0] == name:
        if shown[1].refusal:
            ui.show_refusal(shown[1].refusal)
        else:
            st.success(shown[1].message)
            st.caption("Next: ask a question on **Ask**.")
