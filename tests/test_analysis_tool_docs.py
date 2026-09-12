"""The docstring of compute_analysis, pinned.

Phase 8, Step 9b. Run from the repo root:

    uv run pytest tests/test_analysis_tool_docs.py -q

test_contract_tool_docs.py's own note says a later phase's tool should add a
file rather than lengthen that one indefinitely. This is that file.

Parsed with `ast`, never imported: importing server.py starts FastMCP and
requires the whole dependency stack, and parsing needs only the file.

The sentences asserted here are the ones the conversation depends on. If one
reads as clumsy, rewrite it AND the assertion together, deliberately.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

SERVER = Path("src/analytics_agent/server.py")


@pytest.fixture(scope="module")
def tool() -> ast.FunctionDef:
    if not SERVER.exists():
        pytest.skip(f"{SERVER} not found; run from the repository root")
    tree = ast.parse(SERVER.read_text())
    found = [n for n in ast.walk(tree)
             if isinstance(n, ast.FunctionDef) and n.name == "compute_analysis"]
    if not found:
        pytest.skip("compute_analysis is not registered yet; see Step 9b")
    return found[0]


@pytest.fixture(scope="module")
def doc(tool) -> str:
    return ast.get_docstring(tool) or ""


def test_it_names_every_analysis_and_the_arguments_each_takes(doc):
    """The schema says a parameter exists; only the docstring says which
    analysis it belongs to. An agent passing `column` to top_n gets a refusal
    it could have avoided by reading one line."""
    for name in ("summary_stats", "distribution", "frequency", "cross_tab",
                 "top_n", "group_compare", "pareto", "concentration",
                 "ranking_shift"):
        assert name in doc, f"{name} is not named in the docstring"


def test_it_distinguishes_itself_from_run_analysis(doc):
    assert "run_analysis" in doc
    assert "computes nothing" in doc


def test_it_says_an_unknown_name_comes_back_with_the_list(doc):
    """The Phase 8 Done-When. An agent that expects a traceback retries the
    same guess; one that expects a list reads it."""
    assert "list" in doc.lower()


def test_it_says_the_contract_decides_which_columns_can_be_named(doc):
    assert "contract" in doc.lower()
    assert "declare" in doc.lower()


def test_it_points_at_read_result_file_for_the_rest(doc):
    """F7: a path travels with an instruction to open it, or it does not
    travel."""
    assert "read_result_file" in doc


def test_every_parameter_any_analysis_takes_is_declared(tool):
    """FastMCP builds the schema from the signature, so **params would expose
    a tool the agent cannot pass a column to. The union of nine signatures is
    declared explicitly, and compute_analysis drops the ones nobody gave."""
    names = {a.arg for a in tool.args.args}
    assert {"dataset_name", "analysis_type", "column", "dimension", "measure",
            "rows", "columns", "limit", "n", "bins", "threshold",
            "before_start", "before_end", "after_start", "after_end"} <= names
    assert tool.args.kwarg is None, "a **kwargs here would expose no schema"


def test_it_is_annotated_read_only(tool):
    """It writes a result file, as profile_dataset does, and that one is
    READ_ONLY too: the annotation means it does not modify the user's data."""
    dec = next(d for d in tool.decorator_list if isinstance(d, ast.Call))
    annotations = [kw.value.id for kw in dec.keywords
                   if kw.arg == "annotations" and isinstance(kw.value, ast.Name)]
    assert annotations == ["READ_ONLY"]
