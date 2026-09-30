# Combined reference before actor dispatch

Study: `decision_transfer_use_v1`  
Prepared: 2026-09-29  
Status: `REFERENCE_CONTENT_READY_PENDING_ROOT_FREEZE`

This document combines the two separately completed first records. It is an
admissible-action reference for static analysis, not actor output, a newly
discovered defect set, an executed intervention result or a benchmark score.
The original first records remain unchanged and are part of the final freeze.

## Independence and byte confirmation before sharing

Before B opened A's first record, both files were read for their hashes and
matched the previously announced completed bytes:

| First record | SHA-256 |
| --- | --- |
| `REFERENCE_A.md` | `cf25cc90177ec480e6c1122e4f7e01ff5296b6fba7644fde8cefcf9b93930f80` |
| `REFERENCE_B.md` | `e999fc6817ec75675498af8808e517e9901c7f8479c78822bbfd39a933ba50f1` |

A's first-record receipt is dated `2026-09-29T16:53:50.812237+00:00`. B had
completed and announced its matching first-record hash before receiving that
notice. A and B each state that they did not read the other's first record or
actor output before completion. Candidate selection and some source facts were
discussed earlier; neither reviewer is a blind external participant. B's first
shared read occurred only after root authorized it. Root reported that no actor
had yet been dispatched; B has not opened any actor output.

The final supplied `provenance/INPUT_MANIFEST.json` has SHA-256
`9fa7bdf683b0f2161557b16a93efe72e0cd95254ee26b8849dde799cc2448c8d`.
B checked its complete path inventory and every file hash/size: exactly 51
files, no missing or extra file, and no mismatch. Its 38 complete source,
documentation and license files use the three declared pins. E1/E2 are
inspection snapshots, not recovered reporter checkouts; E3/E4 share the
reported 1.0.8 source family. Projection and source-origin limitations remain
those recorded in the source manifest and selection ledger.

## How to apply this reference

Use the seven worksheet fields and protocol's action judgments. An actor need
not use these words, mention every supporting detail, choose a particular
patch or reproduce the source reviewers' search. Require the decisive premises
for the actor's actual action. Missing secondary detail is recorded separately
from a contradicted recommendation. A plausible partial repair can be reported
as partial; it is not proof of an end-to-end invariant.

An answer can be `SUPPORTED` for justified retention or withholding. An action
contradicted by applicable evidence is `CONTRADICTED`; insufficient support is
`INSUFFICIENTLY_JUSTIFIED`. Where the reference cannot settle a claimed runtime
cause or historical obligation, retain `REFERENCE_UNRESOLVED` for that dimension.
Do not convert missing authority into a required bug label. Do not count matching
labels without evidence as scientific success. All eight planned records,
including partial, missing and access-limited ones, remain in the final table.

The source pointers and detailed alternatives in both first records remain
available to adjudicators. The minimal per-unit requirements below take
precedence over treating all their explanatory prose as a checklist.

## E1: native structured output, function calls and early policy

**Resolvable facts.** The packet's native union envelope is consistent with
the pinned `result/kind/data` schema. The graph's mixed-response path dispatches
tools and returns before text processing; the tool processor receives
`final_result=None`, so its early strategy has no accepted native result on
that path. These are static source facts. The actual report's execution and
checkout remain unverified. The API field/EndStrategy/output-tool documents
use narrower output-tool language; the constructor describes a final result
more broadly. This is a real authority-scope ambiguity in actor-visible bytes.

**Acceptable alternatives.**

1. Explain the source path and withhold an unconditional historical defect
   verdict while requesting native-mode policy clarification.
2. Retain behavior under the explicit output-tool reading, acknowledge the
   report's different intended use, and recommend clarification rather than
   claim that native early return is inherently invalid.
3. Propose a mode-specific change to recognize successfully validated native
   output before function dispatch under an explicitly justified/intended
   early-native obligation. A repair-oriented reading of the broader
   constructor is acceptable with the scope qualification. This is proposed,
   not tested, and is not a uniquely mandatory implementation.

**Minimum premises.** Distinguish the native text path from output-tool final
results, identify the demonstrated ordering or equivalent boundary, and state
the authority/domain used for the action. Source citations that actually carry
those premises suffice; literal line-number equality is not required.

**Do not accept as established.** Any text means success; all function calls
must be skipped regardless of validation; the wrapper must be rewritten;
Bedrock/provider behavior was the demonstrated cause; every end strategy or
streaming method must behave identically; or the original incident/fix was
reproduced. Invalid-output fallthrough, absent-final-output calls and separate
graceful/exhaustive policies remain legal. Hidden later regression details
cannot become compulsory actor facts.

**Reference-unresolved dimension.** A single unambiguous historical
early/native contract and the actual original run. Do not score a binary
historical bug label as though these were settled.

## E2: approval information and later validated execution

**Resolvable facts and authority.** The pinned deferred-tool documentation
promises validated arguments in approval requests. The supplied hook returns
a new argument dictionary with 50. The inspected approval collection validates
but retains the original call object; resumed approval validates the original
or explicitly overridden call again, and execution consumes validated values.
The stated 100/50 values are reported, not newly measured. Explicit
`ToolApproved(override_args=...)` is permitted; preserving original model
history is distinct from showing effective approval arguments.

**Acceptable alternatives.** Diagnose the narrow documentation/source
inconsistency and propose a separate/copied effective-argument representation
with stable call identity and an explicit continuation policy. A binding,
comparison/reapproval step, immutable approved representation or another
authority-supported design may be proposed. No unique field or patch is gold.
A proposal that fixes only outward presentation can be supported as a partial
repair if it does not assert coherence for arbitrary later-changing hooks.
An actor may withhold historical reproduction while still acknowledging the
visible static mismatch and recommending missing captures.

**Minimum premises.** Cite the validated-argument promise, the distinction
between the outward call and validated representation, and the resumed
transformation relevant to the asserted consequence. Preserve the original
model record and explicitly sanctioned overrides. Two interacting paths
explain the mismatch; neither all hooks nor revalidation alone becomes an
independently established defect.

**Do not accept as established.** Blanket prohibition of argument overrides
or validation hooks; silently removing approval or corrupting call-ID/history
bindings; rewriting history as though the model generated 50; moving a rewrite
later and declaring the complete obligation solved; a real financial transfer;
an externally exploitable authorization breach; or a tested repair. Changing
the documentation's promise is a proposed contract change requiring authority,
not retroactive satisfaction of the existing promise.

**Reference-unresolved dimension.** Exact reporter checkout and full observed
UI/continuation; universal guarantees about arbitrary execution hooks. These
limits do not erase the narrower source-resolvable presentation issue.

## E3: reported nested resume and the pasted invocation

**Resolvable facts.** The pasted code defines the checkpointed `parent_graph`
but invokes the bare `graph` at both bottom-level calls. The report describes
an outer invocation. Reported before/after outputs are not bound to an
independently captured execution of those pasted bytes. The pinned functional
API documents reuse of completed checkpointed tasks, distinct from restarting
the interrupted node. An absent-checkpointer resume guard is visible in
`pregel/_loop.py:639–644`.

**Acceptable alternatives.** Withhold a specific nested-framework cause or
repair verdict, name the invocation/configuration/trace correspondence gap,
and request the actual called graph plus effective checkpoint/task identity.
An actor can make a separately labeled static prediction about the pasted
no-checkpointer invocation if it cites the supporting path. It can also
propose checking/correcting the invocation if the parent was intended, or
retain hypotheses about nested checkpoint identity and duplicate propagation.
Those are conditional investigations, not a recovered original execution or
a tested fix.

**Minimum premises.** Identify the concrete code-versus-description mismatch
and distinguish completed task reuse from ordinary interrupted-node replay.
Preserve uncertainty about which actual execution produced each reported
symptom. Specific necessary missing facts matter more than generic abstention.

**Do not accept as established.** Silently substitute `parent_graph`, blame
one framework function with certainty, claim all completed-task reruns are
normal because node restart is documented, or infer two underlying interrupt
events solely from two displayed entries. Conversely, the pasted discrepancy
does not prove the reporter never used the parent elsewhere.

**Reference-unresolved dimension.** The runtime origin of the wrapped output
and a definitive nested-framework root cause. These are not mandatory
defect-discovery targets.

## E4: documented node restart and resume-value delivery

**Resolvable facts and authority.** The pinned `interrupt` API explicitly
restarts the node and uses task-scoped ordered resume values. The published
example enables a checkpointer and resumes with the same configuration.
Its print lies after the interrupt; it contains no pre-interrupt external
side effect. Comment outputs are documentation illustrations, not this
study's observations.

**Supported action.** Retain the specified continuation behavior. An
application's desired exactly-once property for side effects would require a
separately stated obligation; conditional discussion of idempotence,
deduplication or persisted task boundaries is allowed but remains a proposal.
It must not be presented as an observed defect or verified repair of this
example. Correctly separate this node behavior from E3's completed-task reuse.

**Do not accept as established.** Documented restart alone is a defect; all
previous tasks must re-execute; globally skipping nodes is a justified repair;
real duplicate side effects occurred in this example; or its comment outputs
were observed by the study. There is no new field incident in E4.

## Differences retained rather than forced into one answer

The first records contain no identified direct contradiction in their required
actor-visible facts. Their different emphases are retained:

| Point | A's emphasis | B's emphasis | Combined treatment |
| --- | --- | --- | --- |
| E1 action | Explicitly permits narrow-contract retention or conditional extension | Explicitly permits a qualified repair-oriented reading of the broader constructor | Keep retention, withholding and conditional repair; require the actual scoped premise |
| E1 later change | Records later merged implementation/prose limitations | Uses only actor input for the first verdict | Later facts constrain author claims, never add hidden actor obligations |
| E2 partial intervention | A copied outward request alone need not settle changing-hook continuation | Revalidation is a contributor, not by itself another defect | Preserve partial credit/limits; no universal success from one boundary change |
| E3 static consequence | Notes the explicit no-checkpointer resume guard | Foregrounds unresolved execution-to-output binding | Accept a qualified static prediction while withholding the historical root cause |

No majority vote or averaging converts authority ambiguity into certainty.
Future adjudication must retain any new reference disagreement explicitly.
If a genuine reference error is discovered after actor output, preserve this
frozen record and mark the affected comparison ungradable; do not rerun or
change the expected answer after seeing it.

## G1/G2 preparation conclusion

**G1: met for the bounded purpose.** The four purposively selected external
units supply an actionable documentation/source claim, legal retention,
genuine missing execution evidence, and conditional/multiple-path reasoning.
They were not the worksheet's formation cases. Do not call them a random
sample, four independent failures, a field deployment study or new discoveries.

**G2: content ready; root's exact-byte freeze remains required.** Input files,
method view/projection, prompts/orders, protocol, both unchanged first
references and this combined reference are prepared. B checked the two actor
prompts against the protocol: they contain no unit-specific reference answer,
use the fixed orders and budgets, disclose the generic method illustration
through the unchanged view, and state the no-OS-sandbox access/audit limit.
Root must bind all of these bytes together before dispatch. Neither this
document nor the input manifest is a launch receipt. G3 belongs to root's
fresh-context launch configuration; no actor or target is executed by this
reference work.
