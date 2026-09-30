# E2

A public report dated 2026-07-30 supplies a capability hook and an approval-required
tool. The model call described in the report is `transfer(amount=100)`. The
reported approval display contains `{'amount': 100}`, and the reported execution
value is `amount=50`.

`PROVIDED_PROGRAM.txt` and `REPORTED_VALUES.txt` preserve the supplied code and
value blocks exactly. The report supplies a partial example: objects such as
`model` and `executed` are not defined in that excerpt. This packet does not fill
those gaps or assert that a real financial transfer occurred.

The report identifies its source only as `main`. The supplied inspection snapshot
is `577a8e94b500999727cbf61fef569755a889f1ce`, committed at 21:53:49 UTC, immediately
before the report's 22:01:00 UTC creation time. This is a time-selected reference
snapshot, not an exact source revision attested by the reporter. No run has been
performed for this packet.

Relevant complete source and contract material is in `../sources/pydantic_e2/`:

- `pydantic_ai_slim/pydantic_ai/_agent_graph.py` and `_tool_execution.py`
- `pydantic_ai_slim/pydantic_ai/tool_manager.py`, `_deferred.py`, `tools.py`, and
  `messages.py`
- `pydantic_ai_slim/pydantic_ai/capabilities/abstract.py`, `capability.py`, and
  `combined.py`
- `docs/deferred-tools.md` and `docs/capabilities/custom.md`

Analyze the supplied operation under the versioned API and implementation. What
action, if any, is justified? State which values, events, and authorities matter;
which changes are compatible with the contract; and what remains uncertain.
