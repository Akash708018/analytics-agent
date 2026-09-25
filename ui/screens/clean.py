"""Clean: see what the engine would change in a loaded table, and approve it step by step.

Nothing changes by looking. Each step comes with its exact SQL and counts; a step that destroys
something not declared missing says what, with a sample, and is never pre-ticked. Only the steps
the engine itself would run -- lossless and in conflict with nothing -- start ticked. What is
ticked runs in the order shown, all or none (closes P14-O2).
"""

from __future__ import annotations

import streamlit as st

from analytics_agent.webapp.contract import CleaningProposal
from ui import components as ui
from ui import theme


def _short(text: str, width: int = 80) -> str:
    return text if len(text) <= width else text[:width - 1] + "…"


def _propose(be, ws: str, name: str) -> CleaningProposal:
    """Proposing stores a plan engine-side, so it is asked for once per visit, not per rerun."""
    proposals = st.session_state.setdefault("clean_proposal", {})
    if name not in proposals:
        proposals[name] = be.propose_cleaning(ws, name)
    return proposals[name]


def render() -> None:
    theme.eyebrow("02 / Clean")
    st.title("Clean, *by consent.*")
    st.caption("The engine lists every change it could make, with the SQL and the counts. "
               "Nothing runs until you tick it; a step that loses information says what.")
    be, ws = ui.backend(), ui.workspace_id()
    datasets = be.list_datasets(ws)
    if not datasets:
        st.info("Load a file on **Upload & read** first.")
        return

    name = st.selectbox("Dataset", [d.name for d in datasets], key="clean_dataset")
    if st.button("Look again", type="secondary"):
        st.session_state.get("clean_proposal", {}).pop(name, None)
        st.session_state.pop("clean_result", None)
        st.rerun()
    proposal = _propose(be, ws, name)

    shown = st.session_state.get("clean_result")
    if shown and shown[0] == name:
        if shown[1].refusal:
            ui.show_refusal(shown[1].refusal)
        else:
            st.success(shown[1].message)
            st.caption("Next: agree what each column means on **Contract**.")

    if proposal.refusal:
        ui.show_refusal(proposal.refusal)
        return
    if not proposal.steps:
        st.success(proposal.message or f"Nothing to clean in {name}.")
        return

    st.subheader(f"{len(proposal.steps)} change(s) proposed · {proposal.row_count:,} rows")
    ticked: list[str] = []
    for step in proposal.steps:
        with st.container(border=True):
            where = f" on `{step.column}`" if step.column else ""
            label = f"**{step.action_id}** · {step.kind}{where}: {step.intent}"
            if st.checkbox(label, value=step.suggested, key=f"clean_{name}_{step.action_id}"):
                ticked.append(step.action_id)
            st.caption(f"{step.rows_affected:,} row(s) affected")
            if step.lossy and step.kind == "DROP_DUPLICATE_ROWS":
                # Each sample is a whole row as JSON: three of them filled the card with ~2,000
                # characters, under a warning that a kept copy is lost information (recheck,
                # 25/09/2026, retail fixture).
                st.info(f"Removes {step.values_lost:,} extra cop(ies): one of each identical row "
                        f"is kept. Leave this unticked only if the same row can really occur "
                        f"twice -- two identical sales, say.")
                if step.sample:
                    with st.expander("Rows that are duplicated"):
                        st.code("\n".join(step.sample[:3]), language="json")
            elif step.lossy:
                sample = ", ".join(_short(repr(v)) for v in step.sample[:3]) or "no sample"
                st.warning(f"Discards {step.values_lost:,} {step.loss_unit}(s) that are not "
                           f"declared missing: {sample}. That is information, not absence -- "
                           "tick this only if you mean to lose it.")
            with st.expander("SQL"):
                st.code(step.sql, language="sql")

    st.caption("Ticked steps run in the order shown, all of them or none.")
    if st.button(f"Apply {len(ticked)} step(s)", disabled=not ticked, width="stretch"):
        result = be.apply_cleaning(ws, name, ticked)
        st.session_state["clean_result"] = (name, result)
        st.session_state["clean_proposal"].pop(name, None)  # the table changed: propose afresh
        # A contract draft made before cleaning describes the old types; draft it again.
        # Its column grid is seeded once from that draft too (types, suggested roles).
        st.session_state.get("contract_draft", {}).pop(name, None)
        st.session_state.pop(f"c_rows_{name}", None)
        st.session_state.pop(f"contract_cols_{name}", None)
        for key in [k for k in st.session_state if k.startswith(f"clean_{name}_")]:
            st.session_state.pop(key, None)
        st.rerun()
