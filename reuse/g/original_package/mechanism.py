from compatibility import (
    base_shell,
    cp,
    protocol_rejected,
    public_state,
    validate_event,
    validate_state,
)
from native_logs import matches_expected_assertion, parse_native_log

_INVENTORY_NONPASS_OR_MISSING = {"MISSING", "SKIPPED", "XFAIL", "XPASS", "ERROR"}
_MAX_OBSERVATION_CHARS = 24000


def _sorted_strings(values):
    return sorted(values)


def _request_id(n):
    return f"req-{n}"


def _message_id(n):
    return f"msg-{n}"


def _run_effect(n, snapshot_ref, domain):
    return {
        "kind": "run_isolated",
        "request_id": _request_id(n),
        "snapshot_ref": snapshot_ref,
        "execution_spec": cp(domain["execution_spec"]),
        "projection_spec": cp(domain["projection_spec"]),
        "limits": cp(domain["limits"]),
    }


def _receipt_matches_outstanding(receipt, effect):
    return (
        receipt["request_id"] == effect["request_id"]
        and receipt["snapshot_ref"] == effect["snapshot_ref"]
        and receipt["execution_spec"] == effect["execution_spec"]
        and receipt["projection_spec"] == effect["projection_spec"]
        and receipt["limits"] == effect["limits"]
    )


def _public_freeze_view(freeze):
    if freeze is None:
        return None
    return {
        "id": freeze["id"],
        "base_snapshot_ref": freeze["base_snapshot_ref"],
        "classifications": cp(freeze["classifications"]),
    }


def _set_public(state, inventory, freeze, decision):
    state["public"] = public_state(list(inventory), _public_freeze_view(freeze), decision)


def _prepare_state(state):
    prepared = base_shell() if state == {} else cp(state)
    if "public" not in prepared:
        prepared["public"] = public_state([], None, None)
    if "pending_msgs" not in prepared or not isinstance(prepared["pending_msgs"], dict):
        prepared["pending_msgs"] = {}
    if "next_req" not in prepared:
        prepared["next_req"] = 1
    if "next_msg" not in prepared:
        prepared["next_msg"] = 1
    return prepared


def _observation_content(decision, freeze_id, execution_request_id):
    lines = [decision["status"]]
    for test_id in _sorted_strings(decision["observations"].keys()):
        observation = decision["observations"][test_id]
        if observation["disposition"] != "PRESERVE" or observation["observed"] != "PASSED":
            lines.append(f"{test_id}: {observation['observed']}")
    lines.append(f"freeze={freeze_id}")
    lines.append(f"execution={execution_request_id}")
    short = "\n".join(lines)
    if len(short) <= _MAX_OBSERVATION_CHARS:
        return short

    fallback = "\n".join(
        [
            decision["status"],
            "Details omitted because the full decision exceeds the feedback limit; see the full decision and receipt record via the references below.",
            f"freeze={freeze_id}",
            f"execution={execution_request_id}",
        ]
    )
    if len(fallback) > _MAX_OBSERVATION_CHARS:
        fallback = fallback[:_MAX_OBSERVATION_CHARS]
    return fallback


def _execution_issues(receipt, parsed, observations):
    issues = []

    if receipt["timed_out"] or receipt["cancelled"]:
        issues.append("EXECUTION_TIMEOUT_OR_CANCELLED")
    if receipt["truncated"] or receipt["stage"] != "completed":
        issues.append("EXECUTION_NOT_FULLY_OBSERVED")
    if receipt["projection"]["guard_changed"]:
        issues.append("CONFIGURATION_CHANGED")
    if not receipt["projection"]["applied"]:
        issues.append("PROJECTION_NOT_ESTABLISHED")
    if not parsed["native_complete"]:
        issues.append("NATIVE_INCOMPLETE")
    if any(ob["observed"] in _INVENTORY_NONPASS_OR_MISSING for ob in observations.values()):
        issues.append("MISSING_OR_NONPASS_INVENTORY")

    observed_failure_like = any(
        status in ("FAILED", "ERROR", "XPASS") for status in parsed["observed"].values()
    )
    return_code = receipt["return_code"]
    if (
        return_code not in (0, 1)
        or (return_code == 0 and observed_failure_like)
        or (return_code == 1 and not observed_failure_like)
    ):
        issues.append("UNEXPLAINED_EXIT_STATUS")

    return issues


def _build_decision(freeze, receipt, parsed):
    inventory = freeze["inventory"]
    classifications = freeze["classifications"]
    inventory_set = set(inventory)

    observations = {}
    unresolved = set()
    unmatched_expected_failures = set()
    noninventory_failures = set()

    for test_id in inventory:
        row = classifications[test_id]
        observed_status = parsed["observed"].get(test_id, "MISSING")
        assertion_match = matches_expected_assertion(test_id, observed_status, row, parsed)

        observations[test_id] = {
            "disposition": row["disposition"],
            "observed": observed_status,
            "matches_expected_assertion": bool(assertion_match),
        }

        if row["disposition"] == "UNRESOLVED":
            unresolved.add(test_id)
        if row["disposition"] == "EXPECTED_CHANGE" and observed_status == "FAILED" and not assertion_match:
            unmatched_expected_failures.add(test_id)

    for test_id, status in parsed["observed"].items():
        if test_id not in inventory_set and status in ("FAILED", "ERROR", "XPASS"):
            noninventory_failures.add(test_id)

    execution_issues = _execution_issues(receipt, parsed, observations)
    execution_complete = len(execution_issues) == 0

    preserve_ids = [test_id for test_id in inventory if classifications[test_id]["disposition"] == "PRESERVE"]
    regressions = [test_id for test_id in preserve_ids if observations[test_id]["observed"] in ("FAILED", "ERROR")]
    expected_ids = [test_id for test_id in inventory if classifications[test_id]["disposition"] == "EXPECTED_CHANGE"]

    if not preserve_ids:
        preserve_status = "EMPTY"
    elif regressions:
        preserve_status = "REGRESSION_DETECTED"
    elif not execution_complete:
        preserve_status = "UNOBSERVED"
    else:
        preserve_status = "PRESERVED"

    if not execution_complete:
        status = "EXECUTION_UNRESOLVED"
    elif regressions:
        status = "REGRESSION_DETECTED"
    elif unresolved or unmatched_expected_failures or noninventory_failures:
        status = "OBLIGATION_UNRESOLVED"
    elif not preserve_ids:
        status = "NO_PRESERVE_OBLIGATIONS"
    elif expected_ids:
        status = "PRESERVE_SUBSET_PASSED_WITH_EXPECTED_CHANGE"
    else:
        status = "BASE_PASSES_PRESERVED"

    return {
        "status": status,
        "native_complete": bool(parsed["native_complete"]),
        "execution_complete": execution_complete,
        "return_code": receipt["return_code"],
        "execution_issues": execution_issues,
        "preserve_status": preserve_status,
        "overall_preservation_confirmed": status == "BASE_PASSES_PRESERVED",
        "issue_fixed": None,
        "observations": observations,
        "unresolved": _sorted_strings(unresolved),
        "unmatched_expected_failures": _sorted_strings(unmatched_expected_failures),
        "noninventory_failures": _sorted_strings(noninventory_failures),
    }


def _validate_base_receipt_for_freeze(receipt, parsed, classifications):
    if receipt["stage"] != "completed" or receipt["timed_out"] or receipt["cancelled"] or receipt["truncated"]:
        protocol_rejected("base receipt incomplete")
    if not receipt["projection"]["applied"] or receipt["projection"]["guard_changed"]:
        protocol_rejected("base projection invalid")
    if receipt["return_code"] != 0:
        protocol_rejected("base return code invalid")
    if not parsed["native_complete"]:
        protocol_rejected("base native log invalid")
    if any(status in ("FAILED", "ERROR", "XPASS") for status in parsed["observed"].values()):
        protocol_rejected("base has nonpassing tests")

    inventory = _sorted_strings(
        [test_id for test_id, status in parsed["observed"].items() if status == "PASSED"]
    )
    if not inventory:
        protocol_rejected("base inventory empty")
    if set(inventory) != set(classifications.keys()):
        protocol_rejected("classification coverage mismatch")
    return inventory


def handle(event, state):
    validate_state(state)
    validated_event = validate_event(event)
    current_state = _prepare_state(state)
    effects = []

    kind = validated_event["kind"]

    if kind == "base_ready":
        if current_state.get("freeze") is not None or current_state.get("outstanding") is not None:
            protocol_rejected("base_ready invalid in current lifecycle")

        domain = cp(validated_event["domain"])
        classifications = cp(validated_event["classifications"])

        current_state["domain"] = domain
        current_state["classifications_input"] = classifications
        current_state["public_evidence"] = cp(validated_event["public_evidence"])
        current_state["current_snapshot"] = domain["base_snapshot_ref"]

        request_number = current_state["next_req"]
        effect = _run_effect(request_number, domain["base_snapshot_ref"], domain)
        current_state["next_req"] = request_number + 1
        current_state["outstanding"] = {"kind": "base", "effect": cp(effect)}

        _set_public(current_state, [], None, None)
        effects = [effect]

    elif kind == "execution_completed":
        outstanding = current_state.get("outstanding")
        if outstanding is None:
            protocol_rejected("unexpected receipt")

        receipt = validated_event["receipt"]
        effect = outstanding["effect"]
        if not _receipt_matches_outstanding(receipt, effect):
            protocol_rejected("receipt identity mismatch")

        parsed = parse_native_log(current_state["domain"]["parser"], receipt["stdout"], receipt["stderr"])

        if outstanding["kind"] == "base":
            inventory = _validate_base_receipt_for_freeze(
                receipt, parsed, current_state["classifications_input"]
            )
            freeze = {
                "id": "freeze-1",
                "base_snapshot_ref": current_state["domain"]["base_snapshot_ref"],
                "classifications": cp(current_state["classifications_input"]),
                "inventory": list(inventory),
            }
            current_state["freeze"] = freeze
            current_state["outstanding"] = None
            _set_public(current_state, freeze["inventory"], freeze, None)
        else:
            freeze = current_state["freeze"]
            decision = _build_decision(freeze, receipt, parsed)
            current_state["outstanding"] = None
            _set_public(current_state, freeze["inventory"], freeze, decision)

            msg_number = current_state["next_msg"]
            msg_id = _message_id(msg_number)
            current_state["next_msg"] = msg_number + 1
            current_state["pending_msgs"][msg_id] = {
                "execution_request_id": effect["request_id"],
                "freeze_id": freeze["id"],
            }

            effects = [
                {
                    "kind": "observation",
                    "message_id": msg_id,
                    "content": _observation_content(decision, freeze["id"], effect["request_id"]),
                    "evidence_refs": [effect["request_id"], freeze["id"]],
                }
            ]

    elif kind == "workspace_changed":
        if current_state.get("freeze") is None:
            protocol_rejected("workspace_changed before base freeze")
        if current_state.get("outstanding") is not None:
            protocol_rejected("workspace_changed while request outstanding")
        if validated_event["before_snapshot"] != current_state.get("current_snapshot"):
            protocol_rejected("snapshot continuity lost")

        current_state["current_snapshot"] = validated_event["after_snapshot"]

        if (
            validated_event["before_snapshot"] != validated_event["after_snapshot"]
            and validated_event["controller_status"] == "RUNNING"
            and validated_event["remaining_responses"] > 0
            and validated_event["remaining_output_chars"] > 0
            and validated_event["tool"] != "task_complete"
        ):
            request_number = current_state["next_req"]
            effect = _run_effect(request_number, validated_event["after_snapshot"], current_state["domain"])
            current_state["next_req"] = request_number + 1
            current_state["outstanding"] = {"kind": "candidate", "effect": cp(effect)}
            effects = [effect]

    elif kind == "feedback_delivered":
        pending = current_state.get("pending_msgs", {})
        message_id = validated_event["message_id"]
        if message_id not in pending:
            protocol_rejected("unknown or repeated message delivery")
        del pending[message_id]
        current_state["pending_msgs"] = pending

    return {"state": current_state, "effects": effects}
