# Phase 14 Step 3: the real backend -- the UI on the engine

`src/analytics_agent/webapp/real_backend.py` implements `webapp/contract.Backend` on the engine, so
`ANALYTICS_UI_BACKEND=real` runs the Streamlit UI against real files, real contracts and real
workspaces. Chat stays for Step 4 (the model loop); until then `chat` says so, as an error turn.

## Decisions before building

1. In-process, not MCP over HTTP. Every MCP tool returns text; the screens need structure (grid
   cells, columns, unresolved fields), and parsing text is what the contract forbids the UI. The
   backend calls the engine's own functions. P14-D1/D5 say threads on separate workspaces are
   safe; P14-D2/D6 say calls on one workspace must not overlap -- so one lock per workspace id
   around every engine call (P14-D8). Tools that already return text (confirm_ingest_spec, the
   contract confirm) are called as the MCP layer calls them, and their refusals converted once.
2. Workspace ids are "ws_" + 12 hex from `secrets`, validated, and never DEFAULT_WORKSPACE_ID
   (P14-D4: Claude Desktop's process holds "local").
3. Paths from the UI are untrusted. An upload keeps only its base name, must be .csv or .xlsx,
   and lands in <workspace>/uploads/. draft/confirm accept only a path inside that directory;
   read_artifact only a file under charts/, reports/ or results/ of that workspace.
4. A guess is never handed to a form as if it were an answer. Measured before building: with
   `grain` unresolved, propose_contract's contract still holds the guess "one row = one
   order_id". A form prefilled with it and sent back would settle the engine's guess as the
   person's statement. So every field named in `unresolved` reaches the UI blank.
5. confirm_contract re-proposes from the draft's fields and confirms that proposal's JSON only if
   it is confirmable -- the engine, not the draft object, decides.

## Probe, before building (commands run, outputs recorded)

- `draft_for_path(merged_multiheader.xlsx)`: predicted unresolved non-empty. Measured: resolved,
  header_rows [1, 2], sheets ['Sales'] -- the real merge ranges settle it. Prediction wrong.
- `propose_contract(clean_sales)`: unresolved = grain, each measure's definition and agg,
  analysis_window; grain holds 'one row = one order_id' (decision 4); key ['order_id'], date
  order_date, measures units/unit_price/revenue with agg None, dims region/product/channel.

## Commands and outputs

1. tests/test_real_backend.py: Protocol conformance; ids; upload refusals (type, traversal name);
   ingest draft + confirm for the CSV and the merged-header workbook; a path outside uploads is
   refused; datasets listed; contract drafted with unresolved fields blank, refused while
   provisional, confirmed once answered; artifacts from a real render_chart listed and read,
   traversal refused; reset empties; two workspaces isolated; two threads on one workspace
   through the lock raise nothing. Expected: all pass after the build.
2. ui/tests: one AppTest run of app.py with ANALYTICS_UI_BACKEND=real.
3. Engine suite 1787 -> 1787 + new; acceptance unchanged; eval 76/76; UI 26 -> 27.
4. Browser: the UI on the real backend -- upload clean_sales.csv, load, contract, confirm.
5. Records; commit and push.

## Results

1. tests/test_real_backend.py first run: 14 passed, 1 failed -- the conformance test caught
   confirm_contract's parameter named `draft_` (to dodge the `draft` module); a caller passing
   draft= by keyword, as the Protocol names it, would have failed. 1.1: the module is imported
   as ingest_draft and the parameter is `draft`. 15 passed.
   Falsified: handing the guessed grain to the form fails the blank-field test; removing the
   workspace lock fails the concurrency test 3 of 3 runs. Restored: 15 passed.
2. Found reviewing before the first run: web confirmations would export into
   docs/contracts/<ws>/, dirtying the repository per visitor (Cleanup Step 5's namespacing
   applies to every non-default workspace). 2.1: the backend passes export_root = the
   workspace's own contracts/ directory (P14-D19); a test asserts the repository gains nothing.
3. ui/tests: the app runs on the real backend; 26 -> 27.
4. Browser, ANALYTICS_UI_BACKEND=real on :8502: clean_sales.csv uploaded (fetched from a
   temporary copy in ui/static, deleted after), its real grid drawn, loaded -- 500 rows, 8
   columns, DATE/BIGINT/DOUBLE -- and the sidebar redrew. Then a reload opened Contract on an
   EMPTY workspace: a reload is a new Streamlit session, which made a new workspace and orphaned
   the old one. 4.1: the workspace id lives in the URL (?ws=), accepted only in the exact shape
   new_workspace_id() makes, so a URL cannot name "local" or a path (P14-D20). Two reload tests
   and four bad-URL tests; the reload test fails without the fix. Browser again: after a full
   reload onto /contract?ws=..., the dataset was there, the grain field EMPTY (placeholder only,
   not the engine's guess), the engine's eight unresolved fields listed, Confirm disabled.
5. Two ws_ directories were left by the two server starts: opening the page made a workspace,
   because listing datasets opens the database. 5.1: reads of a workspace never written to
   answer "nothing" without creating it (P14-D21); a test, falsified. After the full runs, 0
   ws_ directories remain.
6. Engine 1787 -> 1803; acceptance 99/0/2, 19/0/0, 35/0/1, 26/0/0, 36/0/0; eval 76/76;
   UI 26 -> 32.
