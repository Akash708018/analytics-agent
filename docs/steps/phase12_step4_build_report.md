# Phase 12 Step 4 - build_report, the tool

21/09/2026. Baseline 599615d. Measured before starting: 1748 passed; test_phase8.py 99/0/2;
test_phase9.py 19/0/0; test_phase10.py 35/0/1; test_phase11.py 26/0/0.

## What it takes and what it refuses

`build_report(dataset_name, question, workspace_id)`. The question is an argument because
nothing records why a dataset was loaded (P12-D2), and it is the one section with no record
behind it.

**It refuses only when the dataset is not loaded.** `validate_dataset` refuses a dataset with no
contract, and its reason is good -- "a report saying so would be a page of NOT RUN". A report is
the opposite case. P12-D11 already decided every section appears and says why it is empty, and a
report of a dataset whose grain nobody agreed is still a report: it says the grain was never
agreed, which is the most important thing a reader could be told about those numbers. Refusing
would withhold that.

The layer is `report/tools.py`, mirroring `validate/tools.py` -- a `_not_loaded` refusal in the
same words, then the assembly, then the Rule 4 envelope, which for a report is
`Report.to_text()`: the path, the table of contents and the key findings inline.

## Predictions

1. `test_the_registered_tools_are_exactly_the_expected_ones` fails first. It is a closed set and
   its docstring calls that the intended friction; it fired on render_chart in Phase 11.
2. No forwarding guard is needed. C83 was a roster of twenty-plus parameters declared in one
   place and passed in another; build_report has three arguments and no roster to drift. A
   docstring guard is worth having, a forwarding guard is ceremony.
3. A report of a loaded dataset with no contract is written, not refused, and names the absence.
4. A dataset that is not loaded is refused with DATASET_NOT_LOADED and told what is loaded.
5. Acceptance stays at 99/0/2, 19/0/0, 35/0/1, 26/0/0 -- the end-to-end run on
   merged_multiheader.xlsx is Step 5 and nothing before it calls this tool.
6. Suite rises by the new tests only.

## Commands

1. `src/analytics_agent/report/tools.py`.
2. `build_report` in server.py, docstring written as instructions.
3. Declare it in EXPECTED_TOOLS once prediction 1 fires.
4. Tests: the refusal, the no-contract case, the Rule 4 envelope, the docstring.
5. Full suite and all four acceptance scripts, then commit.

## Outputs

**1-2.** `report/tools.py` and `build_report` in server.py. Compiles.

**3. Prediction 1 held.** `test_the_registered_tools_are_exactly_the_expected_ones` failed on
the new tool before it was declared -- the intended friction its own docstring describes, firing
for the second time in two phases. Declared, and it passes.

**4.** tests/test_report_tools.py, 7 tests, plus 4 docstring guards in test_tool_docs.py.

**5. Final.** Suite 1748 -> 1759. Acceptance unchanged at 99/0/2, 19/0/0, 35/0/1, 26/0/0.

**All six predictions held.** Prediction 2 is the one worth restating: no forwarding guard was
added, because C83 was a roster of twenty-plus parameters declared in one place and passed in
another, and build_report has three arguments. A guard for a roster that does not exist is
ceremony, and ceremony is what makes a suite slow to read.
