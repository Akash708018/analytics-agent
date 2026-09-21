# Cleanup Step 7: a column type set in an Ingest Spec reaches the loader

Found while writing the Track B UI contract (src/analytics_agent/webapp/contract.py), whose
Ingest Spec editor offers a type per column. Checking that the choice would do something: it
would not, and does not today in Track A either.

## The defect

`ColumnSpec.dtype` is part of the confirmed spec, and `IngestSpec.to_text()` shows it to the
person confirming ("| order_date | order_date | DATE |"). `IngestSpec.to_loader_kwargs()` never
passes it on. Both loaders accept `dtypes: dict[str, str]` keyed on the final column name, and
neither receives it, so the file loads with inferred types while the confirmed spec said
otherwise. to_loader_kwargs' own docstring names this failure -- "dropping it silently would
load the file on different terms than the ones confirmed" -- and its guard cannot see it,
because the guard checks keys that were put in `kwargs`, and this one never was.

## The fix

`to_loader_kwargs` adds `dtypes={target_name: dtype}` for every column with a dtype, and only
when at least one has one, so a spec with none produces the same kwargs as before and the
signature guard still covers the new key.

## Commands and outputs

1. Falsify: tests in tests/test_ingest_spec_dtype.py -- a spec with one pinned column puts it in
   the kwargs; a spec with none adds no key; confirming a CSV spec with order_date pinned to
   VARCHAR through server.confirm_ingest_spec loads it as VARCHAR (inferred, it is DATE).
   Expected on the unfixed tree: the two dtype-present tests fail, the no-dtype test passes.
2. Apply. Expected: all pass; pytest 1778 -> 1778 + 3.
3. Acceptance unchanged (99/0/2, 19/0/0, 35/0/1, 26/0/0, 36/0/0), eval 76/76, tree clean.
4. Also in this commit, not part of the defect: webapp/contract.py, the UI/engine interface;
   `[tool.pytest.ini_options] testpaths = ["tests"]` so the UI's own tests, which need
   streamlit, are never collected by the engine's suite. Expected: the count is unchanged by
   testpaths.
5. Records: C96. Commit and push.

## Results

1. Falsify: `2 failed, 1 passed`; `AssertionError: assert 'DATE' == 'VARCHAR'`. As expected.
2. Fix: `3 passed`; full suite `1781 passed`. As expected.
3. Acceptance 99/0/2, 19/0/0, 35/0/1, 26/0/0, 36/0/0; eval 76/76; tree clean. As expected.
4. testpaths added; count 1781, unchanged by it. contract.py imports: 18 names.
5. Records: C96.
