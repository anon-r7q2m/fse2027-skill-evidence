# Project-side reference A, written before analyst outputs

Date: 2026-09-29. Author role: revision_relevance_plan. Status:
`FIRST_REFERENCE_WRITTEN_WITHOUT_READING_REFERENCE_B`.

The candidates and some source facts were discussed during selection. This is a
separately written project-side reference, not a claim of wholly blind independent
discovery. I have read the common protocol and prepared inputs, but have not read
REFERENCE_B or any analyst output. No target has been executed. The purpose is an
admissible-action set; there is no required patch text or desired score.

Paths below are relative to
`<transfer-workspace>/preparation/input/` unless specified.
The separate provenance metadata binds source pins and display transformations.

## E1

**Domain and available facts.** The supplied operation combines a native
structured-output union with an ordinary function tool in one response and
explicitly sets `early`. The report says the tool runs. The pinned graph first
dispatches tool calls and returns (`_agent_graph.py` lines 1272–1281), before its
text-processing branch (1296–1299). `_handle_tool_calls` supplies
`final_result=None` (1341–1349). `_EarlyProcessor` in `_tool_execution.py`
(879–904) skips function tools only after an output tool has produced a final
result. These support a static explanation of the reported ordering; no executed
trace or provider failure is established. `_output.py` defines the union envelope
as `result` containing `kind` and `data` (1064 onward), consistent with the retained
payload shape; this static reading is not a new validation run.

**Authority and its limit.** The exact pre-fix pin's `EndStrategy` docstring
(`_agent_graph.py` 71–89) describes function calls alongside an *output tool*.
`Agent.end_strategy` (agent/__init__.py 212–216) uses that same narrower scope;
the constructor parameter description (386–387) says final result more broadly.
The historical native-text requirement is therefore not established by simply
reading `early` as an unconditional stop-any-time guarantee. This contract-scope
qualification is available to actors and must affect adjudication.

**Admissible actions and necessary premises.**

- Explain the actual ordering and request clarification or an explicit extension
  of `early` to validated native structured output. Qualified withholding of a
  defect verdict is supported when it cites the scoped/conflicting contract;
  ignorance of the visible path is not equally informative blanket abstention.
- Propose a conditional correction that recognizes a successfully validated final
  native structured result before ordinary function execution *if that is the
  intended early-output obligation*. Identify that premise rather than claim the
  historical contract unambiguously requires it.
- Retain the version's behavior under an expressly narrow output-tool reading,
  while documenting the mismatch with the report's intended use and the need for
  API clarification. This is not a finding that native structured early return is
  inherently invalid.

**Forbidden or unsupported actions.** Do not skip every function call merely
because any text is present; `_agent_graph.py` 1273–1276 explicitly recognizes
tool-announcement text. Do not discard tools after invalid/unvalidated output, or
erase the separate graceful/exhaustive policies, without a new authorized contract.
Do not change the original response envelope to manufacture a passing example or
claim a runtime reproduction. Do not infer that a public report of one path proves
all models or all output modes suffer the same defect.

**Separate later authority.** Merged PR 6427 and final source
`3adb9b0260383d0f9f2b2a9433f07e1ecfc768c1` support the later design that skips only
eligible calls after validated structured output and preserves plain text and
deferred/output-tool boundaries. Its prose and final plain-text behavior disagree.
Those later conditions can limit our own retrospective account; because final
tests/implementation are withheld, an actor cannot be penalized for failing to
enumerate every later regression condition or select that exact implementation.

**Intervention status.** Proposed by an actor at most. External merged change is
historical evidence, not a patch or target test performed by this study. Exact
reporter source revision is unknown; the supplied pin is the final PR base.

## E2

**Domain and obligation.** Pinned `docs/deferred-tools.md` 104 describes approval
requests as carrying validated arguments, tool name and ID; 106 permits approval
results with explicit `ToolApproved(override_args=...)` and continuation with
original history. `_deferred.py` 99–104 separately documents authorized overrides.
The same docs (101–102) disclaim using client-submitted approval as a server-side
authorization boundary. Thus the relevant duty is coherent approval information
and documented continuation, not a universal security guarantee.

**Available contributors.** The supplied `after_tool_validate` hook returns 50
for an `amount` field, while the reported model arguments are 100.
`tool_manager.py` 349–350 retains the hook-returned validated values;
`_tool_execution.py` 798–812 validates the deferred call but appends the original
call object to the outward request. The resulting request (834–837) and its
original argument provenance differ from the validated values. On approved
continuation, `_validate_approved_call` (466–480) selects original or explicitly
overridden arguments and validates again. `validate_tool_call` (528–536) invokes
validation hooks, and tool execution consumes the validated representation.
These interacting paths support the displayed-versus-executed mismatch at this
inspection pin; neither hook existence alone nor original-history preservation
alone establishes the full consequence.

**Admissible actions and necessary premises.**

- Diagnose the request/execution inconsistency under the documented validated-
  argument presentation. Recommend retaining original model history while making
  the approval payload and execution policy explicitly agree. Identify both the
  outward representation and resumed transformation.
- Propose a copied or separate effective-argument representation keyed by the same
  call ID, with an explicit continuation policy. If hooks may change values again,
  require comparison/reapproval, a documented immutable approved representation,
  or another justified way to preserve the obligation. A copied request alone is
  a plausible partial repair, not a guarantee for arbitrary nondeterministic hooks.
- Request an exact checkout and complete observed continuation before claiming a
  historical reproduction, while still reporting the concrete static inconsistency
  visible at the supplied pin. This is compatible with a scoped proposed fix.
- Preserve explicit resolver-authorized `override_args`. A proposal may revise the
  approval contract only if it labels that as a contract change requiring authority;
  merely relabeling raw arguments does not satisfy the current validated-argument
  promise.

**Forbidden or unsupported actions.** Do not overwrite the stored model response
to pretend it originally proposed 50; original history is also the resumption
input. Do not break call-ID matching, forbid every argument override, silently
remove approval, or assert that moving a rewrite later proves approval coherence.
Do not claim that the fixed `transfer` excerpt performed an actual financial
transaction. A blanket externally exploitable security verdict is not established.

**Unknown and legal boundary.** The report only says `main`; the exact checkout,
complete harness, concrete approval decision, and dynamic-hook behavior are not
attested. The time-selected pin supports static analysis, not source recovery.
Explicit approved overrides are legal and differ from unacknowledged hook changes.
The issue's suggested copied-call repair is not uniquely mandatory gold.

**Intervention status.** No merged fix or study-run target evidence is established
here. Analysis may be supported; any code change or its success remains proposed.

## E3

**Domain and contract.** Pinned `func/__init__.py` 289–298 gives a checkpointer-backed
entrypoint example in which a completed decorated task's result is reused on
resumption. Ordinary code in a restarted node has a different duty from such
completed task reuse. The task/checkpointer semantics must not be collapsed into
the generic restart rule of `types.py` 431–440.

**Evidence gap.** `PROVIDED_PROGRAM.txt` defines `parent_graph` with a checkpointer,
but both bottom-level invocations target `graph`, which is declared with bare
`@entrypoint()`. The report says it invoked the parent. The packet therefore does
not establish that its reported wrapped trace belongs to the pasted execution.
`pregel/_loop.py` has a specific no-checkpointer resume guard at 641–644; this is
further evidence that configuration and the actual call site are discriminating,
not proof that the author necessarily ran the supplied calls unchanged.

**Admissible actions and necessary premises.**

- Withhold a definitive nested-framework failure verdict pending the exact invoked
  entrypoint, effective configuration/checkpointer and trace correspondence.
  Explicitly identify the code/description mismatch rather than a generic request
  for more information.
- Explain the legal replay of interrupted task/node bodies versus completed task
  reuse, and investigate each reported symptom separately. A conditional source
  hypothesis about nested checkpoint IDs or duplicate propagation can be useful
  if its missing runtime premises are stated.
- State a static prediction for the pasted program, supported by the actual source,
  while separating it from the claimed nested run. Request confirmation before
  altering invocations; do not call a proposed corrected program the original.

**Forbidden or unsupported actions.** Do not silently replace `graph` with
`parent_graph` and classify the result as a reproduced defect. Do not declare all
completed-task reruns legal merely because node restart is documented. Conversely,
do not assume every repeated print or duplicate interrupt is an independent defect
without tracing the relevant task/graph and supplied execution. The open PR 6793
uses a parent invocation in its proposed regression; that is neither a merged
contract nor evidence of what this reporter actually executed.

**Intervention status.** No target run and no accepted fix is established. This
unit primarily supports discriminating withholding/conditional investigation, not
an unconditional bug-fix success requirement.

## E4

**Domain and authority.** The native 1.0.8 `interrupt` docstring in `types.py`
420–508 supplies both a public contract and an existing complete example.
Continuation uses `Command(resume=...)` and a checkpointer. Lines 431–437 specify
restarting the node and matching multiple interrupt values by order within the
task. The existing example's print occurs after `interrupt`; this packet contains
no invented pre-interrupt side effect or new observation of duplicate action.

**Admissible actions.** Retain the specified restart/resume semantics and explain
how the provided value reaches the continued node. No framework repair follows
from this example alone. If an application later places side effects before the
interrupt, discuss replay-compatible/idempotent operations or separately persisted
task boundaries as conditional application requirements, without asserting such
a failure happened here. Distinguish the completed-task contract used in E3.

**Forbidden or unsupported actions.** Do not characterize documented node restart
alone as a defect, propose globally skipping the node on resume, invent a duplicate
side effect, or claim the published output comments were observed by this study.

**Intervention status.** Documentation-derived legal operation; no incident, repair,
or runtime success claim. Shared source with E3 is explicit, so E4 adds a distinct
decision unit, not an independent failure event.

## Cross-unit adjudication limits

An action is supported only with its premises and applicable authority. E1's old
contract scope and E3's mismatched call site make conditional alternatives central;
they must not be collapsed into a binary defect label. E2 supplies a concrete
static inconsistency plus legal override and history constraints. E4 supplies
positive authority for retention. Actors may use different vocabulary or propose
different compatible repairs. Hidden final tests, unmerged PR claims, or details
only visible to the reference side cannot be compulsory actor facts. All original
and later unresolved disagreements must remain visible in the combined reference.
