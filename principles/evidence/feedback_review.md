# Shared-prefix feedback v2: bounded outcome review

Reviewer: `/root/feedback_v2_outcome_review`. Date: 2026-09-22.

## A. Findings fixed before official score release

This section uses the frozen eight-task design, the entry-v2 protocol, public
issues, submitted checkers, B/U/V captures, recorded model inputs, and execution
observations. Official scores have not been read. No model, container, test, or
scorer was run for this review. The review does not revise any gate, selector,
endpoint, denominator, or frozen artifact.

**The treatment reached the model and changed code. The two activated checkers
both introduce requirements beyond the public issue; one directs a concrete
regression in shared JSON path semantics.** These are semantic findings about
the generated checks, not evidence that the official benchmark tasks are invalid.

### Actual treatment and selection

For ranks 191 and 192, both arms received the same full B projection, source
excerpts, issue, prior patch, model configuration, tools, and remaining-four-request
hint. Comparing the recorded first request bodies shows that the only input
addition in V is the recorded behavioral-observation section. The source context
is byte-identical between U and V: 24,479 bytes for rank 191 and 13,174 for rank
192. These excerpts contain the B edits, not just the original source.

The complete modified files were reconstructed in memory from the captured base
source and each sealed patch. Their bytes match the content hashes in all six
B/U/V manifests. This supports the code comparisons below without creating or
executing an alternative candidate.

| Rank / issue | U relative to B | V relative to B | Post-check U / V | Frozen selection |
|---|---|---|---|---|
| 191 / Django 14725 | Edits unbound form counting to suppress extras when `can_create=False` | Also caps bound form count at the initial count when `can_create=False` | REPRODUCED / REPRODUCED | G(U)=B; G(V)=B |
| 192 / Django 15503 | No edit; identical final tree | Changes generic JSON path compilation so only actual `int` inputs become array indexes | REPRODUCED / COVERED_PASS | G(U)=B; G(V)=V |

All four continuations used four requests and ended at the request limit with
captured worktrees. All first attempted `pytest -q`, which returned exit 127
(`pytest: command not found`). Rank 191 U/V then edited on request 2 and spent
requests 3–4 reading source. Rank 192 U spent the remaining requests listing and
reading source without editing; V edited on request 3 and used request 4 on
another unavailable `pytest` invocation. This is observed ineffective use of
part of the allowance, not proof that a larger allowance would create gain.

Evidence under `results_cache/raw_issue_feedback_effect_v2/live/{191,192}/`:

- `requests/{U,V}/native/request_01/begin.json`: actual first request bodies.
- `entry/{U,V}/host/current_source/context.json` and `entry/common_B_source.json`.
- `entry/{U,V}/host/trajectory.json`: tool calls and their recorded outcomes.
- `entry/B/host/source_view.json`, `entry/B_sealed.json`, and
  `entry/both_branches_sealed.json`: source, patch, and full-tree identities.
- `entry/policy_endpoints.json`, `entry/post_U/observation.json`, and
  `entry/post_V/observation.json`: the actual frozen decisions.

### Rank 191: a feature request became an unsupported existing-parameter rule

The complete public issue asks for a way to disallow new objects in model
formsets. It explicitly says `extra=0` only controls displayed extra forms and
is not a reliable prohibition. It does not specify a new API name, require
`max_num=0` to become that prohibition, or explicitly state a backwards
compatibility policy.

The checker nevertheless calls `modelformset_factory(..., extra=0, max_num=0)`
and requires `save()` to return no new objects. It never requests B's new
`can_create=False` mode. The public base code gates maximum validation on
`validate_max`, whose factory default is false; bound form counting is limited
by `absolute_max`, not by `max_num` alone. Thus the checker has selected an
additional API design that is neither entailed by the issue nor the existing
implementation.

B adds an optional `can_create` argument and checks it in `BaseModelFormSet.clean()`.
U and V both continue that optional-mode implementation rather than changing
`max_num` semantics. Their retained checker failures show that they did not
implement the checker's extra requirement. They do not, by themselves, show
that the requested edit-only capability is absent. Conversely, this static
review does not establish that B/U/V completely or correctly implement that
capability. Official scores remain a separate outcome.

Evidence:

- `experiments/raw_issue_feedback_effect_v2/screen/191/public_issue.json`.
- `live/191/entry/checker/generated/script.py`, especially
  `test_new_objects_disallowed_by_max_num` and `test_existing_objects_editable`.
- `live/191/entry/B/host/source_view.json`: complete base `formsets.py` and
  `models.py`; base formset lines 143–158 and 391–397 establish the existing
  count/validation distinction.
- `live/191/entry/B/host/snapshots/capture_002/agent.patch`;
  `live/191/entry/{U,V}/host/snapshots/capture_005/agent.patch`.

The three preceding `live/...` paths are relative to
`results_cache/raw_issue_feedback_effect_v2/`.

### Rank 192: a lookup-specific requirement became a wrong generic invariant

The public issue concerns `has_key`, `has_keys`, and `has_any_keys` on SQLite,
MySQL, and Oracle. Its concrete example checks whether an object has key
`"1111"`. The generated checker does not exercise those lookups; it requires
the general helper `compile_json_path(["1111"])` to return `$."1111"` by
default. Its controls cover `"foo"` and the actual integer `3` only.

B introduces `allow_array_index` with a true default, and supplies false for
the scalar has-key RHS on those backends. A lookup-specific repair can therefore
leave the generic helper's numeric-string default unchanged and still address
the public example. Whether B handles all required lookup cases is not proved
by this review.

V changes the generic helper to treat all strings as object keys. The unchanged
public `KeyTransform.__init__` converts **every** input with
`self.key_name = str(key_name)`, and `preprocess_lhs` forwards those strings to
the generic helper from the SQLite, MySQL, and Oracle implementations. Therefore
an ordinary numeric transform such as `KeyTransform(0, ...)` now compiles a
quoted object key `$."0"` where the base/B compile array index `$[0]`.
This semantic change follows directly from the code. No benchmark execution is
needed to identify it; its measured test impact is still unknown before release.
The integer control cannot detect the regression because real KeyTransform
inputs have already been converted to strings.

V's actual feedback contains the numeric-string assertion, V's edit implements
it, and the same checker then passes and selects V. This is a concrete trajectory
consistent with optimizing an incorrect proxy. It does not establish a general
causal law or justify changing the frozen selection after seeing scores.

Evidence:

- `experiments/raw_issue_feedback_effect_v2/screen/192/public_issue.json`.
- `results_cache/raw_issue_feedback_effect_v2/live/192/entry/checker/generated/script.py`.
- `live/192/entry/B/host/source_view.json`: base `json.py` lines 304–350,
  including conversion at line 310 and backend calls at 326, 331, and 350.
- `live/192/entry/B/host/snapshots/capture_002/agent.patch` and
  `live/192/entry/V/host/snapshots/capture_006/agent.patch`.
- `live/192/entry/post_V/observation.json`: all three proxy cases pass.

The last three `live/...` paths are relative to
`results_cache/raw_issue_feedback_effect_v2/`.

### The other six tasks: first nonactivation layer

| Rank / issue | Frozen nonactivation | First observed responsibility layer |
|---|---|---|
| 186 / SymPy 24539 | Base CONTROL_FAILED | The default-symbol control compares expression `Symbol` objects with ring `PolyElement` generators; its assertion fails. Checker fixture/expectation error. |
| 187 / Matplotlib 25479 | Base UNKNOWN | Importing pyplot reaches FontManager's timer and raises `RuntimeError: can't start new thread`; issue cases never execute. Execution/dependency layer; the precise resource or sandbox cause is not established. |
| 188 / Django 15268 | Base REPRODUCED, B UNKNOWN | B's check ends with return code -9 after 30.01 seconds and no output. Unresolved execution termination, not a passing/failed issue assertion. |
| 189 / Django 16801 | Base UNKNOWN | Generated `DummyMeta` lacks `add_field`; both cases raise `AttributeError` in `contribute_to_class`. Checker fixture error. |
| 190 / SymPy 22914 | Base UNKNOWN | The checker process ends with return code -9 after 13.35 seconds. The raw receipt remains UNKNOWN and the underlying signal cause is unresolved. |
| 193 / Django 14915 | Base REPRODUCED, B COVERED_PASS | B already passes the generated issue and control checks. No additional-repair opportunity under the frozen gate. |

Primary evidence is each task's `entry/gate.json`,
`entry/checker/execution/execution_001/behavior_receipt.json`, and, where present,
`entry/gate_check/execution/execution_001/behavior_receipt.json`. Rank 186's
`entry/checker/generated/script.py` shows the type mismatch directly.

### Decision boundary before scores

Keep all eight tasks and the actual G decisions. Do not delete activated tasks
because their checker semantics are flawed. Do not relabel generated
REPRODUCED/COVERED_PASS as independently validated issue correctness.

The design's predeclared stop rule remains controlling: if G(V) does not improve
on both B and G(U), close this strategy version without unchanged expansion.
Regardless of score direction, these trajectories establish that reliable issue
semantics is an unresolved dependency of the feedback strategy. An additional
larger sample alone would not address that failure mechanism.

## B. Supplement after official score release

Added after the main agent reported the original scorer's wait/exit 0 at
2026-09-22 16:46:28 UTC and released the results. This supplement checks
`results_cache/raw_issue_feedback_effect_v2/REPORT.md`,
`completion_summary.json`, and `scores/reconciliation.json`. Their reported
totals and contrasts agree; the completion summary contains the identical
reconciliation. Section A remains unchanged, including its pre-release
observations and uncertainty. No hidden test patch was read.

### Released result and stopping decision

**Close this version and stop unchanged expansion.** B, U, G(U), and G(V) each
resolve **4/7 scored tasks**, with the same success set. Rank 188 remains missing
for every endpoint; it is neither an eighth failure nor an excluded task.
The fixed panel still contains eight tasks and has two gate activations.

All four predeclared contrasts, U−B, G(U)−U, G(V)−G(U), and G(V)−B, have seven
complete pairs and observed net difference **0**. Retain the frozen conservative
eight-task net bounds **[-1,+1]** and rate bounds **[-0.125,+0.125]**. These bounds
are not confidence intervals. The observed tie does not establish equivalence
or absence of benefit on other tasks.

G(V) has not shown an improvement over either B or G(U), so it does not satisfy
the design's condition for continuing the same strategy. Do not append tasks,
remove the two semantically problematic activations, amend G, or rescore this
panel. The complete research goal remains unfinished; another investment needs
a distinct mechanism explanation or the existing discovery roadmap.

### What the activated cases now establish

| Rank / issue | Official B / U / V | Meaning of the recorded selection |
|---|---|---|
| 191 / Django 14725 | 0 / 0 / 0 | Both checker-rejected continuations and the retained B fail official scoring. This does not validate the checker's unsupported `max_num=0` requirement. |
| 192 / Django 15503 | 0 / 0 / 0 | The checker selects V after its proxy passes, but V still fails official scoring. B and U already fail, so there is no observed binary score decline caused by selecting V. |

The rank-192 change to generic array-index semantics identified in section A
is a code-level regression on the documented call path. The released scores do
**not** show a lost officially solved task: B=U=V=0. The appropriate interpretation
is that feedback induced an edit which satisfied a faulty proxy without producing
an official solve; it is not that feedback reduced the measured pass rate. This
also does not establish that the proxy defect is the only reason the task fails.

Both activated tasks consumed the continuation allowance without adding an
official success. Thus this panel provides no measured gain from gated additional
computation, selection, or feedback information. It also provides no measured
score loss for these policies.

The main agent's separate read-only diagnosis places rank 188's missing score at
the inner official verifier's 900-second timeout: the exception is
`VerifierTimeoutError`, also recorded as 900.0 seconds in `trial.log`, under
`scores/188-B/trials/a2s-feedback-effect-score-188-b/`.
`trial_finalization_failure_v6.json` records the subsequent finalization failure.
The outer scorer has `WAIT_FINISHED`, 926.56 seconds, exit 1,
`timed_out=false`, and confirmed cleanup. This identifies the failing layer;
the underlying cause remains unproved and is not assigned to the candidate,
environment, or benchmark validity. Rank 188 remains missing. The earlier
generated check's UNKNOWN alone does not establish the cause of this timeout.

### Accounting and manuscript wording

The release records 132 model requests (60 new checker requests and 72 solver
requests), 996,935 input and 128,027 output tokens, and zero unknown-usage
requests. Eight task children and eleven scorer processes give cumulative
benchmark starts **914/1387**; twelve solver Host invocations are a separate
count. Extraction closes at **535 used + 88 retired = 623**. Actual currency
cost remains TBD, and equal actual cost is not claimed.

Suggested manuscript wording:

> In a prospectively fixed eight-task development panel using the calibrated
> entry, the shared-prefix policy B, unguided continuation U, and the selected
> policies G(U) and G(V) each resolved 4/7 scored tasks; one task remained
> unscored. The gate activated on two tasks. All four predeclared paired
> contrasts were zero on the seven complete pairs, with the frozen conservative
> eight-task net bounds [-1,+1]. Feedback was delivered and produced edits, but
> neither activated task gained an official success. Pre-score semantic review
> found that both activated checkers imposed requirements beyond the public
> issue; in one case the feedback-induced edit passed that proxy while changing
> existing array-index semantics. B, U, and V all failed official scoring on
> that task, so no decline in binary task success was observed. We closed this
> strategy version under its predeclared stopping rule.

Keep this panel separate from the preceding 3/6 panel and older positive blocks.
It is evidence about this fallible-feedback deployment, not a comparison with N,
all constituent mechanisms, a naive reimplementation, or a full harness.
