# Phase 14 Step 5: the two open items -- workspaces expire, cleaning gets a screen

Opened 24/09/2026 in a cloud session (Linux, no Postgres, no .env). Closes P14-O1 and P14-O2.

## Measured before designing

M1. What cleaning the web app must offer, on the fixture P14-O2 names. merged_multiheader.xlsx,
uploaded, drafted and confirmed through RealBackend, then clean.tools.propose_cleaning_plan:

    unresolved [] []
    True
    merged_multiheader
    1 change(s) proposed for merged_multiheader (150 row(s)). Nothing has been changed.
      C001  CONVERT_TYPE on order_date: read order_date as DATE (150 row(s))
    CleaningAction(action_id='C001', kind=<ActionKind.CONVERT_TYPE: 'CONVERT_TYPE'>,
      intent='read order_date as DATE', sql='CREATE OR REPLACE TABLE "merged_multiheader" AS
      SELECT * REPLACE (TRY_CAST("order_date" AS DATE) AS "order_date") ...', column='order_date',
      rows_affected=150, values_lost=0, loss_unit='value', sample=())

   The stored CleaningAction already carries every field a screen needs (id, kind, column,
   intent, SQL, counts, loss, sample). The screen reads plan.latest(), never the text.

M2. What a workspace weighs and what a READ does to its files. clean_sales.csv loaded, contract
confirmed, summary_stats computed, a report built, then a snapshot of every file's mtime; one
second later list_datasets, list_artifacts and draft_contract; snapshot again.
Expected: a few MB, mostly session.duckdb; opening the database changes its mtime.

    files 9 bytes 1634484
      contracts/clean_sales.yaml 938
      reports/clean_sales_20260924-111808.md 2327
      results/summary_stats_20260924-111808.csv 269
      session.duckdb 1585152
      uploads/clean_sales.csv 29414
    changed by reads: []

   The size prediction held (1.6 MB, 97% the database, for a 29 KB upload). The mtime prediction
   was WRONG: reads touch nothing. So file times cannot tell a person who is still reading from
   one who left -- an expiry keyed on them would delete a workspace in use. Hence decision 2.

## Decisions

1. Expiry is age-based, and "age" is the time since this workspace was last USED.
2. Use is recorded, not inferred: every RealBackend call on a workspace that exists touches
   `<workspace>/.last_used` (M2: reads leave no other trace). Age = the newest of that marker and
   every file's mtime, so a workspace from before the marker existed is aged by its files.
3. Only web workspaces are ever swept: names matching ^ws_[0-9a-f]{12}$. "local" (Claude
   Desktop's) and anything else under workspace/ is never touched.
4. A workspace whose lock is held is skipped, not waited on.
5. When: at most once an hour, from new_workspace_id() (a new visitor is when disk grows), and
   on demand from scripts/sweep_workspaces.py for a cron. TTL from ANALYTICS_WORKSPACE_TTL_HOURS,
   default 72; 0 disables the sweep.
6. Cleaning screen: the Backend contract gains `propose_cleaning(ws, dataset)` returning a
   CleaningProposal of CleaningStep rows, and `apply_cleaning(ws, dataset, approved_ids)`
   returning an ActionResult. The screen shows each step with its SQL and loss, pre-ticks only
   what the engine itself suggests (lossless, conflict-free), and applies exactly what is ticked,
   in the order shown. Refusals (stale plan, conflict, unknown id) come back as Refusal.
7. The assistant's note for propose/apply_cleaning_plan points at the Cleaning screen, and the
   system prompt names it.

## Commands

1. tests for the sweep (tests/test_real_backend.py): old ws_ removed, fresh kept, a read keeps
   one alive, "local" and a non-ws name never removed, a locked one skipped, TTL 0 disables.
   Expected: fail before the code, pass after.
2. tests for cleaning: real backend on merged_multiheader proposes C001 with suggested=True,
   applies it, the contract then confirms with order_date as the date; an unknown id refused;
   nothing approved refused. UI: the Cleaning screen renders, ticks the suggested step, applies.
3. Engine suite; UI suite; acceptance scripts; eval.
4. Records; commit and push.

## Results

1. Sweep tests (7, in tests/test_real_backend.py): an idle ws_ removed and a fresh one kept; only
   ws_ + 12 hex ever swept ("local", "ws_short", upper-case hex, "mine" at 400 days all kept); a
   read keeps a workspace alive; looking at a missing workspace creates nothing; a workspace whose
   lock is held is skipped, then swept once released; TTL 0 is off; a second new visitor within
   the hour does not sweep again.

       23 passed in 5.46s

   1.1 Falsified: workspace.touch() made a no-op.
   Expected: test_a_read_keeps_a_workspace_alive fails, the rest pass.

       FAILED tests/test_real_backend.py::test_a_read_keeps_a_workspace_alive - Asse...
       1 failed, 22 passed in 4.93s

   Restored from a copy; the diff shows only the intended files.

   1.2 The suite must never sweep the developer's real workspace/: tests/conftest.py and a new
   ui/tests/conftest.py set ANALYTICS_WORKSPACE_TTL_HOURS=0 for every test; the sweep's own tests
   point workspace.WORKSPACE_ROOT at tmp_path and set 72.

   1.3 `scripts/sweep_workspaces.py --dry` on this machine:

       0 idle web workspace(s) older than 72h:

2. Cleaning tests. Real backend (4): merged_multiheader -- a contract naming order_date as the date
   is refused before cleaning; propose_cleaning returns [("C001", "CONVERT_TYPE", "order_date")],
   suggested, lossless, 150 rows, TRY_CAST in its SQL; apply_cleaning(["C001"]) ok; the next
   proposal is empty ("Nothing to clean"); the same contract then confirms. Refusals: [] ->
   NOTHING_APPROVED, ["C999"] -> ACTION_NOT_IN_PLAN, unknown table -> DATASET_NOT_LOADED. A
   never-written workspace asked to clean creates nothing.

   2.1 My first lossy-step test used broken_sales.csv, predicting a lossy step. WRONG: loaded
   through the web path it has nothing to clean at all ("Nothing to clean in broken_sales. 186
   row(s)..."), because the loader already types every column. The test now uses
   mixed_types.xlsx with every column forced to VARCHAR, as phase 6 reads it: its lossy steps
   are never suggested and each carries a sample, and at least one lossless step is.

       27 passed in 7.13s

   UI (6 new): the Clean screen renders (fake and real); on the fake, C001 pre-ticked and C002 not,
   the loss warning names 'north'; ticking C002 and applying reports "Applied C001, C002" and the
   fresh look says "Nothing to clean"; nothing ticked disables Apply. On the real engine through
   the widgets: C001 ticked, "Apply 1 step(s)" clicked, then "Nothing to clean" and order_date
   typed DATE. Fake backend: ids, suggestion flags, refusals.

       43 passed in 10.98s

3. Suite, acceptance, eval.
   Expected: engine 1839 + 11 = 1850; UI 43; acceptance as measured this morning in this
   container (no Postgres: 55/0/3, 0/0/1, 0/0/1, 26/0/0, 36/0/0); eval 76/76.

       1850 passed in 75.13s (0:01:15)
       phase8: 55 passed, 0 failed, 3 skipped
       phase9: 0 passed, 0 failed, 1 skipped
       phase10: 0 passed, 0 failed, 1 skipped
       phase11: 26 passed, 0 failed, 0 skipped
       phase12: 36 passed, 0 failed, 0 skipped
       SCORE: 76/76 (100%)

   Held. The phase 8-10 shortfall against the recorded 99/0/2, 19/0/0, 35/0/1 is the container,
   not the change: every extra skip reads "BLOCKED: no configured source named 'olist'." The
   same figures were measured before any edit in this session.
