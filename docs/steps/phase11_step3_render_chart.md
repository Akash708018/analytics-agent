# Phase 11 Step 3 - render_chart, the tool

21/09/2026. Baseline c1826b2 (Step 3a, the parameter fix). Measured before starting:
1699 passed; test_phase8.py 99/0/2; test_phase9.py 19/0/0; test_phase10.py 35/0/1.

## A deviation, recorded rather than tidied away

Steps 1, 2 and 3a had their documents written before anything ran. This one did not: after the
tool surface was decided, the build started and this document was written afterwards from the
commands that were actually run. The predictions below are therefore not predictions and are not
presented as any -- the section that would hold them says what was found instead. The method
exists because an expectation committed to in advance turns a run into a measurement, and a
document written afterwards cannot do that however accurate it is.

## The design, decided before building

`render_chart` mirrors `compute_analysis`: same arguments, plus `chart`, and optionally `x`, `y`
and `title`. Rejected: charting a written CSV, which needs no parameter roster but parses numbers
back out of formatted strings and loses the analysis's summary. The roster duplication is the
real cost of the choice, and Step 3a's forwarding guard is what makes it safe -- the same guard,
applied to the second tool, written in the step that added it rather than two phases later.

## What was built

- `analysis/tools.py`: the ladder every analysis call climbs -- gate, lookup, scope, run, and the
  check that the result says what it was computed over -- extracted into `_produce`, which raises
  `_Refused` carrying the refusal it would have returned. `compute_analysis` and `render_chart`
  both climb it. Two copies of that ladder would be two copies of one ruling, which P9-O6 records
  drifting apart.
- `render_chart` in tools.py, translating `ChartRefused` into an ANALYSIS_NOT_POSSIBLE refusal
  that says the analysis ran and the shape does not fit.
- `server.py`: the MCP tool, 30 parameters, all forwarded.
- `charts/render` imported inside the function rather than at module scope, so importing the
  analysis package does not import matplotlib and through it numpy. Twenty-two analysis modules
  and their tests import that package; none of them draws.

## What was found while building

**`frequency` offers one measure, not two.** Its columns are value, rows and share, and share is
rendered as a percentage -- a string that is not a magnitude, so `is_numeric_column` rejects it.
Two chart tests were written on the assumption that it offered two and failed. The behaviour is
right: two of frequency's three columns are the same count in different clothes, and a grouped
bar of them would be a chart of one number drawn twice. `summary_stats` is the multi-measure
fixture instead, and the assumption is now pinned in a test of its own.

**The closed tool roster fired, correctly.** `test_the_registered_tools_are_exactly_the_expected_ones`
failed on the new tool, which its own docstring says is the intended friction: "Adding a tool is
therefore two edits: the tool, and this set."

## Outputs

    tests/test_analysis_tools.py + test_analysis_tool_docs.py   36 passed
    full suite                                                  1699 -> 1712
    test_phase8.py   99 passed, 0 failed, 2 skipped
    test_phase9.py   19 passed, 0 failed, 0 skipped
    test_phase10.py  35 passed, 0 failed, 1 skipped

Thirteen tests added: ten on the tool's behaviour, three guarding render_chart's roster and its
docstring. Acceptance is unchanged because no acceptance script calls render_chart -- which is
P11-O1, opened in Step 3a and still open.
