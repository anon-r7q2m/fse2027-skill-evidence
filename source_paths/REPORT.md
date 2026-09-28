# Two bounded native source-path checks

## Result and control decision

One source path maps successful and unsuccessful empty command output to the
same successful-command sentence; the other preserves known command status
and enforces complete tool-call groups. Both have ordinary direct tests that
match the full sliced-path judgments. There is no measured advantage of the
analysis over these local tests and no evidence of a task-score change.

The practical decision for the inspected SWE-agent integration is to carry
command status when a consumer needs a success claim, or use neutral wording
when only output is available. The decision for OpenHands is to retain its
existing status formatting and complete-group checks: an incomplete or orphan
tool result does not by itself require a repair. Neither upstream source was
modified.

## Selection, scope and execution

The selection protocol preceded path inspection; preferred hosts were chosen
by role and existing pinned public source availability, not by a known fault.
No fallback or replacement host was used. SWE-agent's specific prior path
exposure is unknown. The OpenHands history-to-CodeActAgent path had already
been inspected during the September 11 transfer. This is not independent
unseen-object validation, cross-host transplantation, or blind sampling.

After source inspection and before execution, per-path protocols fixed two
obligations and four conditions each. Expected outcomes were source-informed;
this is not a prospective prediction claim. All eight conditions finished in
the initial attempt, with **zero fixture corrections**. Outputs and the loaded
method registry are preserved in `results/attempt_0/`. The registry records
loaded native method bodies, not branch coverage. Direct invocations reuse
the same inputs and do not add independent conditions.

SWE-agent revision: `3ea751c087f32b16e039a2233dd6eefecef325d5`.
OpenHands revision: `34bf9c2579ca5a25e452583eed38c6c0e45cebd6`.
Copied source files match the pinned public Git blobs and include both MIT
licenses. Native AST bodies are executed with deterministic runtime/model
records, minimal data carriers, and explicit host/transport mocks. No shell
command, container, external model, benchmark worker, install, commit or push
is part of this execution.

## Full fixed-condition results

| Condition | Observed consumer behavior | Obligation judgments | Same-input direct check |
|---|---|---|---|
| S-A: empty output, status 0 | Default successful-command sentence reaches next query; original call ID retained | Admission/identity supported; success wording supported for this legal case | Same sentence/judgment |
| S-B: empty output, status 1 | The identical successful-command sentence reaches next query; original call ID retained | Admission/identity supported; success wording violated by the independently supplied nonzero status | Same sentence and violation |
| S-C: nonempty `error` output, status 1 | Ordinary `OBSERVATION:` message reaches next query, without a success assertion | Admission/identity supported; narrow no-false-success obligation supported; preserving full status is unassessed | Same observation/judgment |
| S-D: two tool calls | Native parser reports `multiple`; runtime is not invoked | Admission supported; success wording not applicable | Same native parser rejection |
| O-A: complete pair, empty content, status 0 | Tool reply retains `exit code 0` and matching call ID | Status/identity supported; matching supported | Same message list |
| O-B: complete pair, empty content, status 1 | Tool reply retains `exit code 1` and matching call ID | Status/identity supported; matching supported | Same message list |
| O-C: pending two-call group, one reply | No partial tool-call group enters constructed input | Paired-status obligation not yet applicable; complete-group obligation supported | Same legal omission |
| O-D: orphan reply | No tool reply enters constructed input | Paired-status obligation not applicable; matching obligation supported | Same legal omission |

These are eight fixed conditions, not eight tasks, eight independent
mechanisms, an accuracy score, or an estimate of native failures. The
nonzero statuses are fixed boundary inputs, not results of real command
execution. We neither mutate native code to create the discrepancy nor
attribute a live failure rate to it.

## Comparison and limits

The inspected SWE-agent default configuration explicitly says a command ran
successfully when its observation is empty. Native `handle_action` passes
`check='ignore'`; native `communicate` returns runtime output without the
status. Rendering therefore treats the paired empty outputs identically.
The status oracle is external to that renderer, so an empty string alone
cannot distinguish the cases. The direct renderer test is sufficient once
the relevant status obligation and paired input are supplied.

The locally available upstream SWE-agent test for no-output rendering contains
an explicit TODO to assert use of that template. Other inspected tests cover
valid function calling, output delivery, and multiple-call rejection. They
were read, not run as the upstream suite; no all-repository coverage claim is
made. OpenHands' relevant upstream test file is named in the pinned tree but
not locally cached, so its coverage stays unknown. Its native grouping and
filter checks are already sufficient for the fixed legal boundaries.

OpenHands' default NoOp mapping, SWE-agent configuration defaults, and method
links are bound by source inspection, not complete application startup. The
fixtures mock logging, hooks, state collection/tracking, data carriers,
NoOp condensation, provider serialization, runtime and model responses.
Native environment execution, scheduler reachability of the partial-group
fixtures, arbitrary output truncation, full-host behavior, later revisions,
debugging efficiency and official task utility remain unmeasured. There are
no claims about source necessity, stable composition gains or universal
consumer-relative theory.

The check closes here. No extra cases, repairs, runtime experiments or sample
extension are required by this result.
