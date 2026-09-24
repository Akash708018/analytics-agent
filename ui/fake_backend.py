"""An in-memory Backend, so every screen can be built and tested with no engine, no network and
no database. It implements webapp/contract.Backend exactly; `ui/backend.py` swaps it for the real
one with ANALYTICS_UI_BACKEND=real.

It is deliberately deterministic -- ids from a counter, data fixed -- so tests assert exact values.
It behaves like the engine where the UI depends on the behaviour: drafts are PROVISIONAL until
answered, confirming a provisional draft is refused with a NEXT STEP, a subset load carries its
warning, and a chart comes with the engine-style description of what was drawn.
"""

from __future__ import annotations

import datetime as _dt
import struct
import threading
import zlib
from dataclasses import dataclass, field, replace

from analytics_agent.webapp.contract import (
    ActionResult, Artifact, ChatTurn, CleaningProposal, CleaningStep, ColumnDraft, ContractColumn, ContractDraft,
    DatasetSummary, GridPreview, IngestDraft, Limits, Refusal, ToolCall, UploadResult,
)

_MIB = 1024 * 1024
CSV_MAX = 2560 * _MIB
EXCEL_MAX = 100 * _MIB
PG_MAX_ROWS = 750_000

SUBSET_NOTE = (
    "Loaded as a subset: 1,000 of 1,000,163 rows of olist:public.geolocation, copied with "
    "limit=1000. Every figure describes those rows, not the whole table. A limit keeps whichever "
    "rows the database returned first -- not a random sample -- so shares and distinct counts "
    "can be far from the table's."
)

# The messy sheet every upload previews as: a label spanning three columns over their own
# sub-headers, ten rows of data, and a note underneath.
_GRID: list[list[str | None]] = [
    ["Region", "2024 Sales", None, None],
    [None, "Units", "Revenue", "Unit price"],
    ["North", "120", "12,600.00", "105.00"],
    ["South", "95", "9,215.00", "97.00"],
    ["East", "143", "15,873.00", "111.00"],
    ["West", "88", "8,096.00", "92.00"],
    ["North", "131", "13,886.00", "106.00"],
    ["South", "102", "9,996.00", "98.00"],
    ["East", "150", "16,800.00", "112.00"],
    ["West", "79", "7,189.00", "91.00"],
    ["North", "117", "12,285.00", "105.00"],
    ["South", "99", "9,702.00", "98.00"],
    ["Source: internal ledger, figures unaudited", None, None, None],
]
_TOP = ["Region", "2024 Sales", "2024 Sales", "2024 Sales"]  # the merged label, filled
_BOTTOM = ["Region", "Units", "Revenue", "Unit price"]
_TYPES = ["VARCHAR", "BIGINT", "DOUBLE", "DOUBLE"]


def _refusal(reason: str, what: str, why: str, next_step: str) -> Refusal:
    text = f"BLOCKED: {what}\nWHY: {why}\nNEXT STEP: call {next_step}\n\nreason: {reason}"
    return Refusal(reason=reason, what=what, why=why, next_step=next_step, text=text)


def _identifier(name: str) -> str:
    out = "".join(c.lower() if c.isalnum() else "_" for c in name).strip("_")
    while "__" in out:
        out = out.replace("__", "_")
    if not out or not out[0].isalpha():
        out = f"c_{out}"
    return out


def _png(values: list[float], width: int = 360, height: int = 200) -> bytes:
    """A small bar chart as a real PNG, in pure Python (zlib + struct), in the portfolio's
    palette: sandstone paper, terracotta, copper, sunset and sand bars."""
    bg, bars = (251, 244, 233), [(157, 71, 44), (162, 89, 52), (200, 121, 72), (215, 162, 121)]
    top = max(values) or 1.0
    slot = width // max(len(values), 1)
    rows = []
    for y in range(height):
        row = bytearray([0])
        for x in range(width):
            i, inside = x // slot, slot * 0.18 < x % slot < slot * 0.82
            level = height - 14 - int((values[i] / top) * (height - 34)) if i < len(values) else height
            row += bytes(bars[i % len(bars)] if inside and level <= y < height - 14 else bg)
        rows.append(bytes(row))

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data))

    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header)
            + chunk(b"IDAT", zlib.compress(b"".join(rows), 9)) + chunk(b"IEND", b""))


@dataclass
class _Workspace:
    uploads: dict[str, bytes] = field(default_factory=dict)
    datasets: dict[str, DatasetSummary] = field(default_factory=dict)
    columns: dict[str, list[ContractColumn]] = field(default_factory=dict)
    artifacts: list[tuple[Artifact, bytes]] = field(default_factory=list)
    cleaned: dict[str, list[str]] = field(default_factory=dict)  # dataset -> applied step ids


class FakeBackend:
    """Implements analytics_agent.webapp.contract.Backend on in-memory data."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counter = 0
        self._spaces: dict[str, _Workspace] = {}
        self._clock = 0

    # --- helpers --------------------------------------------------------------------------

    def _ws(self, workspace_id: str) -> _Workspace:
        if workspace_id not in self._spaces:
            space = _Workspace()
            space.datasets["geolocation"] = DatasetSummary(
                name="geolocation", rows=1000, columns=5,
                source="postgres - olist:public.geolocation", loaded="loaded 2 hours ago",
                stage="contract v1, ready",
                next_step='compute_analysis(dataset_name="geolocation", analysis_type="summary_stats")',
                notes=[SUBSET_NOTE])
            space.columns["geolocation"] = [
                ContractColumn("geolocation_zip_code_prefix", "INTEGER", "dimension", 812, 0,
                               ["1037", "1046", "1041"]),
                ContractColumn("geolocation_lat", "DOUBLE", "measure", 998, 0, ["-23.54", "-23.55"]),
                ContractColumn("geolocation_lng", "DOUBLE", "measure", 997, 0, ["-46.63", "-46.64"]),
                ContractColumn("geolocation_city", "VARCHAR", "dimension", 3, 0, ["sao paulo"]),
                ContractColumn("geolocation_state", "VARCHAR", "dimension", 1, 0, ["SP"]),
            ]
            self._spaces[workspace_id] = space
        return self._spaces[workspace_id]

    def _now(self) -> str:
        self._clock += 1
        return (_dt.datetime(2026, 9, 22, 18, 0) + _dt.timedelta(minutes=self._clock)).isoformat()

    def _artifact(self, space: _Workspace, kind: str, name: str, title: str, data: bytes,
                  description: str) -> Artifact:
        art = Artifact(kind=kind, path=f"{kind}s/{name}", title=title, created=self._now(),
                       description=description)
        space.artifacts.insert(0, (art, data))
        return art

    # --- Backend ---------------------------------------------------------------------------

    def new_workspace_id(self) -> str:
        with self._lock:
            self._counter += 1
            return f"ws_{self._counter:012x}"

    def limits(self) -> Limits:
        return Limits(
            csv_max_bytes=CSV_MAX, excel_max_bytes=EXCEL_MAX, postgres_max_rows=PG_MAX_ROWS,
            description=("| source | refused above |\n| --- | --- |\n| CSV | 2.5 GiB |\n"
                         "| Excel | 100 MiB |\n| Postgres copy | 750,000 rows |"))

    def save_upload(self, workspace_id: str, filename: str, data: bytes) -> UploadResult:
        lower = filename.lower()
        if not (lower.endswith(".csv") or lower.endswith(".xlsx")):
            r = _refusal("UNSUPPORTED_FILE", f"{filename} is not a CSV or an .xlsx workbook.",
                         "only those two formats have a loader.",
                         'save_upload(filename="<a .csv or .xlsx file>")')
            return UploadResult(verdict="REFUSE", message=r.what, refusal=r)
        cap = EXCEL_MAX if lower.endswith(".xlsx") else CSV_MAX
        if len(data) > cap:
            r = _refusal("SIZE_GATE", f"{filename} is {len(data):,} bytes, over the {cap:,} limit.",
                         "a file that size would not fit in memory on this machine.",
                         'save_upload(filename="<a smaller extract>")')
            return UploadResult(verdict="REFUSE", message=r.what, refusal=r)
        with self._lock:
            self._ws(workspace_id).uploads[filename] = data
        verdict = "WARN" if len(data) > cap // 2 else "OK"
        message = (f"{filename} is large ({len(data):,} bytes); loading will take a while."
                   if verdict == "WARN" else f"{filename} saved.")
        return UploadResult(verdict=verdict, message=message, path=f"uploads/{filename}")

    def draft_ingest(self, workspace_id, path, *, dataset_name=None, sheet=None, header_rows=None,
                     header_join=None, authorised_fill=False) -> IngestDraft:
        with self._lock:
            known = path.split("/", 1)[-1] in self._ws(workspace_id).uploads
        grid = GridPreview(rows=[list(r) for r in _GRID], first_row_number=1,
                           sheet=sheet or "Sheet1", sheet_names=["Sheet1", "Notes"],
                           merged_ranges=["B1:D1"])
        if not known:
            r = _refusal("FILE_NOT_FOUND", f"there is no uploaded file at {path}.",
                         "a draft reads the file, and this workspace holds no such upload.",
                         "save_upload(...) first")
            return IngestDraft(spec={}, grid=grid, dataset_name="", header_rows=[],
                               data_start_row=0, footer_skip_rows=0, header_join="space",
                               columns=[], message=r.what, refusal=r)

        join = header_join or "space"
        rows = list(header_rows) if header_rows else [1]
        name = dataset_name or _identifier(path.rsplit("/", 1)[-1].rsplit(".", 1)[0])
        names = []
        for top, bottom in zip(_TOP, _BOTTOM):
            if rows == [1]:
                names.append(top)
            elif join == "bottom_only" or top == bottom:
                names.append(bottom)
            elif join == "top_only":
                names.append(top)
            else:
                names.append(f"{top}{'_' if join == 'underscore' else ' '}{bottom}")
        columns = [ColumnDraft(n, _identifier(n), None) for n in names]
        unresolved = [] if header_rows else ["header_rows"]
        questions = ([] if header_rows else [
            "Row 2 sits under the merged label '2024 Sales' (B1:D1) and holds no numbers. "
            "Is it a second header row? If so, choose rows 1 and 2 as the header."])
        data_start = max(rows) + 1
        spec = {
            "path": path, "source_type": "excel" if path.endswith(".xlsx") else "csv",
            "dataset_name": name, "sheet": grid.sheet, "header_rows": rows,
            "data_start_row": data_start, "footer_skip_rows": 1, "header_join": join,
            "na_values": None, "delimiter": None, "authorised_fill": authorised_fill,
            "columns": [{"source_name": c.source_name, "target_name": c.target_name,
                         "dtype": c.dtype} for c in columns],
            "assumptions": ["Row 13 reads as a note, not data, so it is skipped."],
            "questions": questions, "unresolved": unresolved,
        }
        return IngestDraft(
            spec=spec, grid=grid, dataset_name=name, header_rows=rows,
            data_start_row=data_start, footer_skip_rows=1, header_join=join, columns=columns,
            assumptions=list(spec["assumptions"]), questions=questions, unresolved=unresolved,
            message="PROVISIONAL -- answer the question below." if unresolved else
                    "Ready to load: every field was read from the file or answered by you.")

    def confirm_ingest(self, workspace_id: str, spec: dict) -> ActionResult:
        if spec.get("unresolved"):
            r = _refusal("SPEC_PROVISIONAL", "this Ingest Spec is still PROVISIONAL.",
                         f"these fields are a guess, not a reading: {', '.join(spec['unresolved'])}.",
                         f'draft_ingest(path="{spec.get("path", "")}", header_rows=[...])')
            return ActionResult(ok=False, message=r.what, refusal=r)
        name = spec["dataset_name"]
        cols = spec["columns"]
        with self._lock:
            space = self._ws(workspace_id)
            space.datasets[name] = DatasetSummary(
                name=name, rows=10, columns=len(cols), source=f"upload - {spec['path']}",
                loaded="loaded just now", stage="loaded, no contract",
                next_step=f'propose_dataset_contract(dataset_name="{name}")')
            space.columns[name] = [
                ContractColumn(c["target_name"], c.get("dtype") or t,
                               "dimension" if t == "VARCHAR" else "measure",
                               4 if t == "VARCHAR" else 10, 0,
                               [str(r[i]) for r in _GRID[2:5]])
                for i, (c, t) in enumerate(zip(cols, _TYPES))]
        lines = "\n".join(f"| {c['target_name']} | {c.get('dtype') or t} |"
                          for c, t in zip(cols, _TYPES))
        return ActionResult(ok=True, message=(f"Loaded **{name}**: 10 rows, {len(cols)} columns."
                                              f"\n\n| column | type |\n| --- | --- |\n{lines}"))

    def list_datasets(self, workspace_id: str) -> list[DatasetSummary]:
        with self._lock:
            return list(reversed(list(self._ws(workspace_id).datasets.values())))

    def draft_contract(self, workspace_id, dataset_name, *, grain=None, primary_key=None,
                       date_column=None, measures=None, dimensions=None, aggregations=None,
                       measure_definitions=None, analysis_window_start=None,
                       analysis_window_end=None, caveats=None) -> ContractDraft:
        with self._lock:
            space = self._ws(workspace_id)
            columns = space.columns.get(dataset_name)
        if columns is None:
            r = _refusal("DATASET_NOT_LOADED", f"there is no dataset called '{dataset_name}'.",
                         "a contract describes a loaded table.", "list_datasets()")
            return ContractDraft(dataset_name, None, [], None, [], [], {}, {}, None, None, [], [],
                                 message=r.what, refusal=r)
        if measures is None:
            measures = [c.name for c in columns if c.suggested_role == "measure"]
        if dimensions is None:
            dimensions = [c.name for c in columns if c.suggested_role == "dimension"]
        aggregations = dict(aggregations or {})
        definitions = dict(measure_definitions or {})
        provisional = []
        if not grain:
            provisional.append("grain")
        for m in measures:
            if m not in aggregations:
                provisional.append(f"aggregation for {m}")
            if not definitions.get(m):
                provisional.append(f"definition for {m}")
        if not (analysis_window_start and analysis_window_end):
            provisional.append("analysis window")
        return ContractDraft(
            dataset_name=dataset_name, grain=grain, primary_key=list(primary_key or []),
            date_column=date_column, measures=list(measures), dimensions=list(dimensions),
            aggregations=aggregations, measure_definitions=definitions,
            analysis_window_start=analysis_window_start, analysis_window_end=analysis_window_end,
            caveats=list(caveats or []), columns=columns, provisional=provisional,
            questions=[f"What does one row of {dataset_name} stand for?"] if not grain else [],
            evidence=[f"{c.name} holds {c.distinct_count} distinct value(s)" for c in columns
                      if c.distinct_count is not None],
            message="PROVISIONAL -- answer what is missing." if provisional else
                    "Ready to confirm.")

    def confirm_contract(self, workspace_id: str, draft: ContractDraft) -> ActionResult:
        if draft.provisional:
            r = _refusal("CONTRACT_PROVISIONAL", "this contract is still PROVISIONAL.",
                         f"still missing: {', '.join(draft.provisional)}.",
                         f'draft_contract(dataset_name="{draft.dataset_name}", ...)')
            return ActionResult(ok=False, message=r.what, refusal=r)
        with self._lock:
            space = self._ws(workspace_id)
            old = space.datasets[draft.dataset_name]
            version = int(old.stage.split("v")[1].split(",")[0]) + 1 if "contract v" in old.stage else 1
            space.datasets[draft.dataset_name] = replace(
                old, stage=f"contract v{version}, ready",
                next_step=(f'compute_analysis(dataset_name="{draft.dataset_name}", '
                           f'analysis_type="summary_stats")'))
        return ActionResult(ok=True, message=(
            f"Contract **v{version}** for **{draft.dataset_name}** confirmed: {draft.grain}. "
            f"Measures: {', '.join(draft.measures) or 'none'}."))

    # Two steps for any dataset, one of each kind the screen must tell apart: a lossless one the
    # engine would suggest, and a lossy one that is the person's call.
    _STEPS = (
        CleaningStep("C001", "TRIM_WHITESPACE", "region", "trim spaces around region",
                     'UPDATE "{t}" SET "region" = trim("region")', 3),
        CleaningStep("C002", "NORMALISE_CASE", "region", "fold region to one spelling per value",
                     'UPDATE "{t}" SET "region" = initcap("region")', 2, values_lost=1,
                     loss_unit="distinct value", sample=["north"], lossy=True),
    )

    def propose_cleaning(self, workspace_id: str, dataset_name: str) -> CleaningProposal:
        with self._lock:
            space = self._ws(workspace_id)
            if dataset_name not in space.datasets:
                r = _refusal("DATASET_NOT_LOADED", f"there is no dataset called '{dataset_name}'.",
                             "cleaning rebuilds a loaded table.", "list_datasets()")
                return CleaningProposal(dataset_name, 0, [], message=r.what, refusal=r)
            done = space.cleaned.get(dataset_name, [])
            rows = space.datasets[dataset_name].rows
        steps = [replace(st, sql=st.sql.format(t=dataset_name), suggested=not st.lossy)
                 for st in self._STEPS if st.action_id not in done]
        if not steps:
            return CleaningProposal(dataset_name, rows, [],
                                    message=f"Nothing to clean in {dataset_name}.")
        return CleaningProposal(dataset_name, rows, steps, message=(
            f"{len(steps)} change(s) proposed for {dataset_name}. Nothing has been changed."))

    def apply_cleaning(self, workspace_id: str, dataset_name: str,
                       approved_action_ids: list[str]) -> ActionResult:
        if not approved_action_ids:
            r = _refusal("NOTHING_APPROVED", "no action ids were approved.",
                         "nothing is run unless it is named.",
                         f'apply_cleaning_plan(dataset_name="{dataset_name}", '
                         f'approved_action_ids=["C001"])')
            return ActionResult(ok=False, message=r.what, refusal=r)
        with self._lock:
            space = self._ws(workspace_id)
            done = space.cleaned.setdefault(dataset_name, [])
            known = {st.action_id for st in self._STEPS} - set(done)
            unknown = [i for i in approved_action_ids if i not in known]
            if unknown:
                r = _refusal("ACTION_NOT_IN_PLAN",
                             f"{', '.join(unknown)} is not in the plan for {dataset_name}.",
                             "an id that is not in the plan cannot be run.",
                             f'propose_cleaning_plan(dataset_name="{dataset_name}")')
                return ActionResult(ok=False, message=r.what, refusal=r)
            done.extend(approved_action_ids)
        return ActionResult(ok=True, message=(
            f"Applied {', '.join(approved_action_ids)} to {dataset_name}; row count unchanged."))

    def chat(self, workspace_id: str, history: list[dict], message: str) -> ChatTurn:
        text = message.lower()
        with self._lock:
            space = self._ws(workspace_id)
            if "fail" in text:
                return ChatTurn(reply="", error="The model provider did not answer in time "
                                "(fake). Nothing in your workspace changed; try again.")
            if "chart" in text:
                values = [12600.0, 9215.0, 15873.0, 8096.0]
                art = self._artifact(
                    space, "chart", "revenue_by_region.png", "Revenue by region",
                    _png(values),
                    "bar chart of revenue (sum) across 4 groups; 4 of 4 point(s) drawn. "
                    "lowest 8,096 at West, highest 15,873 at East; first 12,600 (North), "
                    "last 8,096 (West).")
                return ChatTurn(
                    reply="Here is **revenue by region**. East leads at 15,873; West is lowest "
                          "at 8,096.",
                    tool_calls=[ToolCall("render_chart", {"analysis_type": "group_compare",
                                         "chart": "bar", "dimension": "region",
                                         "measure": "revenue", "y": "total"}, art.description)],
                    artifacts=[art])
            if "trend" in text:
                return ChatTurn(
                    reply="Revenue rose from 21,815 in January to 26,873 in March. **One month "
                          "holds no rows** (February) and is shown blank, not zero.",
                    tool_calls=[
                        ToolCall("compute_analysis", {"analysis_type": "trend"},
                                 "BLOCKED: trend needs a measure.\nNEXT STEP: call "
                                 'compute_analysis(analysis_type="trend", measure="revenue")',
                                 refused=True),
                        ToolCall("compute_analysis", {"analysis_type": "trend",
                                 "measure": "revenue", "grain": "month"},
                                 "3 periods; 1 month(s) hold no rows: 2024-02.")])
            if "report" in text:
                body = ("# Report\n\n## The question asked\n\n" + message +
                        "\n\n## Findings\n\n- East leads revenue at 15,873.\n")
                art = self._artifact(space, "report", "report.md", "Report", body.encode(),
                                     "9 sections; 2 had nothing to report.")
                return ChatTurn(reply="The report is written -- nine sections, two of them "
                                      "empty because nothing was cleaned or validated.",
                                tool_calls=[ToolCall("build_report", {"question": message},
                                                     art.description)],
                                artifacts=[art])
        return ChatTurn(reply="I can load a file, agree a contract with you, and then answer "
                              "questions with analyses, charts and a report. Try *show me a "
                              "chart*, *what's the trend?* or *write the report*.")

    def list_artifacts(self, workspace_id: str) -> list[Artifact]:
        with self._lock:
            return [a for a, _ in self._ws(workspace_id).artifacts]

    def read_artifact(self, workspace_id: str, path: str) -> bytes:
        with self._lock:
            for art, data in self._ws(workspace_id).artifacts:
                if art.path == path:
                    return data
        raise ValueError(f"{path} is not an artifact of this workspace")

    def reset_workspace(self, workspace_id: str) -> ActionResult:
        with self._lock:
            self._spaces.pop(workspace_id, None)
            self._spaces[workspace_id] = _Workspace()
        return ActionResult(ok=True, message="The workspace is empty.")
