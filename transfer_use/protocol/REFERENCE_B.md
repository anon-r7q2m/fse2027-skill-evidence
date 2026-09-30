# Independent first reference B

Study: `decision_transfer_use_v1`  
Prepared: 2026-09-29  
Reviewer: `score_witness_plan`  
Status: `FIRST_RECORD_COMPLETE_BEFORE_SHARED_REFERENCE_AND_ACTOR_OUTPUTS`

I read the fixed actor input and its source/presentation provenance. I did not
read `REFERENCE_A`, any shared reference or actor output before writing this
record. I participated in design and candidate selection and previously read
public issue pages; this is an independent first judgment by a project-side
reviewer, not a blind external human judgment. Source-completeness requests to
A concerned E1's imported tool dispatcher and linked Agent API definition; no
reference conclusion was exchanged. I did not run or import a target, model,
reproducer, test, grader or container. The judgments below do not establish
newly observed runtime outcomes.

All paths below are relative to the fixed actor `input/` directory. Its source
roots are `sources/pydantic_e1` at
`b5f43e4cc4c7d6ae2d7f76007dede1d8ca00c204`, `sources/pydantic_e2` at
`577a8e94b500999727cbf61fef569755a889f1ce`, and `sources/langgraph_1_0_8` at
`a7a27dd43a4229c2ca09ac065a6a39e4ce083063`. In the abbreviated references, `P1`
and `P2` mean the corresponding root's `pydantic_ai_slim/pydantic_ai/`, and `L`
means the LangGraph root's `libs/langgraph/langgraph/`. No fact from a withheld
later fix is necessary for a supported actor answer.

## E1: mixed native text output and a function-tool call

**Consumer/action.** `CallToolsNode` selects tool dispatch versus native text
output processing. Its downstream early tool strategy decides whether to call
`search_documents` or return a skipped-tool record.

**Packet facts.** `E1/PROVIDED_PROGRAM.txt:15–21,47–78` declares the two output
models, returns the `result/kind/data` union envelope alongside the tool call,
and selects `NativeOutput(Response | Clarification)` with `early`. The text is
not an unwrapped `Response` object. Under this snapshot, `_output.py:486–512,
617–628,693–712,1064–1118,1148–1198` builds a native union text processor whose
outer object contains `result`, with `kind` and `data`; the supplied strings
fit the visible envelope and required string fields. No runtime validation is
claimed. A blanket claim that the wrapper is invalid is contradicted by these
source definitions; a specific additional validation concern requires evidence.

`P1/_agent_graph.py:1237–1307` collects text and tool calls, then enters the
tool branch and returns whenever calls are present. Text processing is later.
`P1/_agent_graph.py:1334–1350` supplies `final_result=None` to the tool processor.
`P1/_tool_execution.py:155–175,879–904` selects `_EarlyProcessor`, considers
output-tool calls, and runs function calls when no final result exists. Native
text has not been supplied as an already accepted result on that path. The
same program supplies text alone on subsequent requests. Thus a source-based
explanation for first-response tool execution exists without blaming the
provider or replacing the output validator. The report's actual tool call is
`REPORTED_ONLY`; the snapshot is not an attested copy of the reporter's `main`.

**Authority.** The packet has a real wording/scope boundary. The Agent
constructor parameter says tools requested alongside a final result
(`P1/agent/__init__.py:386–387`), but its field documentation explicitly says
an output tool (`:212–216`), as do `EndStrategy`
(`P1/_agent_graph.py:71–89`) and
`sources/pydantic_e1/docs/output.md:363–388`. The supplied program uses native
text output, not an output-tool call. Therefore the broad obligation “valid
native output under early must always preempt function tools” has plausible
API intent but is not an unambiguous historical promise established by every
provided contract passage. Record this as a scope ambiguity or conditional
obligation, not certainty manufactured from the issue label or a later fix.

**Admissible actions and necessary premises.**

- Explain the evidenced dispatch/recognition boundary and withhold an
  unconditional historical contract-violation verdict until native-mode policy
  is established. Clarifying that policy is a supported action, not failure to
  find a forced bug.
- Propose recognizing and successfully validating native output before
  function dispatch under an explicitly stated early/native obligation. This
  is an untested, mode-specific correction proposal; it can be described as a
  policy-coverage repair if the actor states its authority qualification.
- A repair-oriented answer citing the broader constructor wording is
  acceptable if it acknowledges the narrower passages or otherwise scopes
  the obligation explicitly. Do not require a particular patch or function
  name. Likewise, a retention/clarification answer cannot deny the observed
  source path merely because the contract is ambiguous.

Preserve invalid-output retry/fallthrough, calls when no acceptable final
output is present, graceful/exhaustive behavior, schema validation and required
message-history/tool-return consistency. “Skip every call whenever any text
exists,” accepting invalid native data, or globally changing all strategies
is contradicted by legal neighboring cases. Altering the `Response` schema or
blaming Bedrock as the demonstrated cause lacks support: the supplied program
uses `FunctionModel`. Streaming behavior is not proof of this `agent.run`
path's contract. No claim that a proposed change was tested, that the original
provider incident was reproduced, or that this yielded task-score gain is
admissible.

**Reference uncertainty.** Exact original checkout, original execution trace,
and a single uncontested historical early/native authority remain unresolved.
Static dispatch facts are resolvable; the unqualified historical defect label
is not. Retain this distinction during combined adjudication.

## E2: approval presentation versus validated execution arguments

**Consumer/action.** An approval consumer sees a deferred `ToolCallPart`; after
approval, the tool executor consumes validated arguments. These are different
objects on related paths and must not be silently equated.

**Packet facts.** `E2/PROVIDED_PROGRAM.txt:1–16` replaces an `amount` value with
50 in `after_tool_validate`, returns a new dictionary, and defines an
approval-required tool. The excerpt leaves `model` and `executed` undefined.
`E2/REPORTED_VALUES.txt` states a display of 100 and execution at 50; these are
reported values, not our runtime observations or evidence of a financial
transaction. The temporal pin is explicitly not reporter-attested.

`P2/tool_manager.py:262–304,306–359,443–458,528–548` preserves the original call
and returns separately validated arguments, including the post-validation
hook result. The helper's comment at line 318 does not override the actual
`args_override` use at lines 281–304. `P2/_tool_execution.py:798–812` validates
but appends the original `call` to the unapproved list; `:834–838` publishes
that list. This is the first evidenced object mismatch for a promise to expose
validated arguments. On approval, `:440–480` validates the call again with
`approved=True`, using a replaced call only for explicit `override_args`.
`P2/tool_manager.py:370–425` passes validated arguments into execution hooks
and ultimately execution. For the supplied constant rewrite, these paths
support the reported 100-versus-50 relation as a conditional static explanation.
They are not a capture of the omitted complete run.

**Authority.**
`sources/pydantic_e2/docs/deferred-tools.md:93–106` explicitly describes the
approval list as containing validated arguments. This supports `JUSTIFIED`
authority for that narrower presentation obligation on the pinned API.
`P2/capabilities/abstract.py:703–722` expressly permits post-validation
modification; disabling all such hooks is not an acceptable blanket repair.
`P2/_deferred.py:99–106` and the deferred-tool documentation explicitly permit
`ToolApproved(override_args=...)`. The universal stronger predicate “every
executed byte must equal the original model arguments” is therefore not the
established obligation. Argument differences from explicit authorized
overrides are legal; `ALLOWED_ADAPTATION` requires explaining that permission
and the retained validation/approval obligations.

**Admissible actions and necessary premises.**

- Propose delivering the validated/effective arguments, or a clearly bound
  representation of them, to the approval consumer while preserving the
  original model response separately. Correct the demonstrated delivery
  boundary, not the permissive hook or the approval predicate itself.
- Bind an approved effective-argument snapshot through resumption, or detect
  a later meaningful change and obtain appropriate authorization. Such a
  design is a proposal and must state its domain, preserve explicit overrides,
  and acknowledge remaining execution hooks/context changes. No unique cache,
  copy type, API field or patch is required by this reference.
- A cautious answer may affirm the pinned documentation/source mismatch
  while withholding attribution to the reporter's exact run and proposing the
  missing captures. Merely refusing all analysis because the snippet is
  incomplete overlooks independently visible source and contract evidence.

Keep two contributors separate: the outgoing approval path retains raw call
arguments, and the resumed execution path revalidates/transforms arguments.
They explain the relation jointly; revalidation alone is not a second proven
defect. Mutating the recorded model message to make its history look as though
the model produced the transformed value loses source provenance. Making a
distinct approval representation is not that mutation. Do not claim that an
approval necessarily bypassed endpoint authentication or that real money moved.
The pinned documentation explicitly separates human approval from authorization
against an untrusted client (`docs/deferred-tools.md:101–102`).

**Disallowed shortcuts.** Treat all post-approval argument differences as
defects despite `override_args`; remove permitted validation hooks wholesale;
present an untested proposal as a validated fix; or claim an exact original
checkout/full execution from the temporal pin. A documentation-only narrowing
must be labeled a proposed API/contract change, not retroactive satisfaction
of the currently stated validated-argument promise.

**Reference uncertainty.** Actual UI code, full original model/deferred
history, before/after hook captures and context, and exact original checkout
are missing. A universal invariant for every downstream execution hook is
not established. The narrower approval-object boundary is source-resolvable.

## E3: nested functional invocation with an inconsistent supplied call site

**Consumer/action.** Resume execution selects a graph, checkpoint configuration,
task result and interrupt resume state. The issue concerns reuse of a completed
task and duplicated interrupt entries, not merely any pre-interrupt statement
running twice.

`E3/PROVIDED_PROGRAM.txt:27–43` defines `graph` with `@entrypoint()` and
`parent_graph` with a checkpointer, but both actual bottom-level calls invoke
`graph`. The supplied `config` contains only `thread_id`; the declared parent
is not invoked in those lines. `E3/CASE.md` separately reports the author's
claim to invoke the outer entry point. Preserve this conflict.
`E3/REPORTED_BASE_OUTPUT.txt` prints step 1 once; the wrapped output prints it
again on resume and contains two entries with the same shown interrupt ID.
Those public records are reported outputs, not evidence that the pasted
program and those exact outputs share one captured execution.

`L/func/__init__.py:261–269,289–298` documents checkpointed state and reuse of
a completed task in the demonstrated entrypoint example. Its checkpointer
default is `None` (`:394–427`), passed into the constructed graph at `:557`.
`L/pregel/main.py:2373–2380` uses an inherited configurable checkpointer when
present, otherwise the graph's own one. `L/types.py:428–439` separately
documents node restart and the need for a checkpointer. Thus “node restart
always explains rerunning the already completed task” is not an adequate
diagnosis; checkpointed task reuse and rerunning the interrupted node are
distinct promises/behaviors.

**Admissible actions.** Withhold a definite framework root cause and repair
claim; identify the actual entrypoint/configuration and execution-to-output
binding that must be established. Point out the pasted invocation discrepancy
and propose correction/clarification of the invocation if the outer workflow
was intended, but do not claim that changing `graph` to `parent_graph` has been
tested or is sufficient to fix the reported nested behavior. Request the
actual called object, full configuration/checkpoint identity, prior/resumed
task path or namespace and writes, and the origin/aggregation of the duplicated
interrupt entries. A concrete missing fact is better than blanket uncertainty.

**Authority and alternatives.** Completed-task reuse has `JUSTIFIED` authority
for its documented checkpointed domain. Whether that domain and invocation
actually generated the wrapped report remains `UNKNOWN`. A checkpointer-boundary
or nested task-identity explanation can remain a hypothesis; it is not an
established code defect from this packet. The same displayed interrupt ID twice
does not alone establish two underlying interrupts or duplicate task execution.
An open/closed issue or associated PR state cannot settle that question.

**Disallowed actions.** Silently correct the submitted program and diagnose
that imagined run; assert one specific framework patch as tested; make a
missing-invocation fact prove the reporter never used the parent; or outlaw
normal node restart. Preserve both legal node replay and the separate
checkpointed task-reuse behavior. The selected uncertainty is real in the
external record, not an observation removed by this study.

## E4: the documented state-graph interrupt example

**Consumer/action.** `interrupt` uses the task's ordered resume values; the
resumed node continues after its interrupt returns the supplied value.

`E4/PUBLISHED_EXAMPLE.txt:19–26,33–54` creates a checkpointed state graph,
performs an initial stream and then uses `Command(resume=...)` with the same
configuration. Its printed outputs are published docstring comments, not
observations. This example contains no pre-interrupt external side effect.
Do not invent an execution log or consequence.

`L/types.py:420–439` explicitly states that the first call raises an interrupt,
the graph resumes from the start of the node and re-executes node logic,
resume values match interrupt order and are scoped to a task, and a checkpointer
is required. `:521–540` shows the resume-value lookup and the interrupt when
none is available. These are `PUBLIC_RAW` pinned contract/source bytes, while
the comment outputs remain published-example illustrations.

**Authority and admissible action.** Node restart on resumption is `JUSTIFIED`
under this declared API, so retain it. An exactly-once guarantee for arbitrary
pre-interrupt side effects is a new application requirement, not an established
framework promise. A proposed app may therefore need idempotence, an appropriate
task/persistence boundary or explicit deduplication, but this packet does not
demonstrate such an application defect or verify one solution. It is also
acceptable to distinguish that new desired property as `ASSUMED` until stated
and justified for the application domain.

**Disallowed actions.** Repair the framework merely because node logic restarts;
claim repeated real side effects were observed here; equate repeated node logic
with re-execution of all previously completed checkpointed tasks; or present
published comment outputs as a new run. Removing interruption/resume semantics
or checkpointing without a separately justified contract is not a legal repair.

## Adjudication use, alternatives and eligibility

The first reference supports at least one actionable existing interface claim
(E2), appropriate withholding on a genuinely inconsistent execution record
(E3), and legal retention (E4). E1 adds a directly traceable path together with
an obligation-scope ambiguity; E2 also preserves multiple contributing paths
and explicit authorized override behavior. This meets the fixed roster's
coverage without counting every unit as a discovered defect. These are four
units in two frameworks, not four independent incidents or new target runs.

For an actor answer, evaluate the concrete recommendation together with its
premises. Accept conditional and source-supported alternatives above. An action
label alone is not success. E1's unqualified historical defect label and E3's
specific runtime root cause are reference-unresolved dimensions; mark them as
such, not as known correctness targets. E2's narrower approval-delivery claim
and E4's continuation contract are resolvable. Different authority codes can
be acceptable when their exact scoped obligation differs coherently; do not
grade by string equality or require a maintainer patch.

All eight planned records remain in the eventual table. Missing, partial,
unsupported and contradictory records stay visible. Interventions proposed by
actors remain untested; this reference authorizes no experiment, rerun or
target change. Merge with A only after A's own first record is complete and
retain differences rather than overwriting either first record.

## Narrow integrity check performed before this first record

A static standard-library read checked all 38 entries then present in
`provenance/SOURCE_FILES.json`: bytes and SHA-256 matched for 38/38, at the three
declared commits. This binds local files to the supplied retrieval manifest;
it is not an independent remote-origin attestation or full-repository audit.
All seven `PRESENTATION_TRANSFORMS.json` displayed-file hash records matched.
E2 and E3 program/output blocks are byte-identical to their recorded originals.
E1's AST equals its original after removing only direct print expressions and
empty display-only conditional branches; comments do not enter that AST. Its
configuration, model responses, assignments, calls and union payload remain.
The E4 example was inspected against the fixed `interrupt` docstring and its
display hash matches. No target import or execution occurred. Root must bind
the final input manifest and this first record before dispatch; this check
does not itself satisfy the shared-reference or launch gates.
