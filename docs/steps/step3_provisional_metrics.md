# Step 3: provisional metrics, row filters, and an SLA bench (26/09/2026)

Asked for after a live test on `strict_last_mile_analytics_test.csv` (500 orders, Pune hubs),
scored 5/10 by the user: the engine read the data correctly but refused the SLA question, because
"breach = recorded delivery > promised" is not a column and was not in the contract. The user's
ideal answer names Pune_South worst (63.4% breach) and heavy rain, low address quality and two
attempts as associations, with distance ruled out.

Decided with the user, 26/09/2026:
- The assistant may PROPOSE a derived metric; a person clicks Approve on the Ask screen before
  anything is computed ("Yes, but ask first"). An approved metric is PROVISIONAL: every result
  using it prints its formula and says it is not in the contract. It can be added to the contract.
- The bench grades against the user's own file (`tests/fixtures/logistics_sla.csv`) and their key.

Branch `step3/provisional-metrics` from `step2/free-model-reliability` (8992f89).

## What is built

1. **A comparison measure** (`Measure.compare`: left, op, right): `CAST((left op right) AS
   INTEGER)`, NULL where either side is NULL. Its mean is a rate. Only columns, never SQL text:
   both sides are validated identifiers; op is one of > >= < <= = <>; at use, both sides must be
   numeric, or both dates.
2. **A row filter per analysis** (`where=`): the text after WHERE, through `sql_guard`
   (one statement, no subquery, binds as BOOLEAN). Rows it leaves out are counted in the method
   note ("N filtered out by: ..."), like `groups=`.
3. **Propose, approve, compute.** A tool `propose_metric` (in the assistant's allowlist): the
   engine validates the definition, counts the rows it can evaluate and how many are true, and
   stores it PENDING in the workspace. The Ask screen lists pending metrics with Approve and
   Reject. An approved metric joins the contract in force for analyses only, and every result
   that reads it says "PROVISIONAL (approved <date>, not in the contract): <formula>".
4. **The rules** tell the model to propose a metric when the question needs one the contract
   lacks, rather than refuse, and to use `where=` for "valid delivered orders only".
5. **`scripts/sla_bench.py`**: the user's key as scored checks, run through the engine's own tools
   (no model): hub breach rates, the worst hub, the factors within it, distance ruled out.

## The answer key, reproduced (command 1, before any code)

Plain SQL over the file. Rules that reproduce the key best: exact copies dropped, order_ids that
still repeat with different values dropped (6), status and weather compared trimmed and lower-cased,
delivery minutes from the timestamps, positive only, status 'delivered'.

    hub           orders breaches   key
    Pune_South    94     59         93 / 59   (62.8% vs 63.4%)
    Pune_East     96     58         96 / 58
    Pune_West     86     42         85 / 42
    Pune_Central  77     29         77 / 29
    within Pune_South: heavy rain 12/13 (key 12/13), rain 15/24 (15/23), clear 32/57 (32/57),
    low 10/14 (10/14), medium 22/34 (22/34), high 27/46 (27/45), 2 attempts 12/12 (12/12),
    COD 17/33 (17/33), prepaid 42/61 (42/60); distance breached 8.44 km vs compliant 8.64 (same).

Every figure matches except one compliant Rain/High/Prepaid order in South and one in West; the
two South candidates (ORD2600224, ORD2600289) have nothing unusual. The bench therefore holds the
ranking exactly and each figure to +-1 order and +-1 point.

## Commands and output

(filled in as run)

1. The engine before the build (plain SQL, above) and the old engine: no measure could say
   "breach", so the SLA question could only be refused (the user's live run of 26/09/2026).

2. The build, parts 1-4, and `tests/test_provisional.py` (16 tests: the comparison measure's
   validation, nothing computed before approval, the approved metric labelled PROVISIONAL on
   every result, refusals with reasons, a filter counted and guarded like an exclusion rule).
   Expected all pass. First run 2 failed, both my test's figures: "Judged on 370" was a
   prediction, not a count; measured 372 (126 rows lack minutes, 4 a promise, 2 both).
   2.1 After the fix: 16 passed. A UI test drives the Approve button on the fake backend.

3. `uv run python scripts/sla_bench.py`. Expected: Pune_South worst, rates within 2 points.
   First run: West off (46.2% of 91 vs 49.4% of 85), and a parse error on an empty mean.
   3.1 The key drops orders "delivered" before they were created; an analyst reading the
   caveats does too: the bench's filter adds delivered_at > order_created_at. Then:

    cleaning: approved C001, C002, C003, C004, C005, C006: 6 action(s) applied to logistics_sla. 500 row(s) before, 492 after. The previous contents are kept as _agent_history_logistics_sla_v1.
    
    breach rate by hub, delivered orders (engine vs key):
      Pune_South     63.8% of  94   key  63.4% of  93
      Pune_East      60.4% of  96   key  60.4% of  96
      Pune_West      49.4% of  85   key  49.4% of  85
      Pune_Central   37.7% of  77   key  37.7% of  77
    
    within pune_south:
      weather=heavy rain   92.3% of  13   key  92.3% of  13
      weather=rain         65.2% of  23   key  65.2% of  23
      weather=clear        56.9% of  58   key  56.1% of  57
      address_quality=low          71.4% of  14   key  71.4% of  14
      address_quality=medium       64.7% of  34   key  64.7% of  34
      address_quality=high         60.9% of  46   key  60.0% of  45
      attempt_count=2           100.0% of  12   key 100.0% of  12
      payment_mode=prepaid      70.5% of  61   key  70.0% of  60
      payment_mode=cod          51.5% of  33   key  51.5% of  33
    
    distance in pune_south: breached 8.45 km, compliant 8.64 km (key 8.44 vs 8.64)
    
    19/19 checks right

   East, West and Central match the key exactly; South differs by the one order the data does
   not explain (above). This is the answer the user scored as ideal, computed by the engine.

4. Checks. First run 2 failed in tests/test_tool_docs.py: the closed set of MCP tools must name
   the two new ones, and decide_metric's first docstring line ran over two lines. Both fixed.

5. Live, `uv run python scripts/sla_live.py` (Gemini; Groq is blocked by this container's
   network policy). NOT COMPLETED: gemini-3.8-flash's free daily quota was spent by earlier runs
   today, gemini-3.7-flash answered 503 "high demand" three times. The model had called
   get_workflow_state and summary_stats before the failover. To be re-run.

   5.1 Re-run, 26/09/2026, Gemini only (gemini-3.8-flash's day spent; gemini-3.7-flash through
   seven 503/429 waits, each shown). Turn 1, 132 s: get_workflow_state, describe_dataset,
   validate_dataset, summary_stats, frequency of delivery_status, get_cleaning_ledger, then
   propose_metric(sla_compliance = recorded_delivery_minutes <= promised_minutes, mean): the
   refusal of 26/09 is gone -- the model proposed the metric, gave its coverage (366 of 492 rows
   judged, 47.5% true), asked for approval, and computed nothing (check: 5 of 5 figures match).
   Approved as the button would. Turn 2, 27 s: gemini-3.7-flash's free day ran out after one
   call; the takeover model answered from that one reply that the ranking was not run. NOT YET
   SEEN LIVE: the ranking and the drill-down with the approved metric. Two things the run shows:
   the model spent six calls on data-quality tools before proposing (the rules say to go
   straight to the analyses the question needs), and a free Gemini day holds roughly two such
   questions. The engine side of the answer is proven by the bench (19/19).
