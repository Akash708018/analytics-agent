# Recheck: profiling, cleaning, the web UI, and a check on the assistant's figures (25/09/2026)

Asked for after an external review of a web-app answer on `retail_fixture.csv` (224,955 rows): the
2025 revenue, cost and margin by region were exact, but the answer's data-quality notes said
`customer_age = 'unknown'` in 3,470 rows (the file holds 3,471), blank `customer_state` in 3,470
(3,473), and extreme unit prices at "5-20x list price" (all 25 are 19.42x to 20.58x).

## Where 3,470 came from

Not a tool. `profile_column` says 3,471 and 3,473 (command 1). The figures are in the contract's
caveats (`workspace/ws_e662a43ecb59/contracts/retail_fixture.yaml`, lines 91-100), typed on the
Contract screen from the fixture generator's notes. `Gate.caveats` appends a contract's caveats to
every analysis summary verbatim, and the system prompt says "Carry every caveat a result prints"
-- so the model repeated a person's note as a measured finding. Nothing checked a caveat against
the table.

## Commands and output

1. The engine on the raw file (load_csv, profile_dataset, profile_column x4, propose_cleaning_plan),
   original code. Expected: 3,471 and 3,473 from the profiler. Output as expected, plus:
   - C004 CONVERT_TYPE delivery_date -> DATE "3,030 value(s) will be discarded" -- the dd/mm/yyyy
     values. `proposed_type` accepted the plain cast (98.1% >= CONVERT_MIN_SHARE) and the formats
     reader `_date_conversion`, which reads both, was never tried.
   - rating: "Most frequent value(s), 7 of 6 distinct" (NULL counted as a listed value), and
     "N/A x6,833" for a value written `n/a` (the breakdown grouped by `upper(trim(...))`).
2. Baseline, before any change: `uv run pytest -q` 2104 passed, 1 skipped; UI 50 passed.
3. Fixes (below), then command 1 again: C004 "read delivery_date as DATE, from the date formats it
   is written in; numeric dates read day first" -- no loss line, and now in the NEXT STEP's safe
   set; "6 of 6 distinct and (null)" (predicted "5 of 6": wrong -- `n/a` is the sixth value);
   "n/a x6,833". C004 applied: 157,538 DATE, 67,417 NULL (= the Store rows), 13 delivered before
   ordered (the fixture's 13).
4. `propose_dataset_contract` with the stored 13 caveats:
   "CAVEAT DIFFERS FROM THE DATA ... says 3,470; the table holds 3,471" and "... 3,473"; 120
   duplicates and `units = -1` (8) checked and agree; 9 not a count the engine can check.
5. Browser, real backend, a copy of the web workspace: Contract shows both differences as warnings
   above Confirm; Clean's C001 card was ~2,000 characters of row JSON under "That is information,
   not absence" -- replaced; C004 shows no loss.
6. Ask, live: no answer. Gemini's daily quota for gemini-3.8-flash was spent, the next model
   answered 503 "high demand", and Groq answered HTTP 413 -- 8,917 tokens requested against its
   8,000 tokens-per-minute limit once six tool replies were in the conversation. The figure check
   was therefore not seen live; it is covered by tests/test_verify.py with scripted sessions.
7. All checks after the change:

       uv run pytest -q                      # 2127 passed, 1 skipped
       uv run --group ui pytest ui/tests     # 51 passed
       uv run python tests/test_phase8.py    # 99 passed, 0 failed, 2 skipped
       uv run python tests/test_phase9.py    # 19 passed, 0 failed, 0 skipped
       uv run python tests/test_phase10.py   # 35 passed, 0 failed, 1 skipped
       uv run python tests/test_phase11.py   # 26 passed, 0 failed, 0 skipped
       uv run python tests/test_phase12.py   # 36 passed, 0 failed, 0 skipped
       uv run python eval/run_eval.py        # SCORE: 76/76 (100%)

## What changed

- `contract/caveat_check.py` (new): a caveat carrying one row count, of four shapes (exact
  duplicates; a quoted value in a column; a blank column; a column compared with a number), is
  counted against the table. `propose_contract` adds the result to its notes, differences first.
  Anything else is "not checked", never guessed; a quoted token absent from the table (the loader
  read `-` as NULL) is not checked rather than "differs".
- `state.py`: a person's caveat is printed as "Declared in the contract, not measured: ...".
- `webapp/verify.py` (new) and `webapp/agent.py`: every figure in the model's answer is looked for
  in the tool replies it read -- found (as written or rounded), worked out (sum, difference, ratio,
  percentage change of two replied figures), declared (only in a declared caveat), or unsupported.
  An answer with declared or unsupported figures is sent back once with the list and no tools; the
  rewrite is shown unless it is worse. `ChatTurn.verification` carries one line; Ask shows it as a
  caption, or a warning on a miss. Sessions gained `add_user`. The prompt says to attribute a
  declared caveat ("the contract notes ...").
- `clean/detect.py`: `_more_dates` -- where the formats reading reads more values than the plain
  DATE/TIMESTAMP cast, it is offered instead.
- `profile/column_profile.py`, `profile/table_profile.py`: NULL is not counted among the distinct
  values shown or hidden; a missing token is named as the column writes it.
- `ui/screens/clean.py`: exact duplicates say one of each is kept, rows behind an expander; other
  samples cut at 80 characters. `ui/screens/contract.py`: caveat differences as warnings.

## Not done here

- Groq's 8,000 TPM limit: the request grows by up to 8,000 characters per tool reply
  (RESULT_CHARS), so a question needing several analyses cannot finish on the free tier.
- Ask shows only "Reading the data..." while the provider layer sleeps on 429/503 (up to 60 s a
  retry); this run waited about seven minutes before the failure.
- "5-20x list price" was a caveat too, and has no count shape; it is carried as declared.
