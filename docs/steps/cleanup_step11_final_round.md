# Cleanup Step 11: a turn that runs out of rounds still answers; a refusal names the call its WHY names

Reported by the user at 15:03, 22/09/2026, on localhost:8502 (Cleanup Step 10 code), workspace
ws_74f2b9490dde, the graded question again: "I stopped after 8 rounds of tool calls without a final
answer." No provider failed and no request was too large -- CL10-D1/D2 held.

## What was established before this document

- The eight rounds: get_workflow_state; describe_dataset; validate_dataset; profile_dataset;
  trend by channel; render_chart grouped_bar (July an empty slot); top_n(order_id, n=10,
  period="2025-11") -- ORD-00551 96,049, 37.7%, "The 10 shown hold 63.3% of it together";
  concentration(order_id, period="2025-11") REFUSED. After round seven every figure the answer
  needed was in the conversation. Round eight ended the loop and agent._turn returned only "I
  stopped after 8 rounds", discarding all of it.
- Three of the rounds (describe, validate, profile) were checks nobody asked for on a dataset whose
  workflow state said "contract v1, ready".
- Round eight was spent on CL10-O1: the refusal's WHY said "top_n on order_id says which of its
  groups matter" and its NEXT STEP said propose_dataset_contract, because tools._produce maps every
  ValueError to that call. The same WHY is written at five sites: pareto/concentration
  (_ranked_with_shares), group_compare, ranking_shift, hypothesis_test; sample_adequacy has the cap
  without naming top_n.
- Files shows profile and trend twice (15:01 and 15:02-15:03): two attempts, probably a failover.

## The fix

A. The last round offers no tools (agent._turn, llm sessions). Session.step(final=True): Gemini's
   functionCallingConfig mode NONE, Groq's tool_choice "none", and a note that this is the last
   round and the answer must come from the replies above. A reply that still carries calls on the
   final round is answered with its text; the "I stopped" message is kept only for an empty one.
B. A group cap refuses with the call its WHY names. base.TooManyGroups(ValueError) carries the
   dimension and measure; the six sites raise it; tools._produce names
   compute_analysis(top_n, dimension, measure, plus period and grain if given) -- or
   frequency(column=dimension) when there is no measure. CL10-O1.
C. One more rule: when the workflow state says a contract is ready, go straight to the analyses the
   question needs; describe, profile or validate only when asked.

## Commands and outputs

1. Baseline. `uv run pytest -q`. Expected: 1893 passed.
2. Falsify: test_agent (final round passes final=True and a call-carrying final reply is answered;
   Gemini's final body has mode NONE; Groq's has tool_choice none; the rule exists),
   test_analysis_tools (concentration over too many groups names top_n with the same dimension,
   measure and period, and the call succeeds verbatim). Expected: all fail on the unfixed tree.
3. Apply A, B, C. Expected: the new tests pass; suite 1893 + new. The eval executes NEXT STEPs
   (P13-D3): if a gold question pins the old propose_dataset_contract recovery for a cap, it
   changes, and that is recorded.
4. Live, once, the graded question on a copy of ws_74f2b9490dde. Expected: a final answer within
   eight rounds, or at round eight an answer from what was fetched.
5. Acceptance 99/0/2, 19/0/0, 35/0/1, 26/0/0, 36/0/0. 6. Eval 76/76. 7. UI 37. 8. Records, commit.

## Results

1. Baseline. `1893 passed in 47.74s`. As expected.
2. Falsify. `7 failed, 78 passed`: the six new tests and the updated round-limit test (which now
   expects MAX_ROUNDS - 1 calls, the last round being an answer round) all failed. As expected.
3. Apply.
   3.1. test_agent `2 failed`: test_only_the_successful_attempts_artifacts_come_back's own
        double replaced session.step with a function taking no arguments (TypeError on final=),
        and my Groq test copied the request shallowly, so it read the message list after the
        reply was appended. Both test-side; fixed. `50 passed`.
   3.2. B: base.TooManyGroups at the six cap sites (sample_adequacy's message now names top_n
        too); tools._produce names compute_analysis(top_n, dimension, measure, period, grain),
        or frequency(column) with no measure. test_analysis_tools `35 passed`.
   Suite `1899 passed` (1893 + 6). Eval unchanged: no gold question pinned the old recovery.
4. Live, once, on a copy of ws_74f2b9490dde. Answered in six rounds: get_workflow_state; trend
   by channel; render_chart grouped_bar; concentration(order_id, period 2025-11) REFUSED; top_n
   (order_id, n=10, period 2025-11) -- the refusal's new NEXT STEP, taken at once;
   calendar_coverage. Graded: table and chart -- PASS, every figure the trend reply's; highest
   month 2025-11 254,506.43 -- PASS; "ORD-00551 ... 96,049, representing 37.7% ... driven by a
   single large order" -- PASS; July "an empty slot ... not a zero" -- PASS; the four copies
   included and cleaning not in the web app -- PASS; no screen invented, no call handed over --
   PASS. One lapse: "Excluding ORD-00551, November's remaining order_value is 158,457.43, which
   aligns with typical monthly volume" -- the subtraction is right (254,506.43 - 96,049) but no
   reply stated it, and "typical" is the model's judgement. One sample.
5. Acceptance 99/0/2, 19/0/0, 35/0/1, 26/0/0, 36/0/0. 6. Eval `SCORE: 76/76 (100%)`. 7. UI
   `37 passed`. As expected.

MEASURED VALIDATION line and digests: docs/decisions.md, section Cleanup Step 11.
