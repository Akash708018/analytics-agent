# Cleanup Step 4: a chart refusal whose recovery draws the chart; three dead backups removed

Found by the pre-Phase-14 audit of 21/09/2026, which checked completeness from the code rather
than from the guide or the ledger. All six checks and the eval were green; an end-to-end run of
every analysis and every chart kind through server.py found the one defect below.

## The defect

render_chart refuses a single-measure kind (line, bar, histogram, waterfall) handed a result with
more than one measure, and says "Name one with y". P11-D13 -- refuse rather than pick -- is right
and stays. The NEXT STEP is wrong: it names `compute_analysis(...)` with the analysis parameters.
Made verbatim, that call succeeds and returns a table. The agent asked for a chart and the
recovery does not draw one, so B11's "recovers in one retry" passes against a call that does not
recover. The eval's retry checks that the named call succeeds, not that it is the call that
completes what was asked.

Measured in the audit: 7 of 16 chart calls across all eight kinds refused this way when y was
omitted (trend/line, top_n/bar, group_compare/bar, distribution/histogram,
growth_decomposition/waterfall, mix_shift/waterfall, seasonality/line); all 16 drew when y was
named.

## The fix

1. `ChartRefused` carries `choices`, the measures the result offered, set only by the
   single-measure refusal in `_draw`. Every other ChartRefused has none.
2. With choices, analysis/tools.render_chart names `render_chart(...)` -- the analysis
   parameters, the chart kind, x and title if given, and y set to one choice. Which one: the
   first whose name contains the analysis's `measure` argument, else the first offered. The WHY
   still lists every choice and the DETAIL says any of them works as y.
   This does not reverse P11-D13. D13 forbids the renderer drawing a measure nobody named; a
   suggested call that names its y in plain sight, beside the full list, is a choice the caller
   makes by making it.
3. Without choices (an unknown kind, too few measures for a two-measure kind, a non-finite
   value) the recovery stays `compute_analysis(...)` -- there is no y that fixes those.
4. eval: a behavioural question may carry `retry_tool`, and B11 does: the NEXT STEP must name
   render_chart. Falsified first against the unfixed tree (P13-D9).
5. Delete `src/analytics_agent/{config,server}.py.phase1.bak` and
   `src/analytics_agent/contract/evidence.py.step1.bak` -- tracked since Phase 1 and the
   evidence step, referenced by nothing in src/, tests/, eval/ or docs/steps/.

## Commands and outputs

1. Falsify: add `retry_tool: render_chart` to B11 and the check to run_eval.py, run the eval
   against the unfixed src/.
   Expected: SCORE 75/76, the one failure being B11's new retry-tool check naming
   compute_analysis.
2. Apply the fix (render.py, tools.py), update `test_a_chart_refusal_says_the_analysis_was_fine`
   and add tests for the choice and the no-choice path.
   Expected: pytest 1759 -> 1762 passed.
3. Delete the three .bak files. Expected: pytest unchanged, `git ls-files src | grep -v .py$`
   prints nothing.
4. The five acceptance scripts. Expected unchanged: 99/0/2, 19/0/0, 35/0/1, 26/0/0, 36/0/0.
5. The eval. Expected: SCORE 76/76 (100%).
6. Records: C93 and CL4-D1/D2 in decisions.md, CLAUDE.md tallies. Commit and push.

## Results

1. Falsify. `SCORE: 75/76 (99%)`, the one failure `B11 recovers through render_chart
   (compute_analysis)`. As expected.
2. Fix and tests. `1762 passed`. As expected.
3. Backups removed. `1762 passed`; `git ls-files src | grep -v '\.py$'` prints nothing.
4. Acceptance: 99/0/2, 19/0/0, 35/0/1, 26/0/0, 36/0/0. Unchanged, as expected.
5. Eval: `SCORE: 76/76 (100%)`; B11's NEXT STEP is now
   `render_chart(dataset_name="clean_sales", analysis_type="summary_stats", chart="bar", y="n")`
   and the retry draws. Not predicted: the roster reads 25 of 36, not the 26 of 37 last
   recorded. Measured on HEAD with this step stashed, it also reads 25 of 36 -- the drift
   predates this step.
6. Records: C93, CL4-D1, CL4-D2 in decisions.md; CLAUDE.md tallies.
