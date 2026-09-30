# E1

A public report dated 2026-07-05 describes an agent configured with
`NativeOutput(Response | Clarification)` and `end_strategy="early"`. Its supplied
function-based model returns a text part and a `search_documents` tool call in the
same first response, followed by text on a subsequent request. The report states
that `search_documents` is invoked. No raw provider trace was supplied in the
report's trace field, and this packet has not rerun the example.

The reported environment is Python 3.14, PydanticAI `main`, and a Bedrock provider
SDK. The actual supplied example uses `FunctionModel`. The report does not give an
exact source commit. The packet supplies an inspection snapshot at
`b5f43e4cc4c7d6ae2d7f76007dede1d8ca00c204`; it must not be described as a recovered
author checkout.

`PROVIDED_PROGRAM.txt` presents the supplied example after removal of comments and
display-only expectation/verdict text. Operational imports, declarations, model
responses, tool arguments, counters, agent configuration, and calls are retained.
The removed display branch only printed a verdict. Treat this as a disclosed
source presentation, not an independently observed execution. The text payload
and its union/output wrapper are preserved exactly.

Relevant complete source and contract material is in `../sources/pydantic_e1/`:

- `pydantic_ai_slim/pydantic_ai/_agent_graph.py` and `_tool_execution.py`
- `pydantic_ai_slim/pydantic_ai/_output.py` and `output.py`
- `pydantic_ai_slim/pydantic_ai/tool_manager.py`, `tools.py`, and `messages.py`
- `pydantic_ai_slim/pydantic_ai/models/function.py`
- `pydantic_ai_slim/pydantic_ai/agent/__init__.py`
- `docs/output.md` and `docs/agent.md`

Analyze the reported operation under the supplied configuration, source, and
versioned contract. What action, if any, is justified, and which qualifications or
neighboring behaviors must be preserved? Distinguish report assertions from facts
established by the supplied material.
