# checking_history_hook_v1: public implementation contract

Status: implementation contract for zero-generation calibration, 2026-09-11.
Candidate allocation and freeze follow independent acceptance. This profile
uses `analysis/history_context_v1/{broker,session,delivery,view,isolation}.py`
and the unchanged `analysis/observation_context_v1/{native,loop}.py`.
The latter is the actual solver loop; a new loop or second model ledger is not
introduced. The old checking/observation profiles remain unchanged.

## Package and lifetime

The existing neutral isolated worker loads `package.json` plus one to eight
declared Python modules, with entrypoint `module:function`. Its function is
`handle(event, state) -> {"state": object, "effects": list}`. State persists only
through the returned JSON object. The grammar permits the four existing checking
effects plus `project_history`; this S installation declares exactly
`["model_request", "project_history"]`. G retains its original separate session,
execution effects, and integer solver request IDs.

S receives `prepare` with issue, actual base snapshot, domain and live remaining
resources; `workspace_changed` after ordinary action/G dispatch; and
`before_solver_request` before the next native request is reserved. It must
ignore lifecycle and delivery events when no action is needed. Model requests
are permitted only at the latter boundary, once, with at least two shared calls
remaining. At most one `project_history` follows the completed summary.
No model request, projection or other effect may arise from a delivery ACK.

The domain provides `base_commit`, `base_snapshot_ref`, and `model_limits` with
the actual positive `input_token_limit` and `output_token_limit`. Configuration
16/1/10000 and all OpenHands choices belong to the package. The host contains
no trigger, event selector, summary prompt, truncation function or fallback.
The isolated package environment includes Python's standard library plus its
declared modules; donor and Agent2Skill host libraries are not installed as
package dependencies. Stdlib modules such as `json` and `hashlib` may be used
for pure computation. The existing worker has 3 CPU seconds, 8 seconds wall
time, 384 MiB process address space and an 8 MiB stdout cap per callback.
It is read-only, network-free, unprivileged and fresh for every invocation.
State therefore belongs in the explicit returned JSON, not module globals.

## Complete history representation

The authoritative solver list stays append-only. The ordinary loop legally
appends accepted responses, matching function results, controller messages and
package feedback. Invalid parser responses remain only in the raw request
ledger; only the original parser recovery messages enter the solver list.

The view synchronizes at resolved boundaries. The first user item is its own
immutable `task:0` unit. Every subsequent newly appended suffix is one native
interaction group if it contains a function call, otherwise one control group;
its stable ID is `group:input:<original_start_index>`. This groups each accepted
response with all its results and immediately associated G/controller feedback.
Unmatched, repeated or out-of-order call/result IDs make a group ineligible.
The current loop accepts one action per response; it is not expanded here.

Task, current derived summary and every native/control group each count as one
unit. System instructions, tool declarations and summary calls are not units.
The view revision binds an ordered list of unit IDs and canonical wire digests.
Wire bytes use UTF-8 canonical JSON (`sort_keys=True`, `ensure_ascii=True`,
`allow_nan=False`, `separators=(",", ":")`). Retained unit items, including opaque reasoning, are
copied unchanged to the actual solver body; archived units remain in the source
record and keep their historical charges.

`before_solver_request` contains exactly `kind`, `view_revision`, `boundary_id`,
`history`, `admission`, `limits`, `remaining_responses`, `remaining_output_chars`,
and `remaining_seconds`. Each history row contains:

```
unit_id, kind, wire_sha256, source_refs, visible_items, visible_text,
summary, complete, delivered_request, consumed_request, eligible, protected_reasons
```

`source_refs` is the ordered original-unit lineage, each reference exactly
`{"unit_id": string, "wire_sha256": sha256}`. `visible_items` preserves order and
has exactly these fields on every item (absent values are explicit null):

```
input_index, type, role, content, name, call_id, arguments,
return_code, owner, message_id
```

`content` is a full string or the original ordered text/refusal content parts,
limited to `{"type":"input_text"|"output_text","text":string}` and
`{"type":"refusal","refusal":string}`. A function output uses its full `output`
string as `content`. Tool name, call identity and the complete original argument
string are exposed. Return code/owner/message identity come from real host or
package delivery records; absence is null. Reasoning items, including their
summary and encrypted content, are excluded from this serializer. Unknown visible
item/content formats fail explicitly instead of silently losing information.

`visible_text` is canonical JSON of that complete visible list. A summary row
instead has empty `visible_items`, and `summary`/`visible_text` equal its actual
summary string. Ordinary rows have `summary=null`. The package truncates each
target unit once with the donor algorithm. The host does not pre-truncate.
The unchanged donor prompt's `<EVENT id=n>` tag uses the selected target unit's
stable `unit_id` in place of integer `n`. Its body is the unit's full `visible_text`
passed through the original per-event truncation. Prior summary text appears only
in `<PREVIOUS SUMMARY>`, never again as an EVENT. With no prior summary the
original source's literal `No events summarized` is preserved. This ID mapping
is explicit: donor calibration executes integer event IDs first and maps only
their tags to target unit IDs; it does not recompute expected summary behavior.
Event plus returned-state input is limited by the existing 8 MiB worker carrier;
a carrier failure does not authorize hidden truncation or an uncharged retry.
When S is absent, no visible serialization is needed and N renders its unchanged
original input.

The task, incomplete groups, units not yet included in a completed solver
COMMIT, pending package feedback, and an unacknowledged derived summary are
protected. Their protection does not change view size/order. The package first
selects its donor span; if any selected unit is protected it skips before a
summary call, without selecting a different span.

## Summary request and exact projection

`model_request` retains the existing fields: `kind`, a fresh `request_id`,
`items`, `instructions`, `tools`, and the exact domain `limits`. Items must be
plain `{"role":"user"|"assistant","content":string}`; tools must be empty.
The native purpose becomes `context_summary`. Its usage is charged through the
same controller before any completion callback. No new model/output/deadline
budget exists. A native exception/incomplete/UNKNOWN follows the original stop
path, preserves the request record and cannot fabricate a projection or ACK.

`model_request_completed` returns `receipt` with `request_id`, `query_id`,
`status`, visible `response`, `usage`, `ledger`, and `response_projection`.
The full raw native response remains in capture. Only message text/refusal and
public response metadata are returned to the package, with the ledger's original
`response_sha256` binding them. A completed summary must contain at least one
`output_text` part; the exact accepted summary string joins every such part in
native order without trimming, separators, defaulting or prefixing. Empty text
is allowed. Refusal-only or nontext completion supplies no summary. The host
registers this receipt only from its real metered `_model` call.

The projection object has exactly:

```json
{
  "kind": "project_history",
  "request_id": "fresh-projection-id",
  "view_revision": "<current sha256>",
  "replace_units": [{"unit_id": "<id>", "wire_sha256": "<sha256>"}],
  "source_refs": [{"unit_id": "<original id>", "wire_sha256": "<sha256>"}],
  "summary_request_id": "<completed package model request id>",
  "summary_response_sha256": "<ledger response_sha256>",
  "summary": "<exact completed visible text>"
}
```

Limits: 128 replace units, 512 source references, 65,536 summary characters,
256-character IDs, and two effects per callback. `replace_units` must name an
exact ordered contiguous eligible span with matching digests; `source_refs`
must equal the ordered deduplicated union of its lineage. Any existing summary
must be included in that span. Stale revisions, invalid receipts, changed text,
protected units and partial spans fail before the view changes. The full new
summary string is charged to the existing visible-output pool before the atomic
replacement, in addition to its already charged native model usage.

`projection_completed.receipt` records the fresh projection request, owner,
boundary, previous/new revision, replaced IDs, derived summary unit and charged
characters. Its status is `APPLIED_NOT_DELIVERED`. The actual inserted wire item
is precisely `{"role":"user","content":summary}`, without a host prefix.
Provenance lives in the separate receipt/unit metadata.

## Actual delivery, replay and adaptations

The next solver body is mapped using stable units and original indexes, never
by indexing the shorter input with archived original positions. A known COMMIT
records actual inclusion; only completed solve usage and a real delivery event
permit ACK. Known incomplete inclusion does not grant successful ACK; UNKNOWN
does not assert inclusion. G feedback keeps its integer-ID ACK. Summary ACK is
`{"kind":"projection_delivered","unit_id":...,"projection_request_id":...,
"request_id":"<solver number>","completed":true}`. It never acknowledges an
archived ancestor or asserts original verbatim delivery. Applying a projection,
sending it and acknowledging it are separate recorded operations. Replay
reconstructs view transactions without sending requests or issuing charges.

Explicit donor adaptations: complete target groups instead of event slicing;
configuration 16/1/10000 and positive-tail parameter domain; protection of
pending data; shared 32-request/output/deadline accounting; skip with fewer
than two calls; target event serialization; one user summary; omitted downstream
`ConversationMemory.max_message_chars` truncation. The target sends the full
accepted summary subject to ordinary output/input admission. Donor truncation
markers may exceed `max_event_length`; this is preserved in package behavior.
No semantic retention, failure-log protection or net-token-saving guarantee is
added. Local input estimates and actual provider usage are different evidence.
