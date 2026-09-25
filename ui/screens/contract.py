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


AGG_HELP = ("sum: add them up (units). mean / median: the typical value (a price). min / max. "
            "count / count_distinct: how many. none: meaningful per row only, never combined.")
DATE_MIN = _dt.date(1900, 1, 1)
DATE_MAX = _dt.date(2100, 12, 31)


def _seed(key: str, value) -> str:
    """A widget key whose first value is `value` and whose later values are the person's."""
    if key not in st.session_state:
        st.session_state[key] = value
    return key


def _iso(value) -> str | None:
    return value.isoformat() if isinstance(value, _dt.date) else None


def form_answers(rows: list[dict], grain: str, start, end, caveats: str,
                 aggregations: dict | None = None, definitions: dict | None = None,
                 per: dict | None = None, ratios: dict | None = None,
                 rates: dict | None = None) -> dict:
    """The form as the engine's draft_contract takes it. Reading, not deciding: which of these
    is enough is the engine's call. `ratios` are the ratio-of-sums measures ticked on, each
    {name: {numerator, denominator, scale, definition}}; they are measures of their own."""
    aggregations, definitions = aggregations or {}, definitions or {}
    per, ratios = per or {}, ratios or {}
    measures = [r["column"] for r in rows if r["role"] == "measure"]
    answers = dict(
        grain=grain.strip() or None,
        primary_key=[r["column"] for r in rows if r["role"] == "key"],
        date_column=next((r["column"] for r in rows if r["role"] == "date"), None),
        measures=[r["column"] for r in rows if r["role"] == "measure"],
        dimensions=[r["column"] for r in rows if r["role"] == "dimension"],
        aggregations={r["column"]: aggregations[r["column"]] for r in rows
                      if r["role"] == "measure" and aggregations.get(r["column"])},
        measure_definitions={r["column"]: definitions[r["column"]].strip() for r in rows
                             if r["role"] == "measure"
                             and (definitions.get(r["column"]) or "").strip()},
        analysis_window_start=_iso(start), analysis_window_end=_iso(end),
        caveats=[c.strip() for c in caveats.splitlines() if c.strip()],
        measure_per={m: list(per[m]) for m in measures if per.get(m)})
    if ratios:
        answers["measures"] = measures + [n for n in ratios if n not in measures]
        answers["aggregations"].update({n: "ratio" for n in ratios})
        answers["measure_definitions"].update({n: r["definition"] for n, r in ratios.items()})
        answers["ratios"] = {n: {k: r[k] for k in ("numerator", "denominator", "scale")}
                             for n, r in ratios.items()}
    if rates:
        # A flag's rate: a helper measure reading the 0/1 column, which stays a dimension.
        answers["measures"] = answers["measures"] + [n for n in rates
                                                     if n not in answers["measures"]]
        answers["aggregations"].update({n: "mean" for n in rates})
        answers["measure_definitions"].update(
            {n: f"share of rows where {col} is 1 (true): the mean of a 0/1 column"
             for n, col in rates.items()})
        answers["measure_columns"] = dict(rates)
    return answers


#: How each verdict of contract/llm_filter.py reads under a field.
BADGE = {
    "agree": ":material/verified: checked by the data",
    "llm_only": ":material/smart_toy: from the model; the data cannot check this",
    "overruled": ":material/gavel: the data overruled the model",
    "blocked": ":material/block: blocked",
    "data": ":material/database: from the data",
    "user": ":material/person: yours",
}


def badge(draft: ContractDraft, *paths: str) -> str | None:
    """One caption line for the fields at `paths` that a model fill decided, or None."""
    parts = []
    for path in paths:
        src = draft.sources.get(path)
        if src is None:
            continue
        what = (path.rsplit(".", 1)[-1] if "." in path else "helper measure"
                if path.startswith("measures[") else path.replace("_", " "))
        said = (f" (it said {src.llm!r})" if src.status in ("overruled", "user")
                and src.llm is not None else "")
        conf = f", {src.confidence:.0%} sure" if src.confidence is not None else ""
        parts.append(f"{BADGE.get(src.status, src.status)} · *{what}*{said}{conf} — {src.reason}")
    return "  \n".join(parts) or None


def _refill(name: str) -> None:
    """Ask the model again: forget its fill and every seeded field of this dataset's form."""
    ui.backend().refill_contract(ui.workspace_id(), name)
    st.session_state.get("contract_draft", {}).pop(name, None)
    for key in [k for k in st.session_state
                if (k.startswith("c_") and f"_{name}" in k) or k == f"contract_cols_{name}"]:
        st.session_state.pop(key, None)


def _use_suggestions(name: str, draft: ContractDraft, measures: list[str]) -> None:
    """The strong suggestions into the form, on the person's click -- a callback, so it runs
    before the widgets it sets exist. Never overwrites an answer already given."""
    for m in measures:
        s = draft.suggestions.get(m)
        if s is None or s.strength != "strong" or not s.agg:
            continue
        if st.session_state.get(f"c_agg_{name}_{m}") is None:
            st.session_state[f"c_agg_{name}_{m}"] = s.agg
            if s.per and not st.session_state.get(f"c_per_{name}_{m}"):
                st.session_state[f"c_per_{name}_{m}"] = list(s.per)


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
    theme.eyebrow("03 / Agree")
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
        # The first draft of a table without a contract asks a model to fill it (one call, kept
        # for the table): 30-60 s on a free tier, measured 25/09/2026. Say so while it runs.
        with st.spinner("A model is filling in this contract; the data then checks every "
                        "choice. This happens once per table…"):
            drafts[name] = be.draft_contract(ws, name)
    draft: ContractDraft = drafts[name]
    if draft.refusal:
        ui.show_refusal(draft.refusal)
        return
    if draft.filled_by:
        # The model filled every field; the data checked each choice (webapp/autofill.py).
        note, again = st.columns([5, 1])
        note.info(f"{draft.fill_note} Change anything that is wrong: your change wins, and "
                  f"nothing is used until you confirm.", icon=":material/smart_toy:")
        again.button("Fill again", on_click=_refill, args=(name,), width="stretch",
                     help="Ask the model again. Your edits to this form are cleared.")
    elif draft.fill_note:
        st.caption(draft.fill_note)

    # Every field is keyed per dataset and seeded from the draft ONCE, so the form holds what the
    # person entered rather than whatever the latest draft echoes. For text and dates the engine
    # echoes what was typed, so this changes nothing visible today; for a column marked "ignore"
    # it does not -- the engine leaves the column out, and an unseeded table would reset its role
    # on the next check. Reasoned, not measured: AppTest cannot edit a data_editor (C99).
    st.subheader("What one row is")
    grain = st.text_input("Grain", key=_seed(f"c_grain_{name}", draft.grain or ""),
                          placeholder="one row = one order")
    if (line := badge(draft, "grain", "primary_key")):
        st.caption(line)
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
    if (line := badge(draft, "date_column", "analysis_window")):
        st.caption(line)

    st.subheader("What each column is")
    # Seeded once too: the editor rebuilds when its data changes.
    rows = st.session_state.setdefault(f"c_rows_{name}", [{
        "column": c.name, "type": c.dtype,
        "distinct": c.distinct_count, "nulls": c.null_count,
        "examples": ", ".join(c.sample_values[:3]),
        "role": _role_of(draft, c.name, c.suggested_role),
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
        })

    # Each measure's two answers as their own fields, not the last two columns of a wide grid:
    # there they sat off-screen and took a double-click to edit, and the user was told to fill
    # what they could not see (P14-D35).
    measures = [r["column"] for r in edited if r["role"] == "measure"]
    aggregations: dict[str, str | None] = {}
    definitions: dict[str, str] = {}
    per: dict[str, list[str]] = {}
    ratios: dict[str, dict] = {}
    if measures:
        st.subheader("How each measure adds up")
        st.caption("For every measure, say how it may be combined and what it means. There is no "
                   "default on purpose: summing a price or a rate gives a number that means "
                   "nothing. **none** = per row only, never combined. Under each, how the engine "
                   "reads it and why.")
        strong = [m for m in measures if (s := draft.suggestions.get(m)) is not None
                  and s.strength == "strong" and s.agg]
        if strong and not draft.filled_by:
            st.button(f"Use the engine's {len(strong)} strong suggestion(s)", type="secondary",
                      on_click=_use_suggestions, args=(name, draft, measures),
                      help="Fills only the aggregations the data settles, and only where you "
                           "have not chosen. Definitions stay yours to write.")
        # Any column, not only dimensions: a unit the engine names must be an option, or the
        # multiselect refuses the suggestion it was given.
        units = [r["column"] for r in edited]
        for m in measures:
            a, u, d = st.columns([1, 1, 2])
            aggregations[m] = a.selectbox(
                f"{m} — how it combines", AGGREGATIONS, index=None, placeholder="choose…",
                key=_seed(f"c_agg_{name}_{m}", draft.aggregations.get(m)),
                help=AGG_HELP)
            per[m] = u.multiselect(
                f"{m} — one value per", [c for c in units if c != m],
                key=_seed(f"c_per_{name}_{m}", list(draft.measure_per.get(m, []))),
                help="A value repeated on every line of an order (a fee, a rating) is one value "
                     "per order: counted once each, not once per line.")
            definitions[m] = d.text_input(
                f"{m} — what it means", placeholder="e.g. units x unit_price, before tax",
                key=_seed(f"c_def_{name}_{m}", draft.measure_definitions.get(m, "")))
            s = draft.suggestions.get(m)
            line = badge(draft, f"measures[{m}].agg", f"measures[{m}].per",
                         f"measures[{m}].definition")
            if line:
                st.caption(line)
            if s is not None:
                shown = f"{s.agg}" + (f" per {' + '.join(s.per)}" if s.per else "")
                if line:
                    pass  # the model filled it and the data checked it: the badge says why
                elif s.strength == "strong":
                    st.caption(f":material/lightbulb: Engine: **{shown}** — {s.reason}")
                else:
                    st.caption(f":material/help: {s.question or s.reason}")
                if s.ratio:
                    r = s.ratio
                    if st.checkbox(f"Also add **{r['name']}**: {r['definition']}",
                                   key=_seed(f"c_ratio_{name}_{r['name']}",
                                             r["name"] in draft.ratios)):
                        ratios[r["name"]] = r
    rates: dict[str, str] = {}
    offered = {n: sg for n, sg in draft.suggestions.items() if sg.rule == "F1" and n not in measures
               and n.endswith("_rate") and n[:-5] in {r["column"] for r in edited}}
    if offered:
        st.subheader("Rates from 0/1 columns")
        st.caption("A column of 0 and 1 (or true and false) stays a dimension to group by; its "
                   "rate -- the share of rows that are 1 -- is a measure beside it.")
        for n, sg in offered.items():
            col = n[:-5]
            if st.checkbox(f"Add **{n}**: {sg.reason}",
                           key=_seed(f"c_rate_{name}_{n}", n in draft.measure_columns)):
                rates[n] = col
            if (line := badge(draft, f"measures[{n}]")):
                st.caption(line)
    if draft.measured_caveats:
        st.subheader("What the engine counted")
        st.caption("Counted from the table, not typed. Every result carries these.")
        st.markdown("\n".join(f"- {c}" for c in draft.measured_caveats))
    caveats = st.text_area("Your caveats (one per line)",
                           key=_seed(f"c_caveats_{name}", "\n".join(draft.caveats)),
                           help="What the data cannot show. Results print these as declared, "
                                "not measured -- a count here is checked against the table.")

    answers = form_answers(edited, grain, start, end, caveats, aggregations, definitions,
                           per, ratios, rates)
    left, right = st.columns([1, 1])
    check = left.button("Check what's missing", type="secondary", width="stretch")
    confirm = right.button("Confirm contract", width="stretch")
    if check or confirm:
        fresh, result = submit(be, ws, name, answers, confirm=confirm)
        # Kept after a confirm too. It used to be dropped, the screen re-drafted with no answers,
        # and "Still needed: Grain; ..." appeared under "confirmed" (measured in AppTest, P14-D35).
        drafts[name] = fresh
        if result is not None:
            st.session_state["contract_result"] = (name, result)
        else:
            st.session_state.pop("contract_result", None)
        st.rerun()  # redraw: the sidebar shows the new stage, the list below the fresh check

    # A caveat the table contradicts is said where it cannot be missed: collapsed under "What the
    # data showed", 3,470 was confirmed twice where the table held 3,471 and 3,473 (recheck).
    for e in draft.evidence:
        if e.startswith("CAVEAT DIFFERS"):
            st.warning(e, icon=":material/rule:")
    if draft.evidence:
        with st.expander("What the data showed"):
            for e in draft.evidence:
                st.markdown(f"- {e}")
    for q in draft.questions:
        st.markdown(f"> {q}")
    if draft.provisional:
        st.warning("**Still needed before this can be confirmed:** "
                   + "; ".join(plain(item) for item in draft.provisional)
                   + ("\n\nMeasures are answered under *How each measure adds up*, above."
                      if any(item.startswith("measures[") or "aggregation" in item
                             or "definition" in item for item in draft.provisional) else ""))
    st.caption(draft.message)

    shown = st.session_state.get("contract_result")
    if shown and shown[0] == name:
        if shown[1].refusal:
            ui.show_refusal(shown[1].refusal)
        else:
            st.success(shown[1].message)
            st.caption("Next: ask a question on **Ask**.")
