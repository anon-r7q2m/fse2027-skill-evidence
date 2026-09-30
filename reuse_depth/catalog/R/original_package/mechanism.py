import copy
import json

from source_rules import (
    build_generation_prompt,
    build_model_instructions,
    build_repair_prompt,
    check_source_result,
    clone_json,
    validate_prepare_event,
    validate_source_completion_receipt,
)
from reproduction import parse_model_submission
from case_runner import interpret_execution_receipt


def _reject(reason):
    raise ValueError("PROTOCOL_REJECTED: " + reason)


def _default_state():
    return {
        "version": 1,
        "phase": "new",
        "ended": False,
        "pending": None,
        "issue": None,
        "base_snapshot": None,
        "card": None,
        "domain": None,
        "source_bundle": None,
        "model_requests_made": 0,
        "script_submissions_made": 0,
        "repair_used": False,
        "last_model_output": None,
        "last_feedback": None,
        "admitted_submission": None,
        "checked_snapshots": [],
        "known_messages": [],
        "next_request_id": 1,
        "next_message_id": 1,
        "remaining_responses_estimate": None,
        "remaining_output_chars": None,
    }


def _load_state(state):
    if state == {}:
        return _default_state()
    if type(state) is not dict:
        _reject("state must be an object")
    merged = _default_state()
    for key, value in state.items():
        if key in merged:
            merged[key] = copy.deepcopy(value)
    return merged


def _save_state(state):
    return clone_json(state)


def _new_request_id(state, prefix):
    value = "%s-%d" % (prefix, state["next_request_id"])
    state["next_request_id"] += 1
    return value


def _new_message_id(state):
    value = "message-%d" % (state["next_message_id"])
    state["next_message_id"] += 1
    return value


def _message_known(state, message_id):
    for row in state["known_messages"]:
        if row["message_id"] == message_id:
            return row
    return None


def _remember_message(state, message_id):
    state["known_messages"].append({"message_id": message_id, "acked": False})


def _consume_model_budget(state):
    value = state.get("remaining_responses_estimate")
    if type(value) is int and value > 0:
        state["remaining_responses_estimate"] = value - 1


def _set_event_budget(state, event):
    if "remaining_responses" in event and type(event["remaining_responses"]) is int:
        state["remaining_responses_estimate"] = event["remaining_responses"]
    if "remaining_output_chars" in event and type(event["remaining_output_chars"]) is int:
        state["remaining_output_chars"] = event["remaining_output_chars"]


def _observation_content(status, reason, cases, script=None):
    payload = {"status": status, "reason": reason, "cases": cases}
    if script is not None:
        payload["script"] = script
    content = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    if len(content) <= 24000:
        return content
    payload.pop("script", None)
    content = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    if len(content) <= 24000:
        return content
    short_cases = []
    for row in cases:
        short_cases.append(
            {
                "id": row["id"],
                "role": row["role"],
                "test": row["test"],
                "status": row["status"],
                "reason": row["reason"][:200],
            }
        )
    payload = {"status": status, "reason": reason[:400], "cases": short_cases}
    content = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return content[:24000]


def _emit_observation(state, evidence_refs, status, reason, cases, script=None):
    content = _observation_content(status, reason, cases, script=script)
    remaining = state.get("remaining_output_chars")
    if type(remaining) is int and remaining < len(content):
        return []
    message_id = _new_message_id(state)
    _remember_message(state, message_id)
    return [
        {
            "kind": "observation",
            "message_id": message_id,
            "content": content,
            "evidence_refs": evidence_refs,
        }
    ]


def _build_source_effect(state):
    request_id = _new_request_id(state, "source")
    state["pending"] = {
        "kind": "source_read",
        "request_id": request_id,
        "base_commit": state["domain"]["base_commit"],
        "queries": clone_json(state["card"]["source_queries"]),
    }
    state["phase"] = "waiting_source"
    return [
        {
            "kind": "source_read",
            "request_id": request_id,
            "base_commit": state["domain"]["base_commit"],
            "queries": clone_json(state["card"]["source_queries"]),
        }
    ]


def _build_model_effect(state, prompt_text):
    request_id = _new_request_id(state, "model")
    state["pending"] = {"kind": "model_request", "request_id": request_id}
    state["phase"] = "waiting_model"
    state["model_requests_made"] += 1
    _consume_model_budget(state)
    return [
        {
            "kind": "model_request",
            "request_id": request_id,
            "items": [{"role": "user", "content": prompt_text}],
            "instructions": build_model_instructions(),
            "tools": [],
            "limits": clone_json(state["domain"]["model_limits"]),
        }
    ]


def _build_run_effect(state, snapshot_ref, submission, mode):
    request_id = _new_request_id(state, "run")
    state["pending"] = {
        "kind": "run_isolated",
        "request_id": request_id,
        "snapshot_ref": snapshot_ref,
        "mode": mode,
        "submission": clone_json(submission),
    }
    state["phase"] = "waiting_execution"
    state["script_submissions_made"] += 1
    return [
        {
            "kind": "run_isolated",
            "request_id": request_id,
            "snapshot_ref": snapshot_ref,
            "execution_spec": clone_json(state["domain"]["execution_spec"]),
            "projection_spec": clone_json(state["domain"]["projection_spec"]),
            "limits": clone_json(state["domain"]["execution_limits"]),
            "input_files": {
                "script.py": submission["script"],
                "card.json": submission["card_json"],
            },
        }
    ]


def _repair_possible(state):
    remaining = state.get("remaining_responses_estimate")
    if type(remaining) is not int:
        return True
    return remaining >= 2


def _base_expected(state, pending):
    return {
        "request_id": pending["request_id"],
        "snapshot_ref": pending["snapshot_ref"],
        "input_hashes": clone_json(pending["submission"]["input_hashes"]),
        "script_sha256": pending["submission"]["script_sha256"],
        "card": clone_json(state["card"]),
        "mapping": clone_json(pending["submission"]["mapping"]),
    }


def _simple_cases_from_feedback(feedback):
    return clone_json(feedback.get("cases") or [])


def _handle_prepare(event, state):
    if state["phase"] != "new":
        _reject("duplicate prepare")
    prepared = validate_prepare_event(event)
    state["issue"] = prepared["issue"]
    state["base_snapshot"] = prepared["base_snapshot"]
    state["card"] = prepared["card"]
    state["domain"] = prepared["domain"]
    state["remaining_responses_estimate"] = prepared["remaining_responses"]
    state["remaining_output_chars"] = prepared["remaining_output_chars"]
    if prepared["remaining_output_chars"] <= 0:
        state["phase"] = "inactive"
        return {"state": _save_state(state), "effects": []}
    if prepared["remaining_responses"] < 3:
        state["phase"] = "inactive"
        effects = _emit_observation(
            state,
            ["prepare"],
            "INSUFFICIENT_PREPARATION_BUDGET",
            "INSUFFICIENT_PREPARATION_BUDGET",
            [],
            None,
        )
        return {"state": _save_state(state), "effects": effects}
    effects = _build_source_effect(state)
    return {"state": _save_state(state), "effects": effects}


def _handle_source_completed(event, state):
    pending = state["pending"]
    if not pending or pending.get("kind") != "source_read":
        _reject("unexpected source completion")
    if type(event) is not dict or event.get("kind") != "source_read_completed":
        _reject("invalid source completion event")
    receipt = event.get("receipt")
    result = validate_source_completion_receipt(
        receipt, pending["request_id"], pending["base_commit"]
    )
    ok, reason, bundle = check_source_result(result, pending["queries"])
    state["pending"] = None
    if not ok:
        state["phase"] = "inactive"
        effects = _emit_observation(
            state,
            [pending["request_id"]],
            "SOURCE_NOT_READY",
            reason,
            [],
            None,
        )
        return {"state": _save_state(state), "effects": effects}
    state["source_bundle"] = bundle
    prompt = build_generation_prompt(state["issue"], state["card"], bundle)
    effects = _build_model_effect(state, prompt)
    return {"state": _save_state(state), "effects": effects}


def _maybe_repair_after_parse_failure(state, pending_request_id, failure_reason):
    feedback = {
        "status": "NOT_ADMITTED",
        "reason": failure_reason,
        "cases": [],
    }
    state["last_feedback"] = feedback
    if not state["repair_used"] and _repair_possible(state):
        state["repair_used"] = True
        prompt = build_repair_prompt(
            state["issue"],
            state["card"],
            state["source_bundle"],
            state["last_model_output"] or "",
            feedback,
        )
        return _build_model_effect(state, prompt)
    state["phase"] = "inactive"
    return _emit_observation(
        state,
        [pending_request_id],
        "NOT_ADMITTED",
        failure_reason,
        [],
        None,
    )


def _handle_model_completed(event, state):
    pending = state["pending"]
    if not pending or pending.get("kind") != "model_request":
        _reject("unexpected model completion")
    if type(event) is not dict or event.get("kind") != "model_request_completed":
        _reject("invalid model completion event")
    receipt = event.get("receipt")
    if type(receipt) is not dict or receipt.get("request_id") != pending["request_id"]:
        _reject("stale model completion")
    state["pending"] = None
    if receipt.get("status") != "completed" or type(receipt.get("response")) is not dict:
        state["phase"] = "inactive"
        effects = _emit_observation(
            state,
            [pending["request_id"]],
            "MODEL_RESPONSE_NOT_COMPLETED",
            "MODEL_RESPONSE_NOT_COMPLETED",
            [],
            None,
        )
        return {"state": _save_state(state), "effects": effects}
    parsed = parse_model_submission(state["card"], receipt["response"])
    state["last_model_output"] = parsed.get("raw_output", "")
    if not parsed.get("ok"):
        effects = _maybe_repair_after_parse_failure(
            state, pending["request_id"], parsed.get("reason", "SUBMISSION_INVALID")
        )
        return {"state": _save_state(state), "effects": effects}
    effects = _build_run_effect(
        state, state["base_snapshot"], parsed["submission"], "base"
    )
    return {"state": _save_state(state), "effects": effects}


def _candidate_allowed(state):
    return state["phase"] == "admitted" and state["admitted_submission"] is not None and not state["ended"]


def _handle_execution_completed(event, state):
    pending = state["pending"]
    if not pending or pending.get("kind") != "run_isolated":
        _reject("unexpected execution completion")
    if type(event) is not dict or event.get("kind") != "execution_completed":
        _reject("invalid execution completion event")
    receipt = event.get("receipt")
    if type(receipt) is not dict:
        _reject("invalid execution receipt")
    if receipt.get("request_id") != pending["request_id"] or receipt.get("snapshot_ref") != pending["snapshot_ref"]:
        _reject("stale execution completion")
    state["pending"] = None
    expected = _base_expected(state, pending)
    interpreted = interpret_execution_receipt(receipt, expected, pending["mode"])
    cases = _simple_cases_from_feedback(interpreted)
    if pending["mode"] == "base":
        if interpreted["status"] == "BASE_ADMITTED":
            state["phase"] = "admitted"
            state["admitted_submission"] = clone_json(pending["submission"])
            effects = _emit_observation(
                state,
                [pending["request_id"]],
                "BASE_ADMITTED",
                interpreted["reason"],
                cases,
                pending["submission"]["script"],
            )
            return {"state": _save_state(state), "effects": effects}
        state["last_feedback"] = clone_json(interpreted)
        if state["script_submissions_made"] == 1 and not state["repair_used"] and _repair_possible(state):
            state["repair_used"] = True
            state["phase"] = "waiting_model"
            prompt = build_repair_prompt(
                state["issue"],
                state["card"],
                state["source_bundle"],
                state["last_model_output"] or "",
                interpreted,
            )
            effects = _build_model_effect(state, prompt)
            return {"state": _save_state(state), "effects": effects}
        state["phase"] = "inactive"
        effects = _emit_observation(
            state,
            [pending["request_id"]],
            "NOT_ADMITTED",
            interpreted["status"],
            cases,
            pending["submission"]["script"],
        )
        return {"state": _save_state(state), "effects": effects}
    snapshot = pending["snapshot_ref"]
    if snapshot not in state["checked_snapshots"]:
        state["checked_snapshots"].append(snapshot)
    state["phase"] = "admitted"
    effects = _emit_observation(
        state,
        [pending["request_id"]],
        interpreted["status"],
        interpreted["reason"],
        cases,
        pending["submission"]["script"],
    )
    return {"state": _save_state(state), "effects": effects}


def _handle_workspace_changed(event, state):
    if type(event) is not dict or event.get("kind") != "workspace_changed":
        _reject("invalid workspace event")
    if state["pending"] is not None:
        _reject("workspace changed while effect pending")
    if type(event.get("changed")) is not bool:
        _reject("invalid workspace changed flag")
    if type(event.get("snapshot_ref")) is not str or not event.get("snapshot_ref"):
        _reject("invalid workspace snapshot")
    if type(event.get("tool")) is not str or not event.get("tool"):
        _reject("invalid workspace tool")
    if type(event.get("remaining_responses")) is not int or type(event.get("remaining_output_chars")) is not int:
        _reject("invalid workspace budget")
    _set_event_budget(state, event)
    if state["ended"] or not _candidate_allowed(state):
        return {"state": _save_state(state), "effects": []}
    if not event["changed"]:
        return {"state": _save_state(state), "effects": []}
    if event["snapshot_ref"] in state["checked_snapshots"]:
        return {"state": _save_state(state), "effects": []}
    if event["remaining_responses"] <= 0 or event["remaining_output_chars"] <= 0:
        return {"state": _save_state(state), "effects": []}
    effects = _build_run_effect(
        state,
        event["snapshot_ref"],
        state["admitted_submission"],
        "candidate",
    )
    return {"state": _save_state(state), "effects": effects}


def _handle_feedback_delivered(event, state):
    if type(event) is not dict or event.get("kind") != "feedback_delivered":
        _reject("invalid feedback event")
    if event.get("completed") is not True:
        _reject("feedback not completed")
    if type(event.get("message_id")) is not str or type(event.get("request_id")) is not str or not event.get("request_id"):
        _reject("invalid feedback acknowledgement")
    known = _message_known(state, event["message_id"])
    if known is None or known["acked"]:
        _reject("unknown or duplicate feedback acknowledgement")
    known["acked"] = True
    return {"state": _save_state(state), "effects": []}


def _handle_task_end(event, state):
    if type(event) is not dict or event.get("kind") != "task_end":
        _reject("invalid task end")
    if state["pending"] is not None:
        _reject("task end while effect pending")
    state["ended"] = True
    return {"state": _save_state(state), "effects": []}


def handle(event, state):
    current = _load_state(state)
    if type(event) is not dict or type(event.get("kind")) is not str:
        _reject("invalid event")
    kind = event["kind"]
    if kind == "prepare":
        return _handle_prepare(event, current)
    if kind == "source_read_completed":
        return _handle_source_completed(event, current)
    if kind == "model_request_completed":
        return _handle_model_completed(event, current)
    if kind == "execution_completed":
        return _handle_execution_completed(event, current)
    if kind == "workspace_changed":
        return _handle_workspace_changed(event, current)
    if kind == "feedback_delivered":
        return _handle_feedback_delivered(event, current)
    if kind == "task_end":
        return _handle_task_end(event, current)
    _reject("unknown event kind")
