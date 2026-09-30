def _next_counter(state):
    value = state.get("counter", 0)
    if type(value) is not int or value < 0:
        value = 0
    return value


def _message_id(counter):
    return f"tool-failure-reflection-{counter}"


def _evidence_refs(event):
    kind = event.get("kind", "event")
    action = event.get("action")
    if type(action) is dict:
        tool = action.get("tool")
        if type(tool) is str and tool:
            return [f"{kind}:{tool}"]
    tool = event.get("tool")
    if type(tool) is str and tool:
        return [f"{kind}:{tool}"]
    return [kind if type(kind) is str and kind else "event"]


def _failed_workspace_action(event):
    if type(event) is not dict or event.get("kind") != "workspace_changed":
        return False
    action = event.get("action")
    if type(action) is not dict:
        return False
    code = action.get("return_code")
    return type(code) is int and code != 0


def _failure_content(event):
    action = event.get("action", {})
    observation = action.get("observation")
    if type(observation) is not str:
        observation = str(observation)
    return (
        f"The tool execution failed with error: {observation}. "
        "Consider trying a different approach or fixing the parameters."
    )


def handle(event, state):
    if type(state) is not dict:
        state = {}
    next_state = dict(state)
    effects = []

    if _failed_workspace_action(event):
        counter = _next_counter(next_state)
        effects.append(
            {
                "kind": "observation",
                "message_id": _message_id(counter),
                "content": _failure_content(event),
                "evidence_refs": _evidence_refs(event),
            }
        )
        next_state["counter"] = counter + 1
    else:
        next_state["counter"] = _next_counter(next_state)

    return {"state": next_state, "effects": effects}
