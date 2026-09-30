import copy
import re

HEX64 = re.compile(r"^[0-9a-f]{64}$")


def protocol_rejected(msg):
    raise ValueError("PROTOCOL_REJECTED: " + msg)


def cp(x):
    return copy.deepcopy(x)


def is_obj(x):
    return isinstance(x, dict)


def is_str(x):
    return isinstance(x, str)


def is_nes(x):
    return isinstance(x, str) and x.strip() != ""


def is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def req_obj(x, name, keys=None, allow_extra=False):
    if not is_obj(x):
        protocol_rejected(name + " must be object")
    if keys is not None:
        ks, want = set(x), set(keys)
        if ks != want and not allow_extra:
            protocol_rejected(name + " has wrong fields")
        if not want <= ks:
            protocol_rejected(name + " missing fields")
    return x


def req_nes(x, name, max_len=None):
    if not is_nes(x):
        protocol_rejected(name + " must be nonempty string")
    if max_len is not None and len(x) > max_len:
        protocol_rejected(name + " too long")
    return x


def req_int(x, name, lo=None, hi=None):
    if not is_int(x):
        protocol_rejected(name + " must be integer")
    if lo is not None and x < lo:
        protocol_rejected(name + " below minimum")
    if hi is not None and x > hi:
        protocol_rejected(name + " above maximum")
    return x


def req_bool(x, name):
    if not isinstance(x, bool):
        protocol_rejected(name + " must be boolean")
    return x


def req_str_list(x, name, nonempty=False):
    if not isinstance(x, list):
        protocol_rejected(name + " must be array")
    seen = set()
    for i, v in enumerate(x):
        if not is_str(v):
            protocol_rejected(f"{name}[{i}] must be string")
        if v in seen:
            protocol_rejected(name + " must be unique")
        seen.add(v)
    if nonempty and not x:
        protocol_rejected(name + " must be nonempty")
    return x


def req_relpath(p, name):
    req_nes(p, name)
    if p.startswith("/"):
        protocol_rejected(name + " must be relative path")
    if "\x00" in p:
        protocol_rejected(name + " invalid path")
    parts = p.split("/")
    if any(part in ("", ".", "..", ".git") for part in parts):
        protocol_rejected(name + " invalid path")
    return p


def validate_file_identity(x, name):
    req_obj(x, name, {"sha256", "executable"})
    if not (is_str(x["sha256"]) and HEX64.fullmatch(x["sha256"])):
        protocol_rejected(name + ".sha256 invalid")
    req_bool(x["executable"], name + ".executable")
    return x


def validate_execution_spec(x, name):
    req_obj(x, name, {"command", "cwd"})
    req_nes(x["command"], name + ".command", 16000)
    if x["cwd"] != "/testbed":
        protocol_rejected(name + ".cwd invalid")
    return x


def validate_projection_spec(x, name):
    req_obj(x, name, {"replace_from_base", "expected_files", "guards"})

    req_str_list(x["replace_from_base"], name + ".replace_from_base")
    for i, p in enumerate(x["replace_from_base"]):
        req_relpath(p, f"{name}.replace_from_base[{i}]")

    if not is_obj(x["expected_files"]):
        protocol_rejected(name + ".expected_files must be object")
    for p, ident in x["expected_files"].items():
        req_relpath(p, name + ".expected_files key")
        validate_file_identity(ident, name + ".expected_files[" + p + "]")

    if not is_obj(x["guards"]):
        protocol_rejected(name + ".guards must be object")
    for p, ident in x["guards"].items():
        req_relpath(p, name + ".guards key")
        if ident is None:
            continue
        validate_file_identity(ident, name + ".guards[" + p + "]")

    return x


def validate_limits(x, name):
    req_obj(x, name, {"timeout_seconds", "output_bytes"})
    req_int(x["timeout_seconds"], name + ".timeout_seconds", 1, 120)
    req_int(x["output_bytes"], name + ".output_bytes", 1, 2097152)
    return x


def validate_domain_spec(x):
    req_obj(
        x,
        "domain",
        {
            "base_commit",
            "base_snapshot_ref",
            "parser",
            "origin",
            "execution_spec",
            "projection_spec",
            "limits",
        },
    )
    req_nes(x["base_commit"], "domain.base_commit")
    req_nes(x["base_snapshot_ref"], "domain.base_snapshot_ref")
    if x["parser"] not in ("django_verbose", "pytest_verbose"):
        protocol_rejected("domain.parser invalid")
    req_nes(x["origin"], "domain.origin")
    validate_execution_spec(x["execution_spec"], "domain.execution_spec")
    validate_projection_spec(x["projection_spec"], "domain.projection_spec")
    validate_limits(x["limits"], "domain.limits")
    return x


def validate_assertion(x, name):
    req_obj(x, name, {"file", "line", "source", "exception", "message"})
    req_nes(x["file"], name + ".file")
    req_int(x["line"], name + ".line", 1)
    req_nes(x["source"], name + ".source")
    if x["exception"] != "AssertionError":
        protocol_rejected(name + ".exception invalid")
    req_nes(x["message"], name + ".message")
    return x


def validate_classifications(cls, evidence):
    if not is_obj(cls):
        protocol_rejected("classifications must be object")
    if not is_obj(evidence):
        protocol_rejected("public_evidence must be object")

    for k, v in evidence.items():
        req_nes(k, "public_evidence key")
        if not is_obj(v):
            protocol_rejected("public_evidence value must be object")

    for tid, row in cls.items():
        req_nes(tid, "classification key")
        if not is_obj(row):
            protocol_rejected("classification row must be object")

        disp = row.get("disposition")
        if disp not in ("PRESERVE", "EXPECTED_CHANGE", "UNRESOLVED"):
            protocol_rejected("classification disposition invalid")

        req_nes(row.get("reason"), f"classifications[{tid}].reason")
        req_str_list(row.get("evidence_refs"), f"classifications[{tid}].evidence_refs", True)
        for ref in row["evidence_refs"]:
            if ref not in evidence:
                protocol_rejected("classification evidence ref missing")
        req_nes(row.get("granularity"), f"classifications[{tid}].granularity")

        if disp == "EXPECTED_CHANGE":
            if row.get("granularity") != "single_assertion_test":
                protocol_rejected("EXPECTED_CHANGE granularity invalid")
            req_nes(row.get("issue_requirement"), f"classifications[{tid}].issue_requirement")
            validate_assertion(row.get("assertion"), f"classifications[{tid}].assertion")

    return cls


def validate_projection_receipt(x):
    req_obj(x, "receipt.projection", allow_extra=True)
    if "applied" not in x or "guard_changed" not in x:
        protocol_rejected("receipt.projection missing fields")
    req_bool(x["applied"], "receipt.projection.applied")
    req_str_list(x["guard_changed"], "receipt.projection.guard_changed")
    return x


def validate_receipt_shape(x):
    req_obj(x, "receipt", allow_extra=True)
    need = {
        "request_id",
        "snapshot_ref",
        "execution_spec",
        "projection_spec",
        "limits",
        "stdout",
        "stderr",
        "return_code",
        "timed_out",
        "cancelled",
        "truncated",
        "environment_deleted",
        "stage",
        "projection",
    }
    if not need <= set(x):
        protocol_rejected("receipt missing fields")

    req_nes(x["request_id"], "receipt.request_id", 256)
    req_nes(x["snapshot_ref"], "receipt.snapshot_ref")
    validate_execution_spec(x["execution_spec"], "receipt.execution_spec")
    validate_projection_spec(x["projection_spec"], "receipt.projection_spec")
    validate_limits(x["limits"], "receipt.limits")

    if not is_str(x["stdout"]) or not is_str(x["stderr"]):
        protocol_rejected("receipt stdout/stderr invalid")
    if x["return_code"] is not None and not is_int(x["return_code"]):
        protocol_rejected("receipt.return_code invalid")

    for k in ("timed_out", "cancelled", "truncated", "environment_deleted"):
        req_bool(x[k], "receipt." + k)

    req_nes(x["stage"], "receipt.stage")
    validate_projection_receipt(x["projection"])
    return x


def validate_event(ev):
    if not is_obj(ev) or "kind" not in ev or not is_str(ev["kind"]):
        protocol_rejected("event invalid")

    k = ev["kind"]
    if k == "base_ready":
        req_obj(ev, "event", {"kind", "snapshot_ref", "domain", "classifications", "public_evidence"})
        req_nes(ev["snapshot_ref"], "event.snapshot_ref")
        validate_domain_spec(ev["domain"])
        if ev["snapshot_ref"] != ev["domain"]["base_snapshot_ref"]:
            protocol_rejected("base snapshot mismatch")
        validate_classifications(ev["classifications"], ev["public_evidence"])

    elif k == "execution_completed":
        req_obj(ev, "event", {"kind", "receipt"})
        validate_receipt_shape(ev["receipt"])

    elif k == "workspace_changed":
        req_obj(
            ev,
            "event",
            {
                "kind",
                "before_snapshot",
                "after_snapshot",
                "tool",
                "controller_status",
                "remaining_responses",
                "remaining_output_chars",
            },
        )
        req_nes(ev["before_snapshot"], "event.before_snapshot")
        req_nes(ev["after_snapshot"], "event.after_snapshot")
        req_nes(ev["tool"], "event.tool")
        req_nes(ev["controller_status"], "event.controller_status")
        req_int(ev["remaining_responses"], "event.remaining_responses", 0)
        req_int(ev["remaining_output_chars"], "event.remaining_output_chars", 0)

    elif k == "feedback_delivered":
        req_obj(ev, "event", {"kind", "message_id", "request_id", "completed"})
        req_nes(ev["message_id"], "event.message_id", 256)
        req_int(ev["request_id"], "event.request_id", 1)
        if ev["completed"] is not True:
            protocol_rejected("event.completed invalid")

    else:
        protocol_rejected("unknown event kind")

    return ev


def validate_state(x):
    if not is_obj(x):
        protocol_rejected("state must be object")
    return x


def public_state(inv, freeze, decision):
    return {"inventory": list(inv), "freeze": freeze, "decision": decision}


def base_shell():
    return {
        "public": public_state([], None, None),
        "next_req": 1,
        "next_msg": 1,
        "pending_msgs": {},
    }
