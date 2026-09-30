import copy


def clone_json(value):
    return copy.deepcopy(value)


def _relative_path(path):
    if type(path) is not str or not path or path.startswith("/") or path.startswith("."):
        return False
    return all(part and not part.startswith(".") for part in path.split("/"))


def _simple_case(case):
    return {
        "id": case["id"],
        "role": case["role"],
        "test": case["test"],
        "status": case["status"],
        "reason": case["reason"],
    }


def _unknown(reason, cases=None):
    return {
        "status": "UNKNOWN",
        "reason": reason,
        "cases": [] if cases is None else cases,
    }


def _validate_input_hashes(value, expected):
    return type(value) is dict and value == expected


def _validate_outer_receipt(receipt, expected):
    if type(receipt) is not dict:
        return False, "OUTER_RECEIPT_INVALID"
    if receipt.get("stage") != "completed":
        return False, "OUTER_STAGE_INVALID"
    if receipt.get("return_code") != 0:
        return False, "OUTER_RETURN_CODE_INVALID"
    if receipt.get("timed_out") is not False:
        return False, "OUTER_TIMED_OUT"
    if receipt.get("truncated") is not False:
        return False, "OUTER_TRUNCATED"
    if receipt.get("cancelled") is not False:
        return False, "OUTER_CANCELLED"
    if receipt.get("environment_deleted") is not True:
        return False, "OUTER_ENVIRONMENT_NOT_DELETED"
    if not _validate_input_hashes(receipt.get("input_hashes"), expected["input_hashes"]):
        return False, "OUTER_INPUT_HASH_MISMATCH"
    projection = receipt.get("projection")
    if type(projection) is not dict or "projected_tree" not in projection:
        return False, "OUTER_PROJECTION_INVALID"
    return True, projection["projected_tree"]


def _validate_behavior_execution(behavior, expected, projected_tree):
    if type(behavior) is not dict:
        return False, "BEHAVIOR_EXECUTION_INVALID", None
    if behavior.get("request_id") != expected["request_id"]:
        return False, "BEHAVIOR_REQUEST_ID_MISMATCH", None
    if behavior.get("snapshot_ref") != expected["snapshot_ref"]:
        return False, "BEHAVIOR_SNAPSHOT_MISMATCH", None
    if not _validate_input_hashes(behavior.get("input_hashes"), expected["input_hashes"]):
        return False, "BEHAVIOR_INPUT_HASH_MISMATCH", None
    if behavior.get("host_status") != "COMPLETED":
        return False, "BEHAVIOR_HOST_STATUS_INVALID", None
    if behavior.get("before_tree") != projected_tree or behavior.get("after_tree") != projected_tree:
        return False, "BEHAVIOR_TREE_MISMATCH", None
    if behavior.get("repository_unchanged") is not True:
        return False, "BEHAVIOR_REPOSITORY_CHANGED", None
    child = behavior.get("child")
    if type(child) is not dict:
        return False, "BEHAVIOR_CHILD_INVALID", None
    if child.get("return_code") != 0 or child.get("timed_out") is not False or child.get("truncated") is not False:
        return False, "BEHAVIOR_CHILD_FAILED", None
    observation = behavior.get("observation")
    if type(observation) is not dict:
        return False, "BEHAVIOR_OBSERVATION_INVALID", None
    return True, "READY", observation


def _validate_child_identity(identity):
    if type(identity) is not dict:
        return False
    return (
        identity.get("uid") == 65534
        and identity.get("gid") == 65534
        and identity.get("groups") == []
        and identity.get("no_new_privileges") == 1
    )


def _validate_case_row(case, expected_row):
    if type(case) is not dict:
        return False, "CASE_NOT_OBJECT", None
    needed = ("id", "role", "basis", "test", "status", "reason")
    if not all(type(case.get(k)) is str and case.get(k) for k in needed):
        return False, "CASE_FIELDS_INVALID", None
    if (
        case["id"] != expected_row["id"]
        or case["role"] != expected_row["role"]
        or case["basis"] != expected_row["basis"]
        or case["test"] != expected_row["test"]
    ):
        return False, "CASE_IDENTITY_MISMATCH", None
    if case["status"] not in ("PASS", "FAIL", "UNKNOWN"):
        return False, "CASE_STATUS_INVALID", None
    executed = case.get("executed_source")
    if case["status"] in ("PASS", "FAIL"):
        if type(executed) is not list or not executed:
            return False, "CASE_EXECUTION_SITES_MISSING", None
        clean_sites = []
        for row in executed:
            if (
                type(row) is not dict
                or not _relative_path(row.get("path"))
                or type(row.get("line")) is not int
                or row.get("line") <= 0
            ):
                return False, "CASE_EXECUTION_SITE_INVALID", None
            clean_sites.append({"path": row["path"], "line": row["line"]})
    else:
        clean_sites = []
    clean = {
        "id": case["id"],
        "role": case["role"],
        "basis": case["basis"],
        "test": case["test"],
        "status": case["status"],
        "reason": case["reason"],
        "executed_source": clean_sites,
    }
    return True, "READY", clean


def _validate_observation(observation, expected):
    if observation.get("schema") != "agent2skill.behavior-observations/1":
        return False, "OBSERVATION_SCHEMA_INVALID", None
    if observation.get("host_status") != "COMPLETED":
        return False, "OBSERVATION_HOST_STATUS_INVALID", None
    if observation.get("script_sha256") != expected["script_sha256"]:
        return False, "OBSERVATION_SCRIPT_HASH_MISMATCH", None
    if type(observation.get("repository_imports")) is not list:
        return False, "OBSERVATION_IMPORTS_INVALID", None
    if not _validate_child_identity(observation.get("child_identity")):
        return False, "OBSERVATION_CHILD_IDENTITY_INVALID", None
    cases = observation.get("cases")
    if type(cases) is not list:
        return False, "OBSERVATION_CASES_INVALID", None
    expected_rows = {}
    for row in expected["card"]["obligations"]:
        expected_rows[row["id"]] = {
            "id": row["id"],
            "role": row["role"],
            "basis": row["basis"],
            "test": expected["mapping"][row["id"]],
        }
    if len(cases) != len(expected_rows):
        return False, "OBSERVATION_CASE_COUNT_INVALID", None
    seen = set()
    clean_cases = []
    for case in cases:
        case_id = case.get("id") if type(case) is dict else None
        if case_id in seen or case_id not in expected_rows:
            return False, "OBSERVATION_CASE_ROSTER_INVALID", None
        seen.add(case_id)
        ok, reason, clean = _validate_case_row(case, expected_rows[case_id])
        if not ok:
            return False, reason, None
        clean_cases.append(clean)
    if set(seen) != set(expected_rows):
        return False, "OBSERVATION_CASE_ROSTER_INVALID", None
    return True, "READY", clean_cases


def _classify_base(cases):
    statuses = [case["status"] for case in cases]
    if "UNKNOWN" in statuses:
        return "UNKNOWN", "UNKNOWN_CASE_PRESENT"
    any_issue_fail = any(case["role"] == "issue" and case["status"] == "FAIL" for case in cases)
    any_control_fail = any(case["role"] == "control" and case["status"] != "PASS" for case in cases)
    all_pass = all(case["status"] == "PASS" for case in cases)
    if not any_control_fail and any_issue_fail:
        return "BASE_ADMITTED", "ISSUE_REPRODUCED_WITH_PASSING_CONTROLS"
    if all_pass:
        return "BASE_NOT_REPRODUCED", "ALL_CASES_PASS"
    if any_control_fail:
        return "BASE_NOT_REPRODUCED", "CONTROL_CASE_FAILED"
    if not any_issue_fail:
        return "BASE_NOT_REPRODUCED", "NO_ISSUE_FAILURE"
    return "UNKNOWN", "BASE_CLASSIFICATION_INDETERMINATE"


def _classify_candidate(cases):
    statuses = [case["status"] for case in cases]
    if "UNKNOWN" in statuses:
        return "UNKNOWN", "UNKNOWN_CASE_PRESENT"
    if all(case["status"] == "PASS" for case in cases):
        return "COVERED_PASS", "ALL_CASES_PASS"
    return "COVERED_FAIL", "AT_LEAST_ONE_CASE_FAILED"


def interpret_execution_receipt(receipt, expected, mode):
    ok, projected_tree_or_reason = _validate_outer_receipt(receipt, expected)
    if not ok:
        return _unknown(projected_tree_or_reason)
    ok, reason, observation = _validate_behavior_execution(
        receipt.get("behavior_execution"), expected, projected_tree_or_reason
    )
    if not ok:
        return _unknown(reason)
    ok, reason, clean_cases = _validate_observation(observation, expected)
    if not ok:
        return _unknown(reason)
    simple_cases = [_simple_case(case) for case in sorted(clean_cases, key=lambda row: row["id"])]
    if mode == "base":
        status, classify_reason = _classify_base(clean_cases)
    else:
        status, classify_reason = _classify_candidate(clean_cases)
    return {
        "status": status,
        "reason": classify_reason,
        "cases": simple_cases,
    }
