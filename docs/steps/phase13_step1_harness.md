# Phase 13 Step 1 - the eval harness, and what each suite can actually measure

21/09/2026. Baseline 3ceaa10. Measured before starting: 1759 passed; acceptance 99/0/2, 19/0/0,
35/0/1, 26/0/0, 36/0/0.

Guide line 963, marked DO NOT SKIP: 30-40 gold questions across the fixtures with known answers,
in three suites -- Correctness, Behavioural, Regression -- including cases where the correct
behaviour is to refuse or caveat. Files: `eval/gold_questions.yaml` and `eval/run_eval.py`. The
directory is empty.

## The problem this step has to solve first

**Behavioural asks about an agent, and there is no agent here.** "Does the agent recover from a
gate refusal in one retry? Does it call confirm_ingest_spec without being told twice?" Running a
model against the server and grading it is a different project, and a number produced that way
measures one model on one day.

The property underneath is testable without one. Every refusal in this codebase carries
`next_call`, and `Refusal.__post_init__` already rejects one without parentheses -- because "an
instruction the agent cannot execute is how the apology loop starts". What nothing does is
**execute it**. A refusal recovers in one retry if the call it names, made verbatim, succeeds.
That is stronger than watching a model do it once: it tests the property rather than a sample.

## What a known answer has to be

Computed independently of the tool under test, or the suite tests the tool against itself. For
these fixtures that means SQL run directly against the file, or a count the generator fixes. A
gold answer that came from `compute_analysis` would pass forever, including when both are wrong.

## Scope of this step

The harness and the mechanism of all three suites, with a few questions each -- enough to prove
the format carries them. Filling out to 30-40 is Step 2. Writing forty questions against a
format nobody has run is how a format turns out wrong forty times.

Regression maps to the register at guide line 1077: bounded fill is **F14**, multi-header CSV
typing **F12**, read-only merge parsing **F11**, CTAS type conversion **F15**.

## Predictions

1. The harness can express all three suites in one YAML shape: a question, the suite, what to
   run, and what is expected -- a value, a refusal reason, or a phrase that must appear.
2. Correctness answers computed in SQL against the fixture agree with what the tools return.
3. The four regression traps all have mitigations already in the tree; the tests will pass on
   the first run, because F11, F12 and F14 are marked verified by execution in the register.
4. **Several `next_call` values will not be executable verbatim.** I have read two already:
   `list_datasets() to see what is already here` and
   `propose_dataset_contract(dataset_name="x"), show the draft to the user, then
   confirm_dataset_contract once they agree`. Both carry prose after the call. The constructor
   checks for parentheses, which both have, so nothing has caught it. If that holds it is a real
   finding: F1's whole mitigation is instructional refusals, and an instruction with prose
   glued to it is one an agent has to parse rather than follow.
5. The behavioural suite will therefore need a rule about what counts as executable, and that
   rule is the finding rather than a workaround.

## Commands

1. Inventory every `next_call` in the codebase and test which are executable verbatim.
2. Write `eval/gold_questions.yaml` and `eval/run_eval.py`.
3. Run it; record what each suite measured.
4. Record as P13-D1 onward, open items for anything found, commit.

## Outputs

**SCORE: 27/28 (96%).** correctness 5/5, behavioural 18/19, regression 4/4.

**Predictions 1, 2, 3 and 4 held. 5 held in a way I had not expected.**

Prediction 3: all four regression checks passed first run -- F11 three merge ranges from sheet
XML, F12 types `['BIGINT','DATE','DOUBLE','VARCHAR']` with the first row still data, F14
`col3='Dimensions region' col6='Measures units'`, F15 order_date DATE with 150 rows before and
after.

Prediction 4, the one this step was for: **B04 fails.** `list_datasets() to see what is already
here` is a sentence with a call in it, and an agent has to parse it rather than follow it.

**Three of my own errors, each caught by a measurement disagreeing with another.**

1. The contract would not confirm: `PROVISIONAL analysis_window`. I omitted the window the
   Phase 12 script supplied. The proposal said exactly what was missing.
2. C02 asserted 4 and the tool returned 5. The tool was right: `count(DISTINCT region)` excludes
   NULL and P8-D5 keeps NULL as its own group. The gold answer was the answer to a different
   question.
3. B05 was classified `needs_decision` and is not: the refusal names a clean
   `propose_dataset_contract(dataset_name="clean_sales")`.

**And one in the roster, caught only because two measurements disagreed.** It first reported
0 of 37, having rendered f-strings as `dataset_name=""x""` -- doubled quotes, a syntax error
every time. A probe run minutes earlier had said 22. Nothing about "0 of 37" looked impossible;
the disagreement is what caught it.

**The two numbers are both right and answer different questions.** The probe's regex asked
whether a NEXT STEP *looks* like a call: 22 of 37. The harness asks whether it is one this
process can make -- a registered tool, no positional arguments, literal values: **16 of 37
(43%)**. `propose_dataset_contract(dataset_name="x", primary_key=[...])` looks like a call and
is not one.
