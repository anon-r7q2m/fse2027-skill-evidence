# SEARCH/REPLACE plus Chooser: no additional solves

2026-09-20. **N 2/4; Q_OFF 1/4; Q_ON 1/4; P 2/4; PQ 2/4.** The
composition matches the base host and the editing constituent. Choosing another
candidate changes three editing outputs, but changes no task score. Both paired
selection increments are zero. All original executions and official scores
finished before one-time release; this is a complete tied development result.

| Fixed task | N | Q_OFF | Q_ON | P | PQ |
| --- | ---: | ---: | ---: | ---: | ---: |
| django__django-14534 | 0 | 0 | 0 | 0 | 0 |
| pytest-dev__pytest-7982 | 1 | 0 | 0 | 1 | 1 |
| django__django-15368 | 1 | 1 | 1 | 1 | 1 |
| django__django-12325 | 0 | 0 | 0 | 0 | 0 |
| Total / 4 | **2** | **1** | **1** | **2** | **2** |

The prespecified gate `PQ > max(N, P, Q_ON)` fails with difference zero.
`PQ - P = 0` and `Q_ON - Q_OFF = 0`, with no individual task changing score
within either pair. N, P and PQ solve exactly the same two tasks. The ordinary
six-request prefix Q_OFF is not the independently executed seven-request N.
No result is missing, imputed, or borrowed from another experiment.

## Scope and source identity

P is the unchanged Agentless SEARCH/REPLACE package
`b276b81cbd303ae186cabb004855362d3c1f325649234baf9e10c7e66f623f77`;
Q is the unchanged SWE-agent Chooser package
`0272999914d1f4203224ae94b1f6b263a387a3f82031d771203e6a10bec568e9`.
Both remain L2 given-target transfers with human host integration. This
composition adds neither a mechanism category nor a donor. No candidate code
was manually repaired, and no new extraction request was made.

Before reading tasks, ranks 106--121 and 129 prior exposures were frozen.
Rank 106 exceeded the complete-source byte ceiling; ranks 107--110 were the
first four statically eligible tasks, and screening stopped. Public source
locations and human obligation cards are development exposure, not held-out
confirmation. Every path receives the same task's public materials.

Each task has three fresh executions: ordinary N with up to seven requests;
ordinary Q with up to six requests plus one source Chooser request; and P's
independent K4 construction plus one source Chooser request. These produce five
policy endpoints. The original P vote is frozen before Q, sharing exactly the
same generated pool with PQ. Q_OFF similarly freezes before Q_ON. P and Q_OFF
are shared-prefix controls, not independent repeats. Q replaces the terminal
vote, rather than combining two simultaneous voting algorithms.

All use gpt-5-mini/medium, per-request input/output ceilings 65,536/8,192,
300-second request timeout, and 1,500 solve plus 300 finalization seconds after
setup. P construction is not shortened to reserve Q capacity. Request ceilings
are N/Q/PQ = 7/7/5. Common ceilings do not imply equal actual computation or fees.

## Actual selection behavior

| Rank | Q ordinary candidates shown | P admitted / 4 | P distinct trees | P sample | PQ sample | P/PQ tree changed | P/PQ scores |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 107 | 1 | 4 | 4 | 1 | 2 | Yes | 0 / 0 |
| 108 | 0 | 4 | 1 | 1 | 1 | No | 1 / 1 |
| 109 | 1 | 4 | 2 | 1 | 2 | Yes | 1 / 1 |
| 110 | 1 | 4 | 4 | 1 | 2 | Yes | 0 / 0 |

All sixteen P samples are admitted and vote-eligible. Each PQ chooser sees all
four original candidates, including multiplicity, and makes one request.
No displayed patch receives the source formatter's long-patch invalid marker.
Q ordinary makes three requests: three rosters contain one candidate, while
rank 108 has no changed-tree candidate and retains Q_OFF without a request.
All four Q_ON trees equal Q_OFF. A one-candidate choice does not measure
discrimination between repairs.

PQ does select a different original tree on three tasks. Those choices improve
no official result and harm none. Unselected candidates are not scored, so this
does not establish whether the unsuccessful pools contain a correct repair.
The one permitted existing-trace diagnosis is being completed separately;
no additional candidate, task, seed, prompt tuning, or official scoring is run.

## Execution and cost

| Actual execution | Requests | Input tokens | Output tokens | Sum of original child elapsed seconds |
| --- | ---: | ---: | ---: | ---: |
| N | 22 | 249,888 | 5,096 | 257.43 |
| Q | 26 | 340,849 | 5,849 | 236.05 |
| PQ | 20 | 212,914 | 19,098 | 304.97 |
| Total | **68** | **803,651** | **30,043** | **798.46** |

Elapsed time includes child setup, execution, finalization and cleanup. Recorded
setup totals are 11.15/11.08/15.64 seconds for N/Q/PQ. Q construction and choice
take 165.67/14.85 seconds; PQ construction and choice take 217.53/27.30 seconds.
These phase times do not include all process and cleanup overhead.

| Shared-prefix policy | Requests | Input tokens | Output tokens |
| --- | ---: | ---: | ---: |
| Q_OFF | 23 | 334,092 | 4,898 |
| Q_ON | 26 | 340,849 | 5,849 |
| P | 16 | 184,620 | 16,753 |
| PQ | 20 | 212,914 | 19,098 |

This second table is **not additive**. P is part of PQ and Q_OFF is part of
Q_ON. The actual total sums N, Q_ON and PQ once. Relative to P, PQ adds four
requests, 28,294 input and 2,345 output tokens, with no extra solve. Relative
to Q_OFF, Q_ON adds three requests, 6,757 input and 951 output tokens, also
without an extra solve. No equal-cost or economic advantage follows.

All 68 requests reached COMMIT, without pending work or new UNKNOWN usage.
Cached input 609,792 and reasoning output 19,392 are included in the totals.
The historical two UNKNOWN transactions remain; actual gateway fee is TBD.

Original solver launcher 1914717 exited zero at 19:54:56 UTC without restart;
all twelve solver environments and 37 mechanism workers are cleaned. All twenty
endpoints then sealed into fifteen distinct task/base/tree/scorer inputs. The
five shared mappings follow identical scoring inputs only. Original scorer
launcher 2095398 exited zero at 20:04:48 UTC, with fifteen valid score terminals
and thirty closed resource projects. One-time release followed its exit.

Twelve solver plus fifteen scorer starts consume **27 benchmark starts**,
bringing the ledger from 511 to **538/543**, five remaining, zero in flight.
Scoring deduplication savings are not an allocation for a new experiment.
Extraction remains closed at **320 used + 77 retired = cap 397**.

## Decision and relation to earlier gains

This version is closed with a tied main gate. No conditional naive/full-harness
successor is activated. A next research decision must use the bounded diagnostic
evidence rather than repeat these tasks or tune until the sign changes.

The earlier editing comparison separately records SEARCH/REPLACE 4/4 versus
N and coordinate editing each 1/4. Two later R composition blocks separately
record editing 2/4 versus N 1/4. Those are real local positive differences;
this block adds no positive difference over N or the best constituent. Task
sets, execution versions and sampling differ: no cross-block pooling or arm
substitution is supported. Four exposed tasks and one run per execution do not
establish stability, source necessity, statistical confirmation, naive/full
superiority, or cross-condition gains.

The full research goal remains active and incomplete. Independent outcome
review is pending and recorded separately; completed execution is not approval
or a positive composition result.

Evidence: [frozen design](../../experiments/search_replace_chooser_v1/DESIGN.md),
[execution summary](execution_summary.json), [one-time released scores](scores/reconciliation.json),
[completion summary](completion_summary.json), and
[launch review](../../docs/reviews/search_replace_chooser_v1_launch_20260920.md).
