import ast
import copy
from typing import Any

import donor_logic


CONFIG = {
    "top_n": 3,
    "compress": True,
    "compress_assign": False,
    "keep_old_order": False,
    "context_window": 10,
    "loc_interval": True,
    "fine_grain_only": False,
    "add_space": False,
    "sticky_scroll": False,
    "no_line_number": False,
    "direct_edit_loc": False,
    "cot": False,
    "stage_caps": {"file": 1, "related": 2, "fine": 2},
    "total_model_calls": 5,
}

PROGRESS_KEYS = (
    "donor_found_files",
    "selected_files",
    "related_locations",
    "fine_locations",
    "localized_files",
    "locations",
)

HANDOFF_STATUSES = {
    "LOCALIZED",
    "EMPTY_FILE_LOCALIZATION",
    "EMPTY_RELATED_LOCALIZATION",
    "EMPTY_FINE_LOCALIZATION",
    "EMPTY_FINE_CONTEXT",
    "CONTEXT_LIMIT",
    "SOURCE_UNAVAILABLE",
    "SOURCE_SYNTAX_UNSUPPORTED",
    "MODEL_OUTPUT_FAILED",
}

FILE_PROMPT = """
Please look through the following GitHub problem description and Repository structure and provide a list of files that one would need to edit to fix the problem.

### GitHub Problem Description ###
{problem_statement}

###

### Repository Structure ###
{structure}

###

Please only provide the full path and return at most 5 files.
The returned files should be separated by new lines ordered by most to least important and wrapped with ```
For example:
```
file1.py
file2.py
```
"""


def handle(event, state):
    _validate_event(event)
    _validate_input_state(state)

    if not state:
        if event["kind"] != "begin":
            _reject("first callback must be begin")
        return _handle_begin(event)

    meta = _require_meta(state)
    _validate_identity_match(event, meta)

    if meta.get("terminal"):
        _reject("post-terminal callback")

    pending = meta.get("pending")
    if not isinstance(pending, dict):
        _reject("missing pending request")

    if event["kind"] == "begin":
        _reject("repeated begin")

    if pending["kind"] == "read_files":
        if event["kind"] != "files_ready":
            _reject("expected files_ready")
        if event["request_id"] != pending["request_id"]:
            _reject("foreign files_ready receipt")
        _validate_files_match_pending(event, pending)
        return _handle_files_ready(event, state)

    if pending["kind"] == "model_request":
        if event["kind"] != "model_result":
            _reject("expected model_result")
        if event["request_id"] != pending["request_id"]:
            _reject("foreign model_result receipt")
        if event["stage"] != pending["stage"]:
            _reject("stage mismatch")
        if event["stage"] == "file":
            return _handle_file_result(event, state)
        if event["stage"] == "related":
            return _handle_related_result(event, state)
        if event["stage"] == "fine":
            return _handle_fine_result(event, state)
        _reject("unknown pending stage")

    _reject("unknown pending request kind")


def _handle_begin(event):
    tree, filtered_paths = donor_logic.build_filtered_tree(event["tracked_paths"])
    prompt = FILE_PROMPT.format(
        problem_statement=event["issue"],
        structure=donor_logic.build_structure_string(tree).strip(),
    ).strip()

    progress = _empty_progress()
    meta = {
        "identity": {
            "run_id": event["run_id"],
            "base_commit": event["base_commit"],
            "base_snapshot_ref": event["base_snapshot_ref"],
        },
        "issue": event["issue"],
        "filtered_paths": list(filtered_paths),
        "next_request_index": 1,
        "pending": None,
        "terminal": False,
        "base_files": [],
        "related": None,
        "fine": None,
    }
    state = {"progress": progress, "_meta": meta}
    return _issue_model_request(state, event, "file", prompt)


def _handle_file_result(event, in_state):
    state = _copy_state(in_state)
    meta = state["_meta"]
    progress = state["progress"]

    if event["status"] == "output_failed":
        return _handoff(state, event, "MODEL_OUTPUT_FAILED", "model output failed")
    if event["status"] == "context_limit":
        return _handoff(state, event, "CONTEXT_LIMIT", "file prompt exceeded context")

    found_files = donor_logic.parse_file_selection(
        event["text"] or "",
        meta["filtered_paths"],
    )
    donor_found_files = list(found_files[:3])
    selected_files = _stable_unique(donor_found_files)

    progress["donor_found_files"] = donor_found_files
    progress["selected_files"] = selected_files

    if not selected_files:
        return _handoff(state, event, "EMPTY_FILE_LOCALIZATION", "no files selected")

    request_id = _next_request_id(meta)
    meta["pending"] = {
        "kind": "read_files",
        "request_id": request_id,
        "paths": list(selected_files),
    }
    return {
        "state": state,
        "effects": [
            {
                "kind": "read_files",
                "run_id": event["run_id"],
                "base_commit": event["base_commit"],
                "base_snapshot_ref": event["base_snapshot_ref"],
                "request_id": request_id,
                "paths": list(selected_files),
            }
        ],
    }


def _handle_files_ready(event, in_state):
    state = _copy_state(in_state)
    meta = state["_meta"]

    status = _source_status_from_files(event["files"])
    if status is not None:
        return _handoff(state, event, status, status.lower())

    meta["base_files"] = [
        {
            "path": row["path"],
            "content": row["content"],
            "mode": row["mode"],
        }
        for row in event["files"]
    ]
    parse_names = list(state["progress"]["selected_files"])
    meta["related"] = {
        "attempts": 0,
        "parse_names": list(parse_names),
        "view_roster": list(parse_names),
    }
    meta["fine"] = None
    return _issue_related_request(state, event)


def _handle_related_result(event, in_state):
    state = _copy_state(in_state)
    meta = state["_meta"]
    progress = state["progress"]
    related = meta["related"]

    if event["status"] == "output_failed":
        return _handoff(state, event, "MODEL_OUTPUT_FAILED", "model output failed")

    if event["status"] == "context_limit":
        if len(related["view_roster"]) <= 1:
            return _handoff(state, event, "CONTEXT_LIMIT", "related prompt exceeded context")
        related["view_roster"] = related["view_roster"][:-1]
        return _issue_related_request(state, event)

    related["attempts"] += 1
    parsed = donor_logic.parse_location_response(
        event["text"] or "",
        related["parse_names"],
    )
    progress["related_locations"] = donor_logic.map_to_rows(parsed)

    if donor_logic.check_contains_valid_loc(parsed, meta["base_files"]):
        fine_parse_names = [row["path"] for row in progress["related_locations"]]
        meta["fine"] = {
            "attempts": 0,
            "parse_names": list(fine_parse_names),
            "view_roster": list(fine_parse_names),
        }
        return _issue_fine_request_or_handoff(state, event)

    if related["attempts"] >= 2:
        return _handoff(
            state,
            event,
            "EMPTY_RELATED_LOCALIZATION",
            "no valid related locations",
        )

    return _issue_related_request(state, event)


def _handle_fine_result(event, in_state):
    state = _copy_state(in_state)
    meta = state["_meta"]
    progress = state["progress"]
    fine = meta["fine"]

    if event["status"] == "output_failed":
        return _handoff(state, event, "MODEL_OUTPUT_FAILED", "model output failed")

    if event["status"] == "context_limit":
        if len(fine["view_roster"]) <= 1:
            return _handoff(state, event, "CONTEXT_LIMIT", "fine prompt exceeded context")
        fine["view_roster"] = fine["view_roster"][:-1]
        return _issue_fine_request_or_handoff(state, event)

    fine["attempts"] += 1
    parsed = donor_logic.parse_location_response(
        event["text"] or "",
        fine["parse_names"],
    )
    progress["fine_locations"] = donor_logic.map_to_rows(parsed)

    if donor_logic.check_contains_valid_loc(parsed, meta["base_files"]):
        localized_files, locations = _resolve_fine_locations(
            progress["fine_locations"],
            meta["base_files"],
        )
        progress["localized_files"] = localized_files
        progress["locations"] = locations
        return _handoff(state, event, "LOCALIZED", "localized")

    if fine["attempts"] >= 2:
        return _handoff(
            state,
            event,
            "EMPTY_FINE_LOCALIZATION",
            "no valid fine locations",
        )

    return _issue_fine_request_or_handoff(state, event)


def _issue_related_request(state, event):
    meta = state["_meta"]
    related = meta["related"]
    prompt = donor_logic.build_related_prompt(
        meta["issue"],
        related["view_roster"],
        meta["base_files"],
        compress_assign=False,
    ).strip()
    return _issue_model_request(state, event, "related", prompt)


def _issue_fine_request_or_handoff(state, event):
    meta = state["_meta"]
    fine = meta["fine"]
    coarse_locs = donor_logic.rows_to_map(state["progress"]["related_locations"])
    prompt, topn_content = donor_logic.build_fine_prompt(
        meta["issue"],
        fine["view_roster"],
        coarse_locs,
        meta["base_files"],
        CONFIG,
    )
    if not topn_content.strip():
        return _handoff(state, event, "EMPTY_FINE_CONTEXT", "no fine context available")
    return _issue_model_request(state, event, "fine", prompt.strip())


def _issue_model_request(state, event, stage, prompt):
    meta = state["_meta"]
    request_id = _next_request_id(meta)
    meta["pending"] = {
        "kind": "model_request",
        "request_id": request_id,
        "stage": stage,
    }
    return {
        "state": state,
        "effects": [
            {
                "kind": "model_request",
                "run_id": event["run_id"],
                "base_commit": event["base_commit"],
                "base_snapshot_ref": event["base_snapshot_ref"],
                "request_id": request_id,
                "stage": stage,
                "prompt": prompt.strip(),
            }
        ],
    }


def _handoff(state, event, status, message):
    if status not in HANDOFF_STATUSES:
        raise AssertionError(status)
    state = _copy_state(state)
    state["_meta"]["terminal"] = True
    state["_meta"]["pending"] = None
    request_id = _next_request_id(state["_meta"])
    progress = state["progress"]
    effect = {
        "kind": "localization_handoff",
        "run_id": event["run_id"],
        "base_commit": event["base_commit"],
        "base_snapshot_ref": event["base_snapshot_ref"],
        "request_id": request_id,
        "status": status,
        "message": message,
    }
    for key in PROGRESS_KEYS:
        effect[key] = _copy_value(progress[key])
    return {"state": state, "effects": [effect]}


def _resolve_fine_locations(fine_rows, base_files):
    structure = donor_logic._structure_for_sources(base_files)
    base_by_path = {row["path"]: row["content"] for row in base_files}

    localized_files = []
    locations = []

    for row in fine_rows:
        path = row["path"]
        display_text = _display_text(base_by_path[path])
        line_locs, _ = donor_logic.transfer_arb_locs_to_locs(
            row["locations"],
            structure,
            path,
            0,
            True,
            False,
            file_content=display_text,
        )
        if line_locs:
            localized_files.append(path)
            for start, end in line_locs:
                locations.append({"path": path, "start": start, "end": end})

    return localized_files, locations


def _source_status_from_files(files):
    for row in files:
        if row["status"] != "available":
            return "SOURCE_UNAVAILABLE"
        if row["content"] == "":
            return "SOURCE_UNAVAILABLE"
        try:
            ast.parse(row["content"])
        except SyntaxError:
            return "SOURCE_SYNTAX_UNSUPPORTED"
    return None


def _validate_files_match_pending(event, pending):
    paths = [row["path"] for row in event["files"]]
    if paths != pending["paths"]:
        _reject("file receipt paths differ from pending request")


def _validate_identity_match(event, meta):
    ident = meta.get("identity")
    if not isinstance(ident, dict):
        _reject("missing state identity")
    if event["run_id"] != ident["run_id"]:
        _reject("run_id mismatch")
    if event["base_commit"] != ident["base_commit"]:
        _reject("base_commit mismatch")
    if event["base_snapshot_ref"] != ident["base_snapshot_ref"]:
        _reject("base_snapshot_ref mismatch")


def _require_meta(state):
    meta = state.get("_meta")
    if not isinstance(meta, dict):
        _reject("missing package state")
    return meta


def _empty_progress():
    return {key: [] for key in PROGRESS_KEYS}


def _stable_unique(items):
    out = []
    seen = set()
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _display_text(raw_content):
    return "\n".join(raw_content.splitlines())


def _next_request_id(meta):
    index = meta.get("next_request_index")
    if not isinstance(index, int) or index < 1:
        _reject("invalid request counter in state")
    meta["next_request_index"] = index + 1
    return f"req-{index}"


def _copy_state(state):
    return copy.deepcopy(state)


def _copy_value(value):
    return copy.deepcopy(value)


def _validate_input_state(state):
    if not isinstance(state, dict):
        _reject("state must be an object")
    if not state:
        return
    progress = state.get("progress")
    if not isinstance(progress, dict):
        _reject("noninitial state requires progress")
    if set(progress.keys()) != set(PROGRESS_KEYS):
        _reject("progress fields differ")
    for key in ("donor_found_files", "selected_files", "localized_files"):
        if not isinstance(progress[key], list):
            _reject("progress path list invalid")
        for item in progress[key]:
            if not _is_text(item):
                _reject("progress path entry invalid")
    for key in ("related_locations", "fine_locations"):
        rows = progress[key]
        if not isinstance(rows, list):
            _reject("progress raw locations invalid")
        for row in rows:
            if not isinstance(row, dict) or set(row.keys()) != {"path", "locations"}:
                _reject("progress raw location row invalid")
            if not _is_text(row["path"]) or not isinstance(row["locations"], list):
                _reject("progress raw location row invalid")
            for item in row["locations"]:
                if not isinstance(item, str):
                    _reject("progress raw location text invalid")
    rows = progress["locations"]
    if not isinstance(rows, list):
        _reject("progress resolved locations invalid")
    for row in rows:
        if not isinstance(row, dict) or set(row.keys()) != {"path", "start", "end"}:
            _reject("progress resolved location row invalid")
        if not _is_text(row["path"]) or not isinstance(row["start"], int) or not isinstance(row["end"], int):
            _reject("progress resolved location row invalid")


def _validate_event(event):
    if not isinstance(event, dict) or "kind" not in event:
        _reject("event must be an object with kind")
    kind = event["kind"]
    if kind == "begin":
        expected = {
            "kind",
            "run_id",
            "base_commit",
            "base_snapshot_ref",
            "issue",
            "tracked_paths",
            "config",
        }
        if set(event.keys()) != expected:
            _reject("begin fields differ")
        _validate_common(event)
        if not _is_issue(event["issue"]):
            _reject("issue invalid")
        if not isinstance(event["tracked_paths"], list):
            _reject("tracked_paths invalid")
        for path in event["tracked_paths"]:
            if not _is_path(path):
                _reject("tracked_paths invalid")
        if event["tracked_paths"] != sorted(event["tracked_paths"]) or len(set(event["tracked_paths"])) != len(event["tracked_paths"]):
            _reject("sorted unique tracked paths required")
        if event["config"] != CONFIG:
            _reject("frozen config differs")
        return

    if kind == "files_ready":
        expected = {
            "kind",
            "run_id",
            "base_commit",
            "base_snapshot_ref",
            "request_id",
            "files",
        }
        if set(event.keys()) != expected:
            _reject("files_ready fields differ")
        _validate_common(event)
        if not _is_text(event["request_id"]):
            _reject("request identity required")
        if not isinstance(event["files"], list) or not (1 <= len(event["files"]) <= 3):
            _reject("one to three file receipts required")
        total = 0
        seen = []
        for row in event["files"]:
            if not isinstance(row, dict) or set(row.keys()) != {"path", "status", "content", "mode"}:
                _reject("file receipt shape invalid")
            if not _is_path(row["path"]):
                _reject("file receipt path invalid")
            if row["status"] not in {"available", "missing", "non_utf8", "unavailable"}:
                _reject("file status invalid")
            seen.append(row["path"])
            if row["status"] == "available":
                if not isinstance(row["content"], str):
                    _reject("available file content invalid")
                if row["mode"] not in {"100644", "100755"}:
                    _reject("available file mode invalid")
                total += len(row["content"].encode("utf-8"))
            else:
                if row["content"] is not None or row["mode"] is not None:
                    _reject("unavailable file has content")
        if len(set(seen)) != len(seen):
            _reject("duplicate file receipt paths")
        if total > 512 * 1024:
            _reject("file receipt batch too large")
        return

    if kind == "model_result":
        expected = {
            "kind",
            "run_id",
            "base_commit",
            "base_snapshot_ref",
            "request_id",
            "stage",
            "status",
            "text",
            "input_tokens",
            "query_id",
        }
        if set(event.keys()) != expected:
            _reject("model_result fields differ")
        _validate_common(event)
        if not _is_text(event["request_id"]):
            _reject("request identity required")
        if event["stage"] not in {"file", "related", "fine"}:
            _reject("model stage invalid")
        if event["status"] not in {"completed", "context_limit", "output_failed"}:
            _reject("model status invalid")
        if not isinstance(event["input_tokens"], int) or event["input_tokens"] < 0:
            _reject("input token count invalid")
        if event["status"] == "context_limit":
            if event["text"] is not None or event["query_id"] is not None:
                _reject("context_limit cannot claim a query")
        elif event["status"] == "output_failed":
            if event["text"] is not None:
                _reject("output_failed text invalid")
            if not isinstance(event["query_id"], int) or event["query_id"] <= 0:
                _reject("charged query required")
        else:
            if not isinstance(event["text"], str):
                _reject("completed text invalid")
            if not isinstance(event["query_id"], int) or event["query_id"] <= 0:
                _reject("charged query required")
        return

    _reject("unknown localization callback")


def _validate_common(event):
    if not _is_text(event.get("run_id")):
        _reject("run_id invalid")
    if not _is_hex40(event.get("base_commit")):
        _reject("base_commit invalid")
    if not _is_hex40(event.get("base_snapshot_ref")):
        _reject("base_snapshot_ref invalid")


def _is_issue(value):
    return isinstance(value, str) and value != "" and len(value.encode("utf-8")) <= 100000


def _is_text(value):
    return isinstance(value, str) and value != "" and len(value.encode("utf-8")) <= 256


def _is_hex40(value):
    return isinstance(value, str) and len(value) == 40 and all(ch in "0123456789abcdef" for ch in value)


def _is_path(value):
    if not isinstance(value, str) or value == "":
        return False
    if value.startswith("/") or value.startswith("./") or value.endswith("/"):
        return False
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        return False
    return True


def _reject(message):
    raise ValueError(f"PROTOCOL_REJECTED: {message}")
