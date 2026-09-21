# Phase 11 Step 3a - the parameters compute_analysis never passes

21/09/2026. Baseline 0879d9c. Found while reading `compute_analysis` to mirror its shape for
`render_chart`, which is why it is fixed before Step 3 rather than after: Step 3 would have
copied the pattern.

## Measured, before any edit

    declared in compute_analysis : 20
    forwarded to the tool layer  : 14
    wanted by some analysis      : 23

**Not declared at all** -- no caller can pass them, because FastMCP builds the schema from the
signature: `alpha` (sample_adequacy), `confidence` (confidence_interval), `entity`
(cohort_retention, repeat_behaviour -- REQUIRED by both), `method` (hypothesis_test), `power`
(sample_adequacy), `second_dimension` (effect_size, hypothesis_test).

**Declared but not forwarded**: `against` (bivariate, correlated_shift, correlation),
`baseline` (growth_decomposition, mix_shift, period_compare), `period` (cohort_retention,
growth_decomposition, mix_shift, period_compare).

## What that means for a caller

Eight of twenty-seven analyses cannot be called at all through the tool an agent uses, because
a required parameter never arrives: bivariate, correlated_shift, correlation,
growth_decomposition, mix_shift, period_compare, repeat_behaviour, cohort_retention. Four more
cannot be fully used: sample_adequacy, confidence_interval, hypothesis_test, effect_size.

The refusal blames the caller. Proved rather than reasoned:

    correlation signature: (con, gate, scope, measure, against, **params)
    TypeError raised: correlation() missing 1 required positional argument: 'against'

and tools.py turns that into `ANALYSIS_PARAMS_INVALID -- "correlation was called with arguments
it cannot take."` The agent passed the argument; the server dropped it; the refusal names the
agent. An agent that believes that refusal will stop asking, which is worse than a traceback.

The docstring is already ahead of the signature: it documents `second_dimension` and `method`
for hypothesis_test, neither of which the signature declares, so the tool description instructs
the agent to pass a field the schema does not contain.

## Why nothing caught it

tests/test_analysis_tool_docs.py has `test_every_parameter_any_analysis_takes_is_declared`, and
it checks a hardcoded set with `<=` -- a subset assertion against a roster typed out by hand,
which passes while the roster is stale. That is the shape P10-D39 removed from the tier test and
C72 removed from the docstring roster, surviving in a third place. The three acceptance scripts
call the registry and the tools layer directly and never reach server.compute_analysis, so the
only path that exercises the real MCP surface is the one nothing tests.

## The fix

1. Declare the six missing parameters.
2. Forward all of them.
3. Replace the hardcoded subset assertion with one derived from the registry, and add its
   missing half: every declared parameter must also be forwarded.

## Predictions

1. The derived declaration test fails first on six names, and the forwarding test on three.
2. No existing test changes behaviour: nothing else reads compute_analysis's signature.
3. The acceptance scripts stay exactly where they are, because none of them calls this tool.

## Outputs

**1. Guards written before the fix, and they failed as predicted.**

    FAILED test_every_parameter_any_analysis_takes_is_declared
    FAILED test_every_declared_parameter_reaches_the_analysis_layer
      AssertionError: declared by compute_analysis and never passed on:
      against (needed by bivariate, correlated_shift, correlation);
      baseline (needed by growth_decomposition, mix_shift, period_compare);
      period (needed by cohort_retention, growth_decomposition, mix_shift, period_compare)
    2 failed, 6 passed

**2. Fix.** Six parameters declared, twenty forwarded. `tests/test_analysis_tool_docs.py`
8 passed. Full suite 1698 -> 1699, the one added being the forwarding half nobody had written.

**3. Predictions, scored.** All three held. The declaration test failed on six names and the
forwarding test on three; no existing test changed behaviour; the acceptance scripts stayed at
99/0/2, 19/0/0 and 35/0/1 -- which is itself the finding, and is now P11-O1.

**4. What is left open.** P11-O1: no acceptance script calls a Tier 3 to 7 analysis through the
registered MCP tool. The unit guard catches this defect class structurally. It does not walk the
path a real client walks, and three green acceptance runs said nothing while eight analyses were
unreachable.
