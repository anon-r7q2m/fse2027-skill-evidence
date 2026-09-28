# Qualified objects and no-replacement freeze

The two preferred hosts qualify for the source-slice mode explicitly allowed
by the selection protocol. This is not qualification of complete native host
execution. No fallback host was selected and no defect was used to select a
path. Both objects are now frozen; missing fields close unknown rather than
triggering another source search.

| Field | SWE-agent | OpenHands |
|---|---|---|
| Public origin | https://github.com/SWE-agent/SWE-agent | https://github.com/All-Hands-AI/OpenHands (tree metadata redirects to OpenHands/OpenHands) |
| Full revision | `3ea751c087f32b16e039a2233dd6eefecef325d5` | `34bf9c2579ca5a25e452583eed38c6c0e45cebd6` |
| License | MIT, pinned LICENSE blob `e702436e21844c5c519de31ab68277a6d3b427d9` | MIT, pinned LICENSE blob `af1393b388a10f9a4bcdea4ecee8a89f227b975b` |
| Local origin record | `experiments/automatic_extraction_v1/sources/swe_agent/manifest.json` and `tree.json` | `experiments/openhands_summary_transfer_v1/sources/manifest.json` and `tree.json` |
| Source completeness | Complete pinned lazy-blob tree; default config, agent/tool/history code, relevant test blobs present | Fourteen pinned files include controller, CodeActAgent, ConversationMemory, state, action/observation, serialization and condenser configuration; not a complete application checkout |
| Entry metadata | `config/default.yaml`: function-calling parser, bash enabled, cache-control history processor, next-observation templates | Existing transfer PLAN identifies CodeActAgent entry; `AgentConfig` enables command execution and uses `NoOpCondenserConfig(type='noop')` |
| Frozen object | Default-configured model tool-call response, its parsed/admitted execution request, and the observation passed to the next agent query | Command result event, retained history, message construction and next CodeActAgent input under default NoOp condensation |
| Frozen source path | Default config -> `sweagent/agent/agents.py` -> tool parser/execution -> history processor -> next query | Command observation -> `controller/agent_controller.py` / state -> `memory/conversation_memory.py` -> `agenthub/codeact_agent/codeact_agent.py` |
| Prior path exposure | `exposure_unknown`: prior SWE-agent discovery, file-window and chooser work exists; the inspected coverage index does not establish whether this exact path was analyzed | `previously_exposed`: the 2026-09-11 source review and transfer PLAN explicitly traced ConversationMemory -> CodeActAgent completion |

The matching OpenHands and SWE-agent license text already exists under
`experiments/mechanism_execution_v1/sources/`; its Git blob identity was checked
against the pinned tree. OpenHands entry-class evidence above is a prior public
source review plus local agent configuration, not a fresh complete application
default-resolution execution.

Qualification inspected public source manifests, tree metadata, the SWE-agent
default configuration, OpenHands configuration fields, and public coverage
records. Some OpenHands source-path descriptions were necessarily visible in
those coverage records and are included in its prior-exposure classification.
No path fixture has run at this freeze.

OpenHands upstream `tests/unit/test_conversation_memory.py` is named in the
pinned tree but its blob is not in the local subset. Comparison with that
unread test implementation must remain unknown unless an already-local public
copy is identified within these source records; no fetch or installation is
required or authorized by this check. Missing runtime dependencies are explicit
mock boundaries or unknown fields. Neither host is an independently unseen
sample, and this check does not claim cross-host transplantation.
