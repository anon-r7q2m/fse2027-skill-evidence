from __future__ import annotations

from typing import Any


SOURCE_PROMPT = """You are maintaining a context-aware state summary for an interactive agent. You will be given a list of events corresponding to actions taken by the agent, and the most recent previous summary if one exists. Track:

USER_CONTEXT: (Preserve essential user requirements, goals, and clarifications in concise form)

COMPLETED: (Tasks completed so far, with brief results)
PENDING: (Tasks that still need to be done)
CURRENT_STATE: (Current variables, data structures, or relevant state)

For code-specific tasks, also include:
CODE_STATE: {File paths, function signatures, data structures}
TESTS: {Failing cases, error messages, outputs}
CHANGES: {Code edits, variable updates}
DEPS: {Dependencies, imports, external calls}
VERSION_CONTROL_STATUS: {Repository state, current branch, PR status, commit history}

PRIORITIZE:
1. Adapt tracking format to match the actual task type
2. Capture key user requirements and goals
3. Distinguish between completed and pending tasks
4. Keep all sections concise and relevant

SKIP: Tracking irrelevant details for the current task type

Example formats:

For code tasks:
USER_CONTEXT: Fix FITS card float representation issue
COMPLETED: Modified mod_float() in card.py, all tests passing
PENDING: Create PR, update documentation
CODE_STATE: mod_float() in card.py updated
TESTS: test_format() passed
CHANGES: str(val) replaces f"{val:.16G}"
DEPS: None modified
VERSION_CONTROL_STATUS: Branch: fix-float-precision, Latest commit: a1b2c3d

For other tasks:
USER_CONTEXT: Write 20 haikus based on coin flip results
COMPLETED: 15 haikus written for results [T,H,T,H,T,H,T,T,H,T,H,T,H,T,H]
PENDING: 5 more haikus needed
CURRENT_STATE: Last flip: Heads, Haiku count: 15/20"""

DEFAULT_CONFIG = {
    "max_size": 16,
    "keep_first": 1,
    "max_event_length": 10_000,
}

MAX_REPLACE_UNITS = 128
MAX_SOURCE_REFS = 512
MAX_SUMMARY_CHARS = 65_536
MAX_ID_CHARS = 256


def truncate_content(content: str, max_chars: int | None = None) -> str:
    if max_chars is None or len(content) <= max_chars or max_chars < 0:
        return content
    half = max_chars // 2
    return (
        content[:half]
        + "\n[... Observation truncated due to length ...]\n"
        + content[-half:]
    )


def _default_state() -> dict[str, Any]:
    return {
        "config": dict(DEFAULT_CONFIG),
        "next_request_id": 1,
        "pending_summary": None,
        "pending_projection": None,
    }


def _normalize_state(state: Any) -> dict[str, Any]:
    base = _default_state()
    if not isinstance(state, dict):
        return base
    if isinstance(state.get("config"), dict):
        base["config"].update(state["config"])
    if isinstance(state.get("next_request_id"), int) and state["next_request_id"] > 0:
        base["next_request_id"] = state["next_request_id"]
    if isinstance(state.get("pending_summary"), dict) or state.get("pending_summary") is None:
        base["pending_summary"] = state.get("pending_summary")
    if isinstance(state.get("pending_projection"), dict) or state.get("pending_projection") is None:
        base["pending_projection"] = state.get("pending_projection")
    return base


def _fresh_request_id(state: dict[str, Any], prefix: str) -> str:
    request_id = f"{prefix}-{state['next_request_id']}"
    state["next_request_id"] += 1
    return request_id


def _select_span(history: list[dict[str, Any]], keep_first: int, max_size: int) -> list[dict[str, Any]]:
    target_size = max_size // 2
    head = history[:keep_first]
    events_from_tail = target_size - len(head) - 1
    if events_from_tail > 0:
        return history[keep_first:-events_from_tail]
    return history[keep_first:]


def _is_summary_unit(unit: dict[str, Any]) -> bool:
    return unit.get("kind") == "summary"


def _unit_text_for_previous_summary(unit: dict[str, Any]) -> str:
    summary = unit.get("summary")
    if isinstance(summary, str):
        return summary
    visible_text = unit.get("visible_text")
    if isinstance(visible_text, str):
        return visible_text
    return ""


def _unit_visible_text(unit: dict[str, Any]) -> str:
    visible_text = unit.get("visible_text")
    return visible_text if isinstance(visible_text, str) else ""


def _is_protected(unit: dict[str, Any]) -> bool:
    if not unit.get("complete", False):
        return True
    if not unit.get("eligible", False):
        return True
    protected_reasons = unit.get("protected_reasons")
    return bool(protected_reasons)


def _dedup_source_refs(span: list[dict[str, Any]]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for unit in span:
        refs = unit.get("source_refs")
        if not isinstance(refs, list):
            continue
        for ref in refs:
            if not isinstance(ref, dict):
                continue
            unit_id = ref.get("unit_id")
            wire_sha256 = ref.get("wire_sha256")
            if not isinstance(unit_id, str) or not isinstance(wire_sha256, str):
                continue
            key = (unit_id, wire_sha256)
            if key in seen:
                continue
            seen.add(key)
            result.append({"unit_id": unit_id, "wire_sha256": wire_sha256})
    return result


def _replace_units(span: list[dict[str, Any]]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for unit in span:
        unit_id = unit.get("unit_id")
        wire_sha256 = unit.get("wire_sha256")
        if isinstance(unit_id, str) and isinstance(wire_sha256, str):
            result.append({"unit_id": unit_id, "wire_sha256": wire_sha256})
    return result


def _build_prompt(
    history: list[dict[str, Any]], config: dict[str, Any]
) -> tuple[str, list[dict[str, str]], list[dict[str, str]]]:
    keep_first = int(config["keep_first"])
    max_event_length = int(config["max_event_length"])
    span = _select_span(history, keep_first, int(config["max_size"]))

    if len(history) > keep_first and _is_summary_unit(history[keep_first]):
        previous_summary_raw = _unit_text_for_previous_summary(history[keep_first])
    else:
        previous_summary_raw = "No events summarized"

    prompt = SOURCE_PROMPT
    prompt += "\n\n"
    prompt += (
        "<PREVIOUS SUMMARY>\n"
        f"{truncate_content(previous_summary_raw, max_event_length)}\n"
        "</PREVIOUS SUMMARY>\n"
    )
    prompt += "\n\n"

    for unit in span:
        if _is_summary_unit(unit):
            continue
        unit_id = unit.get("unit_id", "")
        event_content = truncate_content(_unit_visible_text(unit), max_event_length)
        prompt += f"<EVENT id={unit_id}>\n{event_content}\n</EVENT>\n"

    prompt += "Now summarize the events using the rules above."
    return prompt, _replace_units(span), _dedup_source_refs(span)


def _limits_from_event(event: dict[str, Any]) -> dict[str, int]:
    limits = event.get("limits")
    if not isinstance(limits, dict):
        return {"input_token_limit": 0, "output_token_limit": 0}
    input_limit = limits.get("input_token_limit")
    output_limit = limits.get("output_token_limit")
    return {
        "input_token_limit": input_limit if isinstance(input_limit, int) else 0,
        "output_token_limit": output_limit if isinstance(output_limit, int) else 0,
    }


def _extract_summary_text(receipt: dict[str, Any]) -> str | None:
    response = receipt.get("response")
    if not isinstance(response, dict):
        return None
    output = response.get("output")
    if not isinstance(output, list):
        return None

    texts: list[str] = []
    saw_output_text = False

    for item in output:
        if not isinstance(item, dict):
            continue
        content = item.get("content")
        if not isinstance(content, list):
            continue
        for part in content:
            if not isinstance(part, dict):
                continue
            if part.get("type") == "output_text" and isinstance(part.get("text"), str):
                saw_output_text = True
                texts.append(part["text"])

    if not saw_output_text:
        return None
    return "".join(texts)


def _valid_projection(
    replace_units: list[dict[str, str]],
    source_refs: list[dict[str, str]],
    summary: str,
) -> bool:
    if len(replace_units) == 0 or len(replace_units) > MAX_REPLACE_UNITS:
        return False
    if len(source_refs) > MAX_SOURCE_REFS:
        return False
    if len(summary) > MAX_SUMMARY_CHARS:
        return False

    for item in replace_units + source_refs:
        unit_id = item.get("unit_id")
        wire_sha256 = item.get("wire_sha256")
        if not isinstance(unit_id, str) or not isinstance(wire_sha256, str):
            return False
        if len(unit_id) > MAX_ID_CHARS:
            return False
    return True


def _handle_prepare(event: dict[str, Any]) -> dict[str, Any]:
    return {"state": _default_state(), "effects": []}


def _handle_before_solver_request(event: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    if state.get("pending_summary") is not None:
        return {"state": state, "effects": []}

    remaining_responses = event.get("remaining_responses")
    if not isinstance(remaining_responses, int) or remaining_responses < 2:
        return {"state": state, "effects": []}

    history = event.get("history")
    if not isinstance(history, list):
        return {"state": state, "effects": []}

    config = state["config"]
    max_size = int(config["max_size"])
    keep_first = int(config["keep_first"])

    if len(history) <= max_size:
        return {"state": state, "effects": []}

    span = _select_span(history, keep_first, max_size)
    if not span:
        return {"state": state, "effects": []}

    if any(_is_protected(unit) for unit in span):
        return {"state": state, "effects": []}

    prompt, replace_units, source_refs = _build_prompt(history, config)
    request_id = _fresh_request_id(state, "summary")
    limits = _limits_from_event(event)

    state["pending_summary"] = {
        "request_id": request_id,
        "view_revision": event.get("view_revision"),
        "replace_units": replace_units,
        "source_refs": source_refs,
        "remaining_output_chars": event.get("remaining_output_chars"),
    }

    effect = {
        "kind": "model_request",
        "request_id": request_id,
        "items": [{"role": "user", "content": prompt}],
        "instructions": "",
        "tools": [],
        "limits": limits,
    }
    return {"state": state, "effects": [effect]}


def _handle_model_request_completed(event: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    pending = state.get("pending_summary")
    if not isinstance(pending, dict):
        return {"state": state, "effects": []}

    receipt = event.get("receipt")
    if not isinstance(receipt, dict):
        return {"state": state, "effects": []}

    if receipt.get("request_id") != pending.get("request_id"):
        return {"state": state, "effects": []}

    state["pending_summary"] = None

    if receipt.get("status") != "completed":
        return {"state": state, "effects": []}

    summary = _extract_summary_text(receipt)
    if summary is None:
        return {"state": state, "effects": []}

    remaining_output_chars = pending.get("remaining_output_chars")
    if isinstance(remaining_output_chars, int) and len(summary) > remaining_output_chars:
        return {"state": state, "effects": []}

    ledger = receipt.get("ledger")
    if not isinstance(ledger, dict):
        return {"state": state, "effects": []}
    response_sha256 = ledger.get("response_sha256")
    if not isinstance(response_sha256, str):
        return {"state": state, "effects": []}

    replace_units = pending.get("replace_units")
    source_refs = pending.get("source_refs")
    view_revision = pending.get("view_revision")

    if (
        not isinstance(replace_units, list)
        or not isinstance(source_refs, list)
        or not isinstance(view_revision, str)
    ):
        return {"state": state, "effects": []}

    if not _valid_projection(replace_units, source_refs, summary):
        return {"state": state, "effects": []}

    projection_request_id = _fresh_request_id(state, "projection")
    state["pending_projection"] = {"request_id": projection_request_id}

    effect = {
        "kind": "project_history",
        "request_id": projection_request_id,
        "view_revision": view_revision,
        "replace_units": replace_units,
        "source_refs": source_refs,
        "summary_request_id": pending["request_id"],
        "summary_response_sha256": response_sha256,
        "summary": summary,
    }
    return {"state": state, "effects": [effect]}


def _handle_projection_event(event: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    kind = event.get("kind")
    if kind == "projection_delivered":
        pending_projection = state.get("pending_projection")
        if isinstance(pending_projection, dict):
            projection_request_id = event.get("projection_request_id")
            if projection_request_id == pending_projection.get("request_id"):
                state["pending_projection"] = None
    return {"state": state, "effects": []}


def handle(event: Any, state: Any) -> dict[str, Any]:
    state_obj = _normalize_state(state)

    if not isinstance(event, dict):
        return {"state": state_obj, "effects": []}

    kind = event.get("kind")

    if kind == "prepare":
        return _handle_prepare(event)
    if kind == "before_solver_request":
        return _handle_before_solver_request(event, state_obj)
    if kind == "model_request_completed":
        return _handle_model_request_completed(event, state_obj)
    if kind in {"projection_completed", "projection_delivered", "workspace_changed"}:
        return _handle_projection_event(event, state_obj)

    return {"state": state_obj, "effects": []}
