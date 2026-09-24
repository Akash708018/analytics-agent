# Phase 14 Step 14: targeted regression of the Step 13 findings, and Gemini vs Groq as the planner

The user's handoff (24/09/2026): do not repeat the cross-domain benchmark; prove every defect,
performance problem and harness fault it found with before/after evidence, then benchmark two
free-tier LLMs as the planning layer over the deterministic engine.

## Revisions

- ORIGINAL: `2d3d52f` (src identical to `f5dd3d4`, the tree the cross-domain benchmark measured),
  checked out as a detached worktree at /home/user/aa-orig.
- FIXED: branch `step14-fixes-wip` (worktree /home/user/aa-fixes), merged into
  `claude/trusting-edison-en0jnk` once the benchmark's last phases (which measure the original
  code in the main tree) have finished. Every "after" is re-run on the merged tree so that one
  commit stands behind all of them.

## Plan (commands in order)

1. `uv run python scripts/targeted_regression/run.py cases` -- each case in its own process,
   against the original src, then the fixed src (scripts/targeted_regression/runner.py checks
   the import came from the named tree). Cases: D1 D2 D3 D4 D5 D12 RECS (D6-D9)
   PROFILE_CORRECTNESS PROFILE_PERF (P1) CLEANING PRESCREEN (P2) COHORT (D10) WELCH (D11)
   PAGING (D13) CHART_ISOLATION. The light cases run under `nice -n 19` while the benchmark's
   10M tier runs; the performance cases wait for an idle machine.
2. `uv run python scripts/targeted_regression/run.py hj` -- phases H and J of the cross-domain
   benchmark on the fixed code, into /tmp/tr_hj; "before" is the benchmark's own corrected
   rerun of H and J on the original code.
3. `uv run python scripts/targeted_regression/run.py report` -- judges each case against the
   expectation written in JUDGES before any result was read, writes
   docs/benchmark/targeted_regression/*.json and summary.md.
4. The six suites, the eval, UI, scenario matrix, stress matrix, benchmark tests.
5. LLM benchmark (scripts/llm_benchmark/, docs/benchmark/llm_benchmark/RUN.md): planner (120),
   research (20), end-to-end (40, fixed code), report.

## Predictions, stated before the measured runs

- D1-D5, D12, D6-D9, D13: every original failure reproduces on 2d3d52f; every case passes on the
  fixed tree; every control is unchanged.
- profile_column (four sales columns): 1M about 5 s before, 0.3-0.8 s after; 10M about 52 s
  before, 3-6 s after. Growth 1M->10M stays near 10x on both, because the per-column work was
  always linear; what changes is doing it once rather than for all 19 columns.
- propose_cleaning_plan on the dirty financial 1M: about 2x faster, the same actions word for
  word; date-format queries fall to near zero on id and label columns.
- cohort heatmap at 100k: 10,692 characters before (measured in Step 13), under 3,000 after.
- H on the fixed code: no exception; isolation all PASS. J: 6 of 6 PASS.
- LLM: no score is predicted. The Gemini free tier may run out mid-run; Groq cannot run until
  `api.groq.com` is allowed by the environment's network policy.

## Results

### 0. Decisions taken before any scored LLM item

- 0.1 The handoff says "Grok"; the product is configured for Groq (webapp/llm.py). Asked: the
  user chose Groq. No other model is included.
- 0.2 The configured Gemini alias `gemini-flash-latest` is served by `gemini-3.8-flash`, whose
  free tier allows 20 requests a day (measured: `generate_content_free_tier_requests, limit:
  20, model: gemini-3.8-flash`) -- about 19 days for ~380 requests. Asked: the user left it to
  me. `gemini-2.5-flash` answered 404 ("no longer available to new users"); the app's own
  ladder entry `gemini-flash-lite-latest` answered, served by `gemini-3.5-flash-lite`. That
  concrete id is pinned (GEMINI_MODEL, which the app honours) for every Gemini item. The 3
  error-only records made under the alias were moved aside unscored.
- 0.3 Rubric faults found by the smoke run (3 planner items, 1 research case, on a scratch
  directory), fixed before any scored item: a declined causal question lost 10 for naming no
  metric; SUPPORTED_ASSOCIATION against a gold NOT_ESTABLISHED scored 0 though both are
  non-causal (now 15 of 30; ESTABLISHED stays 0). Scores are recomputed from the stored answers
  at every report, so one rubric scores both providers.

### 1. Targeted regression, light cases (fixed tree at fc6ffd8 / 6f67a57; to be re-run merged)

- 1.1 RECS, D1 and D3 first met a harness fault: a NEXT STEP parse returned a key named `tool`,
  colliding with the observation's own argument -- only on the fixed code, whose next steps are
  runnable. Renamed `next_tool`; re-run on both revisions.
- 1.2 D3 first called summary_stats with `measure=`, which it does not take, so the old
  failure never reproduced and the controls looked changed. G's exact calls are summary_stats
  (all measures) and trend(measure, grain): re-run.
- 1.3 D2's control `tiny_two_each` changed: my D11 fix printed Welch df with one decimal, so
  1.471 became 1.5. A real regression, caught by the control. Fixed in src (four significant
  figures below 1,000, the separator form above), test extended, commit 6f67a57.
- 1.4 After 1.1-1.3: 55 cases, 0 failing; every targeted original failure reproduced
  -- 26 in all, counted from before_after.json: BinderException 8, ZeroDivisionError 5,
  ConversionException 1, IndexError 1, and 11 of the non-exception kind (a next step that could
  not run, a cap applied without a word, a chart reply judged against isolation).

### 2. The original benchmark's last phases, and what they found

- 2.1 Sales 10M (original code): 63/63 checks, 0 crashes, 2,618 s, worker peak 511 MiB. Its two
  exceptions are D5 at 5,851,188 tied values (INT64 overflow in the tie term): the D5 case now
  adds a 6M-row point (5,739,130 ties) beside 2.3M.
- 2.2 J (reproducibility, original code, corrected setup): 5 of 6 PASS. crm 100k printed one
  total two ways in two identical runs -- 3,032,008,136.98 and 3,032,008,136.9801 (summary_stats,
  group_compare, cross_tab). Measured: the DISTINCT that drops duplicates stores rows in the
  order its parallel hash leaves them (4 orders in 20 rebuilds of one file) and a DOUBLE sum
  depends on order (19 values in 20; fsum 2). The same table queried 60 times gave 1 value:
  the variation is the rebuild, not the sum. D14, fixed: the rebuild keeps first occurrences
  in file order (GROUP BY ALL with min(rowid)); 12 rebuilds, 1 order, 1 sum; NULL rows collapse
  as under DISTINCT; the counts use the same grouped projection, keeping the rule that a count
  and its statement share one expression (tests/test_cleaning_sql.py caught my first draft).
- 2.3 The final report of the original run: 6,159,473 checks, 0 incorrect; 12,763 calls; 0 worker
  crashes, 18 exceptions (D1-D5, D12).
- 2.4 Merged `step14-fixes-wip` at a7573c6: engine suite 1994 passed.

### 3. Targeted regression, heavy cases (merged tree a7573c6)

- 3.1 PROFILE_CORRECTNESS, first run, was a harness fault: the case held a read-only connection
  open while calling profile_column, so every call on BOTH revisions raised ConnectionException,
  and the judge -- comparing texts -- called two equal failures "unchanged". Calls now run
  first; the judge requires a real result (and a refusal for the missing column). The invalid
  raw files are kept at /tmp/tr_data/invalid, not in the repository. The same weakness was
  closed in the cleaning and D2 judges.
- 3.2 D5 (after): 8 of 8 match scipy's statistic and p to every printed digit at 100k, 1M, 2.3M
  and 6M rows; before, 2.3M and 6M raised OutOfRangeException.
- 3.3 CLEANING, 1M rows: dirty 23.01 s -> 14.94 s (1.54x), clean 16.22 s -> 7.91 s (2.05x);
  date-format query time 8.86 s -> 0.20 s and 8.21 s -> 0.21 s; 357 and 260 detector queries
  on both revisions; the same actions (kind, column, counts). The texts differed only in the
  example values each action quotes -- which a second proposal on ONE revision also changes:
  five sample queries (and the profile's cast examples) ended in LIMIT with no ORDER BY. D15,
  LOW. The patch is held back (/tmp/tr_data/d15.patch) until the timing cases finish, so that
  they measure the merged commit and nothing uncommitted.
