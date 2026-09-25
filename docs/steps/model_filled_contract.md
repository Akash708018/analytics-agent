# The model fills the contract; the data filters it; the person corrects it (25/09/2026)

Decided with the user after the vNext brainstorm: "let the LLM fill the fields by itself, and if
the user sees one is not correct they change it -- and put a proper filter on the LLM based on the
data". This reverses, for the web app only, the rule that a drafted field reaches the form blank
(P14-D18, `Measure.agg` without a default): a model's choice now fills it -- but every choice is
checked against the data, every field says who decided it, the person's change always wins, and
nothing is used until Confirm. Added in the same step, as the user asked: geo and distance columns,
and 0/1 columns as helper rates.

## What was built

- `contract/llm_filter.py` -- the filter. Each field gets one verdict: **agree** (the model and a
  STRONG data reading agree), **llm_only** (the data cannot check it: a meaning, a grain sentence,
  an unnamed number, or agreement with a reading of the name only), **overruled** (the data's
  answer replaces the model's; both kept), **blocked** (a column that does not exist, arithmetic on
  text), **data** (filled by the data where the model said nothing: a unit, a ratio of sums, a
  flag's rate, the window). Hard rules: never a sum on a price/rate/percentage/score, a coordinate,
  a code or year, a snapshot, a ratio, or a time something took; never a mean of a ratio; a key is
  verified unique; a unit is verified constant; below 70% model confidence, a choice the data cannot
  check is left blank.
- `webapp/autofill.py` -- one request per table (`llm.complete_json`, 5-second rate-limit waits,
  provider failover), kept in the workspace by fingerprint; the filter re-runs on every draft from
  the kept answer. The model is shown column facts and measured repetition -- never the engine's
  own readings, so agreement is not agreement by construction. On by default in the web app only
  (`ANALYTICS_AUTOFILL`); off in every test and script.
- The contract stores `provenance`: per field, the verdict, what the model said, the reason, the
  model. `scripts/autofill_report.py` counts them across workspaces.
- Contract screen: a banner (model, and the verdict counts), "Fill again", a badge under every
  field (checked by the data / from the model / overruled / from the data / yours), "Rates from 0/1
  columns", a waiting notice, and "Ready to confirm" that says how many fields are the model's
  alone.
- Rules added to `contract/suggest.py`: **F1** a 0/1 or true/false column (mean = the share of 1s;
  offered as `<flag>_rate` beside a flag that stays a dimension); **G1** latitude/longitude, strong
  when every value is in range; **G2** distance travelled (sum, likely) vs a gap between recorded
  and expected points (none); **D2** a time something took (delivery, delay, latency: never a sum).
- `contract/measured_caveats.py`: **M7** coordinates out of range, swapped, or at (0, 0); **M8** a
  value written more than one way ('Pune_West' / 'PUNE_WEST').

## Measured

Bench (`scripts/suggest_bench.py`, now with a last-mile case shaped like the vNext plan's):

    strong 29: 29 right, 0 wrong; likely 8: 8 right; 76.3% of labelled measures settled strongly
    caveats: 100% of expected found; 27 of 27 lines recounted apart held; 0 false alarms (clean)
    filter, a model that sums everything:  raw 11 right / 18 wrong -> filtered 27 right / 2 wrong
    filter, the live free-tier model:      raw 15 right / 7 wrong / 7 blank
                                        -> filtered 21 right / 1 wrong / 7 blank
    wrong while marked "checked by the data": 0 in both. The wrong that remain are marked
    "from the model" for the person (session_seconds summed; customer_credit_limit summed).

Live model: groq/openai/gpt-oss-120b (Gemini's first model had spent its daily quota; one run went
to gemini-3.6-flash). Two live runs of the same five datasets differed: 17 then 15 right raw --
the reason a fill is kept per table rather than asked again.

What the bench and the live walk found, and what was changed:

1. The first live run: margin_pct "mean" passed as "both non-additive". The mean of a ratio is the
   retail C5 trap (25.79% vs 18.40%). Fixed: never a mean of a ratio. And the ratio of sums was
   missed when the model left a part off its measures: the filter now reads every number.
2. A match with a name-only reading came out "agree" (green). Fixed: agree needs strong evidence.
3. A delivery time summed stayed as the model's choice. Added D2 (the vNext guardrail "duration is
   normally non-additive", narrowed to times taken; hours worked may still sum).
4. `kept` (the cache check) was shadowed by a local of the same name: an existing UI test caught
   the UnboundLocalError.
5. The report read contracts through store.current(), which creates its table and fails read-only;
   the exception was swallowed and the report found nothing. Fixed: read the table directly.
6. "Ready to confirm: nothing in it is a guess" after a model's fill. Fixed: it counts the fields
   that are the model's alone.

Live walk, real backend, retail fixture with no contract: the form filled in about 60 s -- "17
agree with the data, 16 from the model only, 1 overruled by the data, 3 filled by the data". The
model's key `line_id` was overruled (it repeats in 120 rows: the 120 exact duplicates);
rep_monthly_salary "sum" overruled to mean per rep_id (the J2 trap); pages_viewed "none" overruled
to sum per order_id; margin_pct kept per row with margin_pct_of_sums added; is_returned_rate
offered. Confirmed; the report then read 39 fields: agree 17, llm_only 16, overruled 3, data 3.

## Checks

    uv run pytest -q                      # 2157 passed, 1 skipped
    uv run --group ui pytest ui/tests     # 53 passed
    uv run python tests/test_phase8.py    # 99 passed, 0 failed, 2 skipped
    uv run python tests/test_phase9.py    # 19 passed, 0 failed, 0 skipped
    uv run python tests/test_phase10.py   # 35 passed, 0 failed, 1 skipped
    uv run python tests/test_phase11.py   # 26 passed, 0 failed, 0 skipped
    uv run python tests/test_phase12.py   # 36 passed, 0 failed, 0 skipped
    uv run python eval/run_eval.py        # SCORE: 76/76 (100%)

## Limits

- The model's confidence is its own; the filter trusts the data, not the number.
- Meanings cannot be checked by data: every one stays "from the model" until the person reads it.
- In Claude Desktop the server cannot call a model (no sampling); the fill is the web app's.
- The bench is small and built here; the live figures are two runs of five tables.
- Not done from the vNext list: caveats once per answer (the context fix), OpenRouter, allowed
  summaries per measure, last-value aggregation for snapshots.
