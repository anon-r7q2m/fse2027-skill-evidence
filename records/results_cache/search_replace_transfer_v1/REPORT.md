# P2 SEARCH/REPLACE migration: behavior and actual-entry qualification complete

2026-09-20 10:13 UTC. One raw Direct generation produced a package that passed
4/4 public cases, a corrected independent evaluation's 5/5 cases, and one
scripted actual-entry control. The original independent run remains
**EVALUATION_INVALID** because its input sorting error preceded candidate
execution. No benchmark or official score was produced. This is an L2
given-target, same-source P2 editing variant, not a new mechanism or gain.

## Generation and public acceptance

The fixed Agentless SEARCH/REPLACE source and unchanged generated P2 parent
were supplied under `experiments/search_replace_transfer_v1/PLAN.md`.
Only `_build_prompt` and `edit_parser_pkg.py` were replaced with raw model
output; all other parent bytes are inherited. There were no human candidate
code repairs. The first request passed, the final package was sealed, and the
unused second request slot was retired.

- Original package: `b276b81cbd303ae186cabb004855362d3c1f325649234baf9e10c7e66f623f77`.
- Public acceptance: 4/4 cases, 14 scripted samples, 16 workers, cleanup confirmed.
- Actual generation: 1 COMMIT, 19,764 input / 16,029 output tokens.
- Original launcher 286819 exited 0 at 09:59:36.752121 UTC, without a restart.
- Extraction allocation closed: 308 used + 72 retired = cap 380; none available
  or in flight. Actual gateway fees remain TBD.
- Benchmark ledger unchanged at 426/512, 86 remaining, none in flight.

## Independent evaluation and current boundary

The independent suite was sealed before generation. Its original evaluator
returned `INDEPENDENT_FAIL`, 4/5 cases, with 16 workers and confirmed cleanup.
The evaluator maintainer subsequently located `INVALID_EVENT` at the input
validation boundary, before the candidate ran on that case: file paths were
not in the required unique sorted order. This establishes an evaluation-input
defect, not a candidate semantic failure. The raw result and original suite
remain unchanged; the run as a whole cannot establish independent PASS or FAIL.

A separate acceptance v2 changed only that mechanical input ordering. Exact
equality to the sorted original and five begin/sample-batch input checks passed
without candidate execution. Candidate bytes, expected behavior, sample order,
comparator and worker remained fixed. No private examples or expected outputs
were returned to generation. After the narrow independent review, its one
complete evaluation passed 5/5 cases with 20 workers, confirmed cleanup and
original process exit 0. It is a corrected evaluation of the same generated
sample; the original raw 4/5 and invalid disposition remain preserved.

`analysis/search_replace_entry_v1.py` then ran once on that exact package through
the existing `DiagnosticHost`. Four scripted responses led to three admitted
candidates, first index 1 and vote index 2, and publication of the two original
selected bundles. Three owned environments and four workers were cleaned.
All four scripted transactions committed; no model or official scorer ran.
Original child 410925 exited 0 after 50.88 seconds, without timeout or forced
cleanup, and its original wait owner recorded an empty remaining process group.
This establishes execution continuity for the public synthetic fixture only.

A distinct prospective editing-effect design is now prepared at
`experiments/search_replace_effect_v1/DESIGN.md`: fresh N and two independent
P2 pools, original coordinate edit versus SEARCH/REPLACE, with actual costs and
first-admitted/vote controls. No new task has been inspected or paid effect
allocation made. The closed RP v3 and its inactive conditional comparator remain
closed; passing component and entry checks is not a score improvement.

The most recent complete score comparison is still N/R/P2/RP2 = 2/1/1/1 out of
four tasks in `results_cache/rp_independent_comparison_v3/REPORT.md`. Stable
aggregation, best-constituent, naive and complete-harness advantages remain
unestablished. The full research goal stays active and incomplete.

Evidence: `generation/direct/final.json`, `generation/all_final_seal.json`,
`generation/generation_terminal.json`, `generation/direct/attempt_1/public/result.json`,
`allocation_close.json`, `supervision/launcher_exited.json`, and the preserved
`independent_disposition.json`; acceptance v2's public `summary.json` and
`execution_exit.json`; `actual_entry_control/summary.json` and
`actual_entry_supervision/terminal.json`. Private cases and traces remain
evaluator-only.
