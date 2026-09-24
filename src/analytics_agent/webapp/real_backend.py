"""The engine behind the Track B UI: webapp/contract.Backend, implemented in-process.

Why in-process rather than MCP over HTTP (Phase 14 Step 3): every MCP tool returns text, and the
screens need structure -- grid cells, columns, which fields are still a guess. Parsing text is what
the contract forbids the UI, so the backend calls the engine's own functions and hands back the
contract's dataclasses. Tools that only exist as text-returning calls (loading a confirmed spec,
storing a contract) are called exactly as the MCP layer calls them, and their refusals converted
once, here.

Concurrency, from Phase 14 Step 1's measurements: two workspaces on two threads are independent
(P14-D1, D5); two calls on ONE workspace must not overlap (P14-D2, D6). So every engine call runs
under that workspace's lock, and different workspaces never wait for each other.

Everything the UI sends is untrusted: file names keep only their base name, paths must lie inside
the workspace's own directories, and workspace ids are validated as the path segments they are.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import re
import secrets
import threading
import time
from collections import defaultdict
from contextlib import contextmanager
from pathlib import Path

from analytics_agent import server, state, workspace
from analytics_agent.charts.render import CHARTS_DIRNAME
from analytics_agent.config import (
    DEFAULT_WORKSPACE_ID, SIZE_GATES, WORKSPACE_ROOT, describe_size_gates, validate_workspace_id,
)
from analytics_agent.clean import plan as clean_plan
from analytics_agent.clean import tools as clean_tools
from analytics_agent.contract import ContractRefused
from analytics_agent.contract import tools as contract_tools
from analytics_agent.contract.propose import propose_contract
from analytics_agent.contract.refusals import reason_of
from analytics_agent.ingest import csv_loader, excel, merges, preview, sizegate
from analytics_agent.ingest import draft as ingest_draft
from analytics_agent.ingest.csv_loader import LoadRefused
from analytics_agent.ingest.postgres import ROW_REFUSE
from analytics_agent.report.assemble import REPORTS_DIRNAME
from analytics_agent.util import db
from analytics_agent.util.results import RESULTS_DIRNAME
from analytics_agent.analysis import runs as analysis_runs

from .contract import (
    ActionResult, Artifact, ChatTurn, CleaningProposal, CleaningStep, ColumnDraft,
    ContractColumn, ContractDraft,
    DatasetSummary, GridPreview, IngestDraft, Limits, Refusal, UploadResult,
)

UPLOADS_DIRNAME = "uploads"
_ALLOWED = (".csv", ".xlsx")
_SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._ -]{0,120}$")
_ARTIFACT_DIRS = {CHARTS_DIRNAME: "chart", REPORTS_DIRNAME: "report", RESULTS_DIRNAME: "result"}
_GRID_ROWS = 40  # rows of the sheet shown in the editor
DEFAULT_TTL_HOURS = 72  # a web workspace unused this long is removed (P14-O1)
SWEEP_EVERY = 3600  # seconds between sweeps triggered by new visitors


def refusal_from_text(text: str) -> Refusal:
    """Any engine refusal as the contract's Refusal.

    Two shapes exist: contract.refusals.Refusal.to_text() (BLOCKED / WHY / ... / NEXT STEP: call
    X / reason: CODE) and the older LoadRefused messages (BLOCKED / WHY? / NEXT STEP: prose). The
    fields are read from their line prefixes; a missing one is left empty rather than invented.
    """
    what = why = step = ""
    for line in text.splitlines():
        if line.startswith("BLOCKED:"):
            what = what or line[len("BLOCKED:"):].strip()
        elif line.startswith("WHY:"):
            why = why or line[len("WHY:"):].strip()
        elif line.startswith("NEXT STEP:"):
            step = step or line[len("NEXT STEP:"):].strip()
    if step.startswith("call "):
        step = step[len("call "):]
    if not what:
        what = text.strip().splitlines()[0] if text.strip() else "refused"
    reason = reason_of(text)
    return Refusal(reason=reason.value if reason else "LOAD_REFUSED", what=what, why=why,
                   next_step=step, text=text)


def _refused(text: str) -> bool:
    return reason_of(text) is not None or text.lstrip().startswith("BLOCKED")


def _cell(v) -> str | None:
    if v is None:
        return None
    s = str(v).strip()
    return s if s else None


class RealBackend:
    """Implements analytics_agent.webapp.contract.Backend on the engine."""

    def __init__(self) -> None:
        self._guard = threading.Lock()
        self._locks: dict[str, threading.Lock] = defaultdict(threading.Lock)
        self._last_sweep = 0.0

    # --- expiry (P14-O1) ---------------------------------------------------------------------

    @staticmethod
    def ttl_seconds() -> float:
        """ANALYTICS_WORKSPACE_TTL_HOURS, default 72; 0 turns expiry off."""
        raw = os.environ.get("ANALYTICS_WORKSPACE_TTL_HOURS", "").strip()
        return float(raw or DEFAULT_TTL_HOURS) * 3600

    def _lock(self, workspace_id: str) -> threading.Lock:
        with self._guard:
            return self._locks[workspace_id]

    def sweep(self, *, now: float | None = None) -> list[str]:
        """Remove web workspaces unused for longer than the TTL. One in use is skipped."""
        removed = workspace.sweep_idle(self.ttl_seconds(), now=now, lock_for=self._lock)
        with self._guard:
            for wid in removed:
                self._locks.pop(wid, None)
        return removed

    def _maybe_sweep(self) -> None:
        """At most once per SWEEP_EVERY seconds: a new visitor is when the disk grows."""
        now = time.time()
        with self._guard:
            if now - self._last_sweep < SWEEP_EVERY:
                return
            self._last_sweep = now
        self.sweep(now=now)

    # --- plumbing -------------------------------------------------------------------------

    @contextmanager
    def _workspace(self, workspace_id: str):
        """This workspace's lock, held for the whole engine call (P14-D8)."""
        validate_workspace_id(workspace_id)
        with self._lock(workspace_id):
            try:
                yield
            finally:
                # Use, recorded: reads leave no other trace on disk (step 5, M2). Only a
                # workspace that exists is marked -- looking still creates nothing (P14-D21).
                workspace.touch(workspace_id)

    @staticmethod
    def _exists(workspace_id: str) -> bool:
        """Whether this workspace has ever been written to -- checked WITHOUT creating it.

        workspace.workspace_dir and db.connect both create on touch, so a sidebar listing the
        datasets of a first visit made a directory and a database for everyone who merely opened
        the page (seen: one per server start, P14-D21). Reads of a workspace that does not exist
        answer "nothing" instead.
        """
        return (WORKSPACE_ROOT / workspace_id / "session.duckdb").is_file()

    def _uploads(self, workspace_id: str) -> Path:
        path = workspace.workspace_dir(workspace_id) / UPLOADS_DIRNAME
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _own_upload(self, workspace_id: str, path: str) -> Path | None:
        """The path, if and only if it is a file in this workspace's uploads directory."""
        root = self._uploads(workspace_id).resolve()
        candidate = Path(path).resolve()
        if candidate.parent != root or not candidate.is_file():
            return None
        return candidate

    @staticmethod
    def _not_an_upload(path: str) -> Refusal:
        return refusal_from_text(
            f"BLOCKED: {Path(path).name or path} is not a file uploaded to this workspace.\n"
            f"WHY: drafts and loads read only what was uploaded here.\n"
            f'NEXT STEP: call save_upload(filename="...") and use the path it returns.')

    # --- Backend ---------------------------------------------------------------------------

    def new_workspace_id(self) -> str:
        self._maybe_sweep()
        wid = f"ws_{secrets.token_hex(6)}"
        assert wid != DEFAULT_WORKSPACE_ID  # Claude Desktop's process holds "local" (P14-D4)
        return validate_workspace_id(wid)

    def limits(self) -> Limits:
        return Limits(csv_max_bytes=SIZE_GATES.csv_refuse_bytes,
                      excel_max_bytes=SIZE_GATES.excel_refuse_bytes,
                      postgres_max_rows=ROW_REFUSE,
                      description=describe_size_gates())

    def save_upload(self, workspace_id: str, filename: str, data: bytes) -> UploadResult:
        name = Path(filename).name
        if not _SAFE_NAME.match(name) or not name.lower().endswith(_ALLOWED):
            r = refusal_from_text(
                f"BLOCKED: {name!r} is not a CSV or .xlsx file name this server will store.\n"
                f"WHY: only .csv and .xlsx have a loader, and a name becomes a file on disk.\n"
                f'NEXT STEP: call save_upload(filename="sales.csv") with a plain name.')
            return UploadResult(verdict="REFUSE", message=r.what, refusal=r)
        cap = (SIZE_GATES.excel_refuse_bytes if name.lower().endswith(".xlsx")
               else SIZE_GATES.csv_refuse_bytes)
        if len(data) > cap:
            r = refusal_from_text(
                f"BLOCKED: {name} is {len(data):,} bytes, over this server's {cap:,}-byte limit.\n"
                f"WHY: a file that size would not fit in memory here.\n"
                f"NEXT STEP: call save_upload(...) with a smaller extract.")
            return UploadResult(verdict="REFUSE", message=r.what, refusal=r)
        with self._workspace(workspace_id):
            target = self._uploads(workspace_id) / name
            target.write_bytes(data)
            gate = sizegate.check_file(target)
            if not gate.allowed:
                target.unlink(missing_ok=True)
                r = refusal_from_text(gate.message)
                return UploadResult(verdict="REFUSE", message=r.what or gate.message, refusal=r)
        verdict = "WARN" if gate.verdict.value == "WARN" else "OK"
        message = gate.message if verdict == "WARN" else f"{name} saved."
        return UploadResult(verdict=verdict, message=message, path=str(target))

    def draft_ingest(self, workspace_id, path, *, dataset_name=None, sheet=None, header_rows=None,
                     header_join=None, authorised_fill=False) -> IngestDraft:
        empty = GridPreview(rows=[], first_row_number=1, sheet=None, sheet_names=[])
        with self._workspace(workspace_id):
            p = self._own_upload(workspace_id, path)
            if p is None:
                r = self._not_an_upload(path)
                return IngestDraft(spec={}, grid=empty, dataset_name="", header_rows=[],
                                   data_start_row=0, footer_skip_rows=0, header_join="space",
                                   columns=[], message=r.what, refusal=r)
            try:
                d = ingest_draft.draft_for_path(p, dataset_name=dataset_name, sheet=sheet,
                                         header_rows=header_rows, header_join=header_join,
                                         authorised_fill=authorised_fill)
                grid = self._grid(p, d)
            except LoadRefused as exc:
                r = refusal_from_text(str(exc))
                return IngestDraft(spec={}, grid=empty, dataset_name="", header_rows=[],
                                   data_start_row=0, footer_skip_rows=0, header_join="space",
                                   columns=[], message=r.what, refusal=r)
        spec = d.spec
        if spec is None:
            r = refusal_from_text(
                "BLOCKED: this file could not be read into a draft.\n"
                f"WHY: {' '.join(d.guess.questions or d.guess.reasons) or 'no header was found'}\n"
                f'NEXT STEP: call draft_ingest(path="{path}", header_rows=[...]) naming the header.')
            return IngestDraft(spec={}, grid=grid, dataset_name="", header_rows=[],
                               data_start_row=0, footer_skip_rows=0, header_join="space",
                               columns=[], questions=list(d.guess.questions), message=r.what,
                               refusal=r)
        notes = [d.pivot.message] if d.pivot.is_pivot_dump and d.pivot.message else []
        message = ("PROVISIONAL -- " + "; ".join(spec.unresolved) + " still a guess."
                   if spec.unresolved else
                   "Ready to load: every field was read from the file or answered by you.")
        return IngestDraft(
            spec=spec.model_dump(mode="json"), grid=grid, dataset_name=spec.dataset_name,
            header_rows=list(spec.header_rows), data_start_row=spec.data_start_row,
            footer_skip_rows=spec.footer_skip_rows, header_join=spec.header_join,
            columns=[ColumnDraft(c.source_name, c.target_name, c.dtype) for c in spec.columns],
            assumptions=list(spec.assumptions) + notes, questions=list(spec.questions),
            unresolved=list(spec.unresolved), message=message)

    @staticmethod
    def _grid(p: Path, d: ingest_draft.Draft) -> GridPreview:
        """The top of the sheet exactly as it sits there, before any interpretation."""
        if d.source_type == "excel":
            raw = excel.preview_rows(p, d.sheet, n=_GRID_ROWS)
            merged = merges.merged_ranges(str(p), d.sheet)
        else:
            raw = preview.parse_csv_preview(csv_loader.preview_lines(p, n=_GRID_ROWS))
            merged = []
        rows = [[_cell(v) for v in r] for r in raw]
        width = max((len(r) for r in rows), default=0)
        rows = [r + [None] * (width - len(r)) for r in rows]
        return GridPreview(rows=rows, first_row_number=1, sheet=d.sheet,
                           sheet_names=list(d.sheets), merged_ranges=list(merged))

    def confirm_ingest(self, workspace_id: str, spec: dict) -> ActionResult:
        with self._workspace(workspace_id):
            if self._own_upload(workspace_id, str(spec.get("path", ""))) is None:
                r = self._not_an_upload(str(spec.get("path", "")))
                return ActionResult(ok=False, message=r.what, refusal=r)
            text = server.confirm_ingest_spec(spec_json=json.dumps(spec),
                                              workspace_id=workspace_id)
        if _refused(text):
            r = refusal_from_text(text)
            return ActionResult(ok=False, message=r.what, refusal=r)
        return ActionResult(ok=True, message=text)

    def list_datasets(self, workspace_id: str) -> list[DatasetSummary]:
        with self._workspace(workspace_id):
            if not self._exists(workspace_id):
                return []
            con = db.connect(workspace_id)
            try:
                states = state.dataset_states(con)
            finally:
                con.close()
        out = []
        for s in states:
            notes = list(s.notes) + ([f"Blocked: {s.blocked_by}"] if s.blocked_by else [])
            out.append(DatasetSummary(
                name=s.dataset_name, rows=s.row_count, columns=s.column_count, source=s.source,
                loaded=s.age_phrase, stage=s.stage,
                next_step=s.next_call or f'run_analysis(dataset_name="{s.dataset_name}")',
                notes=notes))
        return out

    # --- contracts ---------------------------------------------------------------------

    @staticmethod
    def _window(start: str | None, end: str | None):
        if start and end:
            return (_dt.date.fromisoformat(start), _dt.date.fromisoformat(end))
        return None

    def _propose(self, con, dataset_name: str, **answers):
        record = db.get_dataset(con, dataset_name)
        return propose_contract(
            con, dataset_name,
            grain=answers.get("grain"), primary_key=answers.get("primary_key"),
            date_column=answers.get("date_column"), measures=answers.get("measures"),
            dimensions=answers.get("dimensions"),
            measure_definitions=answers.get("measure_definitions"),
            aggregations=answers.get("aggregations"),
            analysis_window=self._window(answers.get("analysis_window_start"),
                                         answers.get("analysis_window_end")),
            caveats=answers.get("caveats"),
            loaded_at=getattr(record, "loaded_at", None) if record else None)

    def draft_contract(self, workspace_id, dataset_name, *, grain=None, primary_key=None,
                       date_column=None, measures=None, dimensions=None, aggregations=None,
                       measure_definitions=None, analysis_window_start=None,
                       analysis_window_end=None, caveats=None) -> ContractDraft:
        answers = dict(grain=grain, primary_key=primary_key, date_column=date_column,
                       measures=measures, dimensions=dimensions, aggregations=aggregations,
                       measure_definitions=measure_definitions,
                       analysis_window_start=analysis_window_start,
                       analysis_window_end=analysis_window_end, caveats=caveats)
        try:
            with self._workspace(workspace_id):
                con = db.connect(workspace_id)
                try:
                    proposal = self._propose(con, dataset_name, **answers)
                finally:
                    con.close()
        except (ContractRefused, ValueError) as exc:
            r = refusal_from_text(str(exc))
            return ContractDraft(dataset_name, None, [], None, [], [], {}, {}, None, None, [], [],
                                 message=r.what, refusal=r)
        c = proposal.contract
        open_ = set(c.unresolved)
        # A field still named in `unresolved` reaches the form BLANK. Measured: with grain
        # unresolved the contract holds the guess "one row = one order_id"; prefilled and sent
        # back, the engine's guess would be confirmed as the person's statement (P14-D18).
        roles = {name: "measure" for name in (m.name for m in c.measures)}
        roles.update({name: "dimension" for name in c.dimensions})
        if "primary_key" not in open_:
            roles.update({name: "key" for name in c.primary_key})
        if c.date_column and "date_column" not in open_:
            roles[c.date_column] = "date"
        columns = [ContractColumn(
            name=e.name, dtype=e.dtype, suggested_role=roles.get(e.name, "ignore"),
            distinct_count=e.distinct, null_count=e.row_count - e.non_null,
            sample_values=[v for v in (e.min_value, e.max_value) if v is not None])
            for e in proposal.evidence.columns]
        window = c.analysis_window if "analysis_window" not in open_ else None
        return ContractDraft(
            dataset_name=dataset_name,
            grain=None if "grain" in open_ else c.grain,
            primary_key=[] if "primary_key" in open_ else list(c.primary_key),
            date_column=None if "date_column" in open_ else c.date_column,
            measures=[m.name for m in c.measures], dimensions=list(c.dimensions),
            aggregations={m.name: m.agg for m in c.measures
                          if m.agg and f"measures[{m.name}].agg" not in open_},
            measure_definitions={m.name: m.definition for m in c.measures
                                 if m.definition and f"measures[{m.name}].definition" not in open_},
            analysis_window_start=window.start.isoformat() if window else None,
            analysis_window_end=window.end.isoformat() if window else None,
            caveats=list(c.caveats), columns=columns, provisional=list(c.unresolved),
            questions=list(c.questions), evidence=list(proposal.notes),
            message=("PROVISIONAL -- settle what is listed before confirming." if c.unresolved
                     else "Ready to confirm: nothing in it is a guess."))

    def confirm_contract(self, workspace_id: str, draft: ContractDraft) -> ActionResult:
        if draft.provisional:
            r = refusal_from_text(
                "BLOCKED: this contract is still PROVISIONAL.\n"
                f"WHY: still a guess or a blank: {', '.join(draft.provisional)}.\n"
                f'NEXT STEP: call draft_contract(dataset_name="{draft.dataset_name}", ...) '
                f"with the answers.")
            return ActionResult(ok=False, message=r.what, refusal=r)
        # The engine decides, not the draft object: propose again from the draft's own fields
        # and store that proposal's contract only if it is confirmable.
        with self._workspace(workspace_id):
            con = db.connect(workspace_id)
            try:
                try:
                    proposal = self._propose(
                        con, draft.dataset_name, grain=draft.grain,
                        primary_key=draft.primary_key or None, date_column=draft.date_column,
                        measures=draft.measures, dimensions=draft.dimensions,
                        aggregations=draft.aggregations,
                        measure_definitions=draft.measure_definitions,
                        analysis_window_start=draft.analysis_window_start,
                        analysis_window_end=draft.analysis_window_end, caveats=draft.caveats)
                except (ContractRefused, ValueError) as exc:
                    r = refusal_from_text(str(exc))
                    return ActionResult(ok=False, message=r.what, refusal=r)
                if proposal.needs_answer:
                    r = refusal_from_text(
                        "BLOCKED: the engine still finds this contract PROVISIONAL.\n"
                        f"WHY: {', '.join(proposal.contract.unresolved)}.\n"
                        f'NEXT STEP: call draft_contract(dataset_name="{draft.dataset_name}", '
                        f"...) with the answers.")
                    return ActionResult(ok=False, message=r.what, refusal=r)
                # The export goes into the session's own workspace, not docs/contracts: that copy
                # exists to version the canonical contract, and a browser session is not one --
                # exporting there would dirty the repository with every visitor (P14-D19).
                text = contract_tools.confirm(
                    con, proposal.contract.model_dump_json(),
                    export_root=workspace.workspace_dir(workspace_id) / "contracts",
                    workspace_id=workspace_id)
            finally:
                con.close()
        if _refused(text):
            r = refusal_from_text(text)
            return ActionResult(ok=False, message=r.what, refusal=r)
        return ActionResult(ok=True, message=text)

    # --- cleaning (P14-O2) -----------------------------------------------------------------

    def propose_cleaning(self, workspace_id: str, dataset_name: str) -> CleaningProposal:
        """The engine's own proposal, then its stored plan read back as structure: the steps a
        screen shows are the steps the ids resolve against, never a parse of the text."""
        with self._workspace(workspace_id):
            if not self._exists(workspace_id):
                text = clean_tools._not_loaded_text(dataset_name)
            else:
                text = clean_tools.propose_cleaning_plan(workspace_id, dataset_name)
            if _refused(text):
                r = refusal_from_text(text)
                return CleaningProposal(dataset_name, 0, [], message=r.what, refusal=r)
            con = db.connect(workspace_id)
            try:
                rows = con.execute(f'SELECT count(*) FROM "{dataset_name}"').fetchone()[0]
                stored = clean_plan.latest(con, dataset_name)
            finally:
                con.close()
        if text.startswith("Nothing to clean") or stored is None:
            return CleaningProposal(dataset_name, rows, [], message=text)
        suggested = {a.action_id for a in clean_tools._safe_suggestion(stored.actions)}
        steps = [CleaningStep(
            action_id=a.action_id, kind=a.kind.value, column=a.column, intent=a.intent,
            sql=a.sql, rows_affected=a.rows_affected, values_lost=a.values_lost,
            loss_unit=a.loss_unit, sample=list(a.sample), lossy=a.is_lossy,
            suggested=a.action_id in suggested) for a in stored.actions]
        return CleaningProposal(dataset_name, rows, steps, message=text)

    def apply_cleaning(self, workspace_id: str, dataset_name: str,
                       approved_action_ids: list[str]) -> ActionResult:
        with self._workspace(workspace_id):
            text = clean_tools.apply_cleaning_plan(workspace_id, dataset_name,
                                                   list(approved_action_ids))
        if _refused(text):
            r = refusal_from_text(text)
            return ActionResult(ok=False, message=r.what, refusal=r)
        return ActionResult(ok=True, message=text)

    # --- chat, files, reset --------------------------------------------------------------

    def chat(self, workspace_id: str, history: list[dict], message: str) -> ChatTurn:
        """One turn of the agent loop (webapp/agent.py). The workspace lock is taken per tool
        call, not for the turn, so the model's thinking time never blocks the sidebar."""
        validate_workspace_id(workspace_id)
        from . import agent
        return agent.answer(workspace_id, history, message,
                            lock=lambda: self._workspace(workspace_id),
                            list_artifacts=lambda: self.list_artifacts(workspace_id))

    def list_artifacts(self, workspace_id: str) -> list[Artifact]:
        with self._workspace(workspace_id):
            if not self._exists(workspace_id):
                return []
            root = workspace.workspace_dir(workspace_id)
            described: dict[str, str] = {}
            con = db.connect(workspace_id)
            try:
                for d in db.list_datasets(con):
                    for run in analysis_runs.history(con, d.dataset_name):
                        text = " ".join(run.summary)
                        for p in (run.chart_path, run.result_path):
                            if p:
                                described[str(Path(p).resolve())] = text
            finally:
                con.close()
            found = []
            for dirname, kind in _ARTIFACT_DIRS.items():
                folder = root / dirname
                if not folder.is_dir():
                    continue
                for f in folder.iterdir():
                    if f.is_file() and not f.name.startswith("."):
                        found.append((f.stat().st_mtime, Artifact(
                            kind=kind, path=f"{dirname}/{f.name}",
                            title=f.stem.replace("_", " "),
                            created=_dt.datetime.fromtimestamp(f.stat().st_mtime).isoformat(
                                timespec="seconds"),
                            description=described.get(str(f.resolve()), ""))))
        return [a for _, a in sorted(found, key=lambda t: t[0], reverse=True)]

    def read_artifact(self, workspace_id: str, path: str) -> bytes:
        with self._workspace(workspace_id):
            root = workspace.workspace_dir(workspace_id).resolve()
            target = (root / path).resolve()
            if (target.parent.parent != root or target.parent.name not in _ARTIFACT_DIRS
                    or not target.is_file()):
                raise ValueError(f"{path} is not an artifact of this workspace")
            return target.read_bytes()

    def reset_workspace(self, workspace_id: str) -> ActionResult:
        with self._workspace(workspace_id):
            removed = workspace.reset(workspace_id)
        return ActionResult(ok=True, message=(
            f"The workspace is empty: {removed['removed_files']} file(s) removed."
            if removed["existed"] else "The workspace was already empty."))


__all__ = ["RealBackend", "refusal_from_text"]
