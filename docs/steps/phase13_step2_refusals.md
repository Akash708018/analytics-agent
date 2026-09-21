# Phase 13 Step 2 - closing what the harness found

21/09/2026. Baseline e4b6c70. Measured before starting: 1759 passed; acceptance 99/0/2, 19/0/0,
35/0/1, 26/0/0, 36/0/0; eval SCORE 27/28 (96%).

Step 1 built the harness and it found two things. This closes them. Filling the question set to
the guide's 30-40 is Step 3 -- fixing a defect the eval found before writing thirty more
questions against the version that has it is the order that costs less.

## P13-O1, measured precisely

Sixteen of thirty-seven refusals name a call an agent can make verbatim. Of the twenty-one that
do not, the classifier's two buckets were wrong and there are three kinds:

- **Ten are prose glued to a complete call.** `list_datasets() to see what is already here`;
  `propose_dataset_contract(dataset_name="x") and confirm it`. The call is right and the
  sentence is guidance. `Refusal` already has a `detail` field that renders as its own line, so
  the guidance has somewhere to go.
- **Five are the `(..., extra=...)` form**, all in contract/tools.py: "call it again with what
  you had, plus this". Deliberate and not executable, because the arguments it means are the
  ones the caller already passed.
- **Six carry a placeholder the caller must fill** -- `primary_key=[...]`, `grain=...`,
  `path="..."`. Correct: the caller has to decide, and `Refusal`'s own docstring uses
  `confirm_dataset_contract(contract_json=...)` as its example of a good next_call.

So the fix is the ten, and the other eleven are right as they are. A refusal is then either a
call an agent can make, or one that explicitly marks what the caller must supply -- and nothing
in between, which is the property worth having.

## P13-O2

Two scripts now restore docs/contracts/*.yaml by hand after confirming a contract, because C86's
fix was made to one script rather than to the pattern. A shared helper, used by both.

## Predictions

1. Ten sites move prose into `detail`. The roster goes from 16/37 to 26/37.
2. B04 passes, and the eval scores 28/28.
3. Existing tests assert on refusal text. Some will fail -- I expect two to five, and each will
   be a test naming the prose rather than the call.
4. No behaviour changes: the same refusal, the same reason, the same call, with the sentence
   moved one line up. Acceptance stays where it is.

## Commands

1. Move the prose on the ten sites into `detail`.
2. Run the suite; fix whatever prediction 3 turns up.
3. A shared restore helper for the contract export, used by test_phase12.py and run_eval.py.
4. Suite, five acceptance scripts, eval. Record, close both items, commit.

## Outputs

**1. Ten sites edited, and one of them broke the tree.** `contract/compatibility.py:188` already
carried a computed `detail="; ".join(detail)`, so adding a second produced
`SyntaxError: keyword argument repeated` and eighteen collection errors. My assumption that none
of the ten had a detail was never checked -- one grep would have. Fixed by extending the existing
join rather than adding a keyword beside it.

**2. Prediction 1 exact: the roster went 16/37 to 26/37 (70%).** The eleven that remain are the
five `(..., extra=...)` forms and the six placeholders, both correct as they are.

**3. Prediction 3 was wrong, and the reason is worth keeping.** I expected two to five existing
tests to fail on the changed refusal text. None did: every one asserts on the call
(`'propose_dataset_contract(dataset_name="other")' in text`), and the bare call was always a
substring of the prose version. The assertions were testing the right thing already.

**4. The fix broke a gold question, correctly.** B01 was classified `needs_decision` and was
right until the fix; `state.py`'s NO_CONTRACT refusal now names a runnable
`propose_dataset_contract(dataset_name="...")` with the decisions moved to DETAIL. The question
followed the fix. **SCORE: 31/31 (100%)**, behavioural 22/22.

**5. P13-O2 had a better answer than the one it proposed.** It asked for a shared restore helper
for two scripts doing the same bookkeeping. `contract/tools.confirm` reads `store.EXPORT_DIR` at
call time, so a script can point it at its own workspace and nothing outside is written at all.
No restore, no helper, and less code than either script had. The open item named the wrong fix
and the right problem.
