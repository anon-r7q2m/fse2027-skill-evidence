# Native saved-team decision integration v1

Status: implementation under static review; no execution authorized by this file.
Study: `native_decision_integration_v1`. Date: 2026-09-29.

This is a bounded integration extension of the already known a21 source-filter
serialization mechanism. It is not a new defect discovery, a fresh diagnostic
opportunity, a field incident, or part of the closed `prospective_decision_v1`.
All earlier experiments and counts remain closed and unchanged.

## Question and endpoint

Does the documented complete-team configuration lifecycle preserve the declared
requirement that a designated reviewer produce a consistency finding before a
review-required CSV-report workflow stops?

The primary endpoint is actual reviewer-tool invocation, the resulting
`review.json` independently computed from the produced report and original CSV,
and delivery of that finding through the native response and final `TaskResult`.
A native replay provider supplies one fixed tool request, never a verdict.
The known report defect is part of the application fixture, not another
framework defect. Stopping does not certify report correctness.

## Fixed source and components

- Original AutoGen: `027ecf0a379bcc1d09956d46d12d44a3ad9cee14`, complete existing
  snapshot at `/STUDY_ROOT/sources/autogen`.
- Target-source change: the exact unchanged a21 patch at
  `/STUDY_ROOT/diagnostics/a21/intervention.patch`,
  SHA-256 `d2a2251069be3a83141e8d2fdaad814642e68a8abfc58f2cfde2d2644b69f269`.
- Native `RoundRobinGroupChat`, `CodeExecutorAgent`,
  `LocalCommandLineCodeExecutor`, `AssistantAgent`, `ReplayChatCompletionClient`,
  `FunctionTool`, `StaticWorkbench`, and `TextMentionTermination`.
- The source-backed review function is project-authored application code;
  framework invocation, serialization, response construction and termination
  remain native.
- Existing Python 3.12 environment:
  `/STUDY_ROOT/venv/bin/python`. No dependency install.

## Three deployment procedures

D (`direct_original`): construct and run a fresh team on the original source.

R (`reloaded_original`): construct on original source, call the complete team's
`dump_component`, write `team.json`, read that file, call
`BaseGroupChat.load_component`, and run the newly loaded team.

P (`reloaded_patched`): apply only the old a21 patch to a separate complete source
copy; construct from the same declared parameters, export a new full-team JSON,
read/load it through the same native API, and run the newly loaded team.

P does not recover intent from R's already lossy JSON. No JSON field is inserted
manually and no original live component is attached after loading. This is
configuration serialization before any team run, not conversation-state resume.
The loaded team is not exported a second time: that is outside this lifecycle.

## Three scenarios and exactly nine cells

`scenarios.json` fixes the three cases and order. Each is run once under D, R, P.
Within each scenario, task, code, data, provider reply and declared configuration
are identical across procedures, except owned execution-directory roots.

- T: required reviewer, amounts 1200/-200/750, completion marker in an input note.
  The frozen generator filters negative amounts, so it writes two rows/1950;
  the required signed result is three rows/1750.
- C: required reviewer, all-positive amounts 1200/200/750, no marker in notes.
  The same generator writes the correct three rows/2150. This is a normal-behavior
  control, not a one-variable causal contrast with T.
- U: exact T application data and code, but unrestricted stopping (`sources=None`)
  and no mandatory-review policy. Stopping on executor output is legal even
  though the report remains discrepant. Policy legality and report correctness
  are separate fields.

The full completion marker must be absent from the initial task/code. It enters
the group conversation through execution of the CSV-reading code. Every cell
uses a fresh directory; output report and review finding are absent at start.

## Predeclared predictions

| Scenario | D | R | P |
| --- | --- | --- | --- |
| T | One execution; reviewer tool writes discrepancy finding; stops after review | One execution; executor marker stops before reviewer; finding absent | Same required review behavior as D |
| C | One execution; reviewer tool writes clean finding; stops after review | Same | Same |
| U | One execution; executor marker legally stops; reviewer not invoked | Same | Same |

The native reviewer response includes tool events and a tool summary. The marker
may first match `ToolCallExecutionEvent`, before `ToolCallSummaryMessage`.
The actual matching message type/source is observed, not fixed as a prediction.
R/T tests a skipped required review, not an erroneous approval of the report.

## Observation and intervention boundaries

Record the full safe exported JSON, declared and effective source restrictions,
loaded native types, input data, generated report, actual native executor result,
provider `create_calls`, native stream and final `TaskResult`, tool finding, and
all actual calls to `TextMentionTermination.__call__` including its input message
sequence, source restriction and returned stop. A passive process-local profiler
observes the exact native call/return frame and captures the matching `message`
local on a native stop return. It does not replace methods, mutate locals, choose
responses, or add a decision policy. The same observer runs in all procedures.

For an invoked review, require the actual replay-provider input to contain the
executor's report-bearing message with unchanged content. Record the received
messages. Verify the tool request's name, call ID and arguments against the fixed
request, and require JSON-semantic equality between the actual tool result, the
finding file and the tool summary. The reviewer-source summary must link the same
request/result and appear in both the final `TaskResult` and the real termination
input. A file written without this delivery chain does not satisfy the endpoint.

Compare the full R/P exported configurations for each scenario. Normalize only
`/config/participants/0/config/code_executor/config/work_dir` to its owned-root
placeholder and `/config/termination_condition/config/sources` to the original
declared policy. Record the original presence/value of both fields; require the
work directories to match their actual cells and the patched source restriction
to match the declaration. Every other field is retained in the full equality
comparison, including the executor agent's separate `sources` field. Missing
exports or other configuration differences prevent the integration contrast from
being treated as established.

The review function rereads actual artifacts, computes signed integer totals,
records count/total checks and writes the finding before returning its JSON string
with the completion marker. Independent collection also reads both artifacts to classify completeness;
it never supplies a missing reviewer finding. No script response branches on the
source variant, execution outcome, report bytes, or earlier messages.

## Freeze and execution

Before any target import, construction, dump/load, or behavior execution, the root
reviews the code and writes `freeze.json` with status `FROZEN_FOR_EXECUTION`, hashes
for this protocol, scenarios, both CSV inputs, generator, execution script, old
patch and explicit path-configuration JSON, and an exact file manifest of the
original upstream source snapshot. The freeze records the normalized seven path
identities as `paths`, plus `source_root`, `python` and `source_files`.
The executor verifies those entries and uses a new owned study/output tree.
The freeze is a scientific input record, not a user-approval substitute.

The original execution uses `/INTEGRATION_ROOT` for new
source copies/work directories and `results_cache/native_decision_integration_v1`
for results. The runner takes `--paths PATHS.json` with exactly seven absolute
paths: `repo`, `protocol`, `study`, `output`, `source`, `python`, and `patch`.
These path identities and configuration bytes are frozen and forwarded unchanged
to each worker. The interpreter's venv symlink is preserved. The two new owned
destinations must be absent and disjoint, and cannot contain protected inputs.
Public reproduction may choose fresh owned roots and create its own new freeze
from these same protocol/script/input bytes; it must not edit frozen source merely
to relocate paths or present a new run as the original sealed execution.

The runner's environment is an explicit whitelist with no credentials or provider
keys, dotenv disabled, offline/telemetry settings, the existing interpreter and
owned temporary/cache directories. No user environment dump, network task command,
external model call, benchmark score, container, or dependency install is allowed.

Limits per cell: local command 5 seconds, native workflow 60 seconds, child alarm
80 seconds, outer process group 90 seconds. Maximum team turns: 4. The reviewer
has one fixed native FunctionCall response, function calling enabled, streaming
and reflection disabled, and one tool iteration. Unexpected calls and script
exhaustion are inconclusive, not repaired or retried.

All nine cells are attempted once in the fixed order unless the shared source or
freeze identity is invalid. Preserve every stdout/stderr, exception and incomplete
observation. Complete contrary behavior is retained as prediction-not-supported;
missing observations, infrastructure failures or tool execution errors are
inconclusive. No fixture/source changes, extra responses, new scenarios or repeat
runs are permitted after the first target execution. A later study would require
a distinct design/version; this version closes after the fixed matrix.

## Interpretation

Supported contrasts would show preservation or loss of an application review duty
through a complete documented saved-team operation. They would not establish
live-model reviewer competence, task success, production frequency, correctness of
all serialization branches, recovery of previously saved lossy files, or a new
general theory. The three scenarios and nine runs are not independent discoveries.
