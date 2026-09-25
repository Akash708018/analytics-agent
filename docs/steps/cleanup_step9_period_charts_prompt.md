# Cleanup Step 9: which orders drive a month; a chart that keeps its gap; an assistant that does the work

Found by grading the Ask screen's answer of 22/09/2026 12:21 (workspace ws_0b4a3e60bfd6) to: "Using
the deduplicated data, show total order_value by month, split by channel, as a line or bar chart.
Which month is highest overall? Is that peak a real trend or driven by a few orders? What should
the chart show for July?" The one result it fetched was exact for the raw rows and carried the
Cleanup Step 8 copies caveat. The answer failed three of five checks.

## What was established before this document

- The assistant ran 3 of its 8 rounds and deferred the peak question to "a concentration check",
  naming `concentration(dimension=order_id)` -- a whole-year call that cannot say anything about
  November. It could not have answered better from the engine: top_n, concentration and pareto
  rank over the contract's scope, and no analysis narrows to one period. Scope is the contract's,
  not the caller's (Cleanup Step 8).
- The answer, by SQL on the deduplicated rows: November 246,412.22; ORD-00551 (Online) 96,049.00,
  39.0% of it; next ORD-00553 9,577.49 (3.9%). November without ORD-00551 is 150,363.22, below the
  median month 163,606.39. One order, not a trend.
- The 12:17 grouped bar (charts/trend_20260922-121717.png, viewed) has no July slot: 2025-06 sits
  beside 2025-08. `_draw` keeps only x positions where every series has a value, so an absent
  period vanishes from the axis. Its text says "22 of 24 point(s) drawn"; the picture says eleven
  evenly spaced months. The assistant told the person the chart "will automatically show a blank
  for July" -- the product made that false.
- The assistant told the person to "Go to the Cleaning screen". There is none (P14-O2), and the
  tool reply it read carried the note "propose_cleaning_plan: not one of your tools; the person
  does it on no screen yet -- cleaning is not in the web app" (agent._with_screen_notes, applied at
  agent.py:173, matched by the `propose_cleaning_plan(` in the copies caveat).
- It handed the person JSON tool calls to run, including a `chart: "line"` render of a two-channel
  split, which would refuse (line draws one series). The person cannot call tools.
- It explained July's gap as "the data collection period had no orders"; the result says nothing
  about why ("nothing here says whether the business paused or the feed did").

## The fix, in three parts

A. A period on the attribution analyses (analysis/temporal.py, frequency.py, pareto.py).
   `temporal.narrow_to_period(con, gate, scope, period, grain)` returns a Scope holding only the
   rows of one named period. The label is looked up in the generated calendar, as period_compare
   does (P9-D12): a label outside it is refused naming the range; a label inside it with no rows
   narrows to 0 rows and says so. The four-bucket sum still holds: dated rows of other periods move
   to outside_window, undated analysed rows to no_date; method_note names the period.
   top_n, concentration and pareto take `period` (and `grain`, default month). grain without
   period is refused.
B. Charts keep every x slot (charts/render.py). line, bar and grouped_bar place every label on the
   axis and draw only the values present; an x where no series has a value is named in the notes
   as an empty slot. waterfall keeps its filter (a running total cannot skip a part). P11-D4
   measured None as a gap in a line; bars are drawn at the positions that hold values.
C. The assistant's rules (webapp/agent.py SYSTEM): name only the screens that exist; never hand
   the person a tool call or JSON; run the analysis a question needs rather than suggest it while
   rounds remain, and draw the chart when one is asked for; give a cause for a gap only if a result
   states it; when a result says rows are copies and cleaning was asked for, answer on the data as
   it is, labelled, and say cleaning is not in the web app.

## Commands and outputs

1. Baseline. `uv run pytest -q`. Expected: 1867 passed.
2. Falsify: tests for A (tests/test_frequency.py or the file top_n's tests live in, plus
   temporal), B (tests/test_charts_render.py), C (tests/test_agent.py), run on the unfixed src/.
   Expected: every behaviour test fails; guards (grain-without-period refused is new behaviour
   too, so it fails) -- I predict no new test passes before the fix.
3. Apply A, B, C. Expected: new tests pass; suite 1867 + new, 0 failed. Existing chart tests that
   pin drawn counts for grouped_bar may change -- if one does, that is recorded, not adjusted.
4. Live, engine only, through server.py on the ws_0b4a3e60bfd6 upload (read-only copy):
   top_n(dimension=order_id, measure=order_value, n=5, period="2025-11") on the raw rows.
   Expected: ORD-00551 first at 96,049.00; share of the period's total 37.7% (96,049 /
   254,506.43, raw). grouped_bar of the channel split: 12 x ticks, July among them.
5. Live, the assistant, once, on the same question, against a copy of that workspace.
   Expected: it calls top_n with period="2025-11" (or concentration), draws a chart, names
   ORD-00551, names no Cleaning screen, hands over no JSON. A model is not deterministic; this is
   one sample, recorded as such.
6. Acceptance: 99/0/2, 19/0/0, 35/0/1, 26/0/0, 36/0/0. 7. Eval 76/76. 8. UI 37.
9. Records, CLAUDE.md, commit.

## Results

1. Baseline. `1867 passed in 43.51s`. As expected.

2. Falsify. 15 new tests (7 in test_frequency, 4 in test_charts_render, 4 in test_agent), all
   failed on the unfixed src/: `15 failed, 90 passed`. As expected -- no guard passed early this
   time, because every one asserts new behaviour.

3. Apply. test_frequency + test_pareto `48 passed`; charts + tools + matplotlib facts `78 passed`
   -- no existing chart test pinned the old grouped_bar count; test_agent `38 passed`.
   3.1. Printing the new SYSTEM showed an OLD rule contradicting the new one: "If the step is
        something only the person can do (load a file, confirm a contract, approve cleaning),
        tell them where: the Upload & read screen, the Contract screen." -- a rule that names
        cleaning among what a screen does, beside the rule that it has none, and a plausible
        source of the "Cleaning screen". "approve cleaning" removed; a test pins its absence
        (it would have failed on the old text, which held the phrase). C102.
   3.2. server.py's compute_analysis docstring: top_n, pareto, concentration now list period
        and grain.
   Suite `1883 passed` (1867 + 16).

4. Live, engine, on a copy of ws_0b4a3e60bfd6's session.duckdb.
   4.1. THE PREDICTION FAILED. top_n(period="2025-11") through server.compute_analysis:
        `BLOCKED: the analysis produced a result that does not describe itself. ... reason:
        ANALYSIS_RESULT_UNSOUND`. tools._produce checks the result's first summary line against
        the method note of the scope IT built; top_n had narrowed the scope inside itself, so
        its note described rows the tool layer never handed it. The check is right. The unit
        tests called registry.run directly and could not see it. C101.
        Fix: an analysis registers with narrows=True; registry.narrowed() takes period and grain
        off the parameters and narrows the scope before the analysis runs, called from both
        registry.run and tools._produce. The three analyses are back to their own parameters.
        The empty-period sentence ("2024-05 holds no rows") went with the in-analysis code; the
        method note carries it now ("0 of 7 row(s) analysed ... outside the month 2024-05") and
        that test's assertion follows the note -- the claim it tests is unchanged. A tool-layer
        test added: top_n with period through tools. Written after the fix; the failure it
        guards against was observed live in 4.1, not by running it first. Suite `1884 passed`.
   Rerun:
     56 of 604 row(s) analysed. 548 outside the month 2025-11 (within 2025-01-01 to 2025-12-30).
     Share is of 254,506.43, the sum of order_value across all 55 group(s).
     | ORD-00551 | 96,049 | 1 | 37.7% |
     | ORD-00552 | 16,188.42 | 2 | 6.4% |     <- the copied row, visible as rows = 2
     | ORD-00553 | 9,577.49 | 1 | 3.8% |
   As expected: ORD-00551 first, 37.7% of the raw month. The grouped bar
   (charts/trend_20260922-124024.png, viewed): twelve ticks, 2025-07 an empty slot between June
   and August; notes "2025-07 hold(s) no value in any series and stay on the axis as an empty
   slot, not a zero." period="2025-13" refused: "not a month of this calendar, which runs
   2025-01 to 2025-12".

5. Live, the assistant. NOT MEASURED. Two runs, both ended in provider failure:
   gemini "This model is currently experiencing high demand" (503) both times; groq HTTP 413,
   tokens per minute limit 8000, requested 8003 then 8451. Before failing, run 1 called trend
   split by channel and then render_chart(chart="line") on it, refused correctly (a line draws
   one series); run 2 called trend and trend by channel. No final answer, so none of the rule
   checks can be graded.
   5.1. Was the 413 this step's prompt? Measured: SYSTEM 1,090 -> 2,118 characters (~260
        tokens); the run_analysis reply alone is 7,431 characters (~1,850 tokens). Run 2 would
        have been ~8,190 without this step's text, still over 8,000. The overflow is the
        conversation's shape. CL9-O1.

6. Acceptance. 99/0/2, 19/0/0, 35/0/1, 26/0/0, 36/0/0. As expected.
7. Eval. `SCORE: 76/76 (100%)`. As expected.
8. UI. `37 passed in 8.31s`. As expected.

MEASURED VALIDATION line and digests: docs/decisions.md, section Cleanup Step 9.
