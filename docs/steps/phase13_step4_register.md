# Phase 13 Step 4 - the rest of the Failure Mode Register, and closing the phase

21/09/2026. Baseline 06cc992. Measured before starting: 1759 passed; acceptance 99/0/2, 19/0/0,
35/0/1, 26/0/0, 36/0/0; eval SCORE 67/67 over 32 questions, six FMR ids covered (F7, F9, F11,
F12, F14, F15).

The guide asks for regression tests "one test each, mapped to the FMR ID". The register at guide
line 1077 has fifteen. This step covers every one that can be observed without an agent, a
second user or a 1.5 GB file, and says why the one that cannot is left.

## Ground facts, measured before this document was written

    F1   get_workflow_state on a loaded dataset with no contract names propose_dataset_contract
    F3   check_file on a sparse 2 GB .csv (no disk used) -> Verdict.WARN, naming the size;
         a CSV streams, so loadable-with-a-warning is the right answer, not a refusal
    F4   a 50-column result previews 12 and prints "Showing 12 of 50 columns"
    F5   preview_file shows 15 numbered lines ("1: ...") of clean_sales.csv's 501
    F8   the detector exists (preview.PivotVerdict on every Draft) but no fixture triggers it;
         a constructed CSV of region plus twelve month columns reads is_pivot_dump=True,
         "12 of 13 columns are time periods ... This looks like a pivot table export"
    F10  trend on the gapped table names 2024-07
    F13  reset_workspace without confirm is BLOCKED; with it, list_datasets says the workspace
         is empty

Two of my predictions for those were wrong. I expected F8's detection might not exist, and it
does. I expected the F5 probe to count data rows, and it counted zero, because I matched lines
beginning "ORD-" and the preview prefixes each with its line number. The preview was right.

## What is left, and why

**F2**, "IO Error: Could not set lock on file" -- Track B, two or more users. Track B is Phase 14
and is not built. A test here would exercise concurrency the product does not yet offer, and a
green check for a scenario that cannot occur is a false report. It stays uncovered and the
eval says so rather than counting it.

F6 (merged or multi-row headers break the loader) is close to F11 and F14, but those test the
merge parse and the name assembly. F6 is the loader end to end: 150 rows through the spec.

## Predictions

1. Eight new regression checks (F1, F3, F4, F5, F6, F8, F10, F13) all pass first run, since each
   behaviour was observed above. What can go wrong is my check, not the product -- which is
   exactly what C88 was.
2. The regression suite goes from 6 to 14, and fourteen of fifteen ids are covered.
3. Nothing under src/ changes, so the suite and acceptance do not move.
4. The tree is clean after the eval: C90's fence is in mount(), and the constructed files go to
   the scratch workspace, not the repository.

## Also in this step

`CLAUDE.md` has drifted by my own syncs: its first paragraph says "Nothing recorded open except
P9-O4's feature half" twice, and "How a step runs" still says "running all four checks" where
there are six and the eval. Fixed here, since a file loaded into every session that contradicts
itself is the C-series failure in the place it costs most.

## Outputs

**Eight checks added; all passed first run. SCORE 75/75 (100%)**, regression 14/14. Predictions
1, 2, 3 and 4 held -- and prediction 1 turned out to be the wrong kind of good news.

**Every new check was falsified before it was trusted, and one could not fail.** The F10 check
asserted `GAP_MONTH in text`. trend builds its calendar with every period as a row, absent ones
included, so the month was in the table whether or not anything warned about it. Pointed at
2024-03, a month holding rows, it still passed. It now asserts the warning line itself --
"1 month(s) hold no rows and are blank above, not zero: 2024-07." -- and fails on 2024-03.

The others, checked the same way: F1 fails on a workspace where every dataset is contracted; F3's
predicate fails on a 29 KB file (verdict OK); F8's fails on clean_sales; F13's fails on a loaded
workspace ("1 dataset(s)", no "empty"). F4, F5 and F6 assert exact values -- the "12 of 50"
phrase, at most 20 numbered lines, 150 rows -- and plainly can fail.

**Fourteen of fifteen register ids are now covered.** F2 is not, and the eval does not count it:
it is Track B with two or more users, Phase 14, not built.

**Final.** Suite 1759, acceptance 99/0/2, 19/0/0, 35/0/1, 26/0/0, 36/0/0 -- nothing under src/
changed. The tree was clean after every eval run.
