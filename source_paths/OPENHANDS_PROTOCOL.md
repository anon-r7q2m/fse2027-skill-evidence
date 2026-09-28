# OpenHands path protocol, frozen before fixture execution

Revision: `34bf9c2579ca5a25e452583eed38c6c0e45cebd6`. This history-to-CodeActAgent
consumer path was already exposed in the September 11 source review. The
present contribution can only be additional fixed local controls. There are
exactly four conditions; no replacement path or fabricated adaptation.

## Obligations and source map

**O1: retain paired command observation meaning.** For a command observation
with a known status and matching agent tool call, the next tool message retains
the command observation's formatted content, including its exit status, and
the correct tool-call ID. Basis: `CmdOutputObservation.to_agent_observation`
appends a known exit code; `ConversationMemory._process_observation` documents
formatting command results with exit codes and creates a tool reply with the
original metadata identity. We do not require an unknown status (`-1`) to be
invented or require unbounded content retention.

**O2: only complete tool-call groups enter the model input.** Pending groups
wait until every called tool has a reply; orphan replies do not enter final
messages. Basis: `process_events` checks all pending tool-call IDs before
adding a group, and `_filter_unmatched_tool_calls` explicitly promises matching
calls and results. Temporarily omitting an incomplete asynchronous group is a
legal boundary, not lost evidence by definition.

Path: controller event ingestion -> retained history -> NoOp view ->
`CodeActAgent._get_messages` -> `ConversationMemory.process_events` ->
observation formatting/pairing/filtering -> `CodeActAgent.step` completion input.
The local default `AgentConfig` selects NoOp condensation. We retain an ordinary
system/user prefix and use no truncation, vision, microagents, or prompt cache.

## Native slices and mock boundaries

Execute unchanged AST method bodies of `AgentController._on_event`,
`CmdOutputObservation.to_agent_observation`, `ConversationMemory` processing,
`truncate_content`, and CodeActAgent message construction/step. Event/message
data carriers, NoOp view, state tracker, controller scheduling, model message
serialization and response are minimal mocks. No tool command, model,
container, or event persistence is executed. The completion sink records the
exact messages it receives. Full runtime metadata production, asynchronous
scheduler behavior and provider transport remain unknown.

## Frozen conditions

| ID | Retained input events | Expected O1 | Expected O2 |
|---|---|---|---|
| O-A | One complete tool pair; command output `''`, status `0` | supported: known zero status survives formatting and consumption | supported |
| O-B | One complete tool pair; command output `''`, status `1` | supported: known nonzero status survives despite empty raw content | supported |
| O-C | One assistant response calls tools `call-a` and `call-b`, only `call-a` has replied | not_applicable until group completion | supported if neither partial tool group enters the next input |
| O-D | A command reply with `call-orphan` and no corresponding assistant call in retained history | not_applicable for paired-result use | supported if orphan reply is omitted |

The last two are legal synthetic event-boundary fixtures, not alleged native
bugs. Report whether the controller would normally schedule such a step as
unknown; forcing a next-input construction tests the boundary only.

## Existing checks and direct-test comparison

The local pinned tree names `tests/unit/test_conversation_memory.py`, but its
implementation is not cached. That existing-test coverage is unknown; do not
claim upstream missed a case. The inspected native pending-group and unmatched
filter checks themselves are compared with the replay.

For each condition, compare the full sliced event-to-completion result with
direct `ConversationMemory.process_events` on the identical retained history.
For O-A/O-B, also record raw `obs.content` and the direct native
`to_agent_observation()` result; the actual transformed input is the latter.
If direct tests suffice, report sufficiency. Do not credit the new analysis
with an improvement over the existing pairing checks.

At most one limited fixture correction is allowed, preserving the initial
record. Otherwise close unknown. No task score, cross-host transfer, or
debugging-efficiency conclusion follows from these observations.
