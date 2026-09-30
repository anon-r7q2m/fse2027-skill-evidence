import re


_MAX_TEXT_FILES = 64
_MAX_TEXT_BYTES = 256 * 1024
_MAX_COMMANDS = 64
_FENCE_RE = re.compile(r"\A[ \t\r\n]*```python\n(?P<body>.*)\n```[ \t\r\n]*\Z", re.DOTALL)


class ParseError(ValueError):
    pass


class _Command:
    __slots__ = ("path", "search", "replace")

    def __init__(self, path: str, search: str, replace: str) -> None:
        self.path = path
        self.search = search
        self.replace = replace


def _utf8_size(text: str) -> int:
    try:
        return len(text.encode("utf-8"))
    except UnicodeError as exc:
        raise ParseError("INVALID_UTF8_TEXT") from exc


def _context_from_before(before: str) -> str:
    return "\n" + "\n".join(before.splitlines()) + "\n"


def _extract_fenced_body(text: str) -> str:
    if not isinstance(text, str):
        raise ParseError("MISSING_TEXT")
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    match = _FENCE_RE.fullmatch(normalized)
    if match is None:
        raise ParseError("SINGLE_PYTHON_FENCE_REQUIRED")
    body = match.group("body")
    for line in body.split("\n"):
        if line.strip().startswith("```"):
            raise ParseError("NESTED_OR_EXTRA_FENCE")
    return body


def _validate_base_files(base_files: list[dict]) -> dict[str, str]:
    if not isinstance(base_files, list):
        raise ParseError("INVALID_BASE_FILES")
    if len(base_files) > _MAX_TEXT_FILES:
        raise ParseError("FILE_COUNT_LIMIT")

    base_map: dict[str, str] = {}
    for row in base_files:
        if not isinstance(row, dict):
            raise ParseError("INVALID_BASE_FILE")
        path = row.get("path")
        content = row.get("content")
        if not isinstance(path, str) or not isinstance(content, str):
            raise ParseError("INVALID_BASE_FILE")
        if path in base_map:
            raise ParseError("DUPLICATE_BASE_PATH")
        if not content.splitlines():
            raise ParseError("EMPTY_BASE_FILE")
        base_map[path] = content
    return base_map


def _validate_payload_line(line: str) -> None:
    if line in {"<<<<<<< SEARCH", "=======", ">>>>>>> REPLACE"} or line.startswith("### "):
        raise ParseError("STRUCTURAL_MARKER_IN_PAYLOAD")
    if line.strip().startswith("```"):
        raise ParseError("NESTED_OR_EXTRA_FENCE")


def _parse_commands(body: str, base_map: dict[str, str]) -> list[_Command]:
    lines = body.split("\n")
    index = 0
    commands: list[_Command] = []

    while True:
        while index < len(lines) and lines[index].strip() == "":
            index += 1
        if index >= len(lines):
            break

        header = lines[index]
        if not header.startswith("### "):
            raise ParseError("MISSING_COMMAND_HEADER")
        path = header[4:]
        if not path:
            raise ParseError("MISSING_COMMAND_HEADER")
        if path not in base_map:
            raise ParseError("UNKNOWN_PATH")
        index += 1

        if index >= len(lines) or lines[index] != "<<<<<<< SEARCH":
            raise ParseError("MISSING_SEARCH_MARKER")
        index += 1

        search_lines: list[str] = []
        while index < len(lines) and lines[index] != "=======":
            line = lines[index]
            _validate_payload_line(line)
            search_lines.append(line)
            index += 1
        if index >= len(lines):
            raise ParseError("MISSING_DIVIDER")
        if not search_lines:
            raise ParseError("EMPTY_SEARCH")
        search = "\n".join(search_lines)
        index += 1

        replace_lines: list[str] = []
        while index < len(lines) and lines[index] != ">>>>>>> REPLACE":
            line = lines[index]
            _validate_payload_line(line)
            replace_lines.append(line)
            index += 1
        if index >= len(lines):
            raise ParseError("MISSING_REPLACE_MARKER")
        while replace_lines and replace_lines[-1].strip() == "":
            replace_lines.pop()
        replace = "\n".join(replace_lines)
        index += 1

        if search == "..." or search.startswith("...\n") or replace.startswith("...\n"):
            raise ParseError("ELLIPSIS_NOT_ALLOWED")

        commands.append(_Command(path, search, replace))

    if not 1 <= len(commands) <= _MAX_COMMANDS:
        raise ParseError("INVALID_COMMAND_COUNT")
    return commands


def _group_commands(commands: list[_Command]) -> dict[str, list[_Command]]:
    grouped: dict[str, list[_Command]] = {}
    seen_by_path: dict[str, set[tuple[str, str]]] = {}

    for command in commands:
        grouped.setdefault(command.path, [])
        seen = seen_by_path.setdefault(command.path, set())
        key = (command.search, command.replace)
        if key in seen:
            continue
        seen.add(key)
        grouped[command.path].append(command)

    return grouped


def _apply_commands_for_file(
    before: str,
    commands: list[_Command],
    aggregate_before_bytes: int,
    finalized_after_bytes: int,
    remaining_baseline_after_bytes: int,
) -> tuple[str, int]:
    original_context = _context_from_before(before)
    current_context = original_context
    current_after_bytes = _utf8_size(current_context)

    applicable: list[_Command] = []
    for command in commands:
        bounded_search = "\n" + command.search + "\n"
        if bounded_search in original_context:
            applicable.append(command)

    for command in reversed(applicable):
        bounded_search = "\n" + command.search + "\n"
        bounded_replace = "\n" + command.replace + "\n"
        if bounded_search not in current_context:
            continue

        occurrences = current_context.count(bounded_search)
        projected_after_bytes = current_after_bytes + occurrences * (
            _utf8_size(bounded_replace) - _utf8_size(bounded_search)
        )
        projected_total = (
            aggregate_before_bytes
            + finalized_after_bytes
            + projected_after_bytes
            + remaining_baseline_after_bytes
        )
        if projected_total > _MAX_TEXT_BYTES:
            raise ParseError("TEXT_SIZE_LIMIT")

        current_context = current_context.replace(bounded_search, bounded_replace)
        current_after_bytes = projected_after_bytes

    return current_context, current_after_bytes


def parse_sample_text(text: str, base_files: list[dict]) -> list[dict]:
    body = _extract_fenced_body(text)
    base_map = _validate_base_files(base_files)
    commands = _parse_commands(body, base_map)
    grouped = _group_commands(commands)

    touched_paths = sorted(grouped)
    aggregate_before_bytes = 0
    baseline_after_by_path: dict[str, int] = {}

    for path in touched_paths:
        before = base_map[path]
        aggregate_before_bytes += _utf8_size(before)
        baseline_after_by_path[path] = _utf8_size(_context_from_before(before))

    baseline_after_total = sum(baseline_after_by_path.values())
    if aggregate_before_bytes + baseline_after_total > _MAX_TEXT_BYTES:
        raise ParseError("TEXT_SIZE_LIMIT")

    files: list[dict] = []
    finalized_after_bytes = 0
    remaining_baseline_after_bytes = baseline_after_total

    for path in touched_paths:
        before = base_map[path]
        current_baseline_after_bytes = baseline_after_by_path[path]
        remaining_baseline_after_bytes -= current_baseline_after_bytes

        after, after_bytes = _apply_commands_for_file(
            before,
            grouped[path],
            aggregate_before_bytes,
            finalized_after_bytes,
            remaining_baseline_after_bytes,
        )
        finalized_after_bytes += after_bytes
        files.append({"path": path, "before": before, "after": after})

    if aggregate_before_bytes + finalized_after_bytes > _MAX_TEXT_BYTES:
        raise ParseError("TEXT_SIZE_LIMIT")

    return files