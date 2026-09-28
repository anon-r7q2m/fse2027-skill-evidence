# Fixed-case analysis for the reuse principles

2026-09-28. This is a retrospective, property-specific analysis of the fixed
records in [the reviewed proposal](proposal.md). It adds no task
execution, model output, official score or independently sampled case.
The [execution protocol](study_protocol.json)
separates the later offline replays from this analysis.

## Six explanatory families

Labels concern the stated property and use. `violated` requires contrary
evidence; missing evidence is `unassessed`. A prospective requirement is not
retroactively imposed on a historical policy. A whole skill is never assigned
one generic correctness label.

| Family and version | Producer, object and transformation | Property and actual consumer | Evidence label | Action suggested and competing explanation |
|---|---|---|---|---|
| GP v1 | Solver checkpoints; original test-only patches; preservation projection restores four test files to base. | Existing-test preservation on the projected tree; P ranks original candidates using comparable failure counts, keys, votes and order. | Projected preservation: `supported`. First original candidate's syntax: `violated` by a recorded public SyntaxError. Repair correctness of the later candidate: `unassessed`. A historical hard syntax guarantee: `not_applicable`. | Add an explicitly new syntax admission condition on the original object if that is the intended consumer contract. Keep the preservation projection. RAW admission plus the tie-break already explains the bad-syntax choice; scope tracking has no separately defined policy effect. |
| Feedback v2, rank 192 | Public lookup issue; generated generic-helper assertion; actual KeyTransform converts incoming keys to strings before the helper. | The generated assertion is passed by V and selects V; an ordinary array index must retain array-index semantics outside the requested lookup change. | Proxy satisfaction by V: `supported`. Preserved array-index behavior along the recorded call chain: `violated`. Full issue correctness: `unassessed`; no observed lost benchmark solve (official B/U/V all zero). General causal effects remain `unassessed`. | Exercise the real producer path when constructing the preservation control. A simpler direct test on the resulting numeric string can be equivalent; path analysis does not automatically establish a better oracle. |
| NexAU/AHE mapping lineage | Source compactor and message types; target starts with host-owned observations; projection preserves ownership. One continuation changes eligible ownership. | Original proposed consumer requires package-owned observations; continuation requires configuration to reach initially empty state. | Original entry reachability: `violated` by the declared initial state and available effects. Configurable continuation: `unassessed` because configuration delivery is unspecified. No generated package exists. | Adapt ownership and explicitly deliver configuration, or declare a narrower fixed-configuration obligation. This is a proposal-level dependency failure, not observed failure of generated compaction code. |
| Moatless, separate identities | Source history screening consumes typed ViewCode/RunTests summaries. A different accepted cleanup package maps file removals to observation projection. | The first consumer is a source model-history builder; the latter consumer is the target model view. | Source typed-producer dependency: `supported` by source tracing. Delivery of all 30 cleanup replacements: `supported` by the existing trace. Input readmission in that cleanup block: zero observed. Causal score loss from removal: `unassessed`. | Preserve the needed producer when reusing history construction; for cleanup distinguish actual delivery from an absent capacity opportunity. These are separate mechanisms and must not inherit each other's outcomes. |
| Aider handoff | Architect response, editable-file context and independent editor history; declared host editor replaces the original editor. | Deliver full architect advice and declared context to the actual editor consumer. | Declared source and host-entry behavior on its cases: `supported`. Complete Aider equivalence and additional composition gain: `unassessed` or not measured. | Retain the successful declared adaptation as a counterexample to universal inseparability. A/P/AP all solve 3/4 in their block, so reachability is not evidence of an extra combination benefit. |
| Pro evaluator, pinned ca10a60a5fca | Supplied prediction IDs, cached worker outputs and a dictionary keyed by task ID. Missing inputs are unscheduled; duplicates overwrite in completion order. | Standalone mean over surviving unique result keys; report consumer may request a full-manifest or explicit-subset result. | Code-level scheduling/cache/reduction semantics: `supported`. Full-population or changed-patch attribution without matching evidence: `unassessed`. Live leaderboard policy and task validity: `unassessed`. | Check the report's intended population and cache identity. Explicit subset scoring is legitimate; public standalone behavior is not proof of a live leaderboard error. |

The controls oppose three overly strong readings: all projections are unsafe,
all old behavior must be preserved, and every accepted mechanism should improve
task scores. Successful Aider integration and legitimate subset reporting are
positive cases for bounded, explicitly adapted use.

## Complete GP context

The four tasks retain all P-bearing paths. Six paths have one candidate; the
other two use different keys with one vote each. All five GP candidate receipts
are comparable and have zero preservation failures. Those receipts do not
assert issue repair. Original N/G/P/GP totals remain 2/4, 3/4, 3/4 and 1/4.

| Task / path | Candidates | Actual checking and decision | Original outcome | Supported interpretation |
|---|---:|---|---:|---|
| Matplotlib 14623 / P | 2 | Regression disabled; two PY keys tie; first selected, different from current. | 1 | Successful selected candidate; current unscored, so prevented regression is unknown. |
| Matplotlib 14623 / GP | 1 | Preservation 4/4; selected=current. | 0 | Preservation holds on checked object; no between-candidate choice opportunity. |
| Django 13925 / P | 1 | Regression disabled; PY key; selected=current. | 1 | No selection increment can be identified from this path. |
| Django 13925 / GP | 2 | Both projected trees equal base and preserve 4/4; RAW/PY tie selects earlier original. | 0 | A recorded syntax error remains eligible. Later test-only current is not a known correct repair. |
| Matplotlib 24177 / P | 1 | TEXT_SIZE_LIMIT yields RAW key; selected=current. | 0 | Size fallback is not evidence of a syntax error. |
| Matplotlib 24177 / GP | 1 | Preservation 5/5; same size fallback; selected=current. | 0 | Public issue symptoms remain; no alternative candidate to select. |
| Django 11292 / P | 1 | Regression disabled; PY key; selected=current. | 1 | Successful execution, without a comparison between candidates. |
| Django 11292 / GP | 1 | Preservation 6/6; PY key; selected=current. | 1 | Composition can solve; this is not a discriminating-selection positive control. |

Source: [original GP diagnosis](evidence/gp_diagnosis.md).
The offline syntax policy is a new diagnostic intervention; this table does
not change the validity or outcome of any original run.

## Complete feedback-v2 context

The fixed panel has eight tasks, with two gate activations. Its four shared-prefix
policies all solve the same 4/7 scored tasks and have the same one missing task.
These are not four independent samples. Zero paired gain does not establish
that feedback is generally ineffective.

| Rank / task | First relevant boundary | Property-specific interpretation |
|---|---|---|
| 186 / SymPy 24539 | Base CONTROL_FAILED; Symbol and PolyElement are compared as the control. | Checker fixture/expectation error; not a failed solver repair. |
| 187 / Matplotlib 25479 | Import thread-start error before issue cases. | Execution/dependency boundary; underlying cause `unassessed`. |
| 188 / Django 15268 | B checker receives signal 9 with no output. | Checker meaning `unassessed`; the later official missing result remains separately missing. |
| 189 / Django 16801 | DummyMeta lacks add_field. | Generated fixture error; desired issue behavior not evaluated by that execution. |
| 190 / SymPy 22914 | Checker receives signal 9. | Underlying termination cause `unassessed`. |
| 191 / Django 14725 | Activated check requires max_num=0 to prohibit creation; U and V are rejected. | The checker adds an API requirement absent from the issue. B/U/V correctness is not established by this disagreement. |
| 192 / Django 15503 | Activated generic numeric-string assertion; V passes and is selected. | Proxy satisfaction and real producer-path behavior diverge; no measured lost solve. |
| 193 / Django 14915 | B already passes generated issue/control checks. | No further-repair opportunity under the frozen gate; not proof of full task correctness. |

Source: [pre-release semantic review and later outcome supplement](evidence/feedback_review.md).
The new path controls must have their own explicit preservation obligation;
the generated proxy is not promoted to a ground-truth requirement.

## Complete PQ opportunity control

| Task | Distinct P trees | Selected tree changes | P / PQ official outcome |
|---|---:|---|---|
| Django 14534 | 4 | Yes | 0 / 0 |
| Pytest 7982 | 1 | No | 1 / 1 |
| Django 15368 | 2 | Yes | 1 / 1 |
| Django 12325 | 4 | Yes | 0 / 0 |

All sixteen P samples are admitted. PQ changes three outputs without changing
any official result; both endpoints score 2/4. Unselected candidates are not
all scored. Therefore changed decisions do not establish usefulness, and the
unsuccessful pools' recoverable headroom remains unknown (0--2 tasks in this
block). Source: [PQ report](evidence/pq_report.md).

## Claim boundary after analysis

The records justify proposing consumer-relative obligations and choosing the
specific offline diagnostics. They do not independently validate the rules,
establish that the rules would have been discovered before observing these
cases, or show greater utility than ordinary local checks. Labels and suggested
interventions were drafted and cross-checked by in-product coding agents
under the user's research direction; they are not independent human
annotations. The fixed source/version map
and the exact competing explanations must accompany later replay results.

Further sources: [versioned dependency matrix](../study/dependency_cases.md),
[Pro source findings](../audit/pro_evaluator_semantics_followup_2026-08-31.md),
and [six-benchmark public audit](../audit/decision_oriented_delivery_2026-08-31.md).
