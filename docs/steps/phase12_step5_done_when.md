# Phase 12 Step 5 - the Done-When, end to end on merged_multiheader.xlsx

21/09/2026. Baseline e420f05. Measured before starting: 1759 passed; test_phase8.py 99/0/2;
test_phase9.py 19/0/0; test_phase10.py 35/0/1; test_phase11.py 26/0/0.

Guide line 953: **one end-to-end run on `merged_multiheader.xlsx` produces a complete document.**
This is the first time the whole pipeline runs in one script -- ingest spec, load, profile,
clean, contract, validate, analyse, chart, report -- so it is the step most likely to find
something, and the predictions below say where I expect it.

## The fixture, measured before writing anything

`draft.draft_for_path` proposes header rows [1, 2] with `bottom_only`, and the load gives 150
rows as `merged_multiheader`:

    order_id     VARCHAR      order_date   VARCHAR
    region       VARCHAR      product      VARCHAR
    channel      VARCHAR      units        BIGINT
    unit_price   DOUBLE       revenue      DOUBLE

Two of those matter. **`order_date` arrives as VARCHAR**, so a contract naming it as the date
column is a contract over text, and the temporal tiers will either refuse or read it wrongly.
**`revenue` is DOUBLE**, which is the type that broke growth_decomposition until C85 -- so this
run exercises that fix against real data rather than a four-row fixture.

## What "a complete document" has to mean

Nine sections with something in each. P12-D11 makes a report with empty sections still complete
in structure, and that is right for a report of work half-done -- but the Done-When is a run of
the whole pipeline, so an empty section here means a step did not happen. `Report.empty_sections`
is therefore the assertion: it should be empty at the end of this script, and a section that is
not is the finding.

## Predictions

1. The ingest spec path loads 150 rows, as Phase 3 already measured.
2. Profiling records a run, so "Data quality" fills.
3. The cleaning proposal offers something on this data -- most likely a type coercion for
   `order_date`, which is text holding dates. If it offers nothing, the cleaning ledger stays
   empty and the document is not complete, and that is the finding rather than a failure of
   the script.
4. A contract over `revenue` (sum), `units` (sum), `unit_price` (none) and dimensions region,
   product, channel confirms, and validation runs against it.
5. Analyses across several tiers run through `server.compute_analysis`, including
   `growth_decomposition`, which would have refused this DOUBLE measure before C85.
6. At least one chart renders through `server.render_chart`.
7. `build_report` produces nine sections with `empty_sections` empty.
8. **Something will need adjusting.** Nine phases have never run in sequence in one process. I
   do not know what, which is why this prediction is worth writing down rather than leaving as
   a feeling.

## Commands

1. Write `tests/test_phase12.py`.
2. Run it and read every clause.
3. Fix whatever prediction 8 turns up, as a numbered sub-step.
4. Record, mark Phase 12 done if the Done-When passes, commit.

## Outputs

**tests/test_phase12.py: 36 passed, 0 failed, 0 skipped.** The whole pipeline, first run.

    order_date arrives as VARCHAR, which is a fact about spreadsheets
    C001  CONVERT_TYPE on order_date: read order_date as DATE (150 row(s))
    1 action(s) applied. 150 row(s) before, 150 after.
    order_date is now a DATE
    Contract stored for merged_multiheader, version 1.
    merged_multiheader: all 6 check(s) passed.
    seven analyses ran, including growth_decomposition on a DOUBLE measure
    the document: .../reports/merged_multiheader_20260921-132910.md  (8,748 bytes)
    all nine sections present, in the guide's order; none had nothing to report

**Predictions 1 to 7 held. Prediction 8 was wrong, and that is the result worth recording.**
It said something would need adjusting, because nine phases had never run in sequence in one
process. Nothing did. The only change after the first run was mine, to a check of my own that
could have passed vacuously.

**The check I fixed.** "No section had nothing to report" first searched for section names
inside a slice of the reply taken after the words "nothing to report" -- so if that wording ever
changed the check would pass without testing anything. It now asserts directly that the phrase
to_text() prints is absent. P9-O11 and C83 were both a check that could not fail; writing a
third one in the step that closes the phase would have been careless.

**Two probes failed before the script existed, and both were mine.** Calling apply_cleaning_plan
without propose_cleaning_plan first meant no plan existed, the conversion never ran, and the
contract validator refused with "date_column 'order_date' is VARCHAR, not a date. A date held as
text sorts lexically and cannot carry an analysis window." That message is the product working.
