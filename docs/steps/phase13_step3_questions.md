# Phase 13 Step 3 - filling the question set

21/09/2026. Baseline 0510d47. Measured before starting: 1759 passed; acceptance 99/0/2, 19/0/0,
35/0/1, 26/0/0, 36/0/0; eval SCORE 31/31 (100%), refusal roster 26/37 (70%).

The guide asks for 30-40 gold questions across the fixtures, including cases where the correct
behaviour is to refuse or caveat -- "a trend request on a dataset with a missing quarter must
produce a gap warning, not a clean line". There are fourteen, all against one table.

## What the fixtures actually hold, measured

    clean_sales.csv          500 rows, 12 months of 2024, no gap
    broken_sales.csv         186 rows, 19 months spanning 2023-04 to 2025-06, no gap
    gaps_and_dupes.csv       200 rows; the gaps are in the HEADER -- blanks and repeats --
                             and it is the only CSV carrying a literal null sentinel
    merged_multiheader.xlsx  150 rows behind a two-row merged header

So **no fixture has a missing period.** The name gaps_and_dupes is about header blanks and
duplicate column names, not about time. The caveat case the guide names has to be constructed:
load clean_sales, delete a month, and assert calendar_coverage reports it. That is a fair gold
question -- a known condition and a known correct behaviour -- and saying it was constructed is
the difference between a test and a claim.

P9-O2 asked that these span at least three tables. They will: clean_sales, a gapped copy of it,
and merged_multiheader through the Excel path.

## Predictions

1. The harness generalises with a `dataset` field per question; `invoke` stops assuming one
   table.
2. calendar_coverage on the gapped copy names the missing month rather than returning a clean
   line. This is the guide's example and the one I would be most embarrassed to find broken.
3. Regression extends past the four named traps to F7 (no bare file paths) and F9 (coercion
   failures counted), both of which have machinery already.
4. **Roughly twenty new questions will surface at least one product finding.** Fourteen found
   two. I do not know what, and that is the prediction.
5. The score will not be 100% when the step ends, and that is the harness working rather than
   failing.

## Commands

1. Generalise the harness to several datasets.
2. Write the questions to about thirty-four.
3. Run; read every failure and decide whether it is the product or the question.
4. Record, commit.

## Outputs

**32 questions: 14 correctness, 12 behavioural, 6 regression.** SCORE 67/67 (100%), from 31/31
over 14. Three tables -- clean_sales, clean_gapped, merged_multiheader -- and both loaders.

**Prediction 2 held.** calendar_coverage on the gapped copy prints "11 month(s) hold rows and 1
hold none: 2024-07" and "A gap is not a zero -- nothing says whether the business stopped".

**Prediction 4 held: two findings from twenty new questions, one in each direction.**

*B09, a defect I introduced in Phase 11 Step 3.* A chart refusal named
`compute_analysis(dataset_name="clean_sales", analysis_type="frequency")` -- the analysis and
none of its parameters. frequency without its column is refused, so the recovery the refusal
offered was itself refused. Fixed: the call now carries the parameters that were used, rendered
the way the reproduction appendix renders them.

*R09, a gold question accusing the product of something it does not do.* The check searched
`str(result)` for the word "null" and reported F9's mitigation missing. `LoadResult` carries
`coercion_failures` and `coercion_total`, and reading them gives
`10 failure(s) counted per column: {'units': 7, 'unit_price': 3}`. The crash that got me there
was the product working: the default load refuses at row 5101 rather than coercing quietly, and
says what to reload with.

**Prediction 5 was wrong, and I am glad it was.** It said the score would not be 100% at the end
of the step. Both failures turned out to be fixable in the step that found them -- one a real
defect, one a wrong question.
