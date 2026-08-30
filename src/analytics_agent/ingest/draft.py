"""
Path in, draft spec out.

`preview.py` answers "given these rows, where is the header". This answers
"given this path, what is the whole proposal" -- which sheet, which merges,
which tail, rendered into something a person can read and correct.

It exists so `server.py` keeps no logic. A tool should call one function and
return what it gets back.

Nothing here loads data. The draft is returned as JSON alongside its prose, and
`confirm_ingest_spec` takes that JSON back. That is deliberate: it means the
spec the user confirms is the spec that runs, that they can edit any field
before confirming, and that no draft is held in server memory between calls.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from analytics_agent.config import CSV_PREVIEW_LINES, EXCEL_PREVIEW_ROWS
from analytics_agent.ingest import csv_loader, excel, merges, preview, sizegate
from analytics_agent.ingest.csv_loader import LoadRefused
from analytics_agent.ingest.spec import IngestSpec

# Rows read from the end of a sheet when looking for a footer.
TAIL_ROWS = preview.FOOTER_SCAN_ROWS


@dataclass
class Draft:
    spec: IngestSpec | None
    guess: preview.HeaderGuess
    pivot: preview.PivotVerdict
    source_type: str
    sheet: str | None
    sheets: list[str]

    @property
    def needs_answer(self) -> bool:
        return self.spec is None or not self.spec.is_confirmable


def _default_dataset_name(path: Path) -> str:
    stem = "".join(c if c.isalnum() else "_" for c in path.stem).strip("_")
    stem = stem.lower() or "dataset"
    if stem[0].isdigit():
        stem = f"d_{stem}"
    return stem[:63]


def _excel_tail(path: Path, sheet: str) -> list:
    """The last TAIL_ROWS rows of a sheet, for footer detection."""
    from openpyxl import load_workbook

    wb = load_workbook(path, read_only=True)
    try:
        ws = wb[sheet]
        last = ws.max_row or 0
        if not last:
            return []
        start = max(1, last - TAIL_ROWS + 1)
        return [list(r) for r in ws.iter_rows(min_row=start, values_only=True)]
    finally:
        wb.close()


def draft_for_path(
    path: str | Path,
    dataset_name: str | None = None,
    sheet: str | None = None,
    header_rows: list[int] | None = None,
    header_join: str | None = None,
    authorised_fill: bool = False,
) -> Draft:
    """
    Build a draft spec for one file. Reads only the top and tail.

    `header_rows`, `header_join` and `authorised_fill` carry a person's answer
    back in. Supplying `header_rows` settles an ambiguous file, which is the
    only way `unresolved` gets cleared.
    """
    p = Path(path)
    if not p.exists():
        raise LoadRefused(
            f"BLOCKED: no file at {path}.\n"
            f"NEXT STEP: check the path. Relative paths resolve against the "
            f"server's working directory, not your shell's, so an absolute "
            f"path is safer."
        )

    gate = sizegate.check_file(p)
    if not gate.allowed:
        raise LoadRefused(gate.message)

    name = dataset_name or _default_dataset_name(p)
    source_type = sizegate.source_type_for(p)

    if source_type == "excel":
        sheets = excel.list_sheets(p)
        chosen = sheet or merges.active_sheet_name(str(p))
        if chosen not in sheets:
            raise LoadRefused(
                f"BLOCKED: {p.name} has no sheet called {chosen!r}.\n"
                f"Sheets present: {', '.join(sheets)}\n"
                f"NEXT STEP: pass one of those names."
            )
        rows = excel.preview_rows(p, chosen, n=EXCEL_PREVIEW_ROWS)
        spec, guess, pivot = preview.draft_spec(
            rows,
            path=str(p),
            source_type="excel",
            dataset_name=name,
            sheet=chosen,
            merge_refs=merges.merged_ranges(str(p), chosen),
            tail_rows=_excel_tail(p, chosen),
            header_rows=header_rows,
            header_join=header_join,
        )
        return Draft(spec, guess, pivot, "excel", chosen, sheets)

    lines = csv_loader.preview_lines(p, n=CSV_PREVIEW_LINES)
    rows = preview.parse_csv_preview(lines)
    spec, guess, pivot = preview.draft_spec(
        rows, path=str(p), source_type="csv", dataset_name=name,
        header_rows=header_rows, header_join=header_join,
        authorised_fill=authorised_fill,
    )
    return Draft(spec, guess, pivot, "csv", None, [])


def render(draft: Draft) -> str:
    """
    The draft as the user reads it.

    Ordered so the questions come last: whatever is at the bottom of a tool
    result is what gets answered.
    """
    out: list[str] = []

    if draft.source_type == "excel" and len(draft.sheets) > 1:
        others = [s for s in draft.sheets if s != draft.sheet]
        out.append(
            f"Reading sheet '{draft.sheet}'. Also in this workbook: "
            f"{', '.join(others)}."
        )
        out.append("")

    if draft.spec is None:
        out.append("No spec proposed -- this file is ambiguous.")
        out.append("")
        out.append("What was worked out:")
        out += [f"  - {r}" for r in draft.guess.reasons]
        out.append("")
        out.append("What has to be settled first:")
        out += [f"  - {q}" for q in draft.guess.questions]
        out.append("")
        out.append(
            "Answer and I will build the spec. Nothing has been loaded and "
            "nothing has been assumed."
        )
        return "\n".join(out)

    # to_text already prints the assumptions. Printing them again here read
    # as two different lists on the first run, which is worse than terse.
    out.append(draft.spec.to_text())
    out.append("")
    out.append(f"Confidence: {draft.guess.confidence}")
    if draft.spec.assumptions:
        out.append("Every assumption above is yours to overrule.")

    if draft.spec.unresolved:
        out.append("")
        out.append("THIS SPEC CANNOT BE LOADED AS IT STANDS.")
        out.append(
            f"{', '.join(draft.spec.unresolved)} below is a default, not a "
            f"reading of the file. What is shown is what a load WOULD do."
        )
        out.append("")
        out.append("Put these to the user:")
        out += [f"  - {q}" for q in draft.spec.questions]
        out.append("")
        out.append(
            "Then call propose_ingest_spec again with their answer -- "
            "header_rows=[...], and header_join or authorised_fill if "
            "relevant. It returns a spec with nothing outstanding, and that "
            "one can be confirmed."
        )
        return "\n".join(out)

    # spec.questions, NOT guess.questions. The guess describes what the FILE
    # could settle and never changes; the spec describes what is still
    # outstanding after a person has spoken. Reading the guess here printed
    # "Open questions" at someone who had just answered them.
    if draft.spec.questions:
        out.append("")
        out.append("Open questions:")
        out += [f"  - {q}" for q in draft.spec.questions]

    out.append("")
    out.append(
        "Nothing is loaded yet. To load exactly this, pass the JSON below back "
        "to confirm_ingest_spec. To change something, edit a field first -- "
        "the spec that comes back is the spec that runs."
    )
    out.append("")
    out.append("```json")
    out.append(draft.spec.model_dump_json(indent=2))
    out.append("```")
    return "\n".join(out)


def spec_from_json(spec_json: str) -> IngestSpec:
    """Parse a confirmed spec, turning any validation error into a refusal."""
    text = spec_json.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
        text = text.rsplit("```", 1)[0]
    try:
        return IngestSpec.model_validate_json(text)
    except Exception as exc:
        raise LoadRefused(
            f"BLOCKED: that is not a usable ingest spec.\n"
            f"Detail: {exc}\n"
            f"NEXT STEP: call propose_ingest_spec to get a valid one, edit the "
            f"fields you want to change, and pass the whole JSON object back."
        ) from exc


__all__ = ["Draft", "draft_for_path", "render", "spec_from_json"]
