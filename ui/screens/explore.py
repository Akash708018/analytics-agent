"""Explore: run any of the engine's analyses by hand, under the contract, with no model in between.

The Ask screen needs a model key; this one needs only a confirmed contract. Pick an analysis, the
form offers the contract's own declared columns, Run calls the same gated engine functions the
assistant calls -- so a refusal here is the engine's refusal, and every number is the engine's.
The report is one click further (P14-D65).
"""

from __future__ import annotations

import streamlit as st

from analytics_agent.webapp.contract import AnalysisRun, AnalysisSpec
from ui import components as ui
from ui import theme

TIERS = {1: "Descriptive", 2: "Comparative", 3: "Temporal", 4: "Relational", 5: "Anomaly",
         6: "Inferential", 7: "Cohort"}
KEEP = 5  # results kept on screen, newest first


def _field(spec: AnalysisSpec, key: str):
    """One widget per argument, by its kind. Returns the value to send (None for "not given")."""
    values = {}
    cols = st.columns(2)
    for i, p in enumerate(spec.params):
        box = cols[i % 2]
        label = p.name.replace("_", " ") + ("" if p.required else " (optional)")
        k = f"{key}_{p.name}"
        if p.kind in ("measure", "dimension", "choice") and p.options:
            index = p.options.index(p.default) if p.default in p.options else None
            values[p.name] = box.selectbox(label, p.options, index=index, key=k, help=p.help,
                                           placeholder="(engine default)")
        elif p.kind == "number":
            values[p.name] = box.number_input(label, value=p.default, key=k, help=p.help,
                                              placeholder="(engine default)")
        else:
            text = box.text_input(label, value=p.default or "", key=k, help=p.help,
                                  placeholder="(engine default)")
            values[p.name] = text.strip() or None
    return {name: v for name, v in values.items() if v is not None}


def _show(run: AnalysisRun, title: str) -> None:
    be, ws = ui.backend(), ui.workspace_id()
    with st.container(border=True):
        st.markdown(f"**{title}**")
        if run.refusal:
            ui.show_refusal(run.refusal)
            return
        for art in run.artifacts:
            if art.kind == "chart":
                st.image(be.read_artifact(ws, art.path))
                if art.description:
                    st.caption(art.description)
        with st.expander("The engine's account, and the table", expanded=True):
            st.markdown(run.text)
        for art in run.artifacts:
            if art.kind in ("result", "report"):
                st.download_button(f"Download {art.path.rsplit('/', 1)[-1]}",
                                   be.read_artifact(ws, art.path),
                                   file_name=art.path.rsplit("/", 1)[-1], key=f"dl_x_{art.path}")


def render() -> None:
    theme.eyebrow("04 / Explore")
    st.title("Explore, *under contract.*")
    st.caption("Run any of the engine's analyses yourself. The form offers only the columns the "
               "contract declares; a refusal is the engine explaining what the question needs.")
    be, ws = ui.backend(), ui.workspace_id()
    datasets = be.list_datasets(ws)
    if not datasets:
        st.info("Load a file on **Upload & read** first.")
        return
    name = st.selectbox("Dataset", [d.name for d in datasets], key="explore_dataset")
    menu = be.analysis_menu(ws, name)
    if menu.refusal:
        ui.show_refusal(menu.refusal)
        st.caption("Agree what the columns mean on **Contract**, then come back.")
        return

    specs = {s.name: s for s in menu.analyses}
    choice = st.selectbox(
        "Analysis", list(specs), key=f"explore_kind_{name}",
        format_func=lambda n: f"{TIERS.get(specs[n].tier, specs[n].tier)} · {n}")
    spec = specs[choice]
    st.caption(spec.summary)
    params = _field(spec, f"x_{name}_{choice}")
    draw = st.toggle("Draw it", value=spec.chart is not None, disabled=spec.chart is None,
                     key=f"x_{name}_{choice}_draw",
                     help=f"as a {spec.chart} chart" if spec.chart else "a table is the answer")
    runs = st.session_state.setdefault("explore_runs", [])
    if st.button(f"Run {choice}", type="primary", width="stretch"):
        with st.spinner("Computing under the contract…"):
            run = be.run_analysis(ws, name, choice, params, spec.chart if draw else None)
        runs.insert(0, (f"{choice} · {name}", run))
        del runs[KEEP:]

    with st.expander("The whole story: build the report"):
        question = st.text_input("The question the report answers",
                                 value="What does this data show?", key=f"x_{name}_question")
        if st.button("Build the report", width="stretch"):
            with st.spinner("Writing every section…"):
                runs.insert(0, (f"report · {name}", be.build_report(ws, name, question)))
                del runs[KEEP:]

    for title, run in runs:
        _show(run, title)
