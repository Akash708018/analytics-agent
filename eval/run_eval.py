"""The eval harness. Run from the repo root:

    uv run python eval/run_eval.py

Guide line 963, marked DO NOT SKIP. Three suites over gold questions whose answers were computed
without the tool under test -- in SQL against the loaded table, or fixed by the Failure Mode
Register. An answer produced by `compute_analysis` would agree with `compute_analysis` forever,
including when both are wrong.

**Behavioural asks about an agent, and there is no agent here.** Running a model against the
server and grading it measures one model on one day. The property underneath is testable: every
refusal carries a NEXT STEP, and `Refusal.__post_init__` already rejects one without parentheses
because "an instruction the agent cannot execute is how the apology loop starts". What nothing
did was execute it. A refusal recovers in one retry if the call it names, made verbatim,
succeeds -- and that tests the property rather than a sample.

The retry parses the NEXT STEP with `ast` and dispatches through an allowlist of registered
tools. Not `eval`: a harness that evaluated whatever a refusal string happened to contain would
be a worse bug than any it could find.
"""

from __future__ import annotations

import ast
import sys
from collections import Counter
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from analytics_agent import workspace  # noqa: E402
from analytics_agent.contract.refusals import reason_of  # noqa: E402
from analytics_agent.ingest.csv_loader import load_csv  # noqa: E402
from analytics_agent.util import db  # noqa: E402

QUESTIONS = Path("eval/gold_questions.yaml")

# P13-O2, and the better answer than the one it proposed. confirm_dataset_contract exports a
# YAML copy of the contract to docs/contracts/, outside the workspace, where it is meant to be
# version controlled -- so a script that confirms a contract dirties the repository (C86). The
# first fix taught one script to restore what it found, and the next script that confirmed a
# contract hit the same thing. contract/tools.confirm reads store.EXPORT_DIR at call time, so
# pointing it at this script's own workspace means nothing outside is ever written. No restore,
# no shared bookkeeping, and less code than either.
FIXTURES = Path("tests/fixtures")

WITH_CONTRACT = "eval_contract"
NO_CONTRACT = "eval_bare"
DATASET = "clean_sales"

PASSED = 0
FAILED = 0
SKIPPED = 0
BY_SUITE: Counter = Counter()
FAILED_BY_SUITE: Counter = Counter()
FAILURES: list[str] = []


def check(suite: str, label: str, ok: bool, detail: str = "") -> bool:
    global PASSED, FAILED
    BY_SUITE[suite] += 1
    if ok:
        PASSED += 1
        print(f"  PASS  {label}" + (f"  ({detail})" if detail else ""))
    else:
        FAILED += 1
        FAILED_BY_SUITE[suite] += 1
        FAILURES.append(f"{label}" + (f"  ({detail})" if detail else ""))
        print(f"  FAIL  {label}" + (f"  ({detail})" if detail else ""))
    return ok


def skip(label: str, why: str) -> None:
    global SKIPPED
    SKIPPED += 1
    print(f"  SKIP  {label}  ({why})")


def heading(text: str) -> None:
    print()
    print(text)
    print("-" * len(text))


def truth(sql: str, workspace_id: str = WITH_CONTRACT) -> str:
    """The answer, computed against the table rather than asked of the tool."""
    con = db.connect(workspace_id)
    try:
        value = con.execute(sql).fetchone()[0]
    finally:
        con.close()
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return f"{value:,}" if isinstance(value, int) else str(value)


# --- setup -----------------------------------------------------------------------------------

def mount(server) -> bool:
    """Two workspaces: one with a confirmed contract, one deliberately without."""
    csv = FIXTURES / "clean_sales.csv"
    if not csv.exists():
        skip("the fixture", f"{csv} is not on disk; run from the repository root")
        return False

    for ws in (WITH_CONTRACT, NO_CONTRACT):
        workspace.reset(ws)
        con = db.connect(ws)
        try:
            load_csv(con, str(csv), DATASET)
        finally:
            con.close()

    proposal = server.propose_dataset_contract(
        dataset_name=DATASET,
        grain="one row = one order",
        primary_key=["order_id"],
        date_column="order_date",
        measures=["revenue", "units", "unit_price"],
        dimensions=["region", "product", "channel"],
        aggregations={"revenue": "sum", "units": "sum", "unit_price": "none"},
        measure_definitions={
            "revenue": "units x unit_price, gross of tax",
            "units": "items on the order",
            "unit_price": "price of one item; summing it means nothing",
        },
        analysis_window_start="2024-01-01",
        analysis_window_end="2024-12-31",
        workspace_id=WITH_CONTRACT,
    )
    if "```" not in proposal:
        skip("the contract", "the proposal carried no JSON to confirm")
        return False
    body = proposal.rsplit("```", 2)[-2]
    if body.startswith("json"):
        body = body[4:]
    confirmed = server.confirm_dataset_contract(contract_json=body, workspace_id=WITH_CONTRACT)
    if reason_of(confirmed) is not None:
        skip("the contract", confirmed.splitlines()[0][:80])
        return False
    return True


def invoke(server, call: dict, workspace_id: str) -> str:
    tool = getattr(server, call["tool"])
    args = dict(call.get("args") or {})
    args.setdefault("dataset_name", DATASET)
    return tool(workspace_id=workspace_id, **args)


# --- the retry -------------------------------------------------------------------------------

def next_step(text: str) -> str | None:
    for line in text.splitlines():
        if line.startswith("NEXT STEP: call "):
            return line[len("NEXT STEP: call "):].strip()
    return None


def as_call(step: str, server) -> tuple[str, dict] | None:
    """The NEXT STEP as a call this harness can make, or None if it is not one.

    Parsed, never evaluated. A step is usable when it is exactly one call to a registered tool
    with literal arguments -- no prose after it, no second call, no placeholders. Anything else
    is something an agent has to read rather than follow, which is the measurement.
    """
    try:
        node = ast.parse(step.strip(), mode="eval").body
    except SyntaxError:
        return None
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
        return None
    name = node.func.id
    if not callable(getattr(server, name, None)) or node.args:
        return None
    args = {}
    for kw in node.keywords:
        try:
            args[kw.arg] = ast.literal_eval(kw.value)
        except ValueError:
            return None
    return name, args


# --- the suites -------------------------------------------------------------------------------

def run_correctness(server, q: dict) -> None:
    answer = truth(q["sql"])
    reply = invoke(server, q["call"], WITH_CONTRACT)
    if reason_of(reply) is not None:
        check("correctness", f"{q['id']} {q['question']}", False, reply.splitlines()[0][:80])
        return
    missing = [e.format(answer=answer) for e in q["expect"]
               if e.format(answer=answer) not in reply]
    check("correctness", f"{q['id']} {q['question']}", not missing,
          f"answer {answer}" if not missing else f"not found: {missing}")


def run_behavioural(server, q: dict) -> None:
    ws = NO_CONTRACT if q.get("contract") is False else WITH_CONTRACT
    reply = invoke(server, q["call"], ws)
    got = reason_of(reply)
    if not check("behavioural", f"{q['id']} refuses with {q['reason']}",
                 got is not None and got.value == q["reason"],
                 str(got.value if got else "no refusal")):
        return

    for phrase in q.get("expect", []):
        check("behavioural", f"{q['id']} says {phrase!r}", phrase in reply)

    step = next_step(reply)
    if not check("behavioural", f"{q['id']} names a next step", step is not None):
        return
    parsed = as_call(step, server)

    if q.get("needs_decision"):
        check("behavioural", f"{q['id']} marks the decision the caller must make",
              parsed is None, step[:90])
        return

    if not check("behavioural", f"{q['id']} names a call an agent can make verbatim",
                 parsed is not None, step[:90]):
        return
    if q.get("retry"):
        name, args = parsed
        args.setdefault("workspace_id", ws)
        again = getattr(server, name)(**args)
        check("behavioural", f"{q['id']} recovers in one retry",
              reason_of(again) is None, again.splitlines()[0][:80])


# --- regression, one per Failure Mode Register id ----------------------------------------------

def merge_ranges_without_openpyxl() -> tuple[bool, str]:
    """F11: ws.merged_cells raises in read-only mode; the ranges come from the sheet XML."""
    from analytics_agent.ingest import merges
    refs = merges.merged_ranges(str(FIXTURES / "merged_multiheader.xlsx"), "Sales")
    return len(refs) == 3, f"{len(refs)} range(s): {', '.join(refs)}"


def multiheader_csv_types() -> tuple[bool, str]:
    """F12: names assembled in Python with header=false, or every column is VARCHAR and the
    header row becomes data."""
    from analytics_agent.ingest import draft
    d = draft.draft_for_path(str(FIXTURES / "multiheader.csv"))
    if d.spec is None:
        return True, "the loader asks rather than guessing, which is the mitigation"
    ws = "eval_f12"
    workspace.reset(ws)
    con = db.connect(ws)
    try:
        spec = draft.spec_from_json(d.spec.model_dump_json())
        kwargs = spec.to_loader_kwargs(load_csv)
        name = kwargs["dataset_name"]        # the spec names the table; do not pass a second
        load_csv(con, spec.path, **kwargs)
        types = [r[0] for r in con.execute(
            "SELECT data_type FROM information_schema.columns WHERE table_name = ?", [name]
        ).fetchall()]
        first = con.execute(f'SELECT * FROM "{name}" LIMIT 1').fetchone()
        ok = not all(t == "VARCHAR" for t in types)
        return ok, f"types: {sorted(set(types))}; first row starts {str(first[0])[:20]!r}"
    finally:
        con.close()
        workspace.reset(ws)


def bounded_fill_does_not_leak() -> tuple[bool, str]:
    """F14: a group label fills only within its real merge range."""
    from analytics_agent.ingest import merges
    from analytics_agent.ingest.headers import assemble_names
    refs = merges.merged_ranges(str(FIXTURES / "merged_multiheader.xlsx"), "Sales")
    row1 = ["Identifiers", None, "Dimensions", None, None, "Measures", None, None]
    row2 = ["order_id", "order_date", "region", "product", "channel",
            "units", "unit_price", "revenue"]
    names = assemble_names([row1, row2], header_rows_1idx=[1, 2], source_type="excel",
                           join="space", merge_refs=refs).names
    groups = ("Identifiers", "Dimensions", "Measures")
    spans = [n for n in names if sum(g in n for g in groups) > 1]
    ok = not spans and names[2].startswith("Dimensions") and names[5].startswith("Measures")
    return ok, f"col3={names[2]!r} col6={names[5]!r}" + (f" spans={spans}" if spans else "")


def ctas_type_change() -> tuple[bool, str]:
    """F15: UPDATE cannot change VARCHAR to DATE; the apply goes through CTAS and loses nothing."""
    from analytics_agent import server
    from analytics_agent.ingest import draft
    from analytics_agent.ingest.excel import load_excel
    ws, ds = "eval_f15", "merged_multiheader"
    workspace.reset(ws)
    con = db.connect(ws)
    try:
        d = draft.draft_for_path(str(FIXTURES / "merged_multiheader.xlsx"))
        spec = draft.spec_from_json(d.spec.model_dump_json())
        load_excel(con, spec.path, **spec.to_loader_kwargs(load_excel))
    finally:
        con.close()
    server.propose_cleaning_plan(dataset_name=ds, workspace_id=ws)
    applied = server.apply_cleaning_plan(
        dataset_name=ds, approved_action_ids=["C001"], workspace_id=ws)
    con = db.connect(ws)
    try:
        kind = con.execute(
            "SELECT data_type FROM information_schema.columns "
            "WHERE table_name = ? AND column_name = 'order_date'", [ds]).fetchone()
    finally:
        con.close()
        workspace.reset(ws)
    ok = kind is not None and kind[0] == "DATE" and "150 row(s) before, 150 after" in applied
    return ok, f"order_date is {kind[0] if kind else 'gone'}, rows preserved: " \
               f"{'150 row(s) before, 150 after' in applied}"


CHECKS = {
    "merge_ranges_without_openpyxl": merge_ranges_without_openpyxl,
    "multiheader_csv_types": multiheader_csv_types,
    "bounded_fill_does_not_leak": bounded_fill_does_not_leak,
    "ctas_type_change": ctas_type_change,
}


def run_regression(q: dict) -> None:
    fn = CHECKS.get(q["check"])
    if fn is None:
        check("regression", f"{q['id']} ({q['fmr']})", False, f"no check named {q['check']}")
        return
    ok, detail = fn()
    check("regression", f"{q['id']} ({q['fmr']}) {q['question']}", ok, detail)


# --- the roster -------------------------------------------------------------------------------

def next_call_roster(server) -> None:
    """How many refusals in the codebase name a call an agent could make verbatim.

    Not a gold question -- a measurement over the whole surface rather than one path. It is here
    because the number is the point of this phase: "it turns 'I built an AI thing' into 'I
    measured whether it was right, and here is the number'."
    """
    heading("Roster: refusals whose NEXT STEP is a call, not a sentence")
    src = Path("src")
    total = usable = 0
    prose: list[str] = []
    for f in sorted(src.rglob("*.py")):
        tree = ast.parse(f.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            for kw in node.keywords:
                if kw.arg != "next_call":
                    continue
                if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                    text = kw.value.value
                elif isinstance(kw.value, ast.JoinedStr):
                    # A bare x, not '"x"': the literal parts around an f-string expression
                    # already carry the quotes, so dataset_name="{name}" becomes
                    # dataset_name="x". Substituting a quoted x gave dataset_name=""x"", which
                    # is a syntax error, and the roster reported 0 of 37 -- a measurement that
                    # was wrong in the alarming direction and disagreed with a probe run
                    # minutes earlier. That disagreement is what caught it.
                    text = "".join(v.value if isinstance(v, ast.Constant) else "x"
                                   for v in kw.value.values)
                else:
                    continue
                total += 1
                if as_call(" ".join(text.split()), server) is not None:
                    usable += 1
                else:
                    prose.append(f"{f.name}: {' '.join(text.split())[:78]}")
    pct = (usable / total * 100) if total else 0.0
    print(f"  {usable} of {total} refusals ({pct:.0f}%) name a call an agent can make verbatim.")
    print(f"  {total - usable} carry prose, a second call, or a placeholder the caller fills.")
    for line in prose[:6]:
        print(f"    - {line}")
    if len(prose) > 6:
        print(f"    ... and {len(prose) - 6} more")


def main() -> int:
    if not QUESTIONS.exists():
        print(f"{QUESTIONS} is not on disk; run from the repository root")
        return 1
    questions = yaml.safe_load(QUESTIONS.read_text(encoding="utf-8"))
    print(f"Eval harness: {len(questions)} gold question(s)")

    try:
        from analytics_agent import server
    except Exception as exc:  # noqa: BLE001
        print(f"server.py did not import: {type(exc).__name__}: {exc}")
        return 1

    from analytics_agent.contract import store
    store.EXPORT_DIR = workspace.workspace_dir(WITH_CONTRACT) / "contracts"
    try:
        if not mount(server):
            print()
            print(f"{PASSED} passed, {FAILED} failed, {SKIPPED} skipped")
            return 1 if FAILED else 0

        heading("Correctness: does the number match one computed without the tool?")
        for q in [q for q in questions if q["suite"] == "correctness"]:
            run_correctness(server, q)

        heading("Behavioural: does a refusal carry a recovery, and does it work?")
        for q in [q for q in questions if q["suite"] == "behavioural"]:
            run_behavioural(server, q)

        heading("Regression: one per Failure Mode Register id")
        for q in [q for q in questions if q["suite"] == "regression"]:
            run_regression(q)

        next_call_roster(server)
    finally:
        for ws in (WITH_CONTRACT, NO_CONTRACT):
            workspace.reset(ws)

    print()
    for suite in ("correctness", "behavioural", "regression"):
        n = BY_SUITE[suite]
        bad = FAILED_BY_SUITE[suite]
        print(f"  {suite:13s} {n - bad:3d}/{n:<3d} passed")
    total = PASSED + FAILED
    print()
    print(f"SCORE: {PASSED}/{total} ({PASSED / total * 100:.0f}%)"
          if total else "SCORE: no questions ran")
    if FAILED:
        print()
        print("Failing gold questions are findings, not a broken build. Each one is either a")
        print("defect in the product or a wrong answer in the question, and which it is has to")
        print("be decided by reading it. See docs/decisions.md for the open items they opened.")
        for label in FAILURES:
            print(f"  - {label}")
    if SKIPPED:
        print("A skip is an outstanding clause, not a passing one.")
    # Exits 0 on a wrong answer, and non-zero only if the harness itself could not run. An eval
    # that fails the build on any wrong answer is a test suite, and a test suite cannot carry a
    # score -- the number stops being a measurement the moment it has to be 100%.
    return 1 if SKIPPED else 0


if __name__ == "__main__":
    raise SystemExit(main())
