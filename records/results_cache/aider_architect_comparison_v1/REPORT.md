# Aider architect plus SEARCH/REPLACE: complete tied composition comparison

2026-09-20. **N 2/4; architect A 3/4; editing P 3/4; composition AP 3/4.**
The combination solves one more task than the base host, but ties both
constituents on exactly the same three tasks. The prespecified
`AP > max(N, A, P)` gate fails with increment zero. This is a complete official
development comparison, not a composition advantage or a stability estimate.

| Fixed task | N | A | P | AP |
| --- | ---: | ---: | ---: | ---: |
| pylint-dev__pylint-4661 | 0 | 0 | 0 | 0 |
| django__django-13109 | 1 | 1 | 1 | 1 |
| scikit-learn__scikit-learn-12585 | 1 | 1 | 1 | 1 |
| django__django-14787 | 0 | 1 | 1 | 1 |
| Total / 4 | **2** | **3** | **3** | **3** |

Relative to N, AP gains django14787 with no lost solve. Relative to A and P,
it gains and loses zero tasks. All four policies fail pylint4661. Unselected
candidates remain unscored. The earlier SEARCH/REPLACE 4/4 versus N1/4 result
belongs to another task block and is not pooled with this one.

## Frozen comparison and original execution

The unchanged generated Aider handoff package and Agentless SEARCH/REPLACE
package run through the same qualified entries. Each task has four fresh paths:
N (ordinary editor, at most seven requests), A (one architect plus at most six
ordinary-editor requests), P (four same-base SEARCH/REPLACE samples), and AP
(one architect plus four SEARCH/REPLACE samples). A and AP independently generate
advice; the editor receives its exact text and inherited source without the
original issue or architect history. These are L2 given-target transfers with
human public requirements and source locations.

Ranks 111--114 are the first four compatible tasks under the rule sealed before
issue inspection. Screening stopped at four. This is development exposure, not
independent confirmation. No earlier candidate, favorable arm, score or advice
is reused. The sole local gate is AP > max(N, A, P). AP uses one more request per task than
P; equal realized cost and plan diversity are not claimed.

The concrete allocation reserves 16 solver and at most 16 scorer starts, with
at most 92 task-model requests and no automatic retry. Historical usage is 538;
the finite benchmark cap is 570. Extraction remains closed at 322 used plus
77 retired slots, cap399. Reserved starts are not actual use.

The original durable solver service is
`a2s-durable-a4556de154462f40f4de3623.service`; it was submitted once under manifest
`9615d062532216d2ed6daed4a73216a271ade7a9b0810eb62db4f1a36120effe`.
All sixteen original solver paths completed; original launcher3168789 exited
zero at22:11:52 UTC with no restart. Only after all original endpoints and that
exit did the frozen scorer seal every output. Identical task/base/tree/scorer
identities share an official score only under the prespecified map.

The sixteen endpoints are sealed into fourteen distinct task/base/tree/scorer
inputs. The original scoring service
`a2s-durable-dcc04d952125170c02ef95c1.service` was submitted once. All fourteen
original scores completed and all28 scorer resource projects closed; original
score launcher3743453 exited zero at22:35:09 UTC without restart. The full result
was released once afterward. No missing outcome is imputed and no old arm reused.
On django13109, A shares N's exact tree and AP shares P's exact tree; these are
the only two score-sharing mappings. All other score inputs are distinct.

## Completed execution and actual use

| Fresh path family | Requests | Input tokens | Output tokens | Sum of process seconds |
| --- | ---: | ---: | ---: | ---: |
| N | 23 | 347,628 | 44,450 | 1,246.68 |
| A | 23 | 166,341 | 17,231 | 916.64 |
| P | 16 | 97,864 | 24,783 | 356.85 |
| AP | 20 | 122,448 | 23,741 | 416.51 |
| Total | **82** | **734,281** | **110,205** | **2,936.67** |

All requests reached COMMIT, with no pending or new UNKNOWN transaction.
Cached input 337,280 and reasoning output 47,936 are included in their respective
totals. Historical two UNKNOWN transactions remain; actual gateway fee is TBD.
All 56 unique mechanism workers and sixteen solver environments have confirmed
cleanup. Sixteen solver plus fourteen scorer starts consume30 actual starts,
bringing cumulative use to **568/570**, two remaining and zero in flight.
Unused capacity is not a follow-up allocation. Extraction stays closed at
322 used plus77 retired, cap399, with zero available or in flight.

Process time includes startup and cleanup and is the common cross-arm measure.
Host elapsed records differ in cleanup scope between N/A and P/AP; they are
not combined with process time or used for a common comparison. AP uses four
more requests and 24,584 more input tokens than P, but 1,042 fewer output tokens.
No equal-cost or fee advantage is claimed. See [execution summary](execution_summary.json).

## Interpretation and disposition

A and P each show a one-task positive difference from N in this block. AP
retains those same successes but adds none beyond either constituent. The
extra architect request therefore yields no additional selected-task solve
over P here; this is not a paired same-pool selection experiment or proof that
planning can never help. AP's four candidates share one advice, and A/AP
independently generate advice. Exact-text handoff and model-generated code
can be accepted and active without increasing task coverage.

The version is closed. No extra task, K, seed, repeat, prompt tuning, or
scoring of unselected candidates is permitted. The single bounded analysis of
existing trajectories is underway. The reviewed source-blind/complete-harness
successor is **not activated**, because its prerequisite gate failed.
Independent outcome review is pending; completion_summary preserves that
write-time status. It will not convert a tied gate into a positive result.

Four exposed development tasks with one unseeded run per arm do not establish
stable improvement, source necessity, method superiority, statistical interaction,
or cross-condition gains. Naive/full-harness advantage and Harness Performance
Profiles remain TBD. The full research goal remains active and incomplete.

Evidence: [design](../../experiments/aider_architect_comparison_v1/DESIGN.md),
[allocation](../../experiments/aider_architect_comparison_v1/allocation.json),
[launch review](../../docs/reviews/aider_architect_comparison_v1_launch_20260920.md),
[original supervision](supervision/manifest.json),
[released matrix](scores/reconciliation.json), [completion summary](completion_summary.json).

## Completed follow-up, 2026-09-20

The subsequent [independent outcome review](../../docs/reviews/aider_architect_comparison_v1_outcome_20260920.md)
passes the execution, accounting, score mapping and reporting chain. The
composition gate remains false. The pending-review wording above and in the
completion summary records their original write-time status; this follow-up
does not replace or regenerate either result snapshot.

The one permitted [existing-trajectory diagnosis](DIAGNOSIS.md) is complete,
with zero new calls, candidate executions, tests or scores. On django14787,
N's first proposed replacement already contains the closure and metadata
repair, but all seven edits fail exact matching and the final patch is empty.
A applies a local edit successfully; P independently obtains the same scored
success. AP therefore adds no coverage. On pylint4661, the planning advice
specifies implementation details also present in some P candidates; all four
selected outputs still fail and the official failure obligation remains unknown.
Unselected candidates remain unscored.

This diagnosis does not identify a concrete, qualified donor mechanism for
another paid comparison. The next research step is bounded source analysis
and review of how a specific mechanism would add missing information or an
action. No new comparison is allocated or ready. This version and its
conditional naive/full branch stay closed; the full research goal stays active.
