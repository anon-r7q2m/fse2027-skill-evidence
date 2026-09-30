import re
from typing import Any


SYSTEM_TEMPLATE = (
    "You are an expert software engineer reviewing code. Your thinking is very thorough, so it is ok if its very long.\n"
)

INSTANCE_TEMPLATE_PREFIX = (
    "You will be given a problem statement and a list of patch submissions.\n\n"
    "Pick the most reasonable patch.\n"
    "The patch should solve the problem described in the problem statement in a way that is consistent with the rest of the codebase and the conventions of the codebase.\n\n"
    "Note: Disregard all testing code in the patch, as testing was already done in a separate step.\n"
    "Having a test in the patch does not make it any better.\n\n"
    "<IMPORTANT>The last line of your response should be the index of the patch you chose.\n"
    "You must choose a single index no matter what. If you cannot decide between two or more\n"
    "submissions, choose the first one of these.\n"
    "</IMPORTANT>\n\n"
    "Problem statement:\n"
)

INSTANCE_TEMPLATE_MIDDLE = "\n\nSubmissions:\n"

INSTANCE_TEMPLATE_SUFFIX = (
    "\n\n<IMPORTANT>The last line of your response should be the index of the patch you chose without any other text.</IMPORTANT>"
)

SUBMISSION_TEMPLATE_PREFIX = "Patch:\n\n```python\n"
SUBMISSION_TEMPLATE_MIDDLE = "\n```\n\nThe final edited file with 30 lines of context:\n\n```python\n"
SUBMISSION_TEMPLATE_SUFFIX = "\n```"

MAX_LEN_SUBMISSION = 5000

STATE_KEYS = {
    "schema_version",
    "profile",
    "run_id",
    "base_snapshot_ref",
    "phase",
    "request_id",
    "candidate_indices",
    "filtered_identities",
    "cached_effect",
}


def handle(event: Any, state: Any) -> dict[str, Any]:
    stored = _validate_state(state)
    parsed_event = _validate_event(event)

    if stored is None:
        if parsed_event["kind"] != "begin_choice":
            _reject("non-begin event requires existing state")
        return _handle_begin(parsed_event)

    if parsed_event["run_id"] != stored["run_id"]:
        _reject("run_id does not match existing state")
    if parsed_event["base_snapshot_ref"] != stored["base_snapshot_ref"]:
        _reject("base_snapshot_ref does not match existing state")

    phase = stored["phase"]
    kind = parsed_event["kind"]

    if phase == "WAITING":
        if kind == "get_best":
            _reject("get_best is not legal while waiting for model_response")
        if kind == "begin_choice":
            _reject("begin_choice is not legal after choice has begun")
        return _handle_model_response(parsed_event, stored)

    if phase == "DONE":
        if kind == "get_best":
            return {"state": stored, "effects": [stored["cached_effect"]]}
        if kind == "begin_choice":
            _reject("begin_choice may only occur once")
        if kind == "model_response":
            _reject("model_response is not legal after selection is cached")
        _reject("unsupported lifecycle state")

    _reject("unsupported lifecycle state")
    return {"state": stored, "effects": []}


def _handle_begin(event: dict[str, Any]) -> dict[str, Any]:
    problem_statement = event["problem_statement"]
    candidates = event["candidates"]

    filtered = _filter_candidates(candidates)
    candidate_indices = [candidate["sample_index"] for candidate in filtered]

    if not filtered:
        effect = _selection_effect(
            run_id=event["run_id"],
            base_snapshot_ref=event["base_snapshot_ref"],
            status="EMPTY",
            sample_index=None,
            snapshot_ref=event["base_snapshot_ref"],
            candidate_indices=[],
        )
        new_state = _done_state(
            run_id=event["run_id"],
            base_snapshot_ref=event["base_snapshot_ref"],
            request_id=None,
            candidate_indices=[],
            filtered_identities=[],
            cached_effect=effect,
        )
        return {"state": new_state, "effects": [effect]}

    request_id = event["run_id"] + "/chooser/1"
    submissions = [_format_submission(candidate) for candidate in filtered]
    messages = _build_messages(problem_statement, submissions)
    effect = {
        "kind": "chooser_request",
        "run_id": event["run_id"],
        "base_snapshot_ref": event["base_snapshot_ref"],
        "request_id": request_id,
        "messages": messages,
        "candidate_indices": candidate_indices,
    }
    new_state = _waiting_state(
        run_id=event["run_id"],
        base_snapshot_ref=event["base_snapshot_ref"],
        request_id=request_id,
        candidate_indices=candidate_indices,
        filtered_identities=[
            {
                "sample_index": candidate["sample_index"],
                "snapshot_ref": candidate["snapshot_ref"],
            }
            for candidate in filtered
        ],
    )
    return {"state": new_state, "effects": [effect]}


def _handle_model_response(event: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    if event["request_id"] != state["request_id"]:
        _reject("model_response request_id does not match outstanding chooser request")

    status = event["status"]
    candidate_indices = state["candidate_indices"]

    if status != "completed":
        effect = _selection_effect(
            run_id=event["run_id"],
            base_snapshot_ref=event["base_snapshot_ref"],
            status="UNAVAILABLE",
            sample_index=None,
            snapshot_ref=None,
            candidate_indices=candidate_indices,
        )
        new_state = _done_state(
            run_id=state["run_id"],
            base_snapshot_ref=state["base_snapshot_ref"],
            request_id=state["request_id"],
            candidate_indices=state["candidate_indices"],
            filtered_identities=state["filtered_identities"],
            cached_effect=effect,
        )
        return {"state": new_state, "effects": [effect]}

    local_index = _interpret_choice(event["text"])
    if not 0 <= local_index < len(state["filtered_identities"]):
        local_index = 0
    chosen = state["filtered_identities"][local_index]
    effect = _selection_effect(
        run_id=event["run_id"],
        base_snapshot_ref=event["base_snapshot_ref"],
        status="SELECTED",
        sample_index=chosen["sample_index"],
        snapshot_ref=chosen["snapshot_ref"],
        candidate_indices=candidate_indices,
    )
    new_state = _done_state(
        run_id=state["run_id"],
        base_snapshot_ref=state["base_snapshot_ref"],
        request_id=state["request_id"],
        candidate_indices=state["candidate_indices"],
        filtered_identities=state["filtered_identities"],
        cached_effect=effect,
    )
    return {"state": new_state, "effects": [effect]}


def _validate_state(state: Any) -> dict[str, Any] | None:
    if state == {}:
        return None
    if not isinstance(state, dict):
        _reject("state must be an object")
    if set(state.keys()) != STATE_KEYS:
        _reject("state has invalid keys")
    if state["schema_version"] != 1:
        _reject("state schema_version is invalid")
    if state["profile"] != "sweagent_chooser_v1":
        _reject("state profile is invalid")
    _validate_nonempty_string(state["run_id"], "state.run_id", 256)
    _validate_hex40(state["base_snapshot_ref"], "state.base_snapshot_ref")
    if state["phase"] not in ("WAITING", "DONE"):
        _reject("state phase is invalid")
    if state["request_id"] is not None:
        _validate_nonempty_string(state["request_id"], "state.request_id", 512)
    _validate_int_list(state["candidate_indices"], "state.candidate_indices")
    identities = state["filtered_identities"]
    if not isinstance(identities, list):
        _reject("state.filtered_identities must be a list")
    for i, identity in enumerate(identities):
        if not isinstance(identity, dict):
            _reject(f"state.filtered_identities[{i}] must be an object")
        if set(identity.keys()) != {"sample_index", "snapshot_ref"}:
            _reject(f"state.filtered_identities[{i}] has invalid keys")
        if not _is_int(identity["sample_index"]) or identity["sample_index"] <= 0:
            _reject(f"state.filtered_identities[{i}].sample_index is invalid")
        _validate_hex40(identity["snapshot_ref"], f"state.filtered_identities[{i}].snapshot_ref")
    cached_effect = state["cached_effect"]
    if state["phase"] == "WAITING":
        if not isinstance(state["request_id"], str):
            _reject("waiting state requires request_id")
        if cached_effect is not None:
            _reject("waiting state must not have cached_effect")
        if len(state["filtered_identities"]) != len(state["candidate_indices"]):
            _reject("waiting state filtered identities do not match candidate indices")
    else:
        if not isinstance(cached_effect, dict):
            _reject("done state requires cached_effect")
        _validate_selection_effect(cached_effect, state["run_id"], state["base_snapshot_ref"])
    return state


def _validate_event(event: Any) -> dict[str, Any]:
    if not isinstance(event, dict):
        _reject("event must be an object")
    kind = event.get("kind")
    if kind == "begin_choice":
        expected_keys = {"kind", "run_id", "base_snapshot_ref", "problem_statement", "candidates"}
    elif kind == "model_response":
        expected_keys = {"kind", "run_id", "base_snapshot_ref", "request_id", "status", "text"}
    elif kind == "get_best":
        expected_keys = {"kind", "run_id", "base_snapshot_ref"}
    else:
        _reject("event.kind is invalid")
        raise AssertionError("unreachable")

    if set(event.keys()) != expected_keys:
        _reject("event has invalid keys")

    _validate_nonempty_string(event["run_id"], "event.run_id", 256)
    _validate_hex40(event["base_snapshot_ref"], "event.base_snapshot_ref")

    if kind == "begin_choice":
        if not isinstance(event["problem_statement"], str):
            _reject("event.problem_statement must be a string")
        _validate_candidates(event["candidates"])
    elif kind == "model_response":
        _validate_nonempty_string(event["request_id"], "event.request_id", 1024)
        if event["status"] not in ("completed", "incomplete", "failed", "unknown"):
            _reject("event.status is invalid")
        if event["status"] == "completed":
            if not isinstance(event["text"], str):
                _reject("completed model_response requires string text")
        else:
            if event["text"] is not None:
                _reject("non-completed model_response requires null text")
    return event


def _validate_candidates(candidates: Any) -> None:
    if not isinstance(candidates, list):
        _reject("event.candidates must be a list")
    if len(candidates) > 4:
        _reject("event.candidates has too many rows")

    prev_sample_index = None
    seen_request_ids: set[str] = set()

    for i, candidate in enumerate(candidates):
        if not isinstance(candidate, dict):
            _reject(f"event.candidates[{i}] must be an object")
        if set(candidate.keys()) != {"sample_index", "request_id", "snapshot_ref", "exit_status", "patch", "files"}:
            _reject(f"event.candidates[{i}] has invalid keys")

        sample_index = candidate["sample_index"]
        if not _is_int(sample_index) or sample_index <= 0 or sample_index > 4:
            _reject(f"event.candidates[{i}].sample_index is invalid")
        if prev_sample_index is not None and sample_index <= prev_sample_index:
            _reject("candidate sample_index values must be strictly increasing")
        prev_sample_index = sample_index

        _validate_nonempty_string(candidate["request_id"], f"event.candidates[{i}].request_id", 256)
        if candidate["request_id"] in seen_request_ids:
            _reject("candidate request_id values must be unique")
        seen_request_ids.add(candidate["request_id"])

        _validate_hex40(candidate["snapshot_ref"], f"event.candidates[{i}].snapshot_ref")

        if not isinstance(candidate["exit_status"], str):
            _reject(f"event.candidates[{i}].exit_status must be a string")

        patch = candidate["patch"]
        if patch is not None and not isinstance(patch, str):
            _reject(f"event.candidates[{i}].patch must be a string or null")

        files = candidate["files"]
        if not isinstance(files, list):
            _reject(f"event.candidates[{i}].files must be a list")
        if len(files) > 64:
            _reject(f"event.candidates[{i}].files has too many rows")

        if patch in (None, "") and files:
            _reject(f"event.candidates[{i}] empty/null patch must have no files")

        seen_paths: set[str] = set()
        for j, file_row in enumerate(files):
            if not isinstance(file_row, dict):
                _reject(f"event.candidates[{i}].files[{j}] must be an object")
            if set(file_row.keys()) != {"path", "content", "hunks"}:
                _reject(f"event.candidates[{i}].files[{j}] has invalid keys")

            path = file_row["path"]
            _validate_repo_path(path, f"event.candidates[{i}].files[{j}].path")
            if path in seen_paths:
                _reject(f"event.candidates[{i}].files file paths must be unique")
            seen_paths.add(path)

            if not isinstance(file_row["content"], str):
                _reject(f"event.candidates[{i}].files[{j}].content must be a string")

            hunks = file_row["hunks"]
            if not isinstance(hunks, list):
                _reject(f"event.candidates[{i}].files[{j}].hunks must be a list")
            for k, hunk in enumerate(hunks):
                if not isinstance(hunk, dict):
                    _reject(f"event.candidates[{i}].files[{j}].hunks[{k}] must be an object")
                if set(hunk.keys()) != {"target_start", "target_length"}:
                    _reject(f"event.candidates[{i}].files[{j}].hunks[{k}] has invalid keys")
                if not _is_int(hunk["target_start"]) or hunk["target_start"] < 0:
                    _reject(f"event.candidates[{i}].files[{j}].hunks[{k}].target_start is invalid")
                if not _is_int(hunk["target_length"]) or hunk["target_length"] < 0:
                    _reject(f"event.candidates[{i}].files[{j}].hunks[{k}].target_length is invalid")


def _validate_selection_effect(effect: dict[str, Any], run_id: str, base_snapshot_ref: str) -> None:
    if set(effect.keys()) != {
        "kind",
        "run_id",
        "base_snapshot_ref",
        "status",
        "sample_index",
        "snapshot_ref",
        "candidate_indices",
    }:
        _reject("cached selection effect has invalid keys")
    if effect["kind"] != "chooser_selection":
        _reject("cached selection effect kind is invalid")
    if effect["run_id"] != run_id:
        _reject("cached selection effect run_id is invalid")
    if effect["base_snapshot_ref"] != base_snapshot_ref:
        _reject("cached selection effect base_snapshot_ref is invalid")
    if effect["status"] not in ("SELECTED", "EMPTY", "UNAVAILABLE"):
        _reject("cached selection effect status is invalid")
    _validate_int_list(effect["candidate_indices"], "cached selection effect candidate_indices")

    if effect["status"] == "SELECTED":
        if not _is_int(effect["sample_index"]) or effect["sample_index"] <= 0:
            _reject("cached selected sample_index is invalid")
        _validate_hex40(effect["snapshot_ref"], "cached selected snapshot_ref")
    elif effect["status"] == "EMPTY":
        if effect["sample_index"] is not None:
            _reject("cached empty sample_index must be null")
        if effect["snapshot_ref"] != base_snapshot_ref:
            _reject("cached empty snapshot_ref must equal base_snapshot_ref")
        if effect["candidate_indices"] != []:
            _reject("cached empty candidate_indices must be empty")
    else:
        if effect["sample_index"] is not None:
            _reject("cached unavailable sample_index must be null")
        if effect["snapshot_ref"] is not None:
            _reject("cached unavailable snapshot_ref must be null")


def _validate_nonempty_string(value: Any, name: str, max_len: int) -> None:
    if not isinstance(value, str):
        _reject(f"{name} must be a string")
    if not value:
        _reject(f"{name} must be nonempty")
    if len(value) > max_len:
        _reject(f"{name} is too long")


def _validate_hex40(value: Any, name: str) -> None:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{40}", value) is None:
        _reject(f"{name} must be 40 lowercase hex characters")


def _validate_repo_path(path: Any, name: str) -> None:
    if not isinstance(path, str):
        _reject(f"{name} must be a string")
    if not (1 <= len(path) <= 4096):
        _reject(f"{name} has invalid length")
    if "\\" in path:
        _reject(f"{name} must not contain backslash")
    for ch in path:
        code = ord(ch)
        if code < 32 or code == 127:
            _reject(f"{name} must not contain control characters")
    components = path.split("/")
    for component in components:
        if component == "":
            _reject(f"{name} must not contain empty path components")
        if component in (".", "..", ".git", ".hg", ".svn"):
            _reject(f"{name} contains invalid path component")


def _validate_int_list(value: Any, name: str) -> None:
    if not isinstance(value, list):
        _reject(f"{name} must be a list")
    for i, item in enumerate(value):
        if not _is_int(item):
            _reject(f"{name}[{i}] must be an integer")


def _filter_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    submitted = [candidate for candidate in candidates if candidate["exit_status"] == "submitted"]
    if len(submitted) >= 2:
        return submitted
    return list(candidates)


def _build_messages(problem_statement: str, submissions: list[str]) -> list[dict[str, str]]:
    instance_message = _render_instance_template(problem_statement, submissions)
    return [
        {"role": "system", "content": SYSTEM_TEMPLATE},
        {"role": "user", "content": instance_message},
    ]


def _render_instance_template(problem_statement: str, submissions: list[str]) -> str:
    out = [INSTANCE_TEMPLATE_PREFIX, problem_statement, INSTANCE_TEMPLATE_MIDDLE]
    for i, submission in enumerate(submissions):
        out.append("\nSubmission ")
        out.append(str(i))
        out.append(":\n\n")
        out.append(submission)
        out.append("\n\n")
    out.append(INSTANCE_TEMPLATE_SUFFIX)
    return "".join(out)


def _format_submission(candidate: dict[str, Any]) -> str:
    patch = candidate["patch"]
    if patch is None or (isinstance(patch, str) and len(patch) > MAX_LEN_SUBMISSION):
        return "Solution invalid."

    edited_files30 = _format_edited_files30(candidate)
    return (
        SUBMISSION_TEMPLATE_PREFIX
        + patch
        + SUBMISSION_TEMPLATE_MIDDLE
        + edited_files30
        + SUBMISSION_TEMPLATE_SUFFIX
    )


def _format_edited_files30(candidate: dict[str, Any]) -> str:
    patch = candidate["patch"]
    if patch == "":
        return "Empty. No edited files found."

    files_out = []
    for file_row in candidate["files"]:
        starts = []
        stops = []
        for hunk in file_row["hunks"]:
            start = max(1, hunk["target_start"] - 30)
            stop = hunk["target_start"] + hunk["target_length"] + 30
            starts.append(start)
            stops.append(stop)
        content = _format_file(file_row["content"], starts, stops, linenos=True)
        files_out.append(f"[File: {file_row['path']}]\n{content}")
    return "\n\n".join(files_out)


def _merge_intervals(starts: list[int], stops: list[int]) -> tuple[list[int], list[int]]:
    if not starts:
        if stops:
            raise AssertionError("stops must be empty when starts is empty")
        return [], []

    intervals = sorted(zip(starts, stops))
    merged: list[list[int]] = []
    for start, stop in intervals:
        if not merged or merged[-1][1] < start:
            merged.append([start, stop])
        else:
            merged[-1][1] = max(merged[-1][1], stop)
    merged_starts = [pair[0] for pair in merged]
    merged_stops = [pair[1] for pair in merged]
    return merged_starts, merged_stops


def _format_file(text: str, starts: list[int], stops: list[int], *, linenos: bool) -> str:
    if not starts:
        if stops:
            raise AssertionError("stops must be empty when starts is empty")
        return ""

    if len(starts) != len(stops):
        raise AssertionError("starts and stops length mismatch")
    for start in starts:
        if start < 1:
            raise AssertionError("start must be at least 1")
    for start, stop in zip(starts, stops):
        if start >= stop:
            raise AssertionError("start must be less than stop")

    starts, stops = _merge_intervals(starts, stops)

    out: list[str] = []
    if starts[0] > 1:
        out.append(f"[{starts[0] - 1} lines above omitted]")

    last_stop: int | None = None
    lines = text.splitlines()

    for start, stop in zip(starts, stops):
        if last_stop is not None:
            n_omitted = start - last_stop
            if n_omitted < 0:
                raise AssertionError("merged intervals must not overlap")
            if n_omitted:
                out.append(f"\n[{n_omitted} lines omitted]\n")

        these_lines = lines[start - 1 : stop - 1]
        if linenos:
            out.append("\n".join(f"{i:6d}: {line}" for i, line in enumerate(these_lines, start=start)))
        else:
            out.append("\n".join(these_lines))
        last_stop = stop

    if last_stop is not None and last_stop < len(lines):
        omitted = len(lines) - last_stop
        if omitted <= 0:
            raise AssertionError("below omitted count must be positive")
        out.append(f"[{omitted} lines below omitted]")

    return "\n".join(out)


def _interpret_choice(response: str) -> int:
    try:
        return int(re.findall(r"\d+", response)[-1])
    except Exception:
        return 0


def _selection_effect(
    *,
    run_id: str,
    base_snapshot_ref: str,
    status: str,
    sample_index: int | None,
    snapshot_ref: str | None,
    candidate_indices: list[int],
) -> dict[str, Any]:
    return {
        "kind": "chooser_selection",
        "run_id": run_id,
        "base_snapshot_ref": base_snapshot_ref,
        "status": status,
        "sample_index": sample_index,
        "snapshot_ref": snapshot_ref,
        "candidate_indices": list(candidate_indices),
    }


def _waiting_state(
    *,
    run_id: str,
    base_snapshot_ref: str,
    request_id: str,
    candidate_indices: list[int],
    filtered_identities: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "profile": "sweagent_chooser_v1",
        "run_id": run_id,
        "base_snapshot_ref": base_snapshot_ref,
        "phase": "WAITING",
        "request_id": request_id,
        "candidate_indices": list(candidate_indices),
        "filtered_identities": [
            {
                "sample_index": identity["sample_index"],
                "snapshot_ref": identity["snapshot_ref"],
            }
            for identity in filtered_identities
        ],
        "cached_effect": None,
    }


def _done_state(
    *,
    run_id: str,
    base_snapshot_ref: str,
    request_id: str | None,
    candidate_indices: list[int],
    filtered_identities: list[dict[str, Any]],
    cached_effect: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "profile": "sweagent_chooser_v1",
        "run_id": run_id,
        "base_snapshot_ref": base_snapshot_ref,
        "phase": "DONE",
        "request_id": request_id,
        "candidate_indices": list(candidate_indices),
        "filtered_identities": [
            {
                "sample_index": identity["sample_index"],
                "snapshot_ref": identity["snapshot_ref"],
            }
            for identity in filtered_identities
        ],
        "cached_effect": dict(cached_effect),
    }


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _reject(message: str) -> None:
    raise ValueError(f"PROTOCOL_REJECTED: {message}")
