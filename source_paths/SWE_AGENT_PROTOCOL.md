# SWE-agent path protocol, frozen before fixture execution

Revision: `3ea751c087f32b16e039a2233dd6eefecef325d5`. Exposure at this exact
path is unknown. This protocol adds a fixed control set, not an unseen-host
validation. There are exactly four conditions below and no replacement path.

## Obligations and source map

**S1: configured tool admission and identity.** The default function-calling
parser requires exactly one available tool call. A valid `bash` argument must
reach the execution boundary, and its observation must retain the originating
tool-call ID. Public basis: `config/default.yaml` selects `function_calling`;
`FunctionCallingParser.__call__` explicitly requires one call, and
`DefaultAgent._add_templated_messages_to_history` requires one reply ID.

**S2: distinguish observed output from a success assertion.** A message that
claims a command ran successfully must not be justified solely by empty output
when the execution record has a nonzero exit code. The independent obligation
is ordinary shell command semantics: zero and nonzero status differ even when
both commands emit no text. This is not an obligation to preserve all output
or abort every nonzero command. Public source distinguishes status in
`SWEEnv.communicate(check='warn'/'raise')`; the default agent instead uses
`check='ignore'`. No repository repair correctness is asserted.

Binding of the inspected default:

- `config/default.yaml` sets `next_step_no_output_template` to
  `Your command ran successfully and did not produce any output.` and selects
  the function-calling parser, bash tool, and cache-control history processor.
- `DefaultAgent.__init__` defaults `_always_require_zero_exit_code=False`.
  `handle_action` therefore passes `check='ignore'` to `SWEEnv.communicate`.
- `communicate` receives a runtime result containing output/status, returns
  only `r.output`, and does not raise on a nonzero status in that branch.
- `add_step_to_history` selects the no-output template when
  `step.observation.strip() == ''`. `messages` applies configured history
  processors. The resulting messages are the next query input.

## Native slices and mock boundaries

Execute the unmodified AST method bodies for function-call parsing, action
admission/handling, `SWEEnv.communicate`, observation-to-history rendering, and
cache-control history projection. Load default template strings from the
pinned YAML. Existing system Python/Jinja2/PyYAML may be used because the project
venv lacks Jinja2; no packages are installed.

The model is a deterministic response supplier and its next-query sink only
captures input. SWE-ReX/runtime returns fixed `(output, exit_code)` objects;
there is no shell, container, repository, network, or model execution. Logging,
hooks, state collection, unused submission handling dependencies, and data
carrier types are mocks. For these simple bash commands, multiline guarding
is an identity. Record which source methods actually execute. Full bundle
installation, state-command execution, model-provider serialization and task
benefit remain unknown.

## Frozen conditions

| ID | Native path input | Expected S1 | Expected S2 |
|---|---|---|---|
| S-A | One bash call for `true`; runtime output `''`, status `0` | supported | supported: empty success is a legal case |
| S-B | One bash call for `false`; runtime output `''`, status `1` | supported | violated if the same successful-command sentence reaches the next query |
| S-C | One bash call for `printf 'error\\n'; false`; runtime output `'error\n'`, status `1` | supported | supported for the narrow no-false-success obligation if only the output template appears; status preservation itself is unassessed |
| S-D | Two bash calls in one model response | supported if parser rejects before runtime | not_applicable: no command executes |

For every applicable condition, record original response, parsed command,
runtime metadata, returned observation, emitted tool-call identity, final
consumer message, and the two judgments. No actual command is run.

## Public checks and direct-test comparison

The pinned local `tests/test_agent.py` includes `test_function_calling`, whose
assertions cover parsed `ls` and nonempty output delivery. Its
`test_show_no_output_template` overrides the template with `no output template`
and ends with `# todo: actually test that the template is used`. These are
inspected public checks, not evidence that no other repository test covers the
case. Their full native fixture suite is not executed here.

On each same transformed input, directly invoke the original
`add_step_to_history` with the recorded observation and compare the rendered
tool text with the full sliced path. For S-B, the fixture's independent status
provides the oracle. If this ordinary direct test exposes the same assertion,
report that it is sufficient; do not claim that consumer tracing is required
to detect it. Without the upstream status, empty text alone cannot decide
whether success is true. S-D additionally runs the same parser directly.

Any fixture failure permits at most one limited correction with the initial
record retained. Unresolved behavior closes unknown. The result supports only
the disclosed information conversion, not a live failure rate or score loss.
