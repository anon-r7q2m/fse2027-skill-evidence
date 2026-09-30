# Corrected public contract for guard repair

# Full G conditional migration trial v1: public contract

Date: 2026-09-09. Interface: `agent2skill.json-effects.g.trial-v1`.
Scope: one human-specified target, two conditional implementation-migration
paths, A2S and Direct. This is an L2 diagnostic, not unseen-source discovery,
automatic obligation classification, a benchmark run, or proof of general
method superiority.

This is a **new** trial contract. It makes the public result projection and
decision precedence explicit. It does not edit, refreeze, or reinterpret the
old [G preparation contract](../g_package_preparation_v1/MIGRATION_CONTRACT.md),
the old L3 package, or any historical experiment. It implements the behavioral
scope of the [independent acceptance protocol](../g_package_preparation_v1/ACCEPTANCE_PROTOCOL.md).
Readiness, actual invocation budgets, and hidden acceptance results are recorded
separately; the existence of this document does not establish them.

## 1. Deliverable, visibility, and source boundary

Submit exactly three UTF-8 Python source files, `native_logs.py`,
`compatibility.py`, and `mechanism.py`. The entry point is
`mechanism.handle(event, state) -> {"state": ..., "effects": [...]}`.
All three files are replaceable package code. Helpers, algorithms, and private
state are implementation choices. The runtime must not import an existing G
implementation or supply parsed test states, inventory selection, obligation
judgments, or G feedback as a host capability.

The package owns raw-log parsing, actual base-PASSED inventory construction,
validation/freezing of supplied classifications, candidate interpretation,
trigger decisions, and substantive feedback. The host owns snapshot capture,
explicit projection, isolated command execution, resource enforcement, raw
receipts, and message transport. No live model call belongs inside the package.

Both methods receive the same exported public target, source, dependency
information, event/result specification, public examples, and public feedback.
They do not receive the old L3 package, its fixture module or internal state
traces, another method's submissions, hidden cases or answers, official repair
answers, or private annotations. Public expected behavior in this specification
and new public examples is intentionally visible. Neither generation context
may browse the surrounding repository to obtain excluded implementations.

The source is Agentless commit
`5ce5888b9f149beaace393957a55ea8ee46c9f71`: relevant inventory, selector,
regression execution and reranking code. Its requirements do not pin the
historical SWE-bench dependency. Revision
`726c5461e2ef52d83cf1ea2107870a8bb3328d57` is a named grading compatibility
example, not recovery of the exact original dependency stack.

Declared adaptations are complete inventory retention; externally supplied
evidence-linked three-state obligations; strict actual PASSED and execution
completeness; package-owned native parsers; original-test projection onto an
independent complete candidate copy; and feedback inside the repair loop in
place of offline ranking. The source/adaptation account is evaluated separately
from code execution. These adaptations are not called unchanged donor behavior.

## 2. JSON and runtime conventions

All input/output values are finite JSON. `object` means a JSON object with string
keys; `integer` excludes boolean; a nonempty string contains at least one
non-whitespace character. No NaN, infinity, duplicate JSON object keys, or
implicit coercion of string/integer/boolean types is allowed. Unordered ID
collections described as sets are encoded as unique string arrays; their order
is not scored. Paths and test IDs are exact case-sensitive strings.

The package receives the state returned by its previous successful invocation.
The first state is `{}`. Each invocation runs in a fresh process: no mutable
process globals, wall-clock time, filesystem persistence, randomness, or network
access is a source of mechanism state. Retain state in the returned JSON object.
Inputs must not be mutated in place as a substitute for returning state.

The runtime loads the three modules in the listed order using CPython. Pure
standard-library computation and imports between submitted modules are allowed
under the published execution policy. Source acquisition is not a runtime
dependency: do not import the whole donor, host implementation, control package,
or use external files as an undeclared mechanism binding. The exact CPython
version and admitted import/resource policy are part of the common prepared
runtime manifest and must be shown to both methods before generation.

Only JSON envelope output belongs on stdout. The common envelope has exactly
`state` (object) and `effects` (array of 0–2 effects). State must contain the
public projection in §5; all other state keys are private. Comments and free
text on stdout are an invalid envelope, not a successful result.

The common envelope is limited to 8 MiB input and 8 MiB stdout per invocation;
stderr has a separate 64 KiB diagnostic cap. The new runtime profile permits
3 CPU seconds per process, 384 MiB process address space, 512 MiB total container
memory, at most 32 PIDs, and a one-CPU quota. Its attached outer wall deadline is
8 seconds including container startup, with separate 15-second container-create
and 10-second cleanup deadlines. This is the new trial profile, not the old
trusted control's 5-second subprocess wrapper. Exact enforcement commands and
calibration records belong to the shared profile manifest. Limits alone are
not evidence of isolation: the new boundary must be qualified before running
generated code; `trusted_control=True` is not a bypass for admission.

## 3. Input schemas

In the following tables every listed field is **required**, except fields
explicitly marked optional. Event, DomainSpec, execution/projection/limit, and
assertion objects reject additional fields. Classification rows, evidence
objects, raw receipts, and actual projection receipts permit additional
diagnostic metadata; extra metadata cannot change the meaning of required
fields. State itself permits additional private fields. Examples and validators
must follow these same rules.

### 3.1 Domain and human classifications

| Object | Required fields and constraints |
|---|---|
| `DomainSpec` | `base_commit`: nonempty string; `base_snapshot_ref`: nonempty string; `parser`: `django_verbose` or `pytest_verbose`; `origin`: nonempty human-input provenance string; `execution_spec`; `projection_spec`; `limits` |
| `execution_spec` | `command`: nonempty string, at most 16,000 characters; `cwd`: exactly `/testbed` |
| `projection_spec` | `replace_from_base`: unique canonical workspace-relative path array; `expected_files`: map of relative file paths to exact file identities; `guards`: map of relative paths to exact file identity or null (must remain absent); SHA strings are invalid |
| file identity | `sha256`: 64 lowercase hexadecimal characters; `executable`: boolean |
| `limits` | `timeout_seconds`: integer 1–120; `output_bytes`: integer 1–2,097,152 |
| `classifications` | map of exact test ID to a classification row; keys must later equal the actual nonempty base-PASSED set |
| ordinary classification row | `disposition`: `PRESERVE`, `EXPECTED_CHANGE`, or `UNRESOLVED`; `reason`: nonempty string; `evidence_refs`: nonempty unique string array; `granularity`: nonempty string |
| additional `EXPECTED_CHANGE` fields | `granularity`: exactly `single_assertion_test`; `issue_requirement`: nonempty string; `assertion` as below |
| `assertion` | `file`: exact nonempty traceback filename; `line`: positive integer; `source`: nonempty source line; `exception`: exactly `AssertionError`; `message`: nonempty exact exception message |
| `public_evidence` | map from evidence ID to an object; each classification reference must name an existing evidence ID |

Paths admitted by projection are workspace-relative, without `..`, empty path,
or absolute path components. The generic host validates the exact projection
identities and guard structure; the package must pass the supplied projection
unchanged. It must not invent another command, projection, or execution budget.

These human inputs supply semantic classifications. Structural reference
validation does not prove that a natural-language issue entails a disposition.
For semantic acceptance cases the evaluator supplies independently adjudicated
valid classifications. Separate malformed cases check the specified structural
rules; this trial does not require an undeclared entailment classifier.

`PRESERVE` requires actual candidate PASSED. `EXPECTED_CHANGE` permits only
the specified old assertion failure, while still executing/reporting that test.
`UNRESOLVED` remains uncertain even if the test passes. A parent containing
mixed subtests cannot be waived by a `single_assertion_test` label.

### 3.2 Events

| `kind` | Required fields |
|---|---|
| `base_ready` | `snapshot_ref`: nonempty string equal to `domain.base_snapshot_ref`; `domain`: DomainSpec; `classifications`; `public_evidence` |
| `execution_completed` | `receipt`: raw receipt below |
| `workspace_changed` | `before_snapshot`, `after_snapshot`: nonempty strings; `tool`: nonempty string; `controller_status`: nonempty string; `remaining_responses`, `remaining_output_chars`: integers ≥0 |
| `feedback_delivered` | `message_id`: nonempty string; `request_id`: positive integer identifying the actual later completed solver request; `completed`: exactly true |

Only `controller_status == "RUNNING"` permits a new check. Other nonempty
statuses are non-running, not an invitation to infer more resources. A tool
named `task_complete` never triggers a check; the production loop ordinarily
handles completion without an action callback. Snapshot equality is exact.

### 3.3 Raw receipt

A receipt requires `request_id`, `snapshot_ref`, `execution_spec`,
`projection_spec`, and `limits`, exactly equal to the outstanding effect;
`stdout` and `stderr` as strings; `return_code` as integer or null;
`timed_out`, `cancelled`, `truncated`, `environment_deleted` as booleans;
`stage` as a nonempty string; and `projection` as an object.
The only completed stage is exactly `completed`; every other stage indicates
incomplete host execution. The raw projection requires `applied` (boolean)
and `guard_changed` (array of strings), and may contain generic proof metadata.
Session IDs, elapsed time, raw byte counts and cleanup diagnostics are optional
metadata in the package view and are retained by the host.

Missing required receipt fields or mismatched request/specification identity
are protocol rejection. A validly shaped receipt describing timeout,
truncation, failed projection, incomplete host stage, or null return code is an
**execution observation** to report, not malformed input to hide
by protocol rejection. Host-level cancellation may terminate dispatch after
preserving its receipt; if a valid receipt is supplied to `handle`, the package
must interpret it conservatively and emit bounded feedback.
`environment_deleted=false` remains a host cleanup failure in the execution
record. The host must not declare the run qualified while cleanup is unconfirmed;
it is not by itself a new G semantic test-failure category.

## 4. Effects and lifecycle

| Effect `kind` | Required fields; no additional fields |
|---|---|
| `run_isolated` | `request_id`, `snapshot_ref`, `execution_spec`, `projection_spec`, `limits` |
| `observation` | `message_id`, `content`, `evidence_refs` |

`request_id` and `message_id` are nonempty strings, unique within their
respective roles in a run. Their concrete names and hash algorithms are not
fixed across implementations. `content` is a nonempty string of at most
24,000 characters. `evidence_refs` is a unique nonempty string array containing
the corresponding execution request ID and the frozen obligation record ID.
It may include additional public evidence references.

1. From empty state, `base_ready` produces exactly one `run_isolated` for the
   declared base snapshot. The public inventory is empty, freeze is null, and
   decision is null while this request is outstanding. No repair action or
   automatic feedback is admitted before the base completes.
2. A complete successful base receipt establishes the actual unique PASSED
   inventory and exact classification coverage, and freezes the common inputs.
   It emits no observation. Reject a base that is incomplete, contradictory,
   has a nonzero/null return code or any FAILED/ERROR/XPASS state, lacks applied
   projection, or changes guards. Validate the whole receipt
   **before** selecting its PASSED subset. SKIPPED/XFAIL may occur in an
   otherwise successful base run but never enter the inventory. The inventory
   must remain nonempty.
3. While ready, a continuous `workspace_changed` advances the remembered
   snapshot. Request exactly one candidate execution only if before ≠ after,
   controller is RUNNING, both remaining budgets are positive, and the tool is
   not `task_complete`. No-op and terminal/budget cases return no effect. A
   mode-only change within the declared Git capture domain is a real change.
4. While a request is outstanding, another base or workspace event is invalid.
   A matching candidate receipt updates the public decision and emits exactly
   one observation, including on unknown/unsuccessful execution. Inventory and
   freeze remain unchanged. No auxiliary execution or model call is allowed
   from interpreting a receipt.
5. A `feedback_delivered` event must refer to a previously emitted, not-yet-
   acknowledged message and a completed request. It emits nothing and does
   not change the public inventory/freeze/decision. Repeated/unrelated delivery
   is rejected. The host independently checks actual request contents;
   a package acknowledgment alone is not evidence of delivery.

Uninitialized execution, repeated base, duplicate/unrelated receipt, lost
snapshot continuity, unknown kind and malformed required input are protocol
rejections. Frozen input snapshots and classification mappings cannot be
modified by later events or mutable object aliasing. Acceptance reaches these
conditions through public event sequences; it does not corrupt implementation-
private fields and expect a private checksum to match the old L3 algorithm.

The host processes at most four effects in a dispatch chain, charges actual
visible observations to the common output budget, and records execution cost.
The package does not block task submission. Large diagnostic tails may be
truncated explicitly; decisive unknown/failure status and its receipt reference
must survive. No truncation of prose can change the saved semantic decision.

Feedback must contain the exact public `decision.status` token. For a short
result it must also contain each inventory test ID whose disposition is not
PRESERVE or whose observation is not PASSED, together with that item's observed
status token. Other phrasing and formatting are free. When these per-item lines
cannot fit the 24,000-character envelope, retain the total status, an explicit
notice that the full decision is in the referenced receipt, and the execution
and freeze references; do not claim a partial inventory is the whole result.
Large native diagnostic text may be shortened before any decisive semantics.

The host captures the existing Git patch/tree domain: tracked plus admitted
untracked files, including additions, deletions, bytes and executable bits.
Git-ignored untracked files and files outside the workspace are not captured.
Validation applies only the declared original-file projection in an independent
copy; other captured candidate content remains identical. Restoring original
tests does not restore unrelated production code or weaken the candidate into
a different implementation. The solver workspace must remain unchanged by
validation.

## 5. Public semantic projection

Every successful return has `state.public` with **exactly** these three fields:

```json
{
  "inventory": [],
  "freeze": null,
  "decision": null
}
```

`inventory` is a unique string array representing the actual base-PASSED set.
It is empty only before base freeze, and invariant afterward. Order is not
part of acceptance. `freeze` is null before successful base freeze; afterward
it has exactly:

```text
{
  id: nonempty string,
  base_snapshot_ref: nonempty string,
  classifications: the exact supplied classification map over inventory
}
```

The freeze ID identifies this run's immutable domain, inventory,
classifications, and public evidence. A UUID, counter scoped to a run, or
content identity is acceptable if references are unambiguous and the record
never changes. No cross-implementation hash or sorting convention is required.
The host preserves the original supplied inputs alongside the freeze record;
it does not compute semantic correctness from the ID. `base_snapshot_ref` and
`classifications` must equal the inputs. This public projection is produced by
the package, not by host-side reinterpretation of its private state.

`decision` is null until a candidate receipt has been interpreted, and then
records the most recent decision. Beginning a later check, no-op events and
delivery acknowledgments preserve that record. Required decision fields are:

| Field | Type and meaning |
|---|---|
| `status` | one of the six statuses in §7 |
| `native_complete` | boolean: raw native log is structurally complete and internally consistent, independently of receipt flags and inventory coverage |
| `execution_complete` | boolean: all observed-command/projection/completeness requirements in §6 hold |
| `return_code` | exact integer/null from the receipt |
| `execution_issues` | unique nonempty diagnostic strings; empty iff execution is complete; standardized categories below must be present when applicable |
| `preserve_status` | `EMPTY`, `REGRESSION_DETECTED`, `UNOBSERVED`, or `PRESERVED` as in §7 |
| `overall_preservation_confirmed` | boolean; true iff `status == "BASE_PASSES_PRESERVED"` |
| `issue_fixed` | always null |
| `observations` | exact map over all inventory IDs to observation objects |
| `unresolved` | exact set of inventory IDs classified UNRESOLVED |
| `unmatched_expected_failures` | exact set of EXPECTED_CHANGE IDs observed FAILED without a precise assertion match |
| `noninventory_failures` | exact set of observed FAILED/ERROR/XPASS IDs outside inventory |

Decision objects may contain additional diagnostics, but these cannot contradict
the required fields and are not a source of unstated acceptance requirements.
Observation objects require `disposition` equal to the frozen classification,
`observed` in `PASSED`, `FAILED`, `ERROR`, `SKIPPED`, `XFAIL`, `XPASS`, `MISSING`,
and `matches_expected_assertion` as a boolean. Additional reasons and references
are allowed. Set the match boolean true only for an EXPECTED_CHANGE observation
of FAILED satisfying the exact ownership rule. In all other cases it is false.

Conflicting statuses for the same test make native parsing incomplete. The
observation may retain an actually seen status while the conflict is explicit
in diagnostics; it cannot silently count that test as an unqualified success.
Evaluation of malformed/conflicting logs requires preserved evidence and
uncertainty, not a particular arbitrary winner among conflicting lines.

## 6. Native parsing and execution completeness

Supported forms are completed verbose pytest status lines with native summary,
and verbose unittest/Django parent results with native summary, wrapped
descriptions and failing subtest detail. Public cases supply concrete raw
syntax. Do not infer success solely from the words PASSED or OK.

Test identity preserves the native displayed identifier. For unittest/Django,
`test_keep (sample.ContractTests) ... ok` identifies exactly
`test_keep (sample.ContractTests)`, including the method, space and parenthesized
class. Do not convert it to `sample.ContractTests.test_keep`. Wrapped descriptions
and failed subtests retain the displayed parent identity. For pytest, retain the
complete node ID before the status token, including path, class and parameter
suffixes. Supplied classification keys and observation keys use those exact IDs.

The native log must have one completed summary and consistent test/status
counts. Missing/duplicate/conflicting IDs, unfinished parents, incomplete
collection, missing/duplicate terminal and contradictory counts are incomplete.
`FAILED (failures=0)` with only passing tests is not a valid success. Failed
subtest lines belong to their original parent; their absence is not proof of a
complete successful-subtest roster. Native parser diagnostic names are free;
the public category `NATIVE_INCOMPLETE` must also appear when native_complete
is false.

For EXPECTED_CHANGE, only a single unambiguous failure detail for the declared
single-assertion unittest/Django test can match. In one terminal traceback
frame the exact filename, line number, immediately following source (after
trimming surrounding indentation/whitespace), and final `AssertionError:`
message must match. Optional native caret markers do not change the source.
Cross-frame evidence, later helper frames, chained exceptions, multiple details,
mixed subtests, unrelated exceptions and ambiguous paths do not match. Pytest
status-only output cannot establish exact assertion ownership. A failing old
assertion establishes neither the requested new behavior nor issue repair.

The package evaluates stdout/stderr without inventing absent lines or mixing
two different executions. For public cases, the completed native sequence is
present in one stream or in their specified deterministic concatenation; a
new stream-order ambiguity is incomplete. It cannot be repaired by guessing
from prior candidate state.

An execution is complete exactly when there are no applicable issues below.
The listed category is mandatory; additional specific diagnostic strings are
allowed and their literal wording is not compared.

| Condition | Required `execution_issues` category |
|---|---|
| timed_out or cancelled | `EXECUTION_TIMEOUT_OR_CANCELLED` |
| truncated or stage other than completed | `EXECUTION_NOT_FULLY_OBSERVED` |
| nonempty projection.guard_changed | `CONFIGURATION_CHANGED` |
| projection.applied is false | `PROJECTION_NOT_ESTABLISHED` |
| native log incomplete/contradictory | `NATIVE_INCOMPLETE` |
| any inventory ID is MISSING, SKIPPED, XFAIL, XPASS or ERROR | `MISSING_OR_NONPASS_INVENTORY` |
| return_code not 0/1; or code 0 with observed FAILED/ERROR/XPASS; or code 1 without any such observed failure | `UNEXPLAINED_EXIT_STATUS` |

An ordinary assertion FAILED can be an observed complete execution, including
exit 1. ERROR/XPASS of an inventory item does not satisfy this diagnostic's
complete-obligation requirement, even when the native runner terminated
normally. Thus `native_complete=true` and `execution_complete=false` can
coexist. Receipt uncertainty and known per-test failures are reported together;
one does not erase the other.

SKIPPED/XFAIL of an extra noninventory test alone does not create a preservation
failure; inventory coverage and the native summary must still be complete.
Extra FAILED/ERROR/XPASS appears in `noninventory_failures` and prevents whole
preservation confirmation, even when it does not make the raw execution itself
incomplete. Always report both the raw execution and the obligation outcome.

## 7. Decision precedence and truth table

Let `P` be the frozen PRESERVE set, `E` the EXPECTED_CHANGE set, `U` the
UNRESOLVED set, `R` the IDs in P observed FAILED or ERROR, `M` unmatched expected
FAILED IDs, and `X` noninventory failures. Determine `preserve_status` in this
order:

1. `P` empty → `EMPTY`.
2. `R` nonempty → `REGRESSION_DETECTED`, even if execution is also incomplete.
3. execution_complete false → `UNOBSERVED`.
4. Otherwise → `PRESERVED` (every P actually passed).

Choose overall `status` using the first matching row below. This priority
controls only the summary label; all concurrent issues and observations remain.

| Priority | Condition | `status` |
|---|---|---|
| 1 | execution_complete false | `EXECUTION_UNRESOLVED` |
| 2 | R nonempty | `REGRESSION_DETECTED` |
| 3 | U, M, or X nonempty | `OBLIGATION_UNRESOLVED` |
| 4 | P empty | `NO_PRESERVE_OBLIGATIONS` |
| 5 | E nonempty | `PRESERVE_SUBSET_PASSED_WITH_EXPECTED_CHANGE` |
| 6 | otherwise | `BASE_PASSES_PRESERVED` |

All inventory IDs remain visible regardless of disposition. Expected-change
items may PASS or have the exact expected FAILED; the summary does not assert
that an old test failed merely because E is nonempty. `issue_fixed=null` in
every row. A nonempty inventory with no unknown/expected items and all tests
actually PASSED is required for the only overall true result.

| Example observation | Native / execution complete | Preserve status | Overall status / green |
|---|---|---|---|
| nonempty P only; every test PASSED; successful receipt | true / true | PRESERVED | BASE_PASSES_PRESERVED / true |
| P contains an ordinary FAILED; native failures explain exit 1 | true / true | REGRESSION_DETECTED | REGRESSION_DETECTED / false |
| P passed; E has the exact expected FAILED; exit 1 explained | true / true | PRESERVED | PRESERVE_SUBSET_PASSED_WITH_EXPECTED_CHANGE / false |
| P passed; E also PASSED | true / true | PRESERVED | PRESERVE_SUBSET_PASSED_WITH_EXPECTED_CHANGE / false |
| every old test passed but U nonempty | true / true | PRESERVED if P nonempty, else EMPTY | OBLIGATION_UNRESOLVED / false |
| P passed; E exact FAILED; U nonempty | true / true | PRESERVED | OBLIGATION_UNRESOLVED / false |
| P empty; E exact FAILED or PASSED; U empty | true / true | EMPTY | NO_PRESERVE_OBLIGATIONS / false |
| P passed; E FAILED at another frame/assertion | true / true | PRESERVED | OBLIGATION_UNRESOLVED / false |
| one old ID absent from an otherwise completed native run | true / false | UNOBSERVED unless P empty or known regression | EXECUTION_UNRESOLVED / false |
| an old ID is SKIPPED/XFAIL/XPASS/ERROR | true if native consistent / false | follow P/R precedence above | EXECUTION_UNRESOLVED / false |
| known PRESERVE FAILED plus timeout or missing other result | variable / false | REGRESSION_DETECTED | EXECUTION_UNRESOLVED / false; retain known regression |
| expected old failure plus unrelated noninventory failure | true / true if exit/status agree | PRESERVED if P passed | OBLIGATION_UNRESOLVED / false |
| all status lines pass but FAILED terminal or code contradicts them | false if native contradiction / false | UNOBSERVED | EXECUTION_UNRESOLVED / false |

An implementation returning unknown for every input fails the positive cases.
An implementation dropping unknown obligations or reporting only its successful
subset fails the coverage cases. Passing the old suite or matching one old
assertion never changes `issue_fixed` from null.

## 8. Rejection, acceptance, and observations

For a specified protocol violation, raise
`ValueError("PROTOCOL_REJECTED: <diagnostic>")` without producing effects.
The new worker catches only this explicit ValueError prefix and returns:

```json
{"_worker_error":{"kind":"protocol_rejected","message":"..."}}
```

The host records `PackageError(category=PROTOCOL_REJECTED)`. Other exceptions
are `package_exception` / `PACKAGE_EXCEPTION`; timeout, resource denial and
invalid envelope have their own categories. None counts as successful protocol
rejection. Exact diagnostic prose is not graded. The worker error envelope is
separate from successful `{state,effects}` output and is not persisted as state.

A base receipt that fails the explicit preconditions for establishing an
inventory uses the same declared rejection channel and is reported as unusable
base setup. This does not license rejecting validly shaped **candidate** failure
receipts: those must produce the decision and observation specified above.

Because submitted code can itself emit JSON, a reported protocol error is a
**candidate claim**, not a trusted proof of compliance. Positive and negative
behavior tests determine whether rejection was appropriate. Forged errors or
always-reject implementations do not receive behavioral credit.

The evaluator compares the public projection, required effects and actual host
observations, not L3 private keys, helper names, request ID spelling, hash
algorithm, sorting, or feedback prose. Same-package deterministic replay can
use byte equality. Between methods, matching the public obligations is the
criterion; normalization cannot erase a failure, missing test or changed
classification.

The independent evaluator seals cases and expected semantic outcomes before
receiving either candidate. The known human control and relevant mutants must
calibrate the measurement layer. Exposed examples are public development data,
not hidden tests. Both methods fix final candidates before hidden evaluation;
hidden results and the other arm's artifacts never guide generation/repair.
Real-entry acceptance uses an independent synthetic workspace and the same
qualified host, including actual feedback in a later completed scripted request.
It does not run benchmark scoring or establish gain.

## 9. New run and submission rules

This derivative retains sections 1–8's G behavior and source obligations.
For this single-package interface repair, all method/budget/submission rules
are specified by DEVELOPMENT.md. Guards and path rules are additionally
specified by the supplied guard-interface CONTRACT.md and JSON Schema.
They override the earlier underspecified guard row. No old comparison or
failed experiment is reopened.
