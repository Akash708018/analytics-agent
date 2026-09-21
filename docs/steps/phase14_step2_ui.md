# Phase 14 Step 2: the Track B UI on the fake backend -- sunset theme, the ink-written Journey

The user took the UI back from the Codex handover (22/09/2026) and set the design: a warm sunset
colour theme throughout, and a "Harry Potter fade effect" telling the journey and work of the
project -- read as ink that surfaces on parchment, line by line, with Marauder's-map footsteps.

This document was written at the close of the step, not before it -- a departure from "How a
step runs", recorded rather than hidden. The design work was iterative in a browser and the
commands below are listed in the order they actually ran, with their real outputs.

## What was built

- `ui/theme.py` -- palette (dusk #1c1226 to coral #ff7e5f, peach, gold; parchment text), fonts
  (Cinzel headings, Cormorant Garamond for ink, Inter body), one global stylesheet, and an
  ink-in fade on every new block. Reduced-motion users get no animation.
- `ui/journey.py` -- the Journey page: 15 chapters on parchment, each written in with a
  left-to-right blur-to-sharp stroke, an ink drop at its start and footsteps walking the path
  between chapters; then six measured figures. Dates are each phase's first commit.
- `ui/fake_backend.py` -- the whole `webapp/contract.Backend`, deterministic, in memory.
- Screens: Upload & read (the Ingest Spec editor with the sheet drawn at its real row numbers),
  Contract, Ask (charts inline with the engine's description), Files; sidebar with every
  dataset note shown in full and a reset that needs confirming.
- `ui/tests/`: 25 tests (10 backend, 15 app via AppTest), outside the engine's testpaths.

## Commands and findings, in order

1. `uv add --group ui streamlit` -> streamlit 1.64.0. The shared lockfile also moved the ENGINE's
   websockets 17.1 -> 16.1.1 (fastmcp's dependency), because groups resolve together.
   Expected: no engine change. Measured at close: engine suite 1787 passed, F7's HTTP test
   included; acceptance and eval unchanged.
2. Journey rendered unstyled. DOM: the page's <style> block absent, inline <svg> stripped,
   classes and style attributes kept. 2.1: stylesheet sent in its own st.html call, footprints
   as CSS background images. Still unstyled -- the server was running the old module. 2.2:
   SVG data URIs percent-encoded and the server restarted: styled. Which of the two fixed it
   was not isolated at the time.
3. Parchment text cream-on-cream: the theme colours every paragraph parchment. 3.1: ink set
   explicitly inside the paper. The comment written with that fix mentioned a p tag.
4. Unstyled again after restart. I read it as two styles-only st.html calls racing (one lost),
   and merged every page's CSS into one block. That un-themed the whole app: the merged block
   carried the comment from 3.1. 4.1: st.html sanitises with DOMPurify, which discards an
   entire style element whose text holds "<" followed by a letter -- the unencoded SVG in 2 and
   the comment in 3.1 were the same failure. There was no race (C97). Comment reworded;
   theme.apply now raises on any tag-like "<" in a stylesheet. Five fresh loads: styled each
   time.
5. Upload -> re-read with header rows 1,2 -> Confirm and load, in the browser: the draft
   resolved and loaded, but the sidebar still listed only the seeded dataset -- it is drawn
   before the page's button runs. 5.1: st.rerun() after confirming (ingest and contract).
6. The header-row multiselect offered "Select all" (streamlit 1.64's default). 6.1:
   select_all=False -- selecting every row as a header is never an answer.
7. `uv run --group ui pytest ui/tests`: 10 failed, 15 passed -- AppTest.switch_page resolves
   pages as files and these pages are functions routed by url_path. 7.1: screens rendered via
   AppTest.from_function with the app's theme and sidebar; one test still runs app.py. Then 24/1:
   the image element is "image", not "imgs". 7.2: fixed. 25 passed.
8. Falsified the sidebar-refresh test by removing the rerun: 1 failed. Restored: 25 passed.
9. Browser walk-through: Journey writes in; upload/ingest/confirm; Ask draws a chart with its
   description and a "What I did" expander; Contract holds Confirm while provisional.
