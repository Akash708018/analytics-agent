# Cleanup Step 10: the web assistant's request fits the providers (CL9-O1)

Reported by the user at 14:36, 22/09/2026, from the Ask screen: "The assistant could not answer
this time. gemini: no response (TimeoutError); groq: HTTP 413 ... Limit 8000, Requested 8039".
Every graded question since Cleanup Step 9 has ended this way.

## What was measured before this document

- Every request carries the twelve allowlisted tools' descriptions and schemas: 19,616
  characters, about 4,900 tokens, before the question. compute_analysis's description alone is
  7,051 characters -- the hand-written parameter table for all 27 analyses -- and render_chart's
  2,448. SYSTEM is 2,118 characters (~530 tokens).
- run_analysis's reply is 7,431 characters (~1,850 tokens), almost all of it the 27-analysis
  catalogue that compute_analysis's description already carries. Every live run so far called it.
- No output-token reservation is set in llm.py, so Groq's "Requested" is essentially the prompt:
  ~4,900 + ~530 + three or four tool replies = the 8,003 / 8,451 / 8,039 seen. Groq cannot answer
  a four-call question at this size, whatever the question.
- Gemini's TimeoutError is at llm.TIMEOUT_S = 60 seconds; its two earlier failures were 503s.
  Whether request size causes the timeout is not established.
- Separately: a second UI is running from /Users/akash/Desktop/Claude_Work/analytics-agent on
  localhost:8502 (pid 79147, since 12:22), a different checkout without Cleanup Steps 8-9.

## The fix

A. The model gets compact tool descriptions (webapp/agent.py only; Claude Desktop keeps the full
   docstrings). Each tool's description is its docstring's first paragraph. compute_analysis and
   render_chart add a roster DERIVED from the registry -- each analysis_type with the parameters
   its function takes (period and grain added for an analysis registered narrows=True) -- so it
   cannot drift from the code the way a hand-written table can; and render_chart adds one line on
   the chart kinds and the y rule.
B. run_analysis leaves the web allowlist. compute_analysis passes through the same gate
   (tools._produce calls require_contract) and every result carries the same caveats, so nothing
   it said is lost except the catalogue, which A now carries. A tool reply naming run_analysis(
   (get_workflow_state's NEXT STEP does) gets a note that compute_analysis does the same check,
   through the same mechanism as the screen notes.

## Commands and outputs

1. Baseline. `uv run pytest -q`. Expected: 1884 passed.
2. Falsify. tests/test_agent.py: the specs fit a budget of 8,000 characters in total; the
   compute_analysis description names every registered analysis with its parameters, top_n with
   period; run_analysis is not allowlisted; a reply naming run_analysis( carries the note.
   Expected: all four fail on the unfixed tree (19,616 characters; run_analysis present).
3. Apply A and B. Expected: the new tests pass; test_agent's existing tests pass; suite 1884 + 4.
   Measured: total spec characters -- predicted 5,000-7,000.
4. The size of the graded question's conversation, computed without a model: spec characters +
   SYSTEM + the replies of get_workflow_state, compute_analysis(trend by channel),
   compute_analysis(top_n, period 2025-11) and render_chart(grouped_bar) on a copy of
   ws_0b4a3e60bfd6. Expected: under 20,000 characters (~5,000 tokens), against ~33,000 before.
5. Live, once: the graded question through RealBackend.chat on a copy of that workspace.
   Expected, if a provider answers: it draws a chart, runs top_n with period="2025-11", names
   ORD-00551, names no Cleaning screen and hands over no call. If both fail again, recorded as
   such with the reason, and CL9-O1 stays open for whichever cause remains.
6. Acceptance 99/0/2, 19/0/0, 35/0/1, 26/0/0, 36/0/0. 7. Eval 76/76. 8. UI 37.
9. Records, CLAUDE.md, commit.

## Results

1. Baseline. `1884 passed in 43.67s`. As expected.
2. Falsify. `4 failed, 39 passed`: all four new tests failed. As expected.
3. Apply A and B. Spec characters 19,616 -> 6,229, inside the predicted 5,000-7,000. test_agent
   `1 failed, 42 passed`: test_groq_gets_json_schema_nullables_and_gemini_keeps_openapi raised
   StopIteration -- it pinned P14-D27's nullable conversion using run_analysis's `question` as
   its example, and run_analysis had left the allowlist.
   3.1. The property is unchanged, the example moved: compute_analysis's `dimension` is the same
        shape (string or null). `43 passed`. Suite `1888 passed` (1884 + 4). As expected.
4. Conversation size, no model, on a copy of ws_0b4a3e60bfd6 (each reply as the model reads it,
   trimmed and noted): get_workflow_state 845, trend by channel 2,255, top_n 2025-11 1,367,
   grouped_bar 2,351; specs 6,229; SYSTEM 2,118. Total 15,165 characters (~3,791 tokens), from
   ~33,000. Under the predicted 20,000. get_workflow_state's reply now ends "run_analysis: not
   one of your tools; call compute_analysis directly -- it checks the same contract and
   computes."
5. Live, the assistant.
   5.1. Run 1, no answer. It called get_workflow_state, profile_dataset, trend by channel,
        render_chart bar (REFUSED, two series), render_chart grouped_bar (drew), top_n with
        period="2025-11" -- the rules followed -- and then: gemini "the free daily quota for
        gemini-3.8-flash is used up", gemini "no response (TimeoutError)", groq "HTTP 400:
        Parsing failed. The model generated output that could not be parsed ...
        failed_generation". No 413: the size fix held. Two defects surfaced:
        (a) Groq's failed_generation 400 was classified as nothing and ended the turn; the
            session retried only tool_use_failed. Now kind="generation_failed", retried within
            the same three attempts with a note asking for words or valid JSON.
        (b) The failure said "Nothing in your workspace changed" after a chart had been
            written (P14-D28 keeps an abandoned attempt's chart in Files). It now counts files
            written since the turn began and says they are in Files.
        Tests first: `3 failed, 43 passed`, then `46 passed`. Suite `1891 passed`.
   5.2. Run 2, answered. Calls: get_workflow_state; trend by channel; render_chart line
        (REFUSED, two series); render_chart grouped_bar (drew); top_n(order_id, n=5,
        period="2025-11"); concentration(order_id, period="2025-11") REFUSED. Graded:
          chart drawn, July "an empty slot ... not as a zero value" -- PASS, and now true of
            the chart (CL9-D2);
          highest month 2025-11 at 254,506.43 -- PASS (raw, labelled as including copies);
          peak: "ORD-00551 alone contributes 96,049 (~37.7% of November's total) ... driven by
            a few large orders" -- PASS;
          copies: "4 exact duplicate rows ... included in all totals ... Cleaning ... is not
            available in the web app" -- PASS; no Cleaning screen, no JSON -- PASS;
          "The top-5 orders for November account for ~56%" -- FAIL. No reply said it; the five
            shares were 37.7 + 6.4 + 3.8 + 2.7 + 2.5 = 53.1%. The model added a column and got
            it wrong, against the first rule.
          "A grouped-bar (or line) chart" -- the line was refused; a small inaccuracy.
   5.3. The concentration refusal: "order_id has 55 group(s) ... against a cap of 49. top_n on
        order_id says which of its groups matter", NEXT STEP propose_dataset_contract -- the WHY
        names the right recovery, the NEXT STEP a wrong one. Pre-existing; CL10-O1.
   5.4. top_n now states what its rows hold together, so that sum is never the model's: "The 5
        shown hold 53.1% of it together." on the run's rows. Test first (`1 failed`), then
        `30 passed`. Suite `1893 passed`.
6. Acceptance 99/0/2, 19/0/0, 35/0/1, 26/0/0, 36/0/0. 7. Eval `SCORE: 76/76 (100%)`. 8. UI
   `37 passed`. As expected.

MEASURED VALIDATION line and digests: docs/decisions.md, section Cleanup Step 10.
