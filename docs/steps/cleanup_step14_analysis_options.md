# Cleanup Step 14: an event key, no cap where the answer is a few numbers, fences within groups, chosen groups

Third fix step from the retail run. Closes RF-O6 (I2), RF-O8 (D3, D4), G1 and H1/H6.

## What was established before this document

- repeat_behaviour counts ROWS per person (analysis/repeat_behaviour.py:82); a two-line order "came
  back". Retail: 89.135% repeat, busiest 939, against the key's 82.096% and 633 orders.
- pareto and concentration share _ranked_with_shares, which raises TooManyGroups above 49 groups;
  their answers are a count to a threshold and six cut rows plus an index. concentration prints
  HHI with no decimals, so the key's 1.35 would read "1".
- outlier_detection has one global fence; retail's 32,467 Tukey flags are mostly Electronics prices
  set against Grocery's.
- hypothesis_test on a dimension of three groups runs ANOVA; no way to test two of them (H1), and
  sample_adequacy refuses three (H6).

## The fix

A. repeat_behaviour(event=...): a person's events are the distinct values of that column (an order);
   an event's date is its earliest row; rows with no event counted apart. Plus the median gap between
   consecutive events, beside the first-to-second one.
B. pareto and concentration have no group cap: pareto's full ranking goes to the result file;
   concentration adds cuts at 1%, 5% and 10% of the groups once there are 100 or more; HHI below
   100 prints with two decimals.
C. outlier_detection(dimension=...): the three methods' bounds per group, one pass; the summary sets
   the within-group total beside the global Tukey count.
D. groups=[...] on group_compare, hypothesis_test, effect_size, confidence_interval and
   sample_adequacy: the scope narrowed to those members of `dimension` before the analysis runs
   (registry.narrowed, as period), rows of other members counted in the method note; a listed member
   with no rows refused, naming those that exist.

## Commands

1. Baseline 1917.
2. Falsify: tests/test_analysis_options.py. Expected all fail.
3. Apply. Expected 1917 + new; test_analysis_tool_docs keeps every new parameter declared on the MCP
   tools (P11-D16) -- if it fails, the server signatures are the fix.
4. Live, retail (v2 contract of the run): repeat_behaviour(event=order_id) 34,836 people, 28,599
   repeaters (82.096%), busiest 633; pareto(sku) 180 of 500; concentration(customer_id) top 1% (348)
   12.56%, HHI 1.35, effective 7,427; outlier_detection(unit_price, dimension=category) far below
   32,467; hypothesis_test(channel, rating, groups=[Store, Online]) Welch, two groups.
5. Acceptance, eval, UI. 6. Records, commit.

## Results

1. Baseline 1917.
2. Falsify. 8 new tests: `7 failed, 1 passed`; the one that passed pins today's behaviour without an
   event key (a two-line order counts as coming back), which is meant to keep holding.
   2.1. Before any implementation, the concentration test's HHI was corrected from 44.33 to 44.37:
        my hand arithmetic, checked by `python3 -c` (44.3706). Not an expectation moved after
        seeing output -- no output existed.
3. Apply.
   3.1. The HHI edit left a dangling `summary.append(` (my patch, twice); rewritten with a helper.
   3.2. test_pareto's test_too_many_groups_are_refused_with_the_count pinned the cap this step
        removes; it now asserts 60 groups ranked. Two Step 11 tests used concentration to reach
        TooManyGroups; they use group_compare, still capped. The period that Step 11 carried into
        the top_n recovery became unreachable -- no capped analysis takes one now -- and is removed.
   3.3. test_analysis_tool_docs required `event` and `groups` on both MCP tools (P11-D16); declared
        and forwarded, and the web assistant's roster lists `groups`.
   Suite `1925 passed` (1917 + 8).
4. Live, retail (the run's contract v2):
     I2  "34,836 distinct customer_id value(s) across 150,000 distinct order_id event(s) in 224,835
         row(s). 28,599 came back at least once -- a repeat rate of 82.096%." Busiest 633. The
         median gap between consecutive orders is 86 day(s) against the key's 85: date_diff('day')
         counts calendar-day boundaries, pandas' .dt.days floors a timedelta.
     D3  "180 of 500 group(s) reach 80%".
     D4  "top 1% (348) | 12.56%", "HHI 1.35", effective 7,426.6 (the key's 7,427).
     G1  within category: Tukey 8,294, z 2,302, MAD 6,769, "One Tukey fence across all groups at once
         flags 32,467 -- the difference is the spread between groups". The key's exact route to the
         25 planted prices is a ratio to list price, not a fence.
     H1  "56,162 outside the groups Store, Online of channel." "Welch's unequal-variance t-test ...
         Statistic -216.4457" -- the key's line-level t.
     H6  runs on two groups: d 0.0166 at line level (the key's 0.0203 is per order: Step 15).
   The HHI floor printed "between 0 (every group equal)" for 34,836 groups; below 100 it now carries
   two decimals, as the index does.
5. Acceptance 99/0/2, 19/0/0, 35/0/1, 26/0/0, 36/0/0; eval 76/76; UI 37. As expected.

MEASURED VALIDATION line and digests: docs/decisions.md, section Cleanup Step 14.
