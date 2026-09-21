# Phase 14 Step 4: the agent loop -- a free model calling the engine's tools

Guide Phase 14 item 3: "Agent loop calling a free LLM API with your tool definitions. Google
Gemini's free tier is the best default ... Groq is a good failover ...; build a provider switch."
This step builds the loop behind the Ask screen: `RealBackend.chat` stops saying "not connected".

## Measured before designing (engine's own tool list, FastMCP 3.4.7)

29 tools. Their JSON schemas use `anyOf` with a null branch 105 times, `default` 122 times,
`additionalProperties` 36 times, and a `workspace_id` parameter on 23 tools. Gemini's function
declarations accept an OpenAPI subset and reject several of these, so schemas are converted, not
passed through. Descriptions run to 6,640 characters (compute_analysis) -- they are the manual the
model reads and are passed whole.

## Decisions

1. The model gets an ALLOWLIST of 12 tools: list_datasets, describe_dataset, get_workflow_state,
   run_analysis, compute_analysis, render_chart, read_result_file, profile_dataset,
   profile_column, validate_dataset, get_cleaning_ledger, build_report. Excluded, and why:
   anything taking a filesystem path (preview_file, check_file, propose_ingest_spec, load_*) --
   on a public host a path is the server's disk; query_source/describe_source/list_sources --
   SQL against configured databases; everything that changes what a person must agree to
   (confirm_*, propose_dataset_contract, propose/apply_cleaning_plan, reset_workspace) -- those
   are screens with a human click, by the guide's own rule.
2. `workspace_id` is removed from every schema and injected by the server. The model never
   chooses a workspace; a call carrying one anyway has it overwritten.
3. Tools run through server.py's functions -- the same code Claude Desktop calls -- under the
   workspace's lock (P14-D8), one call at a time, so a slow model never holds the lock.
4. No SDKs: both providers are one JSON POST over urllib. Gemini generateContent (function
   calling, the model's own content echoed back verbatim so any signature parts survive); Groq's
   OpenAI-compatible chat/completions with tools.
5. Models are measured, not recalled: GEMINI_MODEL / GROQ_MODEL if set, otherwise the provider's
   own model list is read and a model chosen from it (Gemini: a stable flash model supporting
   generateContent). My knowledge of model names is a year older than this code.
6. Keys come from the environment or a gitignored .env at the repository root, loaded without
   overwriting what is set and never printed. The user creates the file; no key passes through
   this conversation.
7. Failover: providers in ANALYTICS_LLM order (default gemini,groq), each skipped if it has no
   key. A retryable failure (429, 5xx, timeout) restarts the turn on the next provider; the
   tools are read-only or write only new files, so a restart repeats no harm.
8. Bounds: at most 8 tool rounds a turn; each result truncated to 8,000 characters for the model
   (the UI's "What I did" keeps the full text); the last 12 history messages sent.
9. Artifacts of the turn are the workspace's artifacts after it minus those before it.

## Commands and outputs

1. Ground facts: the converted schemas of all 12 tools contain no anyOf, default, title,
   additionalProperties or workspace_id, and every required field survives. Expected: holds.
2. tests/test_agent.py with a scripted provider (no network): tool execution with the
   workspace injected, a model-supplied workspace_id overwritten, a tool outside the allowlist
   refused, refusals marked, the round limit, artifacts, failover on a retryable error, no
   failover on a fatal one, both providers' wire formats translated from canned JSON.
3. Engine suite 1803 -> + new; acceptance unchanged; eval 76/76; UI tests unchanged.
4. Live, once the user has created .env with a key: scripts/agent_live.py runs one real
   question end to end. Its output recorded here.
5. Records; commit and push.

## Results

1. Ground facts: all 12 converted schemas are free of anyOf, default, title (as a keyword),
   additionalProperties and workspace_id; compute_analysis keeps required [dataset_name,
   analysis_type] and its column is {type: string, nullable: true}. My first checker flagged
   render_chart's parameter named "title" -- a property name, not the keyword; the test walks
   keywords only. Two tools have no parameters left once workspace_id goes, so their Gemini
   declarations omit `parameters` (an OBJECT with empty properties is a shape Gemini rejects).
2. tests/test_agent.py first run: 17 passed, 1 failed -- the Groq test compared against a
   request body captured by reference; the session appends to that same list. Test fixed; the
   code sent the right thing. 18 passed.
   Falsified: honouring a model-supplied workspace fails the override test -- after first
   strengthening it, since "clean_sales" in the reply would not prove which workspace answered
   ("local" may hold one); it now asserts the workspace's own name. Disabling the allowlist
   fails its test (the reset ran against the test's throwaway workspace only).
3. The full suite then failed one test, and it had reached the network: the old "not connected"
   chat test called Gemini and got "API key not valid". Cause: the env test's
   delenv(raising=False) on an absent variable registered nothing to undo, so the key load_env
   wrote outlived it (P14-D24). 3.1: that test runs on a private environment; the chat test
   stubs providers; tests/conftest.py refuses urllib network access suite-wide, proven by a
   temporary test that tried a real request and was stopped (then deleted).
4. One stray ws_ directory appeared once and was not reproduced in any later run, alone or
   together; the real-backend server on :8502 was live and reloading on my edits at the time,
   and is the likeliest source. Recorded, not attributed.
5. Engine 1803 -> 1821; acceptance 99/0/2, 19/0/0, 35/0/1, 26/0/0, 36/0/0; eval 76/76; UI 32.
6. OUTSTANDING: the live run. There is no key on this machine yet (checked by name: no .env,
   no GEMINI_/GROQ_API_KEY in the environment); scripts/agent_live.py says so and exits 1.
   Nothing here has been shown to work against a real model. This clause stays open until the
   script runs with a key and its output is pasted here.

## The live run (the outstanding clause), 22/09/2026

The user created .env with GEMINI_API_KEY and GROQ_API_KEY and ran scripts/agent_live.py. Every
diagnostic after that printed names and error text only, never a key.

L1. User's run: Gemini chose "gemini-omni-1.1-flash"; Groq's model discovery 403 "error code:
    1010"; the turn reported only the Groq error. Diagnosis, measured:
    - Gemini: my discovery sorted names as strings and "omni" sorts after "3.8"; that model's
      free tier answered 429 on the first request. gemini-flash-latest 200 (serving
      gemini-3.8-flash); gemini-2.5-flash -- the name I would have hard-coded -- 404 "no longer
      available to new users".
    - Groq: Cloudflare's 1010 refuses Python's default User-Agent; the same request with a
      named agent returned 200. llama-3.3-70b-versatile is no longer offered; openai/gpt-oss-120b is.
    - The earlier Gemini failure was dropped from the message when Groq failed fatally.
    L1.1: gemini-flash-latest if offered, else the highest-NUMBERED plain flash model; a named
    User-Agent on every request; every provider's failure in the message (P14-D25).
L2. Gemini 503 "high demand"; Groq 429 tokens-per-minute (8,000; each request ~5,000 tokens,
    measured: descriptions 14,943 chars, schemas 4,009, system 967). L2.1: wait as the provider
    asks (Retry-After, "try again in Xs", retryDelay) and retry, up to a cap (P14-D26).
L3. Gemini made its first real tool call (get_workflow_state, answered), then 429 at 5 requests a
    minute asking 40.26 s -- over the 20 s cap, so it failed over; Groq then refused gpt-oss's own
    call, `"question": null`, because `nullable` is OpenAPI, not JSON Schema. L3.1: the cap is one
    rate-limit window, 60 s; Groq gets JSON Schema with type lists (P14-D26, D27).
L4. SUCCESS. Gemini, four tool calls: get_workflow_state, run_analysis, compute_analysis
    (group_compare region x revenue), render_chart (bar, y=total). Answer: South leads, 378,416.78,
    27.5% of 123 orders; table of all regions; the 28 null-region rows named as kept. Checked
    against SQL computed without the tool: South 123 / 378,416.78 / 27.5, North 108 / 320,593.28 /
    23.3, West 124 / 317,651.57 / 23.1, East 117 / 288,064.05 / 20.9, (null) 28 / 73,171.16 / 5.3,
    all 500 / 1,377,896.84 -- every figure matches. But the chart drew the (all) roll-up as a sixth
    bar, "highest value 1.378e+06 at (all)" (C98, fixed in charts/render.py).
L5. Rerun after C98: a first attempt failed over mid-turn; Groq answered via top_n, its render_chart
    refused for want of y, and the model retried with the y the refusal named (C93, working live).
    Correct figure again. Two small findings: the abandoned attempt's chart was listed under the
    answer (per-turn snapshot; now per attempt, P14-D28), and the model wrote "$378,416.78" -- a
    currency nothing states (a rule added to the system prompt).
Falsified this round: removing the User-Agent, restoring string sorting, reporting only the last
failure, sending OpenAPI nullables to Groq, taking the artifact snapshot per turn -- each fails
its test. The roll-up test failed on the unfixed render layer.

Final: engine 1803 -> 1832; acceptance 99/0/2, 19/0/0, 35/0/1, 26/0/0, 36/0/0; eval 76/76; UI 32.
The live clause is CLOSED by L4.
