"""Upload & read: the Ingest Spec editor.

The file is shown exactly as it sits on the sheet, with the real row numbers, and the engine's
proposal for reading it laid over the top: header rows glow, skipped rows are struck through. A
person corrects what the engine could not work out; the engine decides whether it is now
readable. Confirm stays disabled while the draft is PROVISIONAL.
"""

from __future__ import annotations

import html

import streamlit as st

from analytics_agent.webapp.contract import DTYPES, HEADER_JOINS, IngestDraft
from ui import components as ui
from ui import theme

INFER = "(infer)"

_GRID_CSS = """
<style>
.aa-grid { width: 100%; border-collapse: separate; border-spacing: 0; font-size: .86rem;
  border-radius: 9px; overflow: hidden; border: 1px solid #cdae938c; background: #fbf4e9ee;
  box-shadow: 0 15px 40px #7141240b; }
.aa-grid th, .aa-grid td { padding: .4rem .65rem; border-bottom: 1px solid #e3cdb4; }
.aa-grid th { background: #efdcc2; color: #945836; font: 500 .72rem/1.4 var(--mono);
  letter-spacing: .09em; text-align: left; }
.aa-grid td.rn { color: #945836; width: 3.2rem; text-align: right; font: 500 .75rem var(--mono);
  font-variant-numeric: tabular-nums; }
.aa-grid tr.hdr td { background: #eac29d; color: #503326; font-weight: 600; }
.aa-grid tr.skip td { color: #b39a85; text-decoration: line-through; }
.aa-grid tr.data td { color: var(--text); }
.aa-grid td.empty { color: #cbb29b; }
.aa-legend { margin-top: .4rem; }
.aa-legend span { margin-right: 1rem; font: 500 .72rem var(--mono); letter-spacing: .05em;
  color: var(--muted); }
.aa-legend b.h { background: #eac29d; color: #503326; padding: 0 .3rem; border-radius: 3px; }
.aa-legend b.s { text-decoration: line-through; }
</style>
"""


def stylesheet() -> str:
    return _GRID_CSS


def _grid_html(draft: IngestDraft, header_rows: list[int], data_start: int, footer: int) -> str:
    g = draft.grid
    width = max((len(r) for r in g.rows), default=0)
    letters = [chr(ord("A") + i) for i in range(width)]
    last = g.first_row_number + len(g.rows) - 1
    out = ['<table class="aa-grid"><tr><th></th>']
    out += [f"<th>{c}</th>" for c in letters] + ["</tr>"]
    for i, row in enumerate(g.rows):
        n = g.first_row_number + i
        kind = ("hdr" if n in header_rows else
                "skip" if n < data_start or (footer and n > last - footer) else "data")
        cells = "".join(
            f'<td class="empty">·</td>' if v is None else f"<td>{html.escape(str(v))}</td>"
            for v in (row + [None] * (width - len(row))))
        out.append(f'<tr class="{kind}"><td class="rn">{n}</td>{cells}</tr>')
    out.append("</table>")
    return "".join(out)


def _draft(**kwargs) -> None:
    state = st.session_state["ingest"]
    args = {**state.get("args", {}), **{k: v for k, v in kwargs.items()}}
    state["args"] = args
    state["draft"] = ui.backend().draft_ingest(ui.workspace_id(), state["path"], **args)
    state.pop("loaded", None)


def render() -> None:
    theme.eyebrow("01 / Ingest")
    st.title("Upload & *read.*")
    st.caption("Show the engine a file. It proposes how to read it; you correct what it "
               "could not work out; nothing loads until you agree.")
    be, ws = ui.backend(), ui.workspace_id()
    limits = be.limits()

    upload = st.file_uploader("CSV or Excel workbook", type=["csv", "xlsx"])
    if upload is not None:
        token = (upload.name, upload.size)
        if st.session_state.get("ingest", {}).get("token") != token:
            cap = limits.excel_max_bytes if upload.name.lower().endswith(".xlsx") \
                else limits.csv_max_bytes
            if upload.size > cap:
                st.error(f"**{upload.name} is {upload.size:,} bytes**, over this server's "
                         f"{cap:,}-byte limit for that kind of file. Nothing was sent.")
                st.markdown(limits.description)
                return
            saved = be.save_upload(ws, upload.name, upload.getvalue())
            if saved.refusal:
                ui.show_refusal(saved.refusal)
                return
            if saved.verdict == "WARN":
                st.warning(saved.message)
            st.session_state["ingest"] = {"token": token, "path": saved.path, "args": {}}
            _draft()

    state = st.session_state.get("ingest")
    if not state or "draft" not in state:
        with st.expander("What this server accepts"):
            st.markdown(limits.description)
        return

    draft: IngestDraft = state["draft"]
    if draft.refusal:
        ui.show_refusal(draft.refusal)
        return

    g = draft.grid
    if len(g.sheet_names) > 1:
        chosen = st.segmented_control("Sheet", g.sheet_names, default=g.sheet, key="ingest_sheet")
        if chosen and chosen != g.sheet:
            _draft(sheet=chosen)
            st.rerun()

    row_numbers = list(range(g.first_row_number, g.first_row_number + len(g.rows)))
    left, right = st.columns([3, 2], gap="large")
    with right:
        st.subheader("How to read it")
        with st.form("reread"):
            header_rows = st.multiselect(
                "Header rows", row_numbers, default=draft.header_rows, select_all=False,
                help="Every row that names the columns. Stacked headers take several.")
            join = st.selectbox("Join stacked headers with", HEADER_JOINS,
                                index=HEADER_JOINS.index(draft.header_join))
            if st.form_submit_button("Re-read with these choices", use_container_width=True):
                _draft(header_rows=sorted(header_rows) or None, header_join=join)
                st.rerun()
        name = st.text_input("Dataset name", value=draft.dataset_name)
        c1, c2 = st.columns(2)
        data_start = c1.number_input("Data starts at row", min_value=1,
                                     value=draft.data_start_row, step=1)
        footer = c2.number_input("Footer rows to skip", min_value=0,
                                 value=draft.footer_skip_rows, step=1)
    with left:
        st.subheader("The sheet, as it is")
        st.html(_grid_html(draft, draft.header_rows, int(data_start), int(footer)))
        st.html('<div class="aa-legend"><span><b class="h">header</b> row</span>'
                '<span><b class="s">struck</b> skipped</span>'
                + (f"<span>merged: {html.escape(', '.join(g.merged_ranges))}</span>"
                   if g.merged_ranges else "") + "</div>")

    for a in draft.assumptions:
        st.info(a)

    st.subheader("Columns")
    edited = st.data_editor(
        [{"on the sheet": c.source_name, "name": c.target_name, "type": c.dtype or INFER}
         for c in draft.columns],
        column_config={
            "on the sheet": st.column_config.TextColumn(disabled=True),
            "name": st.column_config.TextColumn(required=True),
            "type": st.column_config.SelectboxColumn(options=[INFER, *DTYPES], required=True),
        },
        hide_index=True, use_container_width=True, key=f"cols_{len(draft.columns)}_{draft.header_rows}")

    if draft.unresolved:
        st.warning("**Still a guess:** " + ", ".join(draft.unresolved))
        for q in draft.questions:
            st.markdown(f"> {q}")
    st.caption(draft.message)

    blocked = bool(draft.unresolved)
    if st.button("Confirm and load", disabled=blocked,
                 help="Answer the question above first." if blocked else None):
        spec = dict(draft.spec)
        spec.update(dataset_name=name, data_start_row=int(data_start),
                    footer_skip_rows=int(footer))
        spec["columns"] = [
            {**col, "target_name": row["name"],
             "dtype": None if row["type"] == INFER else row["type"]}
            for col, row in zip(draft.spec["columns"], edited)]
        state["loaded"] = be.confirm_ingest(ws, spec)
        st.rerun()  # the sidebar was drawn before this click; redraw it with the new dataset
    result = state.get("loaded")
    if result is not None:
        if result.refusal:
            ui.show_refusal(result.refusal)
        else:
            st.success("Loaded.")
            st.markdown(result.message)
            st.caption("Next: agree what the columns mean on **Contract**.")
