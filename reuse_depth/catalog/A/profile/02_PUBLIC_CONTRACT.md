# Public ABI: aider_architect_v1

Implement `handle(event, state) -> {"state": object, "effects": [one effect]}`.
Raise `ValueError("PROTOCOL_REJECTED: ...")` on malformed events or invalid
lifecycle. State is JSON only. No filesystem, network, subprocess, actual model
calls, host imports or donor imports. Use standard library and declared own
modules. Implement the mechanism in generated code, not a binding to a prewritten
target implementation.

`package.json` has exactly schema_version=1, profile=`aider_architect_v1`,
entrypoint=`mechanism:handle`, modules=[Python basenames], and
capabilities=[`architect_request`, `editor_handoff`, `architect_terminal`].
Use 1..8 modules, <=1 MiB each and <=4 MiB total; event/state/effect <=3 MiB.
No truncation. Persistent state internals are not prescribed.

All events/effects include exactly `kind`, `run_id` (nonempty <=256 chars),
`base_snapshot_ref` (40 lowercase hex), plus the fields below. File views are
ordered lists of <=64 unique `{path, content}` rows. Path is a canonical
repository-relative POSIX path, <=4096 chars, no controls, backslash, empty/
dot/parent component or VCS directory; content is any string. Both lists are
sorted by path and disjoint. `files` is nonempty, `readonly_context` may be empty.
The latter contains explicitly supplied source views (possibly labeled excerpts
in the host); inherit their exact bytes and do not infer missing source.

## Events and lifecycle

`begin_architect` adds `issue` (string), `files`, `readonly_context`, `model`
(nonempty <=256 chars), `editor_format` (`ordinary` or `search_replace_k4`),
`max_calls` (integer 1..7), `editor_min_calls` (integer 1..4). It requires empty
state and emits one architect_request. One model request is counted even if
the returned content is empty. Language is fixed English, auto-accept true,
no separately selected editor model, no architect editing or tool use.

`architect_result` adds `request_id`, `status` (`completed`, `incomplete`,
`failed`, `unknown`), `text`, `usage`. request_id matches the outstanding request.
Completed text is a string, all other text is null. usage is exactly
`{input_tokens: nonnegative int, output_tokens: nonnegative int}` except unknown
may use null. Process the receipt once, count one call, retain actual usage.

- Non-completed -> terminal UNAVAILABLE, final_snapshot_ref=null.
- Empty/whitespace completed -> terminal EMPTY, final_snapshot_ref=base.
- Nonempty completed but max_calls-1 < editor_min_calls -> terminal BUDGET_STOP,
  final_snapshot_ref=base. Do not ask an editor or retry the architect.
- Otherwise emit exactly one editor_handoff and wait for editor_result.

`editor_result` adds `handoff_id`, `status` (`completed`, `resource_stop`),
`snapshot_ref` (40 lowercase hex), `calls_used` (integer 0..remaining_calls),
`usage` (nonnegative integer input/output pair). It represents one whole editor
run; id must match the outstanding handoff. Emit terminal COMPLETE, propagate
snapshot/status, add editor usage to architect usage and calls_used to one.
Snapshot capture is host supplied; package cannot fabricate edits or extra calls.

`get_result` has no additional fields, legal only after terminal. Return the
identical cached terminal. Repeated begin/result, wrong order/run/base/ID, extra
keys and wrong types reject. No repeated request or silent fallback.

## Exact request construction from donor

architect_request adds `request_id`=run_id+`/architect/1`, `model`=input model,
and `messages`. The first message is system with the exact
`ArchitectPrompts.main_system.format(language="English")`. File message
ordering is readonly pair (if nonempty), editable pair, then the original issue
as a user message. Use fixed triple-backtick fences. Each file view renders:
`"\n" + path + "\n```\n" + content + "```\n"` (no invented trailing newline).
Concatenate views in supplied order. Editable prefix/assistant reply are the
exact ArchitectPrompts attributes; readonly prefix is CoderPrompts attribute,
with assistant reply `Ok, I will use these files as references.`
These are the fixed donor text-file methods with no repo map, images, examples,
prior messages, platform reminder or shell suggestions. All source strings are
supplied in the public packet; do not copy a prewritten target package.

## Exact handoff

editor_handoff adds:

```
handoff_id = run_id + "/editor/1"
task_text = architect text unchanged, including surrounding whitespace
files = original files
readonly_context = original readonly_context
model = original model
editor_format = original editor_format
cur_messages = []
done_messages = []
preproc = false
settings = {suggest_shell_commands:false, map_tokens:0, cache_prompts:false,
            num_cache_warming_pings:0, summarize_from_coder:false}
remaining_calls = max_calls - 1
calls_used = 1
usage = architect receipt usage
```

No original issue, obligation card or architect history in the handoff except
what the architect itself wrote. The same file views are inherited separately.
These behaviors are from ArchitectCoder.reply_completed; model/config selection
is constrained to this admitted domain. The ordinary/P editor replacement is
declared outside the package. For P, task_text replaces begin.issue verbatim;
read-only views are delivered separately as data, not appended original issue.

architect_terminal adds exactly `status` (UNAVAILABLE/EMPTY/BUDGET_STOP/COMPLETE),
`final_snapshot_ref`, `editor_status` (null except COMPLETE), `calls_used`,
`usage` (summed pair, or null only for unknown). This JSON accounting and
snapshot mapping replaces donor cost/automatic-commit fields. It does not
permit git commits. Global host budgets/termination have priority.

Official outcomes, hidden tests, current benchmark tasks and future task choices
are never inputs to generation or acceptance. All model calls are interpreted,
charged and recorded by the host; handle itself is a pure computation.
