# E3

A public report dated 2026-02-12 describes starting with a documented functional
workflow and adding an outer entrypoint. The author says they invoked that outer
entrypoint, after which a previously completed task prints again on resumption and
the interrupt output contains two entries. The provided program and both supplied
outputs are included without correction.

- `PROVIDED_PROGRAM.txt`: the report's complete pasted program.
- `REPORTED_BASE_OUTPUT.txt`: output the report associates with its starting
  workflow.
- `REPORTED_WRAPPED_OUTPUT.txt`: output the report associates with the described
  modification.

The report names LangGraph 1.0.8, Python 3.14.2, macOS, `langchain_core` 1.2.10,
and `langchain` 1.2.10. The corresponding LangGraph 1.0.8 source tag resolves to
`a7a27dd43a4229c2ca09ac065a6a39e4ce083063`. The packet has not executed the example
or independently verified the reported outputs.

Relevant complete modules are in `../sources/langgraph_1_0_8/`:

- `libs/langgraph/langgraph/func/__init__.py` and `types.py`
- `libs/langgraph/langgraph/pregel/main.py`, `_loop.py`, `_algo.py`, `_call.py`,
  `_runner.py`, `_retry.py`, and `_checkpoint.py`
- `libs/langgraph/langgraph/config.py` and `graph/state.py`
- `libs/checkpoint/langgraph/checkpoint/base/__init__.py` and
  `memory/__init__.py`

The public API contracts are the docstrings in these pinned modules. Analyze what
the supplied evidence establishes about the reported operation and what action,
if any, is justified. State the applicable obligations and any qualifications or
uncertainty.
