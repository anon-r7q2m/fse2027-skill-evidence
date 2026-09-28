# checking_context_hook_v1 public host contract

Status: implemented and publicly calibrated; not a discovered mechanism.
This is the declared successor to `checking_hook_v1`. The complete eight-arm
experiment and its checking-only packages remain unchanged.

## Package and execution boundary

The package contains `package.json` and one to eight flat Python modules. The
manifest has exactly `schema_version: 1`, `profile: "checking_context_hook_v1"`,
`entrypoint: "module:function"`, `modules: ["module.py", ...]`, and
`capabilities`, a unique subset of the five effects below. Module basenames
cannot shadow standard-library modules. Each module is at most 1 MiB; all
modules together are at most 4 MiB. Extra files and implicit donor installations
are not accepted. The entrypoint is `handle(event, state)` and returns exactly
`{"state": <JSON object>, "effects": [<effect>, ...]}` with at most two effects.

Each callback starts a fresh isolated Python worker; JSON state is the only
mechanism state passed between callbacks. Workers have no network, no writable
workspace, a read-only package, and bounded CPU/memory/input/output. Declared
pure Python dependencies may be packaged as modules, and Python standard-library
computation is available. Environment effects must be requested through the host.
The actual validators are distributed with migration materials; no relaxed
surrogate schema is used by the public evaluator.

## Lifecycle and receipts

- `prepare`: `kind`, public task `issue`, `base_snapshot`, public `domain`,
  `remaining_responses`, `remaining_output_chars`.
- `workspace_changed`: `kind`, `tool`, `action` with `tool`, `return_code`,
  `observation`; `before_snapshot`, `after_snapshot`, `remaining_responses`,
  `remaining_output_chars`. This follows an actual ordinary tool action and
  snapshot capture. Equal before/after snapshots are legal.
- `source_read_completed`, `execution_completed`, `model_request_completed`:
  `kind` and the actual `receipt` linked to the requesting `request_id`. The
  completion names are exact. No callback is fabricated for unknown acceptance.
- `feedback_delivered`: `kind`, `message_id`, `request_id` (solver query string),
  `completed: true`. It follows inclusion of the exact original feedback in a
  completed solver request. ACK callbacks must return no effects.
- `before_solver_request`: the additional boundary below. It occurs after all
  ordinary/checking actions and before the next solver reservation.
- `projection_completed`: `kind`, application `receipt`; it is not a delivery
  acknowledgement.
- `projection_delivered`: `kind`, `derived_id`, `occurrence_id`, `request_id`
  (solver query string), `completed: true`. It acknowledges the derived text
  actually included in a completed solver request. Return no effects.

The `domain` gives immutable base/snapshot identity and the capabilities
available to this particular public workspace: `execution_spec`,
`projection_spec`, `execution_limits`, and `model_limits` when those effects
are available. Packages must reproduce these capability objects exactly in
effects; they cannot invent a new command or increase limits. Snapshot guards
are file-identity objects or null as defined by the distributed projector,
not SHA strings. There is no human-authored G/R operation card or prewritten
donor mechanism in this host.

## Effects

`source_read` has exactly `kind`, `request_id`, `base_commit`, `queries`.
Each of one to four queries has `operation: "read"|"search"`, public relative
`path`, `text`, `start`, `end` with `1 <= start <= end` and fewer than 250 lines
between them. Search text is nonempty; plain reads may use `text: ""`.
This reads the **task workspace's fixed base source**, not the extraction donor.
The receipt carries raw stdout/stderr, return status, and parsed `result`.

`run_isolated` has `kind`, `request_id`, `snapshot_ref`, `execution_spec`,
`projection_spec`, `limits`, `input_files`. The snapshot must exist. Its command
runs only in an independently materialized copy with the declared projection.
`input_files` is empty or at most eight `.py`/`.json` basenames, each at most
1 MiB and together at most 2 MiB. They appear at `/tmp/a2s-check-input/`; names
`operations.py`, `bootstrap.py`, `host_request.json` and dot names are forbidden.
The receipt includes `stage`, `stdout`, `stderr`, `return_code`, `timed_out`,
`truncated`, input hashes, projection result and `environment_deleted`. Actual
runtime failures are not converted to successful test results.

`model_request` has `kind`, `request_id`, `items`, `instructions`, `tools`,
`limits`. It uses the same model, controller and deadline as solving. Its
completion receipt contains `request_id`, `query_id`, `status`, `response`,
`usage`, and the authoritative `ledger`. Task-time requests count against
the common budget. A context-boundary request has purpose `context_summary`.

`observation` has exactly `kind`, a unique `message_id`, `content`, and a
nonempty `evidence_refs` list. It appends visible feedback; producing it does
not establish delivery. Content length is charged to the common output pool.

`project_observations` has exactly `kind`, a unique `request_id`,
`view_revision`, and one to 64 `replacements`. Each replacement has exactly:

```json
{
  "occurrence_id": "input:4",
  "original_wire_sha256": "<64 hex characters from the event>",
  "current_wire_sha256": "<64 hex characters from the event>",
  "content": "replacement text selected by the package",
  "lossy": true,
  "source_refs": [{"occurrence_id": "input:4", "original_wire_sha256": "<same original digest>"}]
}
```

`content` is at most 24,000 characters; there are one to 16 source references.
Each reference identifies an observation in this event, and the target's own
original reference is required. `lossy: false` is accepted only for text exactly
equal to the original content. The flag is a provenance declaration, not proof
that a summary preserves meaning. All replacements are validated and charged
atomically before application; stale, duplicate, or protected targets fail.

## Context-boundary event and restrictions

The event contains `view_revision`, monotonic `boundary_id`, `observations`,
`protected_items`, current `admission`, `limits`, `remaining_responses`,
`remaining_output_chars`, and `remaining_seconds`.
Each observation contains `occurrence_id`, `input_index`, `owner`, `call_id`,
`message_id`, `origin_query`, `snapshot_ref`, `return_code`,
`original_wire_sha256`, `current_wire_sha256`, `original_content`, `content`,
`visible_utf8_bytes`, `current_derived_id`, `verbatim_request`, `acknowledged`,
`eligible`, and `protected_reason`. Nullable fields remain null when absent.

Only one designated package can own projection. In each boundary it may make
at most one summary call followed by at most one projection transaction.
Summary input items are exclusively `{"role":"user"|"assistant","content":str}`;
summary `tools` must be empty. The callback receives only visible text and public
metadata projected from the response, with `response_projection` binding the
original raw-response SHA and recording omitted output types. Encrypted
reasoning is never supplied to the package/summarizer. Original raw responses
and their usage remain in the host ledger.

The boundary permits only model summary, observation, and projection effects;
it cannot run tools, recurse, resume a terminal controller, or use an unresolved
request. Thresholds, retention choices, summary prompts and checking policy
belong to the package. No compression policy is installed by this contract.

System/task content, function calls, parser obligations and opaque reasoning
are immutable. Unacknowledged feedback from another package is also protected.
Only observation content changes, preserving order and call/result pairing.
The host adds a `DERIVED_OBSERVATION` prefix containing provenance and return
code. The **entire derived wire content, including this prefix**, is charged
to the common output-character pool; previous costs are never refunded.

The native serializer recomputes admission for the actual rendered request;
preview does not reserve, send, or clear a stop. `VERBATIM`, `DERIVED`, and
`NOT_SENT` are different states. A known incomplete COMMIT records inclusion
without successful ACK. Unknown acceptance binds the actual request's purpose,
query and body; an unreserved solver view blocked by an unknown summary remains
`NOT_SENT`. Derived inclusion never acknowledges an unsent original.

This profile cannot remove whole turns, replace the task, modify reasoning,
write the main workspace, veto submission, or control another package. A donor
needing those capabilities must report a concrete gap rather than relabel a
weaker observation as faithful transfer.

## Evidence and scope

The [implementation review](../../docs/reviews/observation_context_v1_implementation_review.md)
accepts this bounded host. The [public entry terminal](../../results_cache/observation_context_v1/public_entry/attempt_01/terminal.json)
and [calibration report](../../results_cache/observation_context_v1/REPORT.md)
separate real workspace execution from scripted model transport. No donor
fidelity, generated mechanism, benchmark improvement or combination advantage
is established by these infrastructure controls.
