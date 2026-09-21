# Phase 11 Step 2 - the render layer

21/09/2026. Baseline 3a31f0b. Measured before starting: `uv run pytest -q` 1672 passed;
test_phase8.py 99/0/2; test_phase9.py 19/0/0; test_phase10.py 35/0/1.

Scope agreed before building: the render layer only. No MCP tool -- `render_chart` is wired in
Step 3, where the gate and the Rule 4 envelope get their own attention. The tool will mirror
`compute_analysis`'s arguments and chart the `Output` that analysis returns.

## A correction, made before any code was written

When the tool surface was chosen, charting an `Output` was argued for partly on the grounds that
its values "stay typed", against charting a written CSV where `base.number()` has already turned
them into strings. **That was wrong, and measured wrong before it cost anything.** An `Output`
already holds rendered strings:

    headers: ['group', 'n', 'mean', 'stddev', 'skew']
    row: [('a','str'), ('6','str'), ('11.5','str'), ('1.8708','str'), ('-0','str')]
    row: [('(no arm)','str'), ('1','str'), (None,'NoneType'), (None,'NoneType'), (None,'NoneType')]

Every analysis builds its rows with `number()` and `label()`, so a cell is a display string or
None. A parse back into numbers is unavoidable on either path. The two reasons that survive are
the ones that actually decided it: charting through the analysis keeps charts inside the contract
gate, and `Output.summary` carries the sentences Rule 4's "key values" needs
(`summary[0]` is `"14 of 14 row(s) analysed."`). The choice stands; the argument for it was
one third wrong.

The consequence for this step is the design: the parse is isolated in one function with its own
tests, rather than spread through eight drawing functions.

## What `number()` does that the parser must survive

From P11's probe and base.py:41-78 -- thousands separators (`'1,234.56'`), four-place rounding,
trailing zeros stripped, `None` preserved as `None`, `nan` and `inf` returned as the strings
`'nan'` and `'inf'` (P8-D1), a `Decimal`'s own scale kept, and `-0` for a negative that rounds
away. A group label is a string that is not a number at all, which is how the parser tells a
dimension column from a measure column.

## What this step builds

`src/analytics_agent/charts/render.py`:

- `CHARTS_DIRNAME = "charts"` and `charts_dir(workspace_id)`, beside `results/` -- guide line 721
  puts charts in the workspace next to outputs.
- `KINDS`: line, bar, grouped_bar, scatter, histogram, box, heatmap, waterfall (guide line 943).
- `as_number(cell)`: the inverse of `number()`, returning `float | None`, refusing `nan`/`inf`
  and anything non-numeric.
- `series_from_output(output, x=None, y=None)`: the x labels, the named series, and a count of
  what was dropped and why.
- `Chart`: path, kind, label, created_at, dataset_name, description, key values, and `to_text()`.
  Modelled on `util/results.Result`, including the rule that no accessor returns the bare path.
- `render(...) -> Chart`: screens nulls, draws with the backend pinned to Agg, closes the figure
  in a `finally` (P11-D6), writes the PNG.

## Predictions

1. Parsing `'1,234.56'` needs only a comma strip and `float()`; `'-0'` parses to `-0.0`.
2. A digest assertion on a rendered PNG is stable across runs (P11-D7), so a test can pin one.
3. Screening nulls before matplotlib sees them makes the bar case (P11-D4's TypeError)
   unreachable, so no test will be able to provoke it through `render`.
4. The suite rises by the number of new tests and nothing existing moves, because no existing
   module imports `charts/`.

## Outputs

**1. Probe of a real Output** (before any code): headers `['group','n','mean','stddev','skew']`,
row `[('a','str'), ('6','str'), ('11.5','str'), ('1.8708','str'), ('-0','str')]`, and
`summary[0]` = `'14 of 14 row(s) analysed.'`. This is what produced the correction above.

**2. src/analytics_agent/charts/render.py** written whole with `cat >`, 443 lines, max width 99.
Digest `6bd9de77dbed7ab25baee6689c54140f16ae45b8b25b924cf9e246a4a0c569eb`.

**3. tests/test_charts_render.py**, 26 tests. First run: **25 passed, 1 failed**, and the failure
was the test's arithmetic rather than the code -- it asserted the lowest value of
`[4.0, 3.0, 2.0, 1234.56]` was 1 when it is 2, at `east`. The rendered line was right all along:
`one: lowest 2 at east, highest 1,235 at west, first 4, last 1,235, 4 point(s)`. Corrected, and
the series is now spelled out beside the assertion so the next reader does not repeat it.
Digest `d62927aacb4d83f8080bb9a9895da80dcf874ca10435388f2087d8be4d8f25f5`.

**4. Predictions, scored.** All four held.

1. The parse needed only a comma strip and `float()`; `'-0'` parses to `-0.0`, which equals 0.0.
2. Two renders of the same data are byte-identical, so the digest assertion is in the suite.
3. Null screening made matplotlib's `TypeError` unreachable through `render` -- no test can
   provoke it, because a refusal in this project's words fires first. That was the point.
4. Suite 1672 -> 1698, +26, and nothing existing moved.

**5. Final.** Full suite 1698 passed. Acceptance unchanged at 99/0/2, 19/0/0, 35/0/1, as it
should be while nothing in src/ imports charts/. Recorded as P11-D8 to P11-D15 and C82.
