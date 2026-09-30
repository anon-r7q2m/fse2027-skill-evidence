# Complete-script behavior R public contract

Submit four modules: `source_rules.py`, `reproduction.py`, `case_runner.py`,
`mechanism.py`. Helpers may be shared across them; only
`mechanism.handle(event, state)` is an external entrypoint. Suggested ownership:
source prompt/rules; first-fence and receipt interpretation; literal obligation
mapping/input construction; event lifecycle. Use standard library and these four
modules only. The package runs in CPython 3.13 in the existing isolated worker.
Emitted task scripts must support the task's Python 3.6+ interpreter.

Return exactly `{"state": {...}, "effects": [...]}`, at most two effects.
State is deterministic bounded JSON; initialize from `{}`. Effects use the
unchanged public `r_full_package_v1/contracts.py` grammar. No donor runtime,
host imports, filesystem/network capability or target implementation is installed
in the package worker. The four modules are implementation code, not wrappers
around an existing semantic R implementation.

## Public task and events

The initial `prepare` event has exactly `kind`, `issue`, `base_snapshot`, `card`,
`domain`, `remaining_responses`, `remaining_output_chars`.

`card` has `obligations` (2..40 rows, each exactly nonempty string `id`, `role`,
`basis`) and `source_queries` (1..4 fixed `read` queries under the public query
grammar). IDs are unique; roles are `issue`/`control`, with at least one of each.
The bases state expected public behavior, not expected case outcomes or fixes.
Public source queries are already fixed by the caller: preserve them exactly,
read at most 250 lines each, total delivered text at most 24,000 characters.

`domain` contains `base_commit`, `model_limits`, `execution_spec`,
`projection_spec`, `execution_limits`. Copy those supplied capability objects
exactly into effects. The host fixes the complete-script execution command and
limits. Do not derive a shell command or import an observer.

Other events retain the old Session vocabulary:

- `source_read_completed`: `kind`, `receipt` with request_id, base_commit,
  result. The result is `source_reader.read`'s JSON object, containing the same
  base_commit, ordered rows, output_limit and delivered_characters. Each read
  row has path/start/end, status, text, truncated and source/delivered hashes.
- `model_request_completed`: `kind`, `receipt` with request_id, status and
  response when completed. Response is Responses API JSON; concatenate message
  output_text parts in order. Do not execute incomplete responses or tools.
- `execution_completed`: `kind`, `receipt`, described below.
- `workspace_changed`: kind, snapshot_ref, changed (bool), tool,
  remaining_responses, remaining_output_chars.
- `feedback_delivered`: kind, message_id, request_id (actual model request
  string), completed=true. Acknowledge once with no effects.
- `task_end`: kind and optionally reason. End only when no effect is pending.
  This is supported for callers that supply it; the current ordinary loop does
  not promise to dispatch it automatically.

Completion events have kind/receipt, but receipt objects permit additional
transport metadata (query_id, usage, ledger, return_code, stdout/stderr, etc.).

Completions match the one pending kind/request and expected snapshot/base.
Reject unknown event kinds and workspace changes while an effect is pending.
Reject malformed, stale or duplicate lifecycle events with
`ValueError("PROTOCOL_REJECTED: reason")`. Rejection does not commit state.
Unknown/repeated feedback acknowledgements are rejected. An outer execution
request_id/snapshot_ref that differs from the pending request is a stale
completion and is rejected. For a correctly addressed outer receipt, unusable
execution content or nested identities produce UNKNOWN, not protocol rejection.

## Source-first bounded preparation

With <3 remaining responses, emit one `INSUFFICIENT_PREPARATION_BUDGET`
observation if its complete JSON fits the remaining output allowance, then remain
inactive. With zero output allowance, or too little to encode that observation,
return effects=[] and remain inactive. No output debt or extra allowance.
Otherwise emit
one source_read effect for the card's exact queries and fixed base. No model
request occurs before source completes. Require every read row to match its
query with status READ, nonempty text, truncated=false and matching delivered
SHA256. Missing/error/empty/truncated source, a mismatched delivered hash or
more than 24,000 actual delivered characters becomes `SOURCE_NOT_READY`, with an
observation and no generation request. Do not retry source or invent text.

Use the donor's complete-test prompt as the source basis, replacing its marker
output instructions explicitly with the unittest/obligation adaptation. Include
the full issue, complete public card and actual source text in the first model
request. Explain actual repository calls, every declared obligation, unaffected
controls, state isolation/downstream effects when required by the card, and
that assertions must consume actual behavior. Do not imply a complete proof.
Ordinary missing public dependencies are execution errors; a missing required
new API may be asserted inside a test after a real existing repository call.
Never swallow unexpected exceptions into False or synthesize repository output.

All model requests have tools=[], limits=domain.model_limits, <=64 input items
and <=24,000 instruction characters. At most two task-time model responses
and two script submissions total. First completed response supplies code;
on the first syntax/declaration/base failure emit exactly one repair
model_request and no solver observation, if the shared budget remains available.
The second failure terminates without another request. Preserve the
previous output and actual bounded feedback in that repair context. Both requests
count against the solver's shared budget. If delivered to the package, a
noncompleted response ends preparation with `MODEL_RESPONSE_NOT_COMPLETED`.
The actual client may instead charge a committed incomplete response and raise
an outer provider/resource stop without delivering an event; retain that stop
and usage, never synthesize a completion or promise ordinary continuation.
After the second failure emit `NOT_ADMITTED`;
ordinary solving remains available. There is no third preparation request.

## Script and immutable card

Extract the first donor `re.compile(r"```python(.*?)```", re.DOTALL)` match and
strip outer whitespace exactly as donor does. Never use a later fence when the
first is invalid. Maximum extracted UTF-8 code size is 32,768 bytes. Parse before
execution, without importing the module in the package worker.

The script is a normal unittest module, with one top-level literal assignment:

```python
OBLIGATIONS = {"declared-id": "Behavior.test_method", "another-id": "Behavior.test_control"}
```

Its keys exactly equal the public card IDs; values are unique Class.test_method
names, valid identifiers, method starts with `test`. No extra/reassigned mapping.
The runner later requires the loaded unittest roster to equal this mapping.
The package constructs `card.json` itself as `{"obligations": [...]}`, preserving
the public row order and id/role/basis verbatim and adding only `test` from the
literal map. Scripts cannot change the public obligation text or roles.

The only run_isolated input_files are `script.py` (extracted original bytes) and
`card.json` (the constructed JSON text). The common production runner loads the
unittest script. Do not upload case_runner.py or supply a custom runner. First
base admission freezes both exact input strings and their SHA256 values. No
candidate can modify them or trigger new script generation.

## Complete execution receipt

The outer Executor receipt has request_id, snapshot_ref, stage, return_code,
timed_out, truncated, cancelled, environment_deleted, input_hashes, projection,
stdout/stderr, plus `behavior_execution`. Accept it for interpretation only if
stage=completed, return_code=0, flags false, environment_deleted=true and both
input hashes match the outstanding request. Additional transport fields may exist.

`behavior_execution` has matching request_id/snapshot_ref/input_hashes,
host_status=COMPLETED, before_tree/after_tree both equal
outer.projection.projected_tree, repository_unchanged=true, child, observation.
The child must exit 0 without timeout/truncation. The observation is the common
runner's object with schema `agent2skill.behavior-observations/1`, matching
script_sha256, host_status=COMPLETED, cases, repository_imports and child_identity.
Require child uid=gid=65534, groups=[], no_new_privileges=1. Do not reparse
stdout markers to override the structured result.

Each case preserves exactly one public id/role/basis and mapped test method;
order need not match card order because unittest may sort methods. Require the
exact unique roster, status in PASS/FAIL/UNKNOWN, reason string and nonempty
executed_source for every PASS or FAIL. An executed location has relative path
and positive line number. Missing/corrupt/extra case or identity/integrity error
yields UNKNOWN. So does any case UNKNOWN, before considering any FAIL.
The runner supplies reasons and exception traces; preserve bounded diagnostics,
not a fabricated case result. Trace sites establish execution, not full coverage.

Base: all controls PASS and at least one issue FAIL gives `BASE_ADMITTED`.
All cases PASS, any control FAIL, or no reproduced issue gives
`BASE_NOT_REPRODUCED`; any unknown/incomplete evidence gives UNKNOWN. On the
first submission either result requests the one repair as above; on the second
it ends NOT_ADMITTED. They never activate candidate checks.
Candidate: every case PASS gives `COVERED_PASS`; otherwise a valid assertion
FAIL gives `COVERED_FAIL`; UNKNOWN overrides either result. Control FAIL on a
candidate is a real failed check, not environment success or base admission.

After admission, execute unchanged inputs on each previously unseen changed
snapshot only with positive response/output allowance. Mark a snapshot checked
even for UNKNOWN and never rerun an unchanged/previously checked snapshot.
On workspace_changed while inactive/ended, for changed=false or a previously
checked snapshot, or without positive response/output allowance, return
effects=[] silently. Pending-effect conflicts remain protocol rejections.
Candidate results emit observations only. No candidate-time model request,
checker rewrite, workspace mutation or force-complete effect is permitted.

Observations use kind, unique message_id, content<=24,000 characters and 1..16
evidence_refs. Content is one JSON object with nonempty string `status` and
`reason`, `cases` (a list of rows with string id/role/test/status/reason, or [] when
unavailable), and optional string `script` (omit when unavailable/too large). It explicitly calls
these bounded checks rather than official scores. This stable public output is
consumed by later composition; private state field names are not an ABI.
Each observation references actual effects, or `prepare` for the initial resource
refusal. Record feedback delivery once and never emit effects in an ACK.

## Migration submission

Return exactly four FOUR-backtick blocks headed `python source_rules.py`,
`python reproduction.py`, `python case_runner.py`, `python mechanism.py`, with
complete original modules. No old package imports, placeholders or manual edits.
Public acceptance checks concrete synthetic event/receipt sequences in isolated
workers. Hidden acceptance and actual same-package entry are separate. Neither
frozen IDs nor all-green cases alone establish behavior coverage or gain.
