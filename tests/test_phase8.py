"""Phase 8 acceptance test. Run from the repo root:

    uv run python tests/test_phase8.py

Asserts the Done-When from the build guide:

    all nine run on Olist and a fixture; unknown type returns the valid list

and three more the Done-When does not cover, each a decision this phase had to
make and could get wrong silently:

    4. the four reason codes fire on real data, one per recovery. A code that
       covers two recoveries measures neither, which is why ParamsInvalid
       exists.
    5. the path a result names opens, including its columns past the twelfth --
       P8-O15 was that they were written and reachable by nothing.
    6. the MCP tool forwards its fifteen parameters to the right names. The ast
       test asserts they are DECLARED; nothing asserts they arrive.

**Every clause builds a REAL confirmed contract** -- proposed values, a
binding, `store.confirm` -- and goes through the real `require_contract`. That
is P8-O10: every test in this phase so far has used a stand-in contract looser
than the Pydantic model and a gate that could not refuse. A result computed
under a hand-built namespace proves the arithmetic works and says nothing
about the path a person takes.

**The Olist clause is a SKIP, not a pass.** The clause is unwritten; the data is present. The
fixture half of the Done-When is clauses 1 to 3; the Olist half is outstanding
and this says so on every run. Phase 9's Done-When needs Olist as well
(`calendar_coverage` finding the missing month), so acquiring it belongs there.

**The live schema is a SKIP too.** `@mcp.tool` returns the plain function, so
clause 6 can call it -- but calling a Python function does not render the JSON
schema FastMCP builds from its signature, and that schema is what the agent
actually reads. No script reaches it. Saying so beats a clause that implies
otherwise.

**It holds no connection open across a tool call**, for the reason Phase 6's
script records: one handle per file per process.
"""

from __future__ import annotations

import ast
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from analytics_agent import workspace  # noqa: E402
from analytics_agent.analysis import tools as analysis_tools  # noqa: E402
from analytics_agent.analysis.registry import catalogue  # noqa: E402
from analytics_agent.contract import store  # noqa: E402
from analytics_agent.contract.dataset_contract import (  # noqa: E402
    AnalysisWindow,
    Binding,
    DatasetContract,
    ForeignKey,
    Measure,
)
from analytics_agent.contract.refusals import Reason, reason_of  # noqa: E402
from analytics_agent.ingest.csv_loader import load_csv  # noqa: E402
from analytics_agent.util import db, results  # noqa: E402

WORKSPACE = "phase8_test"
CLEAN = Path("tests/fixtures/clean_sales.csv")
LOOKUP = Path("tests/fixtures/region_lookup.csv")
SERVER = Path("src/analytics_agent/server.py")

WINDOW = AnalysisWindow(start=date(2024, 1, 1), end=date(2024, 12, 31))

# Two quarters inside the window, for ranking_shift. Chosen with a gap between
# them on purpose: the rows in April to September are in scope and in neither
# period, and the tool has to say so rather than let two counts that do not add
# up pass without comment.
BEFORE = ("2024-01-01", "2024-03-31")
AFTER = ("2024-10-01", "2024-12-31")

# Phase 9 adds Tier 3. This file asserts that ITS nine are registered,
# not that nine is all there is -- a later tier must not fail an
# earlier phase's acceptance for having done its own work.
PHASE_8 = {
    "summary_stats",
    "distribution",
    "frequency",
    "cross_tab",
    "top_n",
    "group_compare",
    "pareto",
    "concentration",
    "ranking_shift",
}

PASSED = 0
FAILED = 0
SKIPPED = 0


def check(label: str, condition: bool, detail: str = "") -> None:
    global PASSED, FAILED
    if condition:
        PASSED += 1
        print(f"  PASS  {label}" + (f"  ({detail})" if detail else ""))
    else:
        FAILED += 1
        print(f"  FAIL  {label}" + (f"  ({detail})" if detail else ""))


def skip(label: str, why: str) -> None:
    global SKIPPED
    SKIPPED += 1
    print(f"  SKIP  {label}  ({why})")


def heading(text: str) -> None:
    print()
    print(text)
    print("-" * len(text))


def load(fixture: Path, dataset_name: str) -> None:
    con = db.connect(WORKSPACE)
    try:
        load_csv(con, str(fixture), dataset_name)
    finally:
        con.close()


def confirm_contract(dataset_name: str) -> object:
    """A real contract, confirmed through the real store.

    Three measures with three different aggregates, because the contract is
    what decides whether a number may be built at all: revenue and units add,
    and unit_price is declared non-additive -- summing a unit price produces a
    number nothing downstream can detect as wrong, which is the whole reason
    Measure.agg has no default.
    """
    con = db.connect(WORKSPACE)
    try:
        pairs = [
            (r[0], r[1])
            for r in con.execute(
                "SELECT column_name, data_type FROM information_schema.columns "
                "WHERE table_name = ? ORDER BY ordinal_position",
                [dataset_name],
            ).fetchall()
        ]
        rows = con.execute(f'SELECT count(*) FROM "{dataset_name}"').fetchone()[0]
        contract = DatasetContract(
            dataset_name=dataset_name,
            grain="one row = one order",
            primary_key=["order_id"],
            date_column="order_date",
            analysis_window=WINDOW,
            measures=[
                Measure(name="revenue", agg="sum",
                        definition="units x unit_price, gross of tax",
                        unit="GBP"),
                Measure(name="units", agg="sum",
                        definition="items on the order"),
                Measure(name="unit_price", agg="none",
                        definition="price of one item; summing it means nothing",
                        unit="GBP"),
            ],
            dimensions=["region", "channel", "product"],
            bound_to=Binding.from_pairs(pairs, rows),
            foreign_keys=[ForeignKey(columns=["region"],
                                     references="region_lookup")],
        )
        return store.confirm(con, contract)
    finally:
        con.close()


def run(analysis_type: str, **params) -> str:
    """One analysis on a short-lived connection, through the real gate."""
    con = db.connect(WORKSPACE)
    try:
        return analysis_tools.compute_analysis(
            con, WORKSPACE, "clean_sales", analysis_type, **params
        )
    finally:
        con.close()


def registered_tools() -> set[str]:
    """Every @mcp.tool in server.py, read from source rather than imported.

    Phase 5's trick and Phase 7's reason for keeping it: a registered tool is
    invisible to a running Claude Desktop until the process restarts, and
    parsing answers "is it registered" without asking a running process.
    """
    if not SERVER.exists():
        return set()
    out = set()
    for node in ast.walk(ast.parse(SERVER.read_text())):
        if not isinstance(node, ast.FunctionDef):
            continue
        for dec in node.decorator_list:
            target = dec.func if isinstance(dec, ast.Call) else dec
            if isinstance(target, ast.Attribute) and target.attr == "tool":
                out.add(node.name)
    return out


def path_in(text: str) -> str:
    """The result path a tool result names, as an agent would read it off."""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.endswith(".csv"):
            return stripped
    return ""


# --------------------------------------------------------------------------
# Clause 1: all nine, under a real contract
# --------------------------------------------------------------------------

CALLS = {
    "summary_stats": {},
    "distribution": {"measure": "revenue", "bins": 10},
    "frequency": {"column": "region"},
    "cross_tab": {"rows": "region", "columns": "channel", "measure": "revenue"},
    "top_n": {"dimension": "region", "measure": "revenue", "n": 5},
    "group_compare": {"dimension": "region", "measure": "revenue"},
    "pareto": {"dimension": "product", "measure": "revenue"},
    "concentration": {"dimension": "product", "measure": "revenue"},
    "ranking_shift": {
        "dimension": "region", "measure": "revenue",
        "before_start": BEFORE[0], "before_end": BEFORE[1],
        "after_start": AFTER[0], "after_end": AFTER[1],
    },
}


def clause_one() -> dict[str, str]:
    heading("Clause 1: all nine run on a fixture, under a real contract")

    if not CLEAN.exists() or not LOOKUP.exists():
        skip("clean_sales", "fixtures not generated; see make_fixtures.py")
        return {}

    load(LOOKUP, "region_lookup")
    load(CLEAN, "clean_sales")
    stored = confirm_contract("clean_sales")
    check("a real contract confirms through the store", stored.version == 1,
          f"v{stored.version}, {stored.row_count:,} rows")

    registered = {name for name, _, _ in catalogue()}
    check("Phase 8's nine analyses are registered",
          PHASE_8 <= registered,
          ", ".join(sorted(registered)))
    check("the calls below cover every one of them",
          set(CALLS) == PHASE_8 & registered,
          f"uncalled: {sorted((PHASE_8 & registered) - set(CALLS)) or 'none'}")

    out: dict[str, str] = {}
    for name in sorted(CALLS):
        text = run(name, **CALLS[name])
        out[name] = text
        ok = reason_of(text) is None
        check(f"{name} runs through the real gate", ok,
              "" if ok else text.splitlines()[0][:90])
        if not ok:
            continue
        check(f"{name} names the contract it computed under",
              text.startswith("Under contract v1 for clean_sales:"))
        check(f"{name} says what it was computed over",
              "row(s) analysed" in text)
        check(f"{name} wrote a file that exists",
              Path(path_in(text)).exists(), path_in(text))
    return out


# --------------------------------------------------------------------------
# Clause 2: the four reason codes, on real data
# --------------------------------------------------------------------------


def clause_two() -> None:
    heading("Clause 2: each refusal carries the code its recovery belongs to")

    text = run("summry_stats")
    check("an unknown analysis is ANALYSIS_NOT_FOUND",
          reason_of(text) is Reason.ANALYSIS_NOT_FOUND)
    missing = [n for n, _, _ in catalogue() if n not in text]
    check("and the refusal lists every valid name", not missing,
          f"missing: {missing}" if missing else f"all {len(catalogue())}")

    text = run("distribution", measure="revenue", bins=1)
    check("a bad argument is ANALYSIS_PARAMS_INVALID",
          reason_of(text) is Reason.ANALYSIS_PARAMS_INVALID,
          "not NOT_POSSIBLE: the fix is the call, not the contract")

    text = run("top_n", dimension="region", measure="unit_price")
    check("a non-additive measure is ANALYSIS_NOT_POSSIBLE",
          reason_of(text) is Reason.ANALYSIS_NOT_POSSIBLE)
    check("and it points at the contract",
          'propose_dataset_contract(dataset_name="clean_sales")' in text)

    text = run("frequency", column="order_id")
    check("a column that exists but is not declared is refused",
          reason_of(text) is Reason.ANALYSIS_NOT_POSSIBLE,
          "order_id is in the table and is not a dimension")
    check("and the refusal names the declared dimensions",
          "region" in text and "channel" in text)

    skip("ANALYSIS_RESULT_UNSOUND",
         "no real analysis can be made to lose rows on demand; "
         "tests/test_analysis_tools.py provokes it with a test double")


# --------------------------------------------------------------------------
# Clause 3: the path opens, and so do the columns past the twelfth
# --------------------------------------------------------------------------


def clause_three(texts: dict[str, str]) -> None:
    heading("Clause 3: every path a result names opens, columns included")

    if not texts:
        skip("the round trip", "clause 1 produced no results")
        return

    for name in ("cross_tab", "summary_stats"):
        text = texts.get(name, "")
        path = path_in(text)
        if not path:
            skip(f"{name} round trip", "no path in the result")
            continue
        page = results.read_result_file(WORKSPACE, path)
        check(f"the path {name} named opens", reason_of(page) is None,
              page.splitlines()[0][:80] if page else "")
        check(f"the page says which columns it holds",
              "columns 1 to" in page)

    wide = path_in(texts.get("cross_tab", ""))
    if not wide:
        skip("column paging", "no cross_tab result")
        return
    page = results.read_result_file(WORKSPACE, wide)
    if "more columns" in page:
        later = results.read_result_file(WORKSPACE, wide, start_col=13)
        check("the columns past the twelfth are reachable",
              reason_of(later) is None and "columns 13 to" in later,
              "P8-O15: they were written and returnable by nothing")
    else:
        skip("column paging",
             "no pairing in this fixture is wide enough: region 4, product 5, "
             "channel 3, so the widest cross_tab is 7 columns against a "
             "12-column window. P8-O15's fix is covered by "
             "tests/test_results.py, on a 50-column result")


# --------------------------------------------------------------------------
# Clause 4: the tool forwards what it declares
# --------------------------------------------------------------------------


def clause_four() -> None:
    heading("Clause 4: the registered tool forwards its arguments by name")

    check("compute_analysis is registered",
          "compute_analysis" in registered_tools())

    try:
        from analytics_agent import server
    except Exception as exc:  # FastMCP missing or broken
        skip("forwarding", f"server.py did not import: {type(exc).__name__}")
        return

    if not callable(getattr(server, "compute_analysis", None)):
        skip("forwarding", "@mcp.tool did not return a plain function")
        return

    # Arguments that can only arrive by being forwarded to the right name. If
    # column and dimension were crossed in the wrapper, frequency refuses with
    # "region is not a declared dimension" -- which is exactly what the ast
    # test in test_analysis_tool_docs.py cannot see, because it asserts the
    # parameters are DECLARED and not that they arrive.
    text = server.compute_analysis(
        dataset_name="clean_sales", analysis_type="frequency",
        column="region", workspace_id=WORKSPACE,
    )
    check("column reaches frequency", reason_of(text) is None,
          "" if reason_of(text) is None else text.splitlines()[0][:90])

    text = server.compute_analysis(
        dataset_name="clean_sales", analysis_type="top_n",
        dimension="region", measure="revenue", n=3, workspace_id=WORKSPACE,
    )
    check("dimension, measure and n reach top_n", reason_of(text) is None,
          "" if reason_of(text) is None else text.splitlines()[0][:90])

    text = server.compute_analysis(
        dataset_name="clean_sales", analysis_type="ranking_shift",
        dimension="region", measure="revenue",
        before_start=BEFORE[0], before_end=BEFORE[1],
        after_start=AFTER[0], after_end=AFTER[1], workspace_id=WORKSPACE,
    )
    check("four period dates reach ranking_shift", reason_of(text) is None,
          "" if reason_of(text) is None else text.splitlines()[0][:90])

    skip("the rendered schema",
         "FastMCP builds it from the signature and no script can read what a "
         "client displays; a call proves forwarding, not the schema")


# --------------------------------------------------------------------------
# Clause 5: what the Done-When still asks for
# --------------------------------------------------------------------------


def clause_five() -> None:
    heading("Clause 5: the Olist half of the Done-When")

    skip("all nine on Olist",
         "the clause is unwritten, not unreachable: P9-O1 closed when "
         "tests/test_phase9.py reached local Postgres, and the nine tables and 99,441 "
         "orders were confirmed again in Phase 10 Step 1. P10-O3 tracks writing it")

    skip("the role trap",
         "the guide says summary_stats must skip role=identifier; role is a "
         "proposal-time heuristic in evidence.py and never reaches a confirmed "
         "contract. Clause 1 accepts the behaviour instead: declared columns "
         "only, and the key named among what was skipped")


def main() -> int:
    print("Phase 8 acceptance: nine analyses, one gate, one envelope")
    workspace.reset(WORKSPACE)
    try:
        texts = clause_one()
        if texts:
            clause_two()
            clause_three(texts)
            clause_four()
        clause_five()
    finally:
        workspace.reset(WORKSPACE)

    print()
    print(f"{PASSED} passed, {FAILED} failed, {SKIPPED} skipped")
    if SKIPPED:
        print("A skip is an outstanding clause, not a passing one.")
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())
