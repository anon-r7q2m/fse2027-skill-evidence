import hashlib
from typing import Any

from admission_pkg import assess_candidate
from edit_parser_pkg import ParseError, parse_sample_text
from normalize_pkg import build_normalized_key, prepare_normalization_files


def _copy_state(state: Any) -> dict:
    if isinstance(state, dict):
        return dict(state)
    raise ValueError("state must be a JSON object")


def _check_context(state: dict, event: dict) -> None:
    run_id = state.get("run_id")
    base_snapshot_ref = state.get("base_snapshot_ref")
    if run_id is not None and run_id != event.get("run_id"):
        raise ValueError("run_id mismatch")
    if base_snapshot_ref is not None and base_snapshot_ref != event.get("base_snapshot_ref"):
        raise ValueError("base_snapshot_ref mismatch")


def _request_id(run_id: str, base_snapshot_ref: str, sample_index: int) -> str:
    seed = f"{run_id}\n{base_snapshot_ref}".encode("utf-8")
    short = hashlib.sha256(seed).hexdigest()[:12]
    return f"sample-{sample_index}-{short}"


def _render_locations(locations: list[dict]) -> str:
    return "\n".join(
        f"- {row['path']}:{row['start']}-{row['end']}" for row in locations
    )


def _render_numbered_content(content: str) -> str:
    lines = content.splitlines()
    if not lines:
        return ""
    return "\n".join(f"{index}: {line}" for index, line in enumerate(lines, 1))


def _render_files(files: list[dict]) -> str:
    parts: list[str] = []
    for row in files:
        parts.append(
            "\n".join(
                [
                    f"PATH: {row['path']}",
                    f"MODE: {row['mode']}",
                    "CONTENT WITH DISPLAY-ONLY ORIGINAL LINE NUMBERS:",
                    "```",
                    _render_numbered_content(row["content"]),
                    "```",
                ]
            )
        )
    return "\n\n".join(parts)


def _build_prompt(event: dict) -> tuple[str, str]:
    file_sections: list[str] = []
    allowed_paths: list[str] = []
    editable_ranges: list[str] = []
    for row in event["files"]:
        content = row["content"]
        lines = content.splitlines()
        if not lines:
            raise ValueError(f"declared file has zero lines: {row['path']}")
        path = row["path"]
        allowed_paths.append(path)
        editable_ranges.append(f"- {path}: [1, {len(lines)}]")
        file_sections.append(
            "\n".join(
                [
                    f"--- BEGIN FILE: {path} ---",
                    f"MODE: {row['mode']}",
                    "```python",
                    content,
                    "```",
                    f"--- END FILE: {path} ---",
                ]
            )
        )

    locations = "\n".join(
        f"- {row['path']}:{row['start']}-{row['end']}" for row in event["locations"]
    )
    declared_paths = "\n".join(f"- {path}" for path in allowed_paths)
    editable_intervals = "\n".join(editable_ranges)

    user_prompt = "\n".join(
        [
            "We are solving the following repository issue on a frozen same-base snapshot.",
            "",
            "--- BEGIN ISSUE ---",
            event["issue"],
            "--- END ISSUE ---",
            "",
            "Declared paths you may edit:",
            declared_paths,
            "",
            "Declared locations are context only:",
            locations,
            "",
            "Each declared file below is an existing nonempty UTF-8 Python file. Use the complete original file text exactly as shown, with no inserted display line numbers.",
            "For this task, each declared file is editable only as its full same-base interval:",
            editable_intervals,
            "",
            "Every SEARCH/REPLACE command is interpreted independently against the same original declared file content, not against earlier commands. Do not rely on one command changing the search text for another command.",
            "",
            "Return exactly one fenced Python block and nothing else except optional surrounding whitespace.",
            "Inside that single block, write one to 64 SEARCH/REPLACE commands and nothing else.",
            "",
            "Each command must use this exact structure:",
            "### <declared path>",
            "<<<<<<< SEARCH",
            "<one or more exact original lines from that declared file>",
            "=======",
            "<replacement lines, possibly empty>",
            ">>>>>>> REPLACE",
            "",
            "Rules:",
            "- Use only declared paths listed above.",
            "- Do not output line numbers, coordinates, edit_file calls, prose, comments, or any extra code.",
            "- Copy SEARCH text exactly from the original file content, including indentation, spaces, and punctuation.",
            "- Replacement text must include the exact final indentation you want.",
            "- SEARCH text must not be empty.",
            "- You may emit multiple commands for the same file, but each must stand on the same original base file.",
            "- Keep the structural marker lines exactly as written.",
            "- Only whitespace may appear outside the fence or between commands.",
            "",
            "Example:",
            "```python",
            "### package/module.py",
            "<<<<<<< SEARCH",
            "old_line = 1",
            "=======",
            "old_line = 2",
            ">>>>>>> REPLACE",
            "```",
            "",
            "Declared base files:",
            "\n\n".join(file_sections),
        ]
    )
    instructions = (
        "Return only one ```python``` block containing one to 64 exact SEARCH/REPLACE "
        "commands for the declared same-base files."
    )
    return instructions, user_prompt


def _begin_samples(event: dict, state: dict) -> dict:
    instructions, user_prompt = _build_prompt(event)
    requests = []
    for sample_index in range(1, event["max_samples"] + 1):
        requests.append(
            {
                "sample_index": sample_index,
                "request_id": _request_id(
                    event["run_id"], event["base_snapshot_ref"], sample_index
                ),
                "instructions": instructions,
                "items": [{"role": "user", "content": user_prompt}],
                "tools": [],
                "limits": dict(event["limits"]),
            }
        )

    new_state = {
        "run_id": event["run_id"],
        "base_snapshot_ref": event["base_snapshot_ref"],
        "base_commit": event["base_commit"],
        "base_files": list(event["files"]),
        "normalization_flags": {},
    }
    effect = {
        "kind": "sample_batch",
        "run_id": event["run_id"],
        "base_snapshot_ref": event["base_snapshot_ref"],
        "requests": requests,
    }
    return {"state": new_state, "effects": [effect]}


def _sample_batch_ready(event: dict, state: dict) -> dict:
    _check_context(state, event)
    base_files = state.get("base_files")
    if not isinstance(base_files, list):
        raise ValueError("missing base files in state")

    rows = []
    for sample in event["samples"]:
        if sample["status"] != "completed":
            rows.append(
                {
                    "sample_index": sample["sample_index"],
                    "request_id": sample["request_id"],
                    "status": "service_failed",
                    "reason": sample["status"],
                    "files": [],
                }
            )
            continue

        try:
            parsed_files = parse_sample_text(sample["text"], base_files)
            rows.append(
                {
                    "sample_index": sample["sample_index"],
                    "request_id": sample["request_id"],
                    "status": "parsed",
                    "reason": None,
                    "files": parsed_files,
                }
            )
        except ParseError as exc:
            rows.append(
                {
                    "sample_index": sample["sample_index"],
                    "request_id": sample["request_id"],
                    "status": "parse_failed",
                    "reason": str(exc),
                    "files": [],
                }
            )

    effect = {
        "kind": "candidate_batch",
        "run_id": event["run_id"],
        "base_snapshot_ref": event["base_snapshot_ref"],
        "samples": rows,
    }
    return {"state": state, "effects": [effect]}


def _candidate_batch_ready(event: dict, state: dict) -> dict:
    _check_context(state, event)
    new_state = _copy_state(state)
    normalization_flags = dict(new_state.get("normalization_flags", {}))
    rows = []

    for sample in event["samples"]:
        if sample["status"] != "parsed":
            rows.append(
                {
                    "sample_index": sample["sample_index"],
                    "request_id": sample["request_id"],
                    "admission": None,
                    "normalization": None,
                }
            )
            continue

        nested = sample["admission_event"]
        if not isinstance(nested, dict):
            raise ValueError("parsed sample missing admission_event")

        admission = assess_candidate(nested)
        normalization = None

        if admission["status"] == "admit":
            source_files = [
                {
                    "path": row["path"],
                    "before": row["before_text"],
                    "after": row["after_text"],
                }
                for row in nested["content"]["files"]
            ]
            normalized_files, flags = prepare_normalization_files(source_files)
            normalization_flags[sample["request_id"]] = flags
            normalization = {
                "kind": "text_diff",
                "request_id": sample["request_id"],
                "snapshot_ref": admission["snapshot_ref"],
                "files": normalized_files,
            }

        rows.append(
            {
                "sample_index": sample["sample_index"],
                "request_id": sample["request_id"],
                "admission": admission,
                "normalization": normalization,
            }
        )

    new_state["normalization_flags"] = normalization_flags
    effect = {
        "kind": "candidate_assessments",
        "run_id": event["run_id"],
        "base_snapshot_ref": event["base_snapshot_ref"],
        "samples": rows,
    }
    return {"state": new_state, "effects": [effect]}


def _empty_selection(base_snapshot_ref: str) -> dict:
    return {
        "mode": "empty_base",
        "sample_index": None,
        "snapshot_ref": base_snapshot_ref,
    }


def _normalized_batch_ready(event: dict, state: dict) -> dict:
    _check_context(state, event)
    flags_map = state.get("normalization_flags", {})
    if not isinstance(flags_map, dict):
        flags_map = {}

    sample_rows = []
    eligible_rows = []

    for sample in event["samples"]:
        admission = sample["admission"]
        snapshot_ref = admission["snapshot_ref"] if isinstance(admission, dict) else None
        admission_status = admission["status"] if isinstance(admission, dict) else None

        normalized_key = ""
        diff_receipt = sample["diff_receipt"]
        if (
            admission_status == "admit"
            and isinstance(diff_receipt, dict)
            and diff_receipt.get("status") == "completed"
        ):
            flags = flags_map.get(sample["request_id"], [])
            normalized_key = build_normalized_key(diff_receipt["files"], flags)

        row = {
            "sample_index": sample["sample_index"],
            "request_id": sample["request_id"],
            "snapshot_ref": snapshot_ref,
            "admission_status": admission_status,
            "normalized_key": normalized_key,
        }
        sample_rows.append(row)
        if normalized_key:
            eligible_rows.append(row)

    if eligible_rows:
        first = eligible_rows[0]
        first_eligible = {
            "mode": "candidate",
            "sample_index": first["sample_index"],
            "snapshot_ref": first["snapshot_ref"],
        }

        vote_counts: dict[str, int] = {}
        first_by_key: dict[str, dict] = {}
        for row in eligible_rows:
            key = row["normalized_key"]
            vote_counts[key] = vote_counts.get(key, 0) + 1
            if key not in first_by_key:
                first_by_key[key] = row

        winning_key = max(
            first_by_key.keys(),
            key=lambda key: (vote_counts[key], -first_by_key[key]["sample_index"]),
        )
        winner = first_by_key[winning_key]
        vote = {
            "mode": "candidate",
            "sample_index": winner["sample_index"],
            "snapshot_ref": winner["snapshot_ref"],
        }
        winning_votes = vote_counts[winning_key]
    else:
        first_eligible = _empty_selection(event["base_snapshot_ref"])
        vote = _empty_selection(event["base_snapshot_ref"])
        winning_votes = 0

    counts = {
        "attempted": len(sample_rows),
        "admitted": sum(row["admission_status"] == "admit" for row in sample_rows),
        "eligible": len(eligible_rows),
        "distinct_trees": len(
            {row["snapshot_ref"] for row in sample_rows if row["snapshot_ref"] is not None}
        ),
        "distinct_keys": len({row["normalized_key"] for row in eligible_rows}),
        "winning_votes": winning_votes,
    }

    effect = {
        "kind": "sample_selection",
        "run_id": event["run_id"],
        "base_snapshot_ref": event["base_snapshot_ref"],
        "samples": sample_rows,
        "first_eligible": first_eligible,
        "vote": vote,
        "counts": counts,
    }
    return {"state": state, "effects": [effect]}


def handle(event: dict, state: dict) -> dict:
    state_obj = _copy_state(state)
    kind = event.get("kind")
    if kind == "begin_samples":
        return _begin_samples(event, state_obj)
    if kind == "sample_batch_ready":
        return _sample_batch_ready(event, state_obj)
    if kind == "candidate_batch_ready":
        return _candidate_batch_ready(event, state_obj)
    if kind == "normalized_batch_ready":
        return _normalized_batch_ready(event, state_obj)
    raise ValueError(f"unknown event kind: {kind}")
