import ast
import hashlib
import json
import re


CODE_BLOCK_RE = re.compile(r"```python(.*?)```", re.DOTALL)
MAX_SCRIPT_BYTES = 32768


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def extract_response_text(response):
    if type(response) is not dict:
        return ""
    output = response.get("output")
    if type(output) is not list:
        return ""
    parts = []
    for item in output:
        if type(item) is not dict or item.get("type") != "message":
            continue
        content = item.get("content")
        if type(content) is not list:
            continue
        for part in content:
            if type(part) is dict and part.get("type") == "output_text" and type(part.get("text")) is str:
                parts.append(part["text"])
    return "".join(parts)


def extract_first_python_block(text):
    if type(text) is not str:
        return None
    match = CODE_BLOCK_RE.search(text)
    if not match:
        return None
    return match.group(1).strip()


def _mapping_error(reason):
    return {"ok": False, "reason": reason}


def parse_obligations_mapping(script_text, card):
    if type(script_text) is not str:
        return _mapping_error("SCRIPT_NOT_TEXT")
    if len(script_text.encode("utf-8")) > MAX_SCRIPT_BYTES:
        return _mapping_error("SCRIPT_TOO_LARGE")
    try:
        module = ast.parse(script_text, filename="script.py", mode="exec")
    except SyntaxError:
        return _mapping_error("SCRIPT_SYNTAX_ERROR")
    mapping_node = None
    mapping_count = 0
    for node in module.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "OBLIGATIONS":
                    mapping_count += 1
                    if len(node.targets) != 1:
                        return _mapping_error("OBLIGATIONS_ASSIGNMENT_INVALID")
                    mapping_node = node.value
        elif isinstance(node, ast.AnnAssign):
            target = node.target
            if isinstance(target, ast.Name) and target.id == "OBLIGATIONS":
                mapping_count += 1
                mapping_node = node.value
        elif isinstance(node, ast.AugAssign):
            target = node.target
            if isinstance(target, ast.Name) and target.id == "OBLIGATIONS":
                return _mapping_error("OBLIGATIONS_REASSIGNED")
    if mapping_count != 1 or mapping_node is None:
        return _mapping_error("OBLIGATIONS_MISSING")
    try:
        mapping = ast.literal_eval(mapping_node)
    except Exception:
        return _mapping_error("OBLIGATIONS_NOT_LITERAL")
    if type(mapping) is not dict:
        return _mapping_error("OBLIGATIONS_NOT_DICT")
    expected_ids = [row["id"] for row in card["obligations"]]
    expected_set = set(expected_ids)
    actual_keys = list(mapping.keys())
    if any(type(key) is not str for key in actual_keys):
        return _mapping_error("OBLIGATION_ID_INVALID")
    if set(actual_keys) != expected_set or len(actual_keys) != len(expected_ids):
        return _mapping_error("OBLIGATION_KEYS_MISMATCH")
    values = []
    for key in expected_ids:
        value = mapping.get(key)
        if type(value) is not str:
            return _mapping_error("TEST_NAME_INVALID")
        parts = value.split(".")
        if len(parts) != 2:
            return _mapping_error("TEST_NAME_INVALID")
        cls_name, method_name = parts
        if not cls_name.isidentifier() or not method_name.isidentifier() or not method_name.startswith("test"):
            return _mapping_error("TEST_NAME_INVALID")
        values.append(value)
    if len(set(values)) != len(values):
        return _mapping_error("TEST_NAME_DUPLICATE")
    normalized = {}
    for key in expected_ids:
        normalized[key] = mapping[key]
    return {"ok": True, "mapping": normalized, "script": script_text}


def build_card_json(card, mapping):
    obligations = []
    for row in card["obligations"]:
        obligations.append(
            {
                "id": row["id"],
                "test": mapping[row["id"]],
                "role": row["role"],
                "basis": row["basis"],
            }
        )
    return json.dumps({"obligations": obligations}, ensure_ascii=False, separators=(",", ":"))


def build_submission(card, script_text, mapping):
    card_json = build_card_json(card, mapping)
    return {
        "script": script_text,
        "card_json": card_json,
        "mapping": dict(mapping),
        "script_sha256": sha256_text(script_text),
        "input_hashes": {
            "script.py": sha256_text(script_text),
            "card.json": sha256_text(card_json),
        },
    }


def parse_model_submission(card, response):
    full_text = extract_response_text(response)
    code = extract_first_python_block(full_text)
    if code is None:
        return {"ok": False, "reason": "FIRST_CODE_BLOCK_MISSING", "raw_output": full_text}
    parsed = parse_obligations_mapping(code, card)
    parsed["raw_output"] = full_text
    if not parsed["ok"]:
        return parsed
    parsed["submission"] = build_submission(card, parsed["script"], parsed["mapping"])
    return parsed
