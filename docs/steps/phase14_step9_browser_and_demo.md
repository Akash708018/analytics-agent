# Phase 14 Step 9: the app in a real browser, and ready to demo

Opened 24/09/2026. Asked for: make the tool demo-ready within two days, "do not break the tool
concept". The concept stays whole: nothing loads without a confirmed ingest spec, nothing is
cleaned without a tick, nothing is computed without a confirmed contract, every number traces
to a call.

## Commands

1. scripts/browser_check.py: starts `streamlit run ui/app.py` on the real engine, drives headless
   Chromium (Playwright, pulled in only for the check with `uv run --with playwright`, pointed at
   the preinstalled /opt/pw-browsers/chromium), and walks the whole flow: Journey, Upload & read
   (a real file through the file uploader), Clean, Contract (every field filled by the widgets),
   Ask (no model key here: its failure message is the check), Files. Screenshot of each screen
   into docs/demo/screens/; every Streamlit exception box and browser console error recorded.
   Expected: unknown -- this is the first time the screens are drawn by a browser engine.
2. Fix what it finds; a test for each where AppTest can reach it.
3. Demo polish: a sample dataset one click away on Upload, the Journey's figures brought up to
   date, docs/DEMO.md.
4. Checks, records, commit.

## Results

1. First browser run. Playwright pulled in with `uv run --with playwright`; its newest build
   wanted chromium_headless_shell-1243, not installed -- launched with executable_path
   /opt/pw-browsers/chromium (Chromium 141.0.7390.37). The script's own inputs were wrong twice:
   the date input is a segmented react-aria field (typed into its first spinbutton, not
   filled), and a label search matched a dropdown's list too (comboboxes selected by role).
   Then the whole walk ran on merged_multiheader.xlsx:

       screen 01-09: 0 exception box(es) each

   Loaded 150 rows, C001 applied, "contract v1, ready". Console: /<page>/_stcore/health and
   host-config 404s (Streamlit probing relative to a deep link, then the root), Google Fonts
   refused by the sandbox proxy's certificate -- neither the app's. Prediction (unknown) held
   no surprise in the engine; the finding was in the product:

   1.1 WITHOUT A MODEL KEY NO ANALYSIS IS REACHABLE IN THE WEB APP. Ask is the only door to the
   27 analyses, and on a demo without a key -- or with the quota spent, or the network down --
   it answers "No model is configured". Fixed by an Explore screen (decision P14-D65).
   1.2 Also seen: Streamlit's Deploy button; the sidebar's Next shown as a raw call; primary
   button labels dark brown on copper, unreadable (a paragraph Streamlit colours itself).

2. Explore. Backend contract: analysis_menu (the form, from the registry's signatures and the
   contract's declared columns), run_analysis (compute_analysis, and render_chart with
   pick_y), build_report. First pass of the defaults, every analysis run as it appears:

       ok 23 refused 4

   All four were my defaults: optional second_dimension prefilled beside measure (hypothesis_test,
   effect_size refuse "exactly one"), cohort_retention's `period` is a grain, `against` picked
   an agg='none' measure. Second pass: 24/3 -- measure is optional where it is "measure or
   second_dimension", and was left empty. Third:

       ok 27 refused 0

   every chart-kind analysis drew; the report built. 4 real-backend tests (the gate; all 27 from
   defaults with charts and no server path; an engine refusal; the report), 3 UI tests.
   2.1 My UI test of the no-contract refusal failed: the fake's check read "contract" in
   "loaded, no contract". Fixed in the fake (startswith "contract v").
3. Polish: sample workbook (the merged_multiheader fixture, digest-identical) one click from
   Upload through the upload path; Next in words; Deploy hidden (client.toolbarMode = viewer);
   button labels inherit the button colour -- my first CSS comment held a tag-like "<p" and the
   theme's own guard (C97) refused the stylesheet, reworded; the Journey: a sixteenth chapter,
   dates to 24/09, STATS measured (commits replaced: this clone is shallow, 54 visible, so the
   count cannot be measured here -- "95 stress datasets" instead); a failed Ask turn points at
   Explore. docs/DEMO.md and a README run section.
   3.1 DEMO.md's first draft said 1,947 tests and 36 bugs -- both guessed before measuring.
   Measured: 1,900 + 49 = 1,949; bugs 14 + 6 + 9 + 5 = 34. Corrected (C102).

4. Checks.

       1900 passed in 108.88s (0:01:48)
       49 passed in 12.74s
       phase6: 36/0/0  phase8: 55/0/3  phase9: 0/0/1  phase10: 0/0/1  phase11: 26/0/0  phase12: 36/0/0
       SCORE: 76/76 (100%)
       browser: screens 01-11, 0 exception box(es) each; 0 finding(s); 14 known and ignored
