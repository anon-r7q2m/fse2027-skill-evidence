# Static decision records

Records are presented in the assigned order: E3, E4, E1, E2. The context receipt was written before any packet read; none of its four project-history flags is true. Public-case training exposure and backend identity are UNKNOWN.

Method: `METHOD_VIEW.md:3-17` defines the seven fields and separates authority from evidence availability; `METHOD_VIEW.md:21-33` governs alternatives and actions. Source bytes support static conclusions, not claims that a program ran. No intervention or target execution was performed. Line ranges below refer to local packet files.

## E3

### 1. Consumer/action

The consumer is the resumed functional workflow deciding whether to reuse the completed `step_1` task result before continuing the interrupted `human_feedback` task. The obligation considered is reuse of a completed task under checkpoint-backed continuation. The repeated interrupt entries are a related reporting observation, not proof of two distinct task executions or human requests.

### 2. Obligation/domain

**JUSTIFIED, conditional on checkpoint-backed execution:** the public entrypoint example says a completed task is not re-executed on resumption because its result is cached by the checkpointer (`input/sources/langgraph_1_0_8/libs/langgraph/langgraph/func/__init__.py:289-298`). A checkpointer supplies persistence across runs (`.../func/__init__.py:260-262`, with the same full source prefix). The example initially invokes and resumes the same workflow with the same thread configuration (`input/sources/langgraph_1_0_8/libs/langgraph/langgraph/func/__init__.py:317-335`).

This is not a guarantee that every statement before an interrupt runs only once. `interrupt` explicitly restarts the node and re-executes its logic; resume values are scoped to a task and matched by interrupt order, and checkpointing is required (`input/sources/langgraph_1_0_8/libs/langgraph/langgraph/types.py:427-440`). A child with checkpointer `None` may inherit its parent's checkpointer (`input/sources/langgraph_1_0_8/libs/langgraph/langgraph/types.py:74-78`). Thus an undecorated-with-saver child in a genuine nested invocation is not, by itself, evidence of missing persistence.

Whether the historically executed nested path met these conditions is **UNKNOWN**. An unconditional “never print again after resume” rule would be **ASSUMED**, not the API contract. The supplied evidence does not establish a separate uniqueness contract for the aggregated interrupt list.

### 3. Boundary path

Two execution descriptions must remain separate:

- **Pasted path:** create saver → attach it to `parent_graph` → nevertheless directly invoke `graph("foo", config)` and `graph(Command(resume="baz"), config)`. Inside `graph`, await `step_1` → `human_feedback` → `step_3`. Only the parent has an explicit saver (`input/E3/PROVIDED_PROGRAM.txt:6-43`). A thread ID is an identifier, not a saver attachment.
- **Reported modification:** invoke `parent_graph` → its body awaits `graph.ainvoke(input_query)` → child task/checkpoint and interrupt paths → resumed parent/child execution. This is asserted in `input/E3/CASE.md:3-7` and represented by the wrapper body at `input/E3/PROVIDED_PROGRAM.txt:35-38`, but not by the pasted call sites.

Checkpoint selection can consume inherited configuration before falling back to the graph's own saver (`input/sources/langgraph_1_0_8/libs/langgraph/langgraph/pregel/main.py:2373-2380`). The resume input check rejects `Command(resume=...)` without a checkpointer (`input/sources/langgraph_1_0_8/libs/langgraph/langgraph/pregel/_loop.py:638-644`). A separate reporting path accumulates interrupt payloads using `interrupts.extend(ints)` (`input/sources/langgraph_1_0_8/libs/langgraph/langgraph/pregel/main.py:3182-3187`); this does not establish where duplicate payloads originated.

The earliest evidenced mismatch is the outer-invocation claim versus the actual call sites. It precedes any justified attribution to task-cache or namespace internals.

### 4. Available facts

- **E3-P1 — PUBLIC_RAW program:** `graph` uses `@entrypoint()`; `parent_graph` uses `@entrypoint(checkpointer=checkpointer)`; both actual calls use `graph`, with thread ID `"1"` (`input/E3/PROVIDED_PROGRAM.txt:27-43`). `step_1` prints before returning `"<input> bar"`; `human_feedback` prints before interrupting (`input/E3/PROVIDED_PROGRAM.txt:8-19`).
- **E3-P2 — REPORTED_ONLY behavior:** baseline shows `Running step 1` once, `Running step 2` twice, and final `foo bar baz qux` (`input/E3/REPORTED_BASE_OUTPUT.txt:1-6`). Wrapped output shows both step 1 and step 2 twice, then the same final string (`input/E3/REPORTED_WRAPPED_OUTPUT.txt:1-7`). The output files are public bytes, but their association with actual executions is not independently substantiated.
- **E3-P3 — reported duplicate value:** both entries in the wrapped interrupt list have the same prompt and ID `0a61aa843e230733f749283420b28924` (`input/E3/REPORTED_WRAPPED_OUTPUT.txt:3`). The baseline ID is `4269efa37f6079cd4e24b2524750dc4f` (`input/E3/REPORTED_BASE_OUTPUT.txt:3`). Different runs' IDs do not establish checkpoint identity across executions.
- **E3-P4 — PUBLIC_RAW contracts/source:** checkpoint requirement, node replay, inheritance, and resume rejection are cited above. The report names LangGraph 1.0.8 and the packet provides its pinned source, but explicitly has not verified outputs (`input/E3/CASE.md:15-18`).

Missing facts include the exact executed initial and resume call sites, their effective inherited configuration, checkpoint/task identities and saved writes, and interrupt stream provenance. No checkpoint trace is supplied.

### 5. Alternatives

- **SUPPORTED for the pasted program:** the saver-bearing wrapper is bypassed (E3-P1, P4). Discriminator: the executed callable and effective saver on both calls. The pasted calls confirm bypass; they do not establish the callable used in the reported run. Under the pasted standalone configuration, the successful reported resume is inconsistent with the source's no-checkpointer rejection.
- **SUPPORTED as legal behavior:** repetition of `human_feedback`'s pre-interrupt print on resume follows node/task restart semantics (E3-P1, P2, P4). Discriminator: whether the repeated operation belongs to the interrupted task or an already completed separate task. This explains step 2, not automatically step 1.
- **UNRESOLVED:** a genuine nested task-result restoration or identity problem causes step 1 to run again (E3-P2, P4). Discriminator: consistent wrapper call sites plus saved completed-task writes and resumed lookup identities. Those observations are absent. Missing explicit child saver alone does not prove this explanation, because inheritance is legal.
- **UNRESOLVED:** repeated delivery/aggregation of one interrupt contributes to the duplicate list (E3-P3, P4). Discriminator: per-task exception and stream-emission records. Identical IDs and append-style aggregation are compatible with this explanation but do not prove the producer path. The inference that the list proves two independent human-feedback tasks is unsupported.
- **SUPPORTED as an evidence inconsistency; exact cause UNRESOLVED:** pasted code and outputs refer to different effective programs/configurations (E3-P1–P4). A transcription omission or unreported setup could explain it; neither is established.

### 6. Correction/control

**Proposed, not tested:** align a future reproducer's actual initial/resume calls with the intended checkpoint-bearing entrypoint, preserving saver and thread continuity. If the intended subject is the base workflow, explicitly configure persistence on that actual workflow; if it is the nested workflow, consistently invoke the parent and retain the nested path. These are distinct diagnostic configurations, not silent repairs to this packet.

Restore the demonstrated invocation/configuration boundary before judging the reported cache failure. Withhold a framework cache or interrupt-deduplication repair verdict until the actual executed path and trace are available. Preserve legitimate interrupted-node replay and child checkpoint inheritance; do not suppress required feedback execution merely to remove repeated prints. Correcting the pasted calls would not itself prove resolution of the separately reported wrapper behavior.

### 7. Endpoint/limits

The local reported endpoint is `foo bar baz qux`, with the extra prints and duplicate list described above. The static endpoint for the pasted standalone resume path is the no-checkpointer rejection condition, not a demonstrated successful continuation. Neither establishes general nested-workflow correctness or failure. No tested fix, recovered execution, or independently demonstrated task success is claimed.

## E4

### 1. Consumer/action

The consumer is `interrupt` during the resumed `node`: it selects the supplied resume value and permits the node to print and return `human_value`. The decision is whether this initial-call/resume sequence needs a behavioral correction.

### 2. Obligation/domain

**JUSTIFIED:** checkpoint-backed interruption surfaces the prompt, halts execution, then accepts a `Command` resume value while restarting the node from its beginning (`input/sources/langgraph_1_0_8/libs/langgraph/langgraph/types.py:420-440`). The applicable domain is the published single-node example using the same graph, saver, and configuration for both stream calls. Resume-value matching is task-local and ordered, not arbitrary cross-task sharing.

A promise of continuation at a suspended Python instruction without replay, exactly-once execution of arbitrary pre-interrupt side effects, numeric age validation, or durable survival across process loss is **ASSUMED** if added to this example. None is supplied as an application obligation in `input/E4/CASE.md:17-21`.

### 3. Boundary path

Initial state `{"foo": "abc"}` → compiled state graph with `InMemorySaver` and one configured thread → `node` → `interrupt("what is your age?")` → exception/prompt surfaced to client. Separately, client resume command with the same configuration → restored task re-enters `node` → interrupt-index lookup consumes the resume value → print → return `{"human_value": answer}` (`input/E4/PUBLISHED_EXAMPLE.txt:19-54`).

The implementation retrieves the task scratchpad, counts the interrupt index, returns an already recorded indexed resume or consumes a current resume value, and otherwise raises `GraphInterrupt` (`input/sources/langgraph_1_0_8/libs/langgraph/langgraph/types.py:519-543`). The unused local `command` assignment does not prevent resumption: line 50 constructs and passes an equivalent command directly.

### 4. Available facts

- **E4-P1 — PUBLIC_RAW example:** checkpointer attachment is explicit at `input/E4/PUBLISHED_EXAMPLE.txt:33-35`; one `config` is used at lines 43 and 50. The print is after `interrupt`, not before it (lines 19-26).
- **E4-P2 — PUBLIC_RAW contract/implementation:** restart and matching rules are at `input/sources/langgraph_1_0_8/libs/langgraph/langgraph/types.py:431-440`; the return/raise branches are at lines 523-543.
- **E4-P3 — published illustration, not observation:** output comments show an interrupt followed on resume by the supplied string and a node update (`input/E4/PUBLISHED_EXAMPLE.txt:46-54`). Their status is explicit in `input/E4/CASE.md:3-14`.

There is no incident trace or added pre-interrupt external side effect. Availability of example/source bytes does not turn comment output into a measured run.

### 5. Alternatives

- **SUPPORTED:** restart/replay is intended continuation semantics (E4-P1, P2). Discriminator: API statement and placement of logic relative to interrupt; both support restart and reaching the print only after a resume value is available.
- **CONTRADICTED as a contract interpretation:** all node logic must execute only once or resume must jump past the call without re-entry. E4-P2 explicitly says otherwise. An application's newly specified side-effect requirement would be a separate matter.
- **CONTRADICTED for this supplied configuration:** checkpoint attachment or same-config resume is missing (E4-P1). Actual persistence availability in a future integration remains a condition, not a measured fact here.
- **UNRESOLVED as an application need:** the age answer should be validated or side effects should be made idempotent. Discriminator: an explicit integrator requirement and actual added operations. Neither is supplied. The arbitrary example string is permitted by `interrupt(value: Any) -> Any` (`input/sources/langgraph_1_0_8/libs/langgraph/langgraph/types.py:420`).

### 6. Correction/control

**Retain behavior.** Use the documented saver/configuration and `Command` sequence. No framework patch is warranted by this example. If an integration later introduces pre-interrupt side effects, assess those operations under separately stated replay/idempotence requirements; this is not an observed defect in the provided node. Preserve node restart, task-local resume matching, and arbitrary resume values where no application validator is required.

### 7. Endpoint/limits

The specified local result is that `answer` receives `"some input from a human!!!"`, after which the print and `human_value` update are reachable. The published comments illustrate this; no run demonstrated it in this study. There is no evidence of a failed business task, duplicate external effect, or need to guarantee exactly-once execution generally.

## E1

### 1. Consumer/action

The consumer is the non-streaming response-dispatch path deciding whether to process the native structured text as final output before executing the accompanying `search_documents` call. The proposed obligation being evaluated is that `end_strategy="early"` must suppress that function call merely because potentially valid native-output text accompanies it.

### 2. Obligation/domain

The constructor describes `end_strategy` broadly as handling tool calls requested alongside a final result (`input/sources/pydantic_e1/pydantic_ai_slim/pydantic_ai/agent/__init__.py:386-387`). However, the same class's field documentation specifically says “alongside an output tool” (lines 212-216). The detailed versioned documentation likewise scopes its strategy table to output-tool calls: under `early`, function tools are skipped when an output tool succeeds and run when outputs fail (`input/sources/pydantic_e1/docs/output.md:365-388`).

**JUSTIFIED** in that output-tool domain: skip function calls after successful output-tool selection. **UNKNOWN/ambiguous** for a mandatory extension to mixed native-text/function-call responses in this non-streaming operation. Treating the broader constructor phrase alone as a universal text-first ordering rule is insufficient against the narrower detailed contract. Imposing such ordering as a new requirement would be **ASSUMED** until explicitly adopted. A valid-looking `TextPart` and an already accepted final result are different states.

### 3. Boundary path

`FunctionModel` callback produces a `ModelResponse` containing both text and a function call → response dispatcher accumulates text and tool calls in separate variables → nonempty tool-call branch invokes `_handle_tool_calls` and returns before reaching text processing → tool processor receives `final_result=None` → absent a successful output tool, the function call can execute → its result prompts another model request → text-only response reaches native text processing and validation.

The relevant code is `input/sources/pydantic_e1/pydantic_ai_slim/pydantic_ai/models/function.py:127-158`, `input/sources/pydantic_e1/pydantic_ai_slim/pydantic_ai/_agent_graph.py:1239-1299`, `.../_agent_graph.py:1334-1349`, `.../_agent_graph.py:1368-1396`, and `input/sources/pydantic_e1/pydantic_ai_slim/pydantic_ai/_tool_execution.py:879-904` (ellipses here retain the same fully specified Pydantic E1 source directory).

The schema path is independent: `NativeOutput` → flatten union → `UnionOutputProcessor` → structured text processor (`input/sources/pydantic_e1/pydantic_ai_slim/pydantic_ai/_output.py:486-508`, lines 617-628 and 692-734). The earliest evidenced selection boundary is the tool-first dispatch, before first-response text validation. This is not evidence that `early` was omitted from configuration.

### 4. Available facts

- **E1-P1 — PUBLIC_PROJECTION:** the example's operational statements are preserved while display verdicts/comments were removed (`input/E1/CASE.md:16-21`). It configures `FunctionModel`, `NativeOutput(Response | Clarification)`, and explicit `early` (`input/E1/PROVIDED_PROGRAM.txt:73-78`), then calls `agent.run` (line 99), not a streaming run.
- **E1-P2 — supplied payload:** first response contains `{"result":{"kind":"Response","data":{"topic":"contact info","response":"You can contact us at support@example.com"}}}` plus `search_documents`, two query paraphrases, and ID `tooluse_abc123`; subsequent responses contain the same text alone (`input/E1/PROVIDED_PROGRAM.txt:47-69`). The tool sets `tool_was_called=True` and returns `"some documents"` (lines 25-35).
- **E1-P3 — PUBLIC_RAW schema:** the native union uses `result`, `kind`, and `data`; keys derive from object/type names and inner data is validated against the selected member (`input/sources/pydantic_e1/pydantic_ai_slim/pydantic_ai/_output.py:1064-1118`, lines 1129-1157 and 1183-1198). The `Response` declaration requires the two strings that are present (`input/E1/PROVIDED_PROGRAM.txt:15-21`). Thus static inspection supports compatibility with the supplied union wrapper; stripping it would not be a justified repair.
- **E1-P4 — PUBLIC_RAW selection:** the dispatch and early-tool processing branches are cited above. No final native-text result is passed into the first tool-processing invocation.
- **E1-P5 — REPORTED_ONLY:** the report says the tool ran; there is no raw provider trace and no rerun. The inspection snapshot is not a recovered reporter checkout; the environment mentions Bedrock but this example uses `FunctionModel` (`input/E1/CASE.md:3-14`).

### 5. Alternatives

- **SUPPORTED for the snapshot:** tool-first dispatch bypasses first-response native text processing (E1-P1, P2, P4). Discriminator: whether `_handle_text_response` is reached before function execution. The source takes the tool branch and returns first. This explains the report without requiring a provider fault.
- **CONTRADICTED for the supplied schema:** the preserved union envelope is inherently malformed (E1-P2, P3). Discriminator: generated envelope keys and member fields; these match. Actual validation events are not recorded, but malformed-envelope rejection cannot explain a branch that never tries first-response text validation.
- **CONTRADICTED for the supplied configuration:** missing `early`, text/tool order in the parts list, or the default strategy explains the call. `early` is explicit, text is first, and dispatch tests for any tool call (E1-P1, P2, P4).
- **UNRESOLVED as a historical claim; unsupported for this supplied callback:** Bedrock transformed the response or the historical revision behaved differently (E1-P5). Discriminators: exact reporter revision and provider request/response trace. They are absent; the function callback supplies both parts directly.
- **UNRESOLVED contract interpretation:** `early` should commit valid native text before any tool. The broad constructor language supports the expectation, but the detailed output-tool scope and explicit tool-first implementation oppose treating it as an established universal obligation. This ambiguity coexists with the supported static mechanism.

### 6. Correction/control

**Narrow/clarify the requirement before enforcing a framework change; withhold an unconditional defect verdict.** Document the distinction between mixed native-text dispatch and successful output-tool selection. On the detailed supplied contract, the observed static tool-first path can be retained.

If native-text-first termination is explicitly adopted, the proposed change belongs at response selection: validate and accept eligible structured text before selecting function work under the agreed domain. That is a conditional design proposal, not a tested fix or a historical obligation established here. It must not terminate merely on arbitrary narrative text, invalid/incomplete structured data, failed output validation, or text describing intended tool use. Preserve required tools when no output succeeds, existing `graceful`/`exhaustive` semantics, and separately documented streaming behavior. Do not repair the example by flattening its valid union envelope or changing output mode and then claim the same operation was fixed.

### 7. Endpoint/limits

The report's local observation is tool invocation. The snapshot statically supports that branch and a subsequent text-only validation opportunity; successful final completion, request count, and exact historical behavior are not independently measured. No provider-wide failure, tested repair, or proof that every native-text response should preempt tools follows.

## E2

### 1. Consumer/action

The consumer is the approval recipient of `DeferredToolRequests.approvals`, deciding whether to approve the particular deferred `transfer` call. The obligation is delivery of the validated arguments through that approval boundary. The later execution value matters as evidence of which argument object execution consumes, but this record does not assume a blanket ban on argument rewriting.

### 2. Obligation/domain

**JUSTIFIED in the supplied versioned API:** deferred approval requests contain tool name, **validated arguments**, and unique call ID (`input/sources/pydantic_e2/docs/deferred-tools.md:93-106`). The capability hook is explicitly allowed to modify validated arguments; its returned arguments also apply when validation defers (`input/sources/pydantic_e2/pydantic_ai_slim/pydantic_ai/capabilities/abstract.py:703-720`; `input/sources/pydantic_e2/docs/capabilities/custom.md:575-581`). Therefore the approval boundary must not substitute the original raw argument object for the hook's validated result in this operation.

The stronger claim that execution arguments may never differ from initially displayed arguments is not this API's unconditional contract: `ToolApproved.override_args` explicitly supplies replacement arguments (`input/sources/pydantic_e2/pydantic_ai_slim/pydantic_ai/_deferred.py:99-104`), and `before_tool_execute` may modify them (`input/sources/pydantic_e2/pydantic_ai_slim/pydantic_ai/capabilities/abstract.py:765-778`). Permission for hooks is **JUSTIFIED**, but permission from the actual approver for this specific 100→50 change is **UNKNOWN**. No `ALLOWED_ADAPTATION` label is assigned to the historical event: its actual authorization and retained application obligations are missing.

### 3. Boundary path

Model's reported `amount=100` call → tool registered as `requires_approval=True`, hence kind `unapproved` → argument validation → `Rewrite.after_tool_validate` returns a fresh dictionary with `amount=50` → `ValidatedToolCall` carries the original call and separate validated arguments.

The delivery and execution paths then diverge:

- Approval collection uses `validated.args_valid` as its admission check but emits the original `call` and appends that original call to the deferred list. `DeferredToolRequests.approvals` receives that list, not `validated.validated_args` (`input/sources/pydantic_e2/pydantic_ai_slim/pydantic_ai/_tool_execution.py:798-843`).
- On approved continuation, optional `override_args` replaces the call arguments, then `validate_tool_call(..., approved=True)` runs validation/hooks again (`input/sources/pydantic_e2/pydantic_ai_slim/pydantic_ai/_tool_execution.py:448-480`). Execution consumes the validated arguments via execute hooks and the toolset call (`input/sources/pydantic_e2/pydantic_ai_slim/pydantic_ai/tool_manager.py:376-395`, lines 850-853 and 865-884).

The first evidenced relevant mismatch is the post-hook validated result not being delivered at approval collection. The boolean validation status and the displayed original arguments are distinct data. Revalidation on resume coexists with this delivery problem; banning revalidation would not be a justified substitute for fixing it.

### 4. Available facts

- **E2-P1 — PUBLIC_RAW partial example:** the hook returns `{**args, 'amount': 50}` for a dictionary containing `amount`; the tool appends its received amount and returns a string (`input/E2/PROVIDED_PROGRAM.txt:1-16`). The hook constructs a new dictionary rather than mutating `call.args` in place.
- **E2-P2 — REPORTED_ONLY:** display `{'amount': 100}` and execution `amount=50` (`input/E2/REPORTED_VALUES.txt:1-2`). The reported model call is 100 (`input/E2/CASE.md:3-6`).
- **E2-P3 — PUBLIC_RAW implementation:** registration sets `kind='unapproved'` for approval-required tools (`input/sources/pydantic_e2/pydantic_ai_slim/pydantic_ai/tools.py:506`). Validation reads arguments and returns a dictionary (`input/sources/pydantic_e2/pydantic_ai_slim/pydantic_ai/tool_manager.py:281-304`), runs the hook (lines 324-359), and retains `call` and `validated_args` separately (lines 443-458). Collection appends `call` (`input/sources/pydantic_e2/pydantic_ai_slim/pydantic_ai/_tool_execution.py:801-812`). Combined capabilities pass along each hook's returned arguments (`input/sources/pydantic_e2/pydantic_ai_slim/pydantic_ai/capabilities/combined.py:458-469`).
- **E2-P4 — PUBLIC_RAW contracts:** validated approval arguments, permitted hook changes, and explicit approval overrides are cited above.
- **E2-P5 — scope:** `model`, `executed`, initial run, approval UI code, decision object, original message history, and resume calls are not supplied as a complete executable sequence. The reference snapshot is time-selected, not an attested reporter revision (`input/E2/CASE.md:8-17`).

The packet supplies no actual call ID, `DeferredToolRequestsEvent`, approval/denial or override payload, resume event, or execution trace. The tool body itself evidences a list append and returned string, not a real financial transfer.

### 5. Alternatives

- **SUPPORTED statically:** approval collection delivers original 100 while the validated result is 50 (E2-P1, P3). Discriminator: original `call.args` versus `validated.validated_args` at collection. The source retains the former for delivery even though the hook produced the latter; this is sufficient to identify the snapshot's boundary inconsistency under E2-P4.
- **CONTRADICTED as a necessary explanation:** the hook only runs after human approval. Initial deferred collection calls validation, whose hook runs before collection (E2-P3). The later approved path runs it again. No recorded runtime invocation count is inferred from this static fact.
- **SUPPORTED as a legal contributor, conditional on successful approved continuation:** the hook's 50 reaches execution (E2-P1, P3, P4). Discriminator: the actual approved input and validated execution arguments. The implementation provides this route, and the report is compatible with it; the missing continuation prevents calling it a demonstrated historical trace.
- **UNRESOLVED historically:** a UI independently displayed raw model arguments instead of the deferred request, or an approver explicitly supplied an override (E2-P2, P5). Discriminators: delivered request object, UI mapping, approval payload and call ID. None is present. These possibilities do not erase the independently supported collection mismatch in the snapshot.
- **CONTRADICTED as a general API obligation:** every post-validation rewrite is forbidden, or any display/execution difference necessarily proves unauthorized action (E2-P4). Hooks and approval overrides expressly permit changes. The actual application may require stricter binding, but no such complete policy is supplied.
- **UNRESOLVED:** historical version differences or hidden custom hooks alter this mechanism (E2-P5). Discriminators: exact revision and complete capability/model configuration. The time-selected source cannot establish their absence.

### 6. Correction/control

**Proposed framework delivery correction, not tested:** construct deferred approval information from the post-hook validated arguments while retaining tool name, call ID, and relevant metadata; avoid treating `args_valid=True` on the original call as sufficient evidence that its argument payload is the validated payload. Preserve a raw model-call representation where needed for history, but do not present it as the effective validated approval request. The corresponding resume/history linkage must be reviewed so the request approved and the call continued remain correlated; this is a design requirement, not an implemented patch.

Keep argument-transforming hooks, rejection/retry behavior, approval denials, and explicit `ToolApproved.override_args` legal. Do not “fix” the mismatch by deleting the hook, forcing every transfer to 100, or skipping validation. Supplying effective validated arguments at approval addresses the evidenced boundary; it does not guarantee immutability after arbitrary later hooks. If this application requires exact approval-to-execution argument binding, specify its override/transform permissions and require reapproval or rejection of unauthorized later changes under that new policy. That stronger control is conditional and untested, not inferred retroactively from a function named `transfer`.

### 7. Endpoint/limits

The reported local discrepancy is approval display 100 versus execution 50. The supplied implementation supports a concrete mechanism and a versioned delivery-contract mismatch, conditional on the described call reaching the normal deferred path. The partial program and missing approval continuation prevent independently establishing the historical execution, approver intent, or business outcome. No actual transfer, safety incident, completed repair, or tested fix is claimed.

## Access and completion disclosure

- **35 read/search commands**, including the one file-discovery command. Each used one simple command per execution, through one `functions.exec` wrapper calling one `exec_command`; there were no batched independent reads, pipelines, or read scripts. Pure writes to this output directory are excluded: the initial receipt and this final analysis.
- Access/budget violations: **none identified**. Reads were limited to `METHOD_VIEW.md` and `input/`. No parent directories, memory, participant material, external references, credentials, runtime configuration, event logs, or launch metadata were inspected. The packet's `langgraph/config.py` source module was included in one static source search; no operating-system or credential configuration was read. One search output was truncated; no conclusion depends on its unseen portion. The work remained within the 40-command and 20-minute allowances.
- Uncompleted records: **none**. All four records contain seven fields in the assigned order. Unresolved historical questions are explicitly retained rather than filled in.
- Interventions actually run: **none**. No input was edited; no target, import, fixture, test, grader, provider, model, network request, installation, container, experiment, or delegated analysis was run. All corrections are proposals; all execution claims are either reported observations or clearly identified static predictions.
