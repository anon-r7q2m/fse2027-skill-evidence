# Source-to-consumer map and public-check comparison

All source paths below are relative to `public_source/<host>/`. The source
manifest binds copied bytes to the pre-existing pinned public trees. The
fixture loads unchanged function/method bodies with explicit dependency mocks;
it does not import or run a complete agent application.

## SWE-agent

| Boundary | Pinned source | What the fixture establishes |
|---|---|---|
| Default configuration | `config/default.yaml:29–32,64–69`; `sweagent/agent/agents.py:444–462` | Default no-output sentence, function-calling parser/cache processor, and false `_always_require_zero_exit_code` flag are read and bound; no whole configuration loader is executed |
| Model response to action | `sweagent/tools/parsing.py:397–454`; `sweagent/tools/tools.py:353–380` | JSON argument decoding, allowed-command/argument checks, one-call admission, bash invocation, and blocklist check run |
| Action to runtime receipt | `sweagent/agent/agents.py:936–1007`; `sweagent/environment/swe_env.py:197–232` | Native handling chooses `check='ignore'`; native communicate passes a BashAction to the mocked runtime and returns output only |
| Output to next observation | `sweagent/agent/agents.py:675–752` | Empty output selects the default successful-command sentence; nonempty error output selects the ordinary observation template |
| History to consumer | `sweagent/agent/agents.py:540–552,1009–1054`; `sweagent/agent/history_processors.py:288–303` | Tool-call identity survives cache-control conversion; a second native forward reaches the deterministic model sink with the generated history and then intentionally stops |

The runtime result supplies `(output='', exit_code=0)` or
`(output='', exit_code=1)`. `communicate` projects both to the same empty string.
The later renderer receives no exit-code field. A direct invocation of that
same renderer on the same transformed StepOutput emits identical text. With
the known runtime status as an external test oracle, the ordinary direct test
already exposes the unsupported success sentence. Tracing identifies where
that information was dropped and where the sentence is consumed; this check
does not establish an advantage over the direct test.

### Existing public checks actually inspected

- `tests/test_agent.py:246–263`, `test_function_calling`, checks parsed `ls`
  and delivery of a nonempty `file1 file2` output. It does not exercise the
  empty-output/status distinction in that function.
- `tests/test_agent.py:211–221`, `test_show_no_output_template`, replaces the
  template with `no output template` and ends with
  `# todo: actually test that the template is used`.
- `tests/test_parsing.py:83–125`, `test_function_calling_parser`, checks a
  valid call and missing/multiple/invalid call cases. S-D's rejection is a
  normal protection already represented by this public test.

These functions and the adjacent history checks were inspected, not executed
as an upstream test suite. We make no claim about every test elsewhere in the
repository, live SWE-ReX behavior, or later revisions.

## OpenHands

| Boundary | Pinned source | What the fixture establishes |
|---|---|---|
| Default history policy | `openhands/core/config/agent_config.py:46–48` | Default NoOp configuration is read; a transparent NoOp view is mocked, not a complete config/runtime resolution |
| Result event to history | `openhands/controller/agent_controller.py:408–433` | Native event ingestion appends visible events through a mocked tracker; handler effects and automatic scheduling are mocked |
| Known status to formatted observation | `openhands/events/observation/commands.py:156–164` | Native formatting appends exit code 0/1 even when raw content is empty |
| History to message group | `openhands/memory/conversation_memory.py:72–163,182–327,328–389,644–655` | Native action/observation processing associates exact tool-call IDs and waits for all results in the originating response |
| Final matching boundary | `openhands/memory/conversation_memory.py:722–773` | Native final matching filter is executed; in the orphan fixture, the unpaired observation is already left out by the pending-group pipeline |
| Messages to consumer | `openhands/agenthub/codeact_agent/codeact_agent.py:150–203,205–272` | Native step and message construction deliver the structured messages to a deterministic completion sink; provider serialization is a transparent mock |

Complete empty-output events retain accurate known status and IDs. A pending
two-call response with only one result contributes no partial tool group;
an orphan result contributes no tool reply. These are legitimate protections,
not native bugs. Constructing a next input at those boundaries does not show
that the native asynchronous scheduler would ordinarily request a model then.

Direct `ConversationMemory.process_events` on the identical history produces
the same messages as the sliced controller-to-completion path in every fixed
condition. The direct `to_agent_observation` output is the actual transformed
input for the status controls; checking raw empty content would miss it.

### Existing public checks and unavailable tests

The pending-group completion predicate and matching filter are present and
executed. The pinned tree also lists
`tests/unit/test_conversation_memory.py` with blob
`7ae0122f388a60b7d1f45a407f506321cd9979f3`, but that blob is not locally cached.
Its test contents were neither read nor run. Upstream test-suite coverage
therefore remains unknown; the source checks already suffice for these
conditions.
