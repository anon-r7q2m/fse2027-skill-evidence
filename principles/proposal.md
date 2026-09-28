# Principles for agent mechanism reuse: research meeting and bounded validation

**Later completion note, 2026-09-28:** the accepted bounded execution is now
closed at 20 offline conditions (6 GP, 8 feedback, 6 Pro). See the
[result report](REPORT.md),
[fixed-case analysis](case_analysis.md), and
[implementation/claim review](review.md).
The GP factorial was cancelled before execution; equivalent direct-helper
controls detected the same feedback regression. The proposal below is retained
as a historical proposal, not rewritten into a successful preregistration.

2026-09-28. Status: **reviewed research direction and prospective validation
outline; no new experimental result**. The user requested a discussion that
could lead to useful principles or a theory. Three in-product reviewers
examined novelty, falsifiability, and practical value, then exchanged concrete
counterarguments. The primary agent reconciled their proposals below.

This document does not change the frozen experiments, manuscript, scoring
continuation, allocation, or system goal. It is not a retrospective
preregistration. Any later offline execution must first fix its exact inputs,
assertions, interventions, and controls within the limits below.

## 1. Direction chosen

**Study what a particular consumer needs in order to use a transferred
mechanism's output for a particular decision.**

Working principle: when transferring a mechanism, define its obligations
relative to the target consumer and intended use. Preserve or explicitly
adapt the relevant production path, state, configuration, and meaning of
the evidence. If those conditions change, obtain replacement evidence or
narrow the claim supported by the result.

This is a candidate engineering principle grounded in existing contracts and
software-reuse ideas. It is not a new mathematical theorem, a claim that all
agent capabilities can be decomposed, or a proof of a minimal dependency set.
The intended output is an explanatory framework with testable design advice.

| Alternative | Decision and reason |
|---|---|
| Dependency-complete transfer | Retain as the entry condition. Source, state, configuration and consumer dependencies explain why code extraction alone can miss the intended behavior. Completeness and minimality are not established. |
| Evidence relative to a consumer's decision | Main question. It connects concrete object transformations and input paths to specific checks, permitted uses and actions. Its value beyond ordinary local fixes remains to be tested. |
| Activation and opportunity limits | Retain as competing explanations. Invocation, candidate diversity, changed selection and outcome improvement are separate. These distinctions alone are insufficient as the main novelty claim. |
| More mechanisms imply greater fragility | Not supported. No monotonic size law is proposed. |

## 2. Unit of analysis and three candidate principles

The unit is a **declared property used in a concrete consumer action**, not a
whole skill with a single PASS/FAIL label. Record:

- the source profile, authorized adaptations, producer and actual entry path;
- the original object, checked object and intervening transformation;
- the property checked and the evidence actually available to the consumer;
- the consumer's action and which fields its policy actually uses;
- the intended role: hard admission condition, soft ranking/feedback signal,
  or empirical task-utility claim;
- the observed action and separately the already released official outcome.

Classify that specific property as `supported`, `violated`, `unassessed`, or
`not_applicable`. These are analysis labels, not new formal benchmark-validity
dispositions. Missing evidence does not establish a violation. A later proposed
constraint must not be retroactively attributed to the historical policy.

| Candidate principle | Concrete engineering decision | Existing motivation | Condition that limits the principle |
|---|---|---|---|
| **P1: Define the intended use before choosing the extraction boundary.** | Determine which input producer, state ownership, configuration and consumer must be included or adapted. | NexAU's proposed target ownership class was empty; fixing ownership still left configuration delivery unspecified. Aider provides a successful, explicitly adapted handoff. | Reachability is not task benefit. A fixed-configuration adaptation can be useful without preserving every donor option. Unproved reachability is not proved impossibility. |
| **P2: Carry the object and property with the evidence.** | Decide whether a receipt supports the intended use, requires a check on the actual submitted object, or should be used only as a limited signal. | GP preservation checks concern projected trees. Pro evaluator findings concern the identity and population actually evaluated. | A projection may safely discard irrelevant differences. A preservation PASS remains useful for preservation; incomplete evidence may still help heuristic ranking. |
| **P3: Derive controls from the real input path and an explicit obligation.** | Exercise the caller's transformations when checking a shared helper; identify which behavior the requested change must preserve. | Feedback v2's direct integer control bypasses `KeyTransform` string conversion and misses a change in array-index semantics. | Realistic inputs do not make an assertion correct. Requirements or declared adaptations can legitimately change old behavior; preserving all old outputs is not the rule. |

The practical outputs are specific: preserve or adapt a dependency, add a
check on the actual object, restrict the interpretation of a result, or
record that the available evidence cannot resolve the question. The framework
must also identify legitimate transformations and limited uses; rejecting
everything is not useful diagnosis.

## 3. Objections that changed the proposal

**GP does not demonstrate total information loss.** Its two preservation
projections are identical, but the selector also receives different RAW/Python
keys, vote information and order. A public SyntaxError was already recorded.
The relevant question is which evidence constrains the actual decision, not
whether all available information is indistinguishable.

**GP does not demonstrate a false claim of issue repair.** Its receipt records
`issue_fixed=null`; preservation and best-effort ranking were the historical
roles. A new syntax admission requirement is an explicit prospective policy
change. The recorded RAW admission and first-occurrence tie-break are a strong
local explanation of the selected syntax-error candidate. The later candidate
was not independently scored and is not a known lost solve.

**A scope annotation alone is not a decision intervention.** If adding fields
leaves the consumer unchanged, it can improve interpretation but cannot be
credited with changing selection. If a proposed scope policy merely duplicates
a syntax gate, the two interventions are not separately identifiable.

**Production-path controls can be wrong.** A requirement may authorize a
change to existing helper behavior. A preservation obligation must be justified
independently from the old output, using the public requirement, documented
behavior or explicit adaptation. Otherwise the control remains `unassessed`.

**A subset score is not inherently invalid.** The Pro evaluator's supplied
population may be appropriate for an explicitly declared subset report. The
question is whether the actual population and cached input match the claim
being made. The standalone code does not establish live leaderboard policy.

These objections prevent the framework from defining all incomplete agents,
lossy transformations, or narrow evaluations as failures.

## 4. Two empirical questions, with negative stopping outcomes

### H1: What does tracing the evidence add beyond a local syntax fix?

For the fixed historical GP pool, separately examine an original-object syntax
admission change and a concretely specified scope-aware consumer policy.
Retain the original preservation projection, package, candidates and tie-break
outside the declared interventions.

The planned 2-by-2 comparison is permitted only if the two interventions have
distinct operational definitions before execution. If the scope treatment is
only metadata, duplicates syntax admission, or requires inventing an obligation
the consumer never claimed, drop this factorial comparison and report that no
distinct consumer-policy effect was specified. Do not invent a treatment just
to populate a table.

Record the evidence labels, selected candidate, abstention and rejection of
legitimate candidates. Test-only edits, unchanged preservation projections,
and `TEXT_SIZE_LIMIT` must not be rejected merely by category. Known syntax
errors and unknown parse status are different observations.

If only the syntax gate changes the bad selection, the supported result is a
local fix and a framework that helped describe its missing obligation. It does
not establish extra prevention value for generic scope tracking. Both the
explanatory and stronger intervention claims may receive different conclusions.

### H2: Does the real producer path improve these controls?

Fix the existing Base/B/V source objects for feedback v2's JSON-path case.
Compare the original direct-helper checks with a small, matched-count control
set that exercises the real caller transformation. Justify the preserved
behavior before executing either condition. Include a normal case and a
requirement-authorized change as controls.

Record whether the known semantic change is detected, whether legal behavior
is retained, and what additional information is needed. If an equally small
direct-helper control constructed from the same public obligation detects the
same issue, report that the production path helps derive the control, not that
it is uniquely or generally superior to direct tests. If the obligation cannot
be justified, or legal changes are rejected, narrow or abandon the claim.

Neither question predicts a benchmark solve, a better LLM repair, or a general
error-frequency reduction. Replaying exposed cases is diagnostic validation,
not independent prospective validation.

## 5. Two bounded batches

**Batch A: one working day for fixed-record analysis and exact replay design.**

Use six explanatory families: GP, feedback v2, NexAU's target mapping and its
single continuation, Moatless's context-consumer observations, Aider's accepted
handoff, and the pinned Pro evaluator. Within Moatless, source screening and
the accepted cleanup package retain separate identities and claims. Retain the
complete four-task GP panel and its P-bearing controls, the complete eight-task
feedback panel, and the complete four-task PQ panel as an opportunity/outcome
constraint. Do not select only the two striking traces. The existing nine-class
matrix remains the background catalog, not nine independent confirmations.

For each applicable property, record the proposed action, a legitimate-use
counterexample, the strongest competing explanation and unresolved evidence.
These cases are selected retrospectively to contrast stages; the analysis is
not grounded-theory sampling, a prevalence estimate or a held-out test.

Before Batch B, fix the exact fixture list, expected observations and existing
source entry points. Missing public source or executable dependencies yield
`unassessed`; a new surrogate implementation must not masquerade as original
code replay. A reduced illustrative model must be labeled separately.

**Batch B: one working day, at most 20 offline fixture conditions.**

| Group | Maximum | Planned content |
|---|---:|---|
| GP | 6 | Four intervention cells if identifiable, plus two normal multi-candidate controls, including a legitimate test-only change. Constructed controls are explicitly synthetic. |
| Feedback | 8 | Base/B/V under original and production-path checks, plus two legitimate-change/normal controls. |
| Pro evaluator | 6 | Missing IDs, duplicate IDs and cache identity, each paired with a contract-consistent control, including explicitly declared subset reporting. |

Pro uses public code with deterministic worker outcomes at a documented
boundary. It can verify orchestration and reduction behavior, not grading
accuracy, Docker behavior, live leaderboard error rates or task validity.
Transfer reachability in Batch A uses existing source/profile witnesses;
it does not generate another package or invent a successful NexAU execution.

Do not add models, benchmark tasks, seeds, source donors or official scoring.
Do not read private annotations or unreleased scores. Keep the original
scoring continuation separate and follow its existing release rules.

Finish each batch at its limit. Permit one ordinary implementation-fix pass;
if making a result pass requires changing a principle, property or control,
retain the failed version and stop. Do not expand the sample to rescue a claim.
Missing conditions stay missing. Report error detection, normal-control
rejection, abstention, unresolved cases and additional human interpretation
separately; no common rate is formed across heterogeneous fixture families.

## 6. Contribution and naming thresholds

| Claim | Required evidence |
|---|---|
| Candidate engineering principle | Precise intended use, explicit scope, actionable advice and a plausible counterexample. This meeting reaches this proposal stage. |
| Locally tested principle | The specified replay supports the advice and distinguishes at least one legitimate use from the known problem; negative outcomes are retained. This is pending. |
| Explanatory framework | Consistent analysis of the fixed families, explicit competing explanations and direct reproduction of the key mechanisms. It may remain retrospective. Validation is pending. |
| Broader explanatory/predictive theory | Frozen, discriminating predictions tested on independent implementations or host conditions, with comparisons to competing explanations and validated limits. This is not an obligation to open new studies before the deadline. |

A mathematically obvious sufficiency condition is not a novel theorem. Useful
new knowledge must come from identifying concrete migration obligations,
showing when they matter, and documenting when the suggested action is
unnecessary or fails. If the bounded validation adds only case-specific fixes,
retain the narrower empirical study and report those results honestly.

The six-benchmark audit remains an independent contribution to measurement
quality. Its 4,989 heterogeneous review units are not replications of these
principles and do not establish an authoritative blacklist. Pro is one concrete
external-measurement application of object/population reasoning, not a
substitute for validating the agent cases.

## Evidence and theoretical foundations

- [GP original diagnosis](../results_cache/gp_generated_effect_v1/DIAGNOSIS.md).
- [Feedback v2 pre-release semantic review and later outcomes](reviews/raw_issue_feedback_effect_v2_outcome_20260922.md).
- [Complete versioned case inventory](FSE_DEPENDENCY_CASES_20260928.md).
- [PQ selection and outcome report](../results_cache/search_replace_chooser_v1/REPORT.md).
- [Pinned Pro evaluator semantics](../analysis/benchmark_hard_audit_fse_v1/pro_evaluator_semantics_followup_2026-08-31.md).
- [Six-benchmark public delivery](../analysis/benchmark_hard_audit_fse_v1/decision_oriented_delivery_2026-08-31.md).
- [Architectural Mismatch](https://www.cs.cmu.edu/afs/cs/project/able/ftp/archmismatch-icse17/archmismatch-icse17.pdf): implicit environmental assumptions in component reuse.
- [Interface Automata](https://research-explorer.ista.ac.at/record/4622): compatibility of input assumptions and output guarantees, beyond signatures.
- [Qi et al., ISSTA 2015](https://people.csail.mit.edu/rinard/paper/issta15.pdf): passing tests, incorrect repairs and validation-infrastructure errors.
- [Building Theories in Software Engineering](https://plg.uwaterloo.ca/~migod/846/papers/theoriesInSE-chapter.pdf): explicit constructs, propositions, explanations and scope. Our proposed labels are working claim thresholds, not a universal taxonomy of theories.

Review participants: `/root/fse_novelty_assessment`,
`/root/fse_evidence_assessment`, `/root/fse_impact_assessment`.
The primary agent chose the main direction, narrowed the proposed execution
scope and retained the counterarguments. The review is not a conference
acceptance assessment or an experimental result.
