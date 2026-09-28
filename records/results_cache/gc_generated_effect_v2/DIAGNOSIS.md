# G/C effect diagnosis from the sealed execution traces

The completed block has N 1/2, G/C/GC 0/2. Every score is valid. The original
packages executed in the scored host; the failed outcome is not an entry failure.

| Observation | Recorded result |
| --- | --- |
| Real selector calls | 33; 78,050 input and 15,453 output tokens |
| Empty / malformed selections | 12 / 0 |
| Projection transactions / replacements | 21 / 30; all 30 delivered and acknowledged |
| Actual delivered C / G feedback | 33 / 12 |
| Local input readmissions | 0; all cleanup before/after admission checks were below the limit |
| Identical selector payload sent again | 4 calls, following earlier empty selections |
| G checks | 16 including four base checks; twelve post-change checks |

Pytest/G and Astropy/G/N stop at the local input estimate. Pytest/GC and both
Astropy C-bearing runs instead reach 32 shared requests. Pytest/C completes
at 27 requests with an incorrect scored patch. The C-bearing trajectories
therefore do not establish score or realized input/output-token efficiency.

Two concrete retention problems deserve the next design investment:

- Pytest/C removes the first skipping.py source window at selector query 11,
  then reads the identical command at query 12. Astropy/GC removes two card.py
  windows at selector query 8, then reads both again at queries 9 and 10.
- Pytest/C removes input:24 and input:43 after tests run under `|| true`.
  Their shell return code is zero, but both payloads contain the explicit
  `FAILED testing/test_skipping.py::test_errors_in_xfail_skip_expressions`
  marker and internal-error output. Return-code protection is not semantic
  failure protection. These observations were genuinely delivered earlier.

These are trace witnesses, not causal attribution of the lost solve. The
selector sees the issue and first/last snippets, without the full current
repair state. Source deletion/accounting are preserved, while this selector,
pressure trigger and observation mapping were declared development adaptations.

End effect exploration of this frozen G+C strategy. Before any new score block,
inspect an existing donor policy that preserves useful facts or controls when
to summarize, and calibrate it on new public fixtures containing old useful
facts, masked test failures, duplicate observations and scarce remaining calls.
C_naive and mini comparisons have no positive-result trigger in this block.

Evidence: [structured diagnosis](diagnosis.json), [full descriptive report](REPORT.md),
[reconciliation](reconciliation.json). Existing protocol, packages and scores are unchanged.
