import ast
import hashlib


_MAX_TEXT_FILES = 64
_MAX_TEXT_BYTES = 256 * 1024
_IDENTITY_FIELDS = (
    "request_id",
    "input_sha256",
    "base_commit",
    "base_snapshot_ref",
    "snapshot_ref",
    "manifest_sha256",
    "parser_profile_sha256",
)


def _receipt(event: dict, status: str, reason: str) -> dict:
    data = {"kind": "candidate_admission", "status": status, "reason": reason}
    for key in _IDENTITY_FIELDS:
        data[key] = event[key]
    return data


def _git_blob_sha1(text: str) -> str:
    raw = text.encode("utf-8")
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def _remove_empty_lines(code: str) -> str:
    return "\n".join(line for line in code.splitlines() if line.strip() != "")


def _parse_status(text: str) -> str:
    try:
        ast.parse(text)
        return "ok"
    except SyntaxError:
        return "syntax"
    except (MemoryError, RecursionError):
        return "resource"


def assess_candidate(event: dict) -> dict:
    manifest = event["manifest"]
    manifest_files = manifest["files"]

    if len(manifest_files) > _MAX_TEXT_FILES:
        return _receipt(event, "unassessed", "FILE_COUNT_LIMIT")

    total_bytes = 0
    for row in manifest_files:
        before = row["before"]
        after = row["after"]
        if before is not None:
            total_bytes += before["bytes"]
        if after is not None:
            total_bytes += after["bytes"]
    if total_bytes > _MAX_TEXT_BYTES:
        return _receipt(event, "unassessed", "TEXT_SIZE_LIMIT")

    content = event["content"]
    if content["status"] != "available":
        return _receipt(event, "unassessed", "CONTENT_UNAVAILABLE")

    rows = content["files"]

    for row in rows:
        if row["change"] != "M":
            return _receipt(event, "unassessed", "UNSUPPORTED_FILE_CHANGE")

    for row in rows:
        if not row["path"].endswith(".py"):
            return _receipt(event, "unassessed", "NON_PYTHON_FILE")

    for row in rows:
        if row["before"]["git_mode"] != row["after"]["git_mode"]:
            return _receipt(event, "unassessed", "MODE_CHANGE")

    for row in rows:
        after_text = row["after_text"]
        after_meta = row["after"]
        if _git_blob_sha1(after_text) != after_meta["git_oid"]:
            return _receipt(event, "unassessed", "STAGED_CONTENT_TRANSFORM")
        if len(after_text.encode("utf-8")) != after_meta["git_blob_bytes"]:
            return _receipt(event, "unassessed", "STAGED_CONTENT_TRANSFORM")

    for row in rows:
        status = _parse_status(row["before_text"])
        if status == "resource":
            return _receipt(event, "unassessed", "PARSER_RESOURCE_LIMIT")
        if status == "syntax":
            return _receipt(event, "unassessed", "BASE_SYNTAX_ERROR")

    for row in rows:
        if row["after_text"].strip() == "":
            return _receipt(event, "reject", "AFTER_EMPTY_OR_WHITESPACE")

    for row in rows:
        status = _parse_status(row["after_text"])
        if status == "resource":
            return _receipt(event, "unassessed", "PARSER_RESOURCE_LIMIT")
        if status == "syntax":
            return _receipt(event, "reject", "AFTER_SYNTAX_ERROR")

    normalized_after = ""
    normalized_before = ""
    for row in rows:
        normalized_after += _remove_empty_lines(row["after_text"])
        normalized_before += _remove_empty_lines(row["before_text"])

    if normalized_after == normalized_before:
        return _receipt(event, "reject", "BLANK_ONLY_OR_UNCHANGED")
    return _receipt(event, "admit", "SYNTAX_VALID_NONBLANK_CHANGE")
