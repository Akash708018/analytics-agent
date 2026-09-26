# Step 2: the Ask assistant finishes on free-tier models (25/09/2026)

Approved by the user as "step 2" after the recheck of 25/09/2026. The failure it answers, from
`recheck_profiling_cleaning_verifier.md` command 6: on the retail fixture, the question

> For 2025 only, give revenue, cost and margin % by region, and list the data-quality issues I
> should know about.

got no answer. Gemini's free daily quota for gemini-3.8-flash was spent, the next Gemini model
answered 503 "high demand", and Groq (openai/gpt-oss-120b) answered HTTP 413 "Request too large ...
tokens per minute (TPM): Limit 8000, Requested 8917" once six tool replies were in the conversation.
The screen said only "Reading the data..." for about seven minutes while `llm._request` slept on
429/503 (MAX_WAIT_S = 60 s a retry).

Branch `step2/free-model-reliability` from `recheck/profiling-cleaning-verifier` (1408652). No API
key is available in this environment (no `.env` in this tree, none in the environment): nothing here
is verified against a live provider. Every provider test is scripted HTTP.

## What is built, in this order

1. **Caveats once per answer**, in `webapp/agent.py` only -- analysis output and server.py tool
   text are unchanged (Claude Desktop reads them). Within one turn the first tool reply carrying a
   block of `MEASURED`/`DECLARED` caveat lines keeps it in full; a later reply whose block is
   identical gets one line in its place. The figure check (`webapp/verify.py`) is given the reply
   with the block restored, so a declared number is still recognised wherever it is repeated.
2. **A token budget before every provider call** (`webapp/budget.py`, used by the sessions in
   `webapp/llm.py`): tokens estimated as characters / 4 of the JSON request (`CHARS_PER_TOKEN`); one
   registry of per-request limits by provider and model; a request is kept to 75% of its limit
   (`SAFETY`). Over it, the oldest tool replies are shortened first to a head plus a note that
   read_result_file pages the rest; earlier conversation messages after that; the system prompt,
   the question and the latest reply never. HTTP 413 is classified `too_large`; the session reads
   the limit and the count the provider names, shrinks, and retries once before failing over.
3. **Resumable synthesis** (`webapp/agent.py`): when a provider fails after tools have run, the
   next provider is not given the tools. It gets the question and the tool replies already
   gathered, and one final round asking only for the answer. ToolCall records and artifacts of the
   first attempt stay with the answer; the figure check reads the same replies.
4. **OpenRouter** as a third provider (`openrouter`, `OPENROUTER_API_KEY`, OpenAI-compatible
   `POST https://openrouter.ai/api/v1/chat/completions`, `OPENROUTER_MODEL` or the first free
   tool-calling model the account's list offers). `ANALYTICS_LLM` defaults to
   `gemini,groq,openrouter`. Not verified live: there is no key here.
5. **The Ask screen shows waits**: `llm._request` reports every sleep (provider, model, seconds,
   why) to a listener; `agent.answer(progress=...)` forwards it to the screen's status box, and
   `ChatTurn.notes` keeps what the person should still see after the answer (waits, a failover, a
   shortened reply). `Backend.chat` gains an optional `progress` argument. The fake accepts it and ignores it,
   because the protocol test holds their signatures equal. The screen still calls a backend
   without it with three arguments.

## Commands and output

Each command states what it is expected to print before it runs. Run in a cloud session on
26/09/2026 (Linux, no Postgres, no API key).

1. Baseline on the unchanged tree (a worktree at 1408652): `uv run pytest -q` and
   `uv run --group ui pytest ui/tests`. Expected 2168 passed, 1 skipped; 53 passed.

       2169 passed in 171.15s
       53 passed in 14.53s

   The prediction was wrong by one skip. The skip on the user's machine is
   `test_benchmark_fixes.py::test_n13_...`, which skips when the DuckDB postgres extension is
   cached ("the postgres extension is cached here, so nothing is refused"). Here it is not
   cached, so the test runs and passes: 2169 = 2168 + 1.

2. NOT RUN. The plan was to read the retail web answer's recorded analyses from
   `workspace/ws_e662a43ecb59/session.duckdb`. That workspace is on the user's machine and not in
   this tree. The six calls in command 3 remain a reconstruction.

3. `uv run python scripts/request_size.py` on the UNCHANGED loop (the script copied into the
   1408652 worktree). `~/Downloads/retail_fixture.csv` is not in the repository, so the script
   builds a retail-like table itself (`build()`, seed 26, 30,000 lines plus 120 exact copies,
   the fixture's columns and fault kinds) and confirms the fixture's 13 declared caveats.
   Expected: each analysis reply carries the whole block (16 measured lines, an overflow line,
   13 declared: 3,000-5,000 chars); the request carrying six replies is over 8,000 estimated tokens.

    table: built here, 30,123 rows (the fixture's own file is not in the repository)
    contract confirmed: 17 measured caveat line(s), 13 declared
    request 1: 9,949 chars, ~2,488 tokens (chars/4); 0 tool replies
    request 2: 10,982 chars, ~2,746 tokens (chars/4); 1 tool reply
    request 3: 16,686 chars, ~4,172 tokens (chars/4); 2 tool replies
    request 4: 22,379 chars, ~5,595 tokens (chars/4); 3 tool replies
    request 5: 24,818 chars, ~6,205 tokens (chars/4); 4 tool replies
    request 6: 29,296 chars, ~7,324 tokens (chars/4); 5 tool replies
    request 7: 29,839 chars, ~7,460 tokens (chars/4); 6 tool replies
    tool replies as sent in the last request (characters, caveat lines):
      c1 get_workflow_state      804 chars,  0 caveat lines
      c2 compute_analysis      5,265 chars, 30 caveat lines
      c3 compute_analysis      5,257 chars, 30 caveat lines
      c4 validate_dataset      2,162 chars,  0 caveat lines
      c5 profile_dataset       4,187 chars,  0 caveat lines
      c6 get_cleaning_ledger     291 chars,  0 caveat lines

    tool replies as the tools wrote them (characters):
      get_workflow_state      663 chars,  0 caveat lines (0 chars)
      compute_analysis      5,151 chars, 30 caveat lines (4,077 chars)
      compute_analysis      5,143 chars, 30 caveat lines (4,077 chars)
      validate_dataset      2,042 chars,  0 caveat lines (0 chars)
      profile_dataset       4,187 chars,  0 caveat lines (0 chars)
      get_cleaning_ledger     177 chars,  0 caveat lines (0 chars)

    turn: answered: Answered from the replies above.

   Block as expected: 30 lines, 4,077 characters in each compute_analysis reply. Size NOT as
   expected: the last request is 7,460 estimated tokens, below 8,000. The estimate is chars/4;
   Groq counted 8,917 for the live turn, which is why the budget keeps 25% in hand. The table and
   the replies here are not the live ones, so the two counts are not the same turn.

4. The build (parts 1-5) with tests:
   `uv run pytest tests/test_budget.py tests/test_agent.py tests/test_verify.py -q`.
   Expected: all pass, including (a) `test_the_retail_turn_fits_groq_free_tier_and_answers` and
   (b) `test_a_failover_after_tools_ran_answers_without_running_them_again`.

   First run: 3 failed in test_budget.py. Two were tests that asked `fit` for more than the
   floors allow (fixed in the tests). The third was real: (a)'s last request was 6,112
   estimated tokens, over the 6,000 allowance. See 5.1.

   4.1 `test_only_the_successful_attempts_artifacts_come_back` (P14-D28) failed by design: a
   chart drawn before a failover is now kept with the answer. Rewritten as
   `test_a_chart_drawn_before_a_failover_stays_with_the_answer`, which also asserts it was drawn once.
   4.2 The failover test reached the network through Gemini's model ladder (`has_another_model`).
   The test now pins `_ladder`. After the fixes:

       86 passed in 10.51s      (test_agent, test_budget, test_verify)
       55 passed in 11.04s      (ui/tests, two new)

5. Command 3 on the changed loop. Expected: the first analysis reply keeps the block, the later
   one is shorter by about its size, and every request is at most 6,000 estimated tokens.

   5.1 First run: request 6 was 6,056, over the allowance. Every older reply was already at or
   under REPLY_KEEP (1,200), and the reply carrying the block pins its 30 lines. Fix:
   `budget.fit` makes a last pass that cuts the older replies to REPLY_MIN (600). Caveats only
   (`--caveats-only`, budget off):

    token budget: off
    table: built here, 30,123 rows (the fixture's own file is not in the repository)
    contract confirmed: 17 measured caveat line(s), 13 declared
    request 1: 9,949 chars, ~2,488 tokens (chars/4); 0 tool replies
    request 2: 10,983 chars, ~2,746 tokens (chars/4); 1 tool reply
    request 3: 16,688 chars, ~4,172 tokens (chars/4); 2 tool replies
    request 4: 18,335 chars, ~4,584 tokens (chars/4); 3 tool replies
    request 5: 20,774 chars, ~5,194 tokens (chars/4); 4 tool replies
    request 6: 25,254 chars, ~6,314 tokens (chars/4); 5 tool replies
    request 7: 25,797 chars, ~6,450 tokens (chars/4); 6 tool replies
    tool replies as sent in the last request (characters, caveat lines):
      c1 get_workflow_state      805 chars,  0 caveat lines
      c2 compute_analysis      5,266 chars, 30 caveat lines
      c3 compute_analysis      1,240 chars,  0 caveat lines
      c4 validate_dataset      2,162 chars,  0 caveat lines
      c5 profile_dataset       4,189 chars,  0 caveat lines
      c6 get_cleaning_ledger     291 chars,  0 caveat lines

    tool replies as the tools wrote them (characters):
      get_workflow_state      664 chars,  0 caveat lines (0 chars)
      compute_analysis      5,152 chars, 30 caveat lines (4,077 chars)
      compute_analysis      5,144 chars, 30 caveat lines (4,077 chars)
      validate_dataset      2,042 chars,  0 caveat lines (0 chars)
      profile_dataset       4,189 chars,  0 caveat lines (0 chars)
      get_cleaning_ledger     177 chars,  0 caveat lines (0 chars)

    turn: answered: Answered from the replies above.

   Caveats and budget together:

    table: built here, 30,123 rows (the fixture's own file is not in the repository)
    contract confirmed: 17 measured caveat line(s), 13 declared
    request 1: 9,949 chars, ~2,488 tokens (chars/4); 0 tool replies
    request 2: 10,983 chars, ~2,746 tokens (chars/4); 1 tool reply
    request 3: 16,688 chars, ~4,172 tokens (chars/4); 2 tool replies
    request 4: 18,335 chars, ~4,584 tokens (chars/4); 3 tool replies
    request 5: 20,774 chars, ~5,194 tokens (chars/4); 4 tool replies
    request 6: 23,955 chars, ~5,989 tokens (chars/4); 5 tool replies
    request 7: 23,902 chars, ~5,976 tokens (chars/4); 6 tool replies
    tool replies as sent in the last request (characters, caveat lines):
      c1 get_workflow_state      684 chars,  0 caveat lines
      c2 compute_analysis      5,266 chars, 30 caveat lines
      c3 compute_analysis        917 chars,  0 caveat lines
      c4 validate_dataset      1,332 chars,  0 caveat lines
      c5 profile_dataset       3,600 chars,  0 caveat lines
      c6 get_cleaning_ledger     291 chars,  0 caveat lines

    tool replies as the tools wrote them (characters):
      get_workflow_state      664 chars,  0 caveat lines (0 chars)
      compute_analysis      5,152 chars, 30 caveat lines (4,077 chars)
      compute_analysis      5,144 chars, 30 caveat lines (4,077 chars)
      validate_dataset      2,042 chars,  0 caveat lines (0 chars)
      profile_dataset       4,189 chars,  0 caveat lines (0 chars)
      get_cleaning_ledger     177 chars,  0 caveat lines (0 chars)

    turn: answered: Answered from the replies above.
    note: groq (openai/gpt-oss-120b): 3 earlier tool replies shortened for the model to fit its request limit of 8,000 tokens; every reply is whole under What I did
    note: groq (openai/gpt-oss-120b): 1 earlier tool reply shortened for the model to fit its request limit of 8,000 tokens; every reply is whole under What I did

   As expected: the second compute_analysis reply goes from 5,255 to 1,240 characters (the
   block, 4,077, replaced by one line), and the largest request drops from 7,460 to 5,989
   estimated tokens (the cap is 6,000).

6. All six checks, the eval and the three benches: see "Checks" below.

## Checks (26/09/2026, this tree, no Postgres `olist` source, no key)

    uv run pytest -q                      # 2194 passed, 0 skipped (2169 at 1408652 + 25 new)
    uv run --group ui pytest ui/tests     # 55 passed (53 + 2 new)
    uv run python tests/test_phase8.py    # 55 passed, 0 failed, 3 skipped
    uv run python tests/test_phase9.py    # 0 passed, 0 failed, 1 skipped
    uv run python tests/test_phase10.py   # 0 passed, 0 failed, 1 skipped
    uv run python tests/test_phase11.py   # 26 passed, 0 failed, 0 skipped
    uv run python tests/test_phase12.py   # 36 passed, 0 failed, 0 skipped
    uv run python eval/run_eval.py        # SCORE: 76/76 (100%)
    scripts/suggest_bench.py, marketing_bench.py, marketing_bench_v2.py   # each exit 0

Phases 8-10 differ from the user's 99/0/2, 19/0/0, 35/0/1 only because `olist` is absent here.
These are CLAUDE.md's no-Postgres figures. The engine suite has no skip here for the reason
given in command 1.

## Decisions

S2-D1. CAVEATS ONCE A TURN, IN THE AGENT ONLY. `agent.Gathered.compact` treats a reply's
MEASURED/DECLARED lines as its block. A block identical to one already sent this turn becomes
"Caveats: the same N as in an earlier reply this turn." The tools' text, the person's record
(What I did) and Claude Desktop are unchanged. The figure check reads each reply with its block
restored (`Gathered.seen`). On the retail-like turn, the second analysis reply went from 5,255 to
1,240 characters.

S2-D2. BUDGET. Tokens are estimated as characters / 4 of the request JSON. Limits come from one
registry (`budget.LIMITS`), and a request may use 75% of its limit. Cutting order: older replies
to 1,200 characters, then the earlier conversation to 400, then the older replies again to 600.
The latest reply, the system prompt and the question are never cut. A shortened reply keeps its
first and last lines and its caveat lines. On a 413, the session learns the limit and the count the
provider named, shrinks the request and sends it once more; a second 413 fails over. The last
request of the retail-like turn went from 7,460 to 5,976 estimated tokens.

S2-D3. RESUMABLE SYNTHESIS; P14-D28 SUPERSEDED. After tools have run, the next provider or model
gets no tools, the handover note, and the gathered replies (each can be shortened), and has one
final round. No tool runs twice. The first attempt's ToolCalls and files stay with the answer,
because the answer is written from them. An empty answer counts as a retryable failure.

S2-D4. OPENROUTER. Third in the default order (gemini,groq,openrouter). The model is
OPENROUTER_MODEL, else the preferred free tool-calling model the list offers, else the free
tool-calling model with the longest context. An error returned inside a 200 body is classified
by its code. NOT VERIFIED LIVE: scripted HTTP only.

S2-D5. WAITS ARE SHOWN. Every sleep in `_request` is announced first, as a ChatEvent naming the
provider, the model and the seconds. `agent.answer(progress=)` forwards each event; the Ask
screen's status box shows it, and wait, failover and shortening notes stay on `ChatTurn.notes`.
A progress listener that fails never fails a turn.

MEASURED VALIDATION, 26/09/2026: engine 2194/0 skipped; UI 55; phases 55/0/3, 0/0/1, 0/0/1,
26/0/0, 36/0/0 (no olist); eval 76/76; benches exit 0. Digests:
  b1d1ffcccc911a27d6bdf4c487bbf802417344d53806db9cc1acbf1488293e66  src/analytics_agent/webapp/agent.py
  76c136e28824a05b7c53e5e3c39262c3e383566bc59e5b114f854bd4c2ee2f28  src/analytics_agent/webapp/budget.py
  36581e63bda04d0c10fe41e1a6c611b1773ab13646fca6c626558b778ec3379f  src/analytics_agent/webapp/llm.py
  33a9359c90f0e7fa5668db67de0c7f06aefdade86ec8d7992a2e1dff2adf265d  src/analytics_agent/webapp/contract.py
  3634fb397b858767a9106e670a8377fbbb03c4b7d2eef24650a617de04db373c  src/analytics_agent/webapp/real_backend.py
  ac63fcc842e9a5f9f1e45c99309359a53bca9f0520e7759a87872b3f645d4478  ui/screens/chat.py
  072c7842a00523b8e0e9cf9e82ba43b66b08d29fc1a8cdbbb55d740bd57d3dba  scripts/request_size.py
  ac6a9f4b767ae928698b9624084191e19b5c6ad355cad740db4c5336984d3aff  tests/test_budget.py
