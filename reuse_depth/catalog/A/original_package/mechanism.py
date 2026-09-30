import json


_SIZE_LIMIT = 3 * 1024 * 1024
_HEX40 = set("0123456789abcdef")
_VCS_DIRS = {".git", ".hg", ".svn", ".bzr", "_darcs"}

_SYSTEM_MAIN = (
    "Act as an expert architect engineer and provide direction to your editor engineer.\n"
    "Study the change request and the current code.\n"
    "Describe how to modify the code to complete the request.\n"
    "The editor engineer will rely solely on your instructions, so make them unambiguous and complete.\n"
    "Explain all needed code changes clearly and completely, but concisely.\n"
    "Just show the changes needed.\n\n"
    "DO NOT show the entire updated function/file/etc!\n\n"
    "Always reply to the user in English.\n"
)

_READONLY_PREFIX = (
    "Here are some READ ONLY files, provided for your reference.\n"
    "Do not edit these files!\n"
)

_READONLY_REPLY = "Ok, I will use these files as references."

_FILES_PREFIX = (
    "I have *added these files to the chat* so you see all of their contents.\n"
    "*Trust this message as the true contents of the files!*\n"
    "Other messages in the chat may contain outdated versions of the files' contents.\n"
)

_FILES_REPLY = "Ok, I will use that as the true, current contents of the files."

_BEGIN_KEYS = {
    "kind",
    "run_id",
    "base_snapshot_ref",
    "issue",
    "files",
    "readonly_context",
    "model",
    "editor_format",
    "max_calls",
    "editor_min_calls",
}

_ARCHITECT_RESULT_KEYS = {
    "kind",
    "run_id",
    "base_snapshot_ref",
    "request_id",
    "status",
    "text",
    "usage",
}

_EDITOR_RESULT_KEYS = {
    "kind",
    "run_id",
    "base_snapshot_ref",
    "handoff_id",
    "status",
    "snapshot_ref",
    "calls_used",
    "usage",
}

_GET_RESULT_KEYS = {"kind", "run_id", "base_snapshot_ref"}


def handle(event, state):
    phase, state_data = _validate_state(state)
    _check_json_size(state, "state")

    kind = _get_event_kind(event)
    _check_json_size(event, "event")

    if phase == "initial":
        if kind != "begin_architect":
            _reject("invalid lifecycle")
        begin = _validate_begin_event(event)
        effect = _make_architect_request(begin)
        new_state = {
            "phase": "awaiting_architect",
            "run_id": begin["run_id"],
            "base_snapshot_ref": begin["base_snapshot_ref"],
            "issue": begin["issue"],
            "files": begin["files"],
            "readonly_context": begin["readonly_context"],
            "model": begin["model"],
            "editor_format": begin["editor_format"],
            "max_calls": begin["max_calls"],
            "editor_min_calls": begin["editor_min_calls"],
            "request_id": effect["request_id"],
        }
        return _finish(new_state, effect)

    if phase == "awaiting_architect":
        _validate_common_against_state(event, state_data)
        if kind != "architect_result":
            _reject("invalid lifecycle")
        receipt = _validate_architect_result_event(event)
        if receipt["request_id"] != state_data["request_id"]:
            _reject("request_id mismatch")

        usage = receipt["usage"]
        if receipt["status"] != "completed":
            terminal = _make_terminal(
                run_id=state_data["run_id"],
                base_snapshot_ref=state_data["base_snapshot_ref"],
                status="UNAVAILABLE",
                final_snapshot_ref=None,
                editor_status=None,
                calls_used=1,
                usage=usage,
            )
            new_state = _make_terminal_state(terminal)
            return _finish(new_state, terminal)

        text = receipt["text"]
        if not text.strip():
            terminal = _make_terminal(
                run_id=state_data["run_id"],
                base_snapshot_ref=state_data["base_snapshot_ref"],
                status="EMPTY",
                final_snapshot_ref=state_data["base_snapshot_ref"],
                editor_status=None,
                calls_used=1,
                usage=usage,
            )
            new_state = _make_terminal_state(terminal)
            return _finish(new_state, terminal)

        remaining_calls = state_data["max_calls"] - 1
        if remaining_calls < state_data["editor_min_calls"]:
            terminal = _make_terminal(
                run_id=state_data["run_id"],
                base_snapshot_ref=state_data["base_snapshot_ref"],
                status="BUDGET_STOP",
                final_snapshot_ref=state_data["base_snapshot_ref"],
                editor_status=None,
                calls_used=1,
                usage=usage,
            )
            new_state = _make_terminal_state(terminal)
            return _finish(new_state, terminal)

        effect = _make_editor_handoff(
            run_id=state_data["run_id"],
            base_snapshot_ref=state_data["base_snapshot_ref"],
            handoff_id=state_data["run_id"] + "/editor/1",
            task_text=text,
            files=state_data["files"],
            readonly_context=state_data["readonly_context"],
            model=state_data["model"],
            editor_format=state_data["editor_format"],
            remaining_calls=remaining_calls,
            usage=usage,
        )
        new_state = {
            "phase": "awaiting_editor",
            "run_id": state_data["run_id"],
            "base_snapshot_ref": state_data["base_snapshot_ref"],
            "files": state_data["files"],
            "readonly_context": state_data["readonly_context"],
            "model": state_data["model"],
            "editor_format": state_data["editor_format"],
            "handoff_id": effect["handoff_id"],
            "remaining_calls": remaining_calls,
            "architect_usage": usage,
        }
        return _finish(new_state, effect)

    if phase == "awaiting_editor":
        _validate_common_against_state(event, state_data)
        if kind != "editor_result":
            _reject("invalid lifecycle")
        result = _validate_editor_result_event(event, state_data["remaining_calls"])
        if result["handoff_id"] != state_data["handoff_id"]:
            _reject("handoff_id mismatch")

        total_usage = _sum_usage(state_data["architect_usage"], result["usage"])
        terminal = _make_terminal(
            run_id=state_data["run_id"],
            base_snapshot_ref=state_data["base_snapshot_ref"],
            status="COMPLETE",
            final_snapshot_ref=result["snapshot_ref"],
            editor_status=result["status"],
            calls_used=1 + result["calls_used"],
            usage=total_usage,
        )
        new_state = _make_terminal_state(terminal)
        return _finish(new_state, terminal)

    if phase == "terminal":
        _validate_common_against_state(event, state_data)
        if kind != "get_result":
            _reject("invalid lifecycle")
        _validate_get_result_event(event)
        return _finish(state_data["raw"], state_data["terminal"])

    _reject("invalid state")


def _finish(state, effect):
    _check_json_size(state, "state")
    _check_json_size(effect, "effect")
    return {"state": state, "effects": [effect]}


def _make_terminal_state(terminal):
    return {
        "phase": "terminal",
        "run_id": terminal["run_id"],
        "base_snapshot_ref": terminal["base_snapshot_ref"],
        "terminal": terminal,
    }


def _get_event_kind(event):
    if type(event) is not dict:
        _reject("event must be object")
    if "kind" not in event:
        _reject("missing event.kind")
    if type(event["kind"]) is not str:
        _reject("event.kind must be string")
    if event["kind"] not in {
        "begin_architect",
        "architect_result",
        "editor_result",
        "get_result",
    }:
        _reject("unknown event kind")
    return event["kind"]


def _validate_state(state):
    if type(state) is not dict:
        _reject("state must be object")
    if state == {}:
        return "initial", {}
    if set(state.keys()) != {"phase", "run_id", "base_snapshot_ref", "terminal"} and set(
        state.keys()
    ) != {
        "phase",
        "run_id",
        "base_snapshot_ref",
        "issue",
        "files",
        "readonly_context",
        "model",
        "editor_format",
        "max_calls",
        "editor_min_calls",
        "request_id",
    } and set(state.keys()) != {
        "phase",
        "run_id",
        "base_snapshot_ref",
        "files",
        "readonly_context",
        "model",
        "editor_format",
        "handoff_id",
        "remaining_calls",
        "architect_usage",
    }:
        _reject("invalid state keys")
    if type(state.get("phase")) is not str:
        _reject("state.phase must be string")

    phase = state["phase"]
    if phase == "awaiting_architect":
        _validate_run_id(state["run_id"])
        _validate_snapshot_ref(state["base_snapshot_ref"], "state.base_snapshot_ref")
        if type(state["issue"]) is not str:
            _reject("state.issue must be string")
        files = _validate_file_views(state["files"], "state.files", require_nonempty=True)
        readonly = _validate_file_views(
            state["readonly_context"], "state.readonly_context", require_nonempty=False
        )
        _validate_disjoint_files(files, readonly)
        _validate_model(state["model"], "state.model")
        _validate_editor_format(state["editor_format"], "state.editor_format")
        _validate_int_range(state["max_calls"], "state.max_calls", 1, 7)
        _validate_int_range(state["editor_min_calls"], "state.editor_min_calls", 1, 4)
        if type(state["request_id"]) is not str:
            _reject("state.request_id must be string")
        if state["request_id"] != state["run_id"] + "/architect/1":
            _reject("invalid state.request_id")
        return phase, state

    if phase == "awaiting_editor":
        _validate_run_id(state["run_id"])
        _validate_snapshot_ref(state["base_snapshot_ref"], "state.base_snapshot_ref")
        files = _validate_file_views(state["files"], "state.files", require_nonempty=True)
        readonly = _validate_file_views(
            state["readonly_context"], "state.readonly_context", require_nonempty=False
        )
        _validate_disjoint_files(files, readonly)
        _validate_model(state["model"], "state.model")
        _validate_editor_format(state["editor_format"], "state.editor_format")
        if type(state["handoff_id"]) is not str:
            _reject("state.handoff_id must be string")
        if state["handoff_id"] != state["run_id"] + "/editor/1":
            _reject("invalid state.handoff_id")
        _validate_int_range(state["remaining_calls"], "state.remaining_calls", 0, 6)
        _validate_usage_pair(state["architect_usage"], "state.architect_usage")
        return phase, state

    if phase == "terminal":
        _validate_run_id(state["run_id"])
        _validate_snapshot_ref(state["base_snapshot_ref"], "state.base_snapshot_ref")
        terminal = _validate_terminal_effect(
            state["terminal"], state["run_id"], state["base_snapshot_ref"]
        )
        return phase, {
            "raw": state,
            "terminal": terminal,
            "run_id": state["run_id"],
            "base_snapshot_ref": state["base_snapshot_ref"],
        }

    _reject("invalid state.phase")


def _validate_common_against_state(event, state):
    if type(event) is not dict:
        _reject("event must be object")
    if "run_id" not in event or "base_snapshot_ref" not in event:
        _reject("missing common event fields")
    _validate_run_id(event["run_id"])
    _validate_snapshot_ref(event["base_snapshot_ref"], "event.base_snapshot_ref")
    if event["run_id"] != state["run_id"]:
        _reject("run_id mismatch")
    if event["base_snapshot_ref"] != state["base_snapshot_ref"]:
        _reject("base_snapshot_ref mismatch")


def _validate_begin_event(event):
    _assert_exact_keys(event, _BEGIN_KEYS, "begin_architect")
    if event["kind"] != "begin_architect":
        _reject("event.kind mismatch")
    _validate_run_id(event["run_id"])
    _validate_snapshot_ref(event["base_snapshot_ref"], "event.base_snapshot_ref")
    if type(event["issue"]) is not str:
        _reject("event.issue must be string")
    files = _validate_file_views(event["files"], "event.files", require_nonempty=True)
    readonly = _validate_file_views(
        event["readonly_context"], "event.readonly_context", require_nonempty=False
    )
    _validate_disjoint_files(files, readonly)
    _validate_model(event["model"], "event.model")
    _validate_editor_format(event["editor_format"], "event.editor_format")
    _validate_int_range(event["max_calls"], "event.max_calls", 1, 7)
    _validate_int_range(event["editor_min_calls"], "event.editor_min_calls", 1, 4)
    return event


def _validate_architect_result_event(event):
    _assert_exact_keys(event, _ARCHITECT_RESULT_KEYS, "architect_result")
    if event["kind"] != "architect_result":
        _reject("event.kind mismatch")
    _validate_run_id(event["run_id"])
    _validate_snapshot_ref(event["base_snapshot_ref"], "event.base_snapshot_ref")
    if type(event["request_id"]) is not str:
        _reject("event.request_id must be string")
    if event["status"] not in {"completed", "incomplete", "failed", "unknown"}:
        _reject("invalid event.status")
    if event["status"] == "completed":
        if type(event["text"]) is not str:
            _reject("completed architect_result.text must be string")
    else:
        if event["text"] is not None:
            _reject("non-completed architect_result.text must be null")
    event["usage"] = _validate_architect_usage(event["usage"], event["status"], "event.usage")
    return event


def _validate_editor_result_event(event, remaining_calls):
    _assert_exact_keys(event, _EDITOR_RESULT_KEYS, "editor_result")
    if event["kind"] != "editor_result":
        _reject("event.kind mismatch")
    _validate_run_id(event["run_id"])
    _validate_snapshot_ref(event["base_snapshot_ref"], "event.base_snapshot_ref")
    if type(event["handoff_id"]) is not str:
        _reject("event.handoff_id must be string")
    if event["status"] not in {"completed", "resource_stop"}:
        _reject("invalid event.status")
    _validate_snapshot_ref(event["snapshot_ref"], "event.snapshot_ref")
    _validate_int_range(event["calls_used"], "event.calls_used", 0, remaining_calls)
    event["usage"] = _validate_usage_pair(event["usage"], "event.usage")
    return event


def _validate_get_result_event(event):
    _assert_exact_keys(event, _GET_RESULT_KEYS, "get_result")
    if event["kind"] != "get_result":
        _reject("event.kind mismatch")
    _validate_run_id(event["run_id"])
    _validate_snapshot_ref(event["base_snapshot_ref"], "event.base_snapshot_ref")
    return event


def _validate_terminal_effect(effect, run_id, base_snapshot_ref):
    expected = {
        "kind",
        "run_id",
        "base_snapshot_ref",
        "status",
        "final_snapshot_ref",
        "editor_status",
        "calls_used",
        "usage",
    }
    if type(effect) is not dict:
        _reject("state.terminal must be object")
    _assert_exact_keys(effect, expected, "state.terminal")
    if effect["kind"] != "architect_terminal":
        _reject("invalid state.terminal.kind")
    if effect["run_id"] != run_id:
        _reject("invalid state.terminal.run_id")
    if effect["base_snapshot_ref"] != base_snapshot_ref:
        _reject("invalid state.terminal.base_snapshot_ref")
    if effect["status"] not in {"UNAVAILABLE", "EMPTY", "BUDGET_STOP", "COMPLETE"}:
        _reject("invalid state.terminal.status")
    if not _is_int(effect["calls_used"]) or effect["calls_used"] < 1:
        _reject("invalid state.terminal.calls_used")

    status = effect["status"]
    if status == "COMPLETE":
        _validate_snapshot_ref(effect["final_snapshot_ref"], "state.terminal.final_snapshot_ref")
        if effect["editor_status"] not in {"completed", "resource_stop"}:
            _reject("invalid state.terminal.editor_status")
        _validate_usage_pair(effect["usage"], "state.terminal.usage")
    elif status == "UNAVAILABLE":
        if effect["final_snapshot_ref"] is not None:
            _reject("invalid state.terminal.final_snapshot_ref")
        if effect["editor_status"] is not None:
            _reject("invalid state.terminal.editor_status")
        if effect["usage"] is not None:
            _validate_usage_pair(effect["usage"], "state.terminal.usage")
    else:
        if effect["final_snapshot_ref"] != base_snapshot_ref:
            _reject("invalid state.terminal.final_snapshot_ref")
        if effect["editor_status"] is not None:
            _reject("invalid state.terminal.editor_status")
        _validate_usage_pair(effect["usage"], "state.terminal.usage")
    return effect


def _make_architect_request(begin):
    messages = [
        {"role": "system", "content": _SYSTEM_MAIN},
    ]
    if begin["readonly_context"]:
        messages.append(
            {
                "role": "user",
                "content": _READONLY_PREFIX + _render_file_views(begin["readonly_context"]),
            }
        )
        messages.append({"role": "assistant", "content": _READONLY_REPLY})
    messages.append(
        {
            "role": "user",
            "content": _FILES_PREFIX + _render_file_views(begin["files"]),
        }
    )
    messages.append({"role": "assistant", "content": _FILES_REPLY})
    messages.append({"role": "user", "content": begin["issue"]})

    return {
        "kind": "architect_request",
        "run_id": begin["run_id"],
        "base_snapshot_ref": begin["base_snapshot_ref"],
        "request_id": begin["run_id"] + "/architect/1",
        "model": begin["model"],
        "messages": messages,
    }


def _make_editor_handoff(
    run_id,
    base_snapshot_ref,
    handoff_id,
    task_text,
    files,
    readonly_context,
    model,
    editor_format,
    remaining_calls,
    usage,
):
    return {
        "kind": "editor_handoff",
        "run_id": run_id,
        "base_snapshot_ref": base_snapshot_ref,
        "handoff_id": handoff_id,
        "task_text": task_text,
        "files": files,
        "readonly_context": readonly_context,
        "model": model,
        "editor_format": editor_format,
        "cur_messages": [],
        "done_messages": [],
        "preproc": False,
        "settings": {
            "suggest_shell_commands": False,
            "map_tokens": 0,
            "cache_prompts": False,
            "num_cache_warming_pings": 0,
            "summarize_from_coder": False,
        },
        "remaining_calls": remaining_calls,
        "calls_used": 1,
        "usage": usage,
    }


def _make_terminal(
    run_id,
    base_snapshot_ref,
    status,
    final_snapshot_ref,
    editor_status,
    calls_used,
    usage,
):
    return {
        "kind": "architect_terminal",
        "run_id": run_id,
        "base_snapshot_ref": base_snapshot_ref,
        "status": status,
        "final_snapshot_ref": final_snapshot_ref,
        "editor_status": editor_status,
        "calls_used": calls_used,
        "usage": usage,
    }


def _render_file_views(rows):
    parts = []
    for row in rows:
        parts.append("\n")
        parts.append(row["path"])
        parts.append("\n```\n")
        parts.append(row["content"])
        parts.append("```\n")
    return "".join(parts)


def _sum_usage(left, right):
    return {
        "input_tokens": left["input_tokens"] + right["input_tokens"],
        "output_tokens": left["output_tokens"] + right["output_tokens"],
    }


def _validate_file_views(value, label, require_nonempty):
    if type(value) is not list:
        _reject(label + " must be list")
    if len(value) > 64:
        _reject(label + " exceeds 64 rows")
    if require_nonempty and not value:
        _reject(label + " must be nonempty")

    out = []
    prev_path = None
    for index, row in enumerate(value):
        row_label = f"{label}[{index}]"
        if type(row) is not dict:
            _reject(row_label + " must be object")
        _assert_exact_keys(row, {"path", "content"}, row_label)
        path = row["path"]
        content = row["content"]
        _validate_path(path, row_label + ".path")
        if type(content) is not str:
            _reject(row_label + ".content must be string")
        if prev_path is not None and path <= prev_path:
            _reject(label + " must be sorted by unique path")
        prev_path = path
        out.append({"path": path, "content": content})
    return out


def _validate_disjoint_files(files, readonly):
    file_paths = {row["path"] for row in files}
    readonly_paths = {row["path"] for row in readonly}
    if file_paths & readonly_paths:
        _reject("files and readonly_context must be disjoint")


def _validate_path(path, label):
    if type(path) is not str:
        _reject(label + " must be string")
    if not path or len(path) > 4096:
        _reject(label + " length invalid")
    if "\\" in path:
        _reject(label + " must not contain backslash")
    for ch in path:
        code = ord(ch)
        if code < 32 or code == 127:
            _reject(label + " must not contain controls")
    parts = path.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        _reject(label + " must be canonical")
    if any(part in _VCS_DIRS for part in parts):
        _reject(label + " must not contain VCS directories")


def _validate_model(value, label):
    if type(value) is not str or not value or len(value) > 256:
        _reject(label + " must be nonempty string <=256 chars")


def _validate_editor_format(value, label):
    if value not in {"ordinary", "search_replace_k4"}:
        _reject(label + " invalid")


def _validate_run_id(value):
    if type(value) is not str or not value or len(value) > 256:
        _reject("run_id must be nonempty string <=256 chars")


def _validate_snapshot_ref(value, label):
    if type(value) is not str or len(value) != 40 or any(ch not in _HEX40 for ch in value):
        _reject(label + " must be 40 lowercase hex chars")


def _validate_usage_pair(value, label):
    if type(value) is not dict:
        _reject(label + " must be object")
    _assert_exact_keys(value, {"input_tokens", "output_tokens"}, label)
    if not _is_int(value["input_tokens"]) or value["input_tokens"] < 0:
        _reject(label + ".input_tokens must be nonnegative integer")
    if not _is_int(value["output_tokens"]) or value["output_tokens"] < 0:
        _reject(label + ".output_tokens must be nonnegative integer")
    return {
        "input_tokens": value["input_tokens"],
        "output_tokens": value["output_tokens"],
    }


def _validate_architect_usage(value, status, label):
    if status == "unknown" and value is None:
        return None
    return _validate_usage_pair(value, label)


def _validate_int_range(value, label, low, high):
    if not _is_int(value) or value < low or value > high:
        _reject(f"{label} must be integer in range {low}..{high}")


def _is_int(value):
    return type(value) is int


def _assert_exact_keys(obj, expected_keys, label):
    keys = set(obj.keys())
    if keys != expected_keys:
        missing = sorted(expected_keys - keys)
        extra = sorted(keys - expected_keys)
        details = []
        if missing:
            details.append("missing=" + ",".join(missing))
        if extra:
            details.append("extra=" + ",".join(extra))
        _reject(label + " keys invalid" + (": " + " ".join(details) if details else ""))


def _check_json_size(value, label):
    try:
        encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError):
        _reject(label + " is not valid JSON data")
    if len(encoded) > _SIZE_LIMIT:
        _reject(label + " exceeds 3 MiB")


def _reject(message):
    raise ValueError("PROTOCOL_REJECTED: " + message)
