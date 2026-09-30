import copy
import hashlib
import json


MAX_SOURCE_TEXT = 24000


def clone_json(value):
    return copy.deepcopy(value)


def stable_json(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=False)


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def is_nonempty_string(value):
    return type(value) is str and bool(value)


def is_nonnegative_int(value):
    return type(value) is int and value >= 0


def is_positive_int(value):
    return type(value) is int and value > 0


def validate_prepare_card(card):
    if type(card) is not dict or set(card) != {"obligations", "source_queries"}:
        raise ValueError("PROTOCOL_REJECTED: invalid prepare card")
    obligations = card["obligations"]
    queries = card["source_queries"]
    if type(obligations) is not list or not 2 <= len(obligations) <= 40:
        raise ValueError("PROTOCOL_REJECTED: invalid obligation list")
    if type(queries) is not list or not 1 <= len(queries) <= 4:
        raise ValueError("PROTOCOL_REJECTED: invalid source query list")
    seen_ids = set()
    roles = set()
    clean_obligations = []
    for row in obligations:
        if type(row) is not dict or set(row) != {"id", "role", "basis"}:
            raise ValueError("PROTOCOL_REJECTED: invalid obligation row")
        if not all(is_nonempty_string(row[k]) for k in ("id", "role", "basis")):
            raise ValueError("PROTOCOL_REJECTED: invalid obligation field")
        if row["id"] in seen_ids:
            raise ValueError("PROTOCOL_REJECTED: duplicate obligation id")
        if row["role"] not in ("issue", "control"):
            raise ValueError("PROTOCOL_REJECTED: invalid obligation role")
        seen_ids.add(row["id"])
        roles.add(row["role"])
        clean_obligations.append(
            {"id": row["id"], "role": row["role"], "basis": row["basis"]}
        )
    if roles != {"issue", "control"}:
        raise ValueError("PROTOCOL_REJECTED: issue and control obligations required")
    clean_queries = []
    for row in queries:
        if type(row) is not dict or set(row) != {"operation", "path", "text", "start", "end"}:
            raise ValueError("PROTOCOL_REJECTED: invalid source query")
        if row["operation"] != "read":
            raise ValueError("PROTOCOL_REJECTED: preparation requires read queries")
        if type(row["path"]) is not str or not 1 <= len(row["path"]) <= 512:
            raise ValueError("PROTOCOL_REJECTED: invalid source path")
        if row["path"].startswith(("/", ":", "-")):
            raise ValueError("PROTOCOL_REJECTED: invalid source path")
        parts = row["path"].split("/")
        if not all(part and not part.startswith(".") for part in parts):
            raise ValueError("PROTOCOL_REJECTED: invalid source path")
        if type(row["text"]) is not str or row["text"] != "":
            raise ValueError("PROTOCOL_REJECTED: read query text must be empty")
        if type(row["start"]) is not int or type(row["end"]) is not int:
            raise ValueError("PROTOCOL_REJECTED: invalid source range")
        if not (1 <= row["start"] <= row["end"] and row["end"] - row["start"] < 250):
            raise ValueError("PROTOCOL_REJECTED: invalid source range")
        clean_queries.append(
            {
                "operation": "read",
                "path": row["path"],
                "text": "",
                "start": row["start"],
                "end": row["end"],
            }
        )
    return {"obligations": clean_obligations, "source_queries": clean_queries}


def validate_prepare_domain(domain):
    expected = {
        "base_commit",
        "model_limits",
        "execution_spec",
        "projection_spec",
        "execution_limits",
    }
    if type(domain) is not dict or set(domain) != expected:
        raise ValueError("PROTOCOL_REJECTED: invalid prepare domain")
    if not is_nonempty_string(domain["base_commit"]):
        raise ValueError("PROTOCOL_REJECTED: invalid base commit")
    if type(domain["model_limits"]) is not dict or set(domain["model_limits"]) != {
        "input_token_limit",
        "output_token_limit",
    }:
        raise ValueError("PROTOCOL_REJECTED: invalid model limits")
    if not all(is_positive_int(domain["model_limits"][k]) for k in domain["model_limits"]):
        raise ValueError("PROTOCOL_REJECTED: invalid model limits")
    for key in ("execution_spec", "projection_spec", "execution_limits"):
        if type(domain[key]) is not dict:
            raise ValueError("PROTOCOL_REJECTED: invalid execution domain")
    return clone_json(domain)


def validate_prepare_event(event):
    expected = {
        "kind",
        "issue",
        "base_snapshot",
        "card",
        "domain",
        "remaining_responses",
        "remaining_output_chars",
    }
    if type(event) is not dict or set(event) != expected or event["kind"] != "prepare":
        raise ValueError("PROTOCOL_REJECTED: invalid prepare event")
    if not is_nonempty_string(event["issue"]) or not is_nonempty_string(event["base_snapshot"]):
        raise ValueError("PROTOCOL_REJECTED: invalid prepare identity")
    if not is_nonnegative_int(event["remaining_responses"]) or not is_nonnegative_int(
        event["remaining_output_chars"]
    ):
        raise ValueError("PROTOCOL_REJECTED: invalid prepare budget")
    return {
        "kind": "prepare",
        "issue": event["issue"],
        "base_snapshot": event["base_snapshot"],
        "card": validate_prepare_card(event["card"]),
        "domain": validate_prepare_domain(event["domain"]),
        "remaining_responses": event["remaining_responses"],
        "remaining_output_chars": event["remaining_output_chars"],
    }


def validate_source_completion_receipt(receipt, expected_request_id, expected_base_commit):
    if type(receipt) is not dict:
        raise ValueError("PROTOCOL_REJECTED: invalid source receipt")
    if receipt.get("request_id") != expected_request_id:
        raise ValueError("PROTOCOL_REJECTED: stale source completion")
    if receipt.get("base_commit") != expected_base_commit:
        raise ValueError("PROTOCOL_REJECTED: stale source completion")
    if "result" not in receipt or type(receipt["result"]) is not dict:
        raise ValueError("PROTOCOL_REJECTED: invalid source receipt")
    return receipt["result"]


def check_source_result(result, queries):
    if result.get("base_commit") is None:
        return False, "SOURCE_RESULT_MISSING_BASE", None
    rows = result.get("rows")
    if type(rows) is not list or len(rows) != len(queries):
        return False, "SOURCE_ROW_COUNT_MISMATCH", None
    actual_total = 0
    bundled = []
    for query, row in zip(queries, rows):
        if type(row) is not dict:
            return False, "SOURCE_ROW_INVALID", None
        if (
            row.get("path") != query["path"]
            or row.get("start") != query["start"]
            or row.get("end") != query["end"]
        ):
            return False, "SOURCE_ROW_MISMATCH", None
        if row.get("status") != "READ":
            return False, "SOURCE_ROW_NOT_READ", None
        text = row.get("text")
        if type(text) is not str or not text:
            return False, "SOURCE_ROW_EMPTY", None
        if row.get("truncated") is not False:
            return False, "SOURCE_ROW_TRUNCATED", None
        if row.get("delivered_sha256") != sha256_text(text):
            return False, "SOURCE_HASH_MISMATCH", None
        actual_total += len(text)
        bundled.append(
            {
                "path": query["path"],
                "start": query["start"],
                "end": query["end"],
                "text": text,
            }
        )
    if actual_total > MAX_SOURCE_TEXT:
        return False, "SOURCE_TOO_LARGE", None
    return True, "READY", {"rows": bundled, "delivered_characters": actual_total}


def render_source_text(source_bundle):
    parts = []
    for row in source_bundle["rows"]:
        parts.append(
            "FILE: {path} [{start}:{end}]\n{txt}".format(
                path=row["path"],
                start=row["start"],
                end=row["end"],
                txt=row["text"],
            )
        )
    return "\n\n".join(parts)


def build_model_instructions():
    return (
        "Generate one complete Python unittest module. "
        "Return exactly one first ```python fenced block containing the script. "
        "Use no tools. "
        "The script must use real repository behavior and the issue's actual public API operation chain. "
        "Assertions must consume actual observed behavior rather than fabricated output. "
        "For obligations about isolation, shared state, propagation, or downstream effects, configure distinct instances through the specified public API, invoke the required public setter or operation on one instance, and observe the other through the public API and downstream effects. "
        "Do not replace a required public operation with direct internal state or attribute assignment, monkeypatching, or substitute helpers; attributes that are themselves the specified public API remain valid. "
        "A missing required new API may be asserted only after real existing repository interaction. "
        "Keep unexpected exceptions visible, do not swallow them into False, and include a top-level literal OBLIGATIONS mapping from every public obligation id to a unique Class.test_method."
    )


def build_generation_prompt(issue, card, source_bundle):
    donor = []
    donor.append("We are currently solving the following issue within our repository.")
    donor.append("Here is the issue text:")
    donor.append("--- BEGIN ISSUE ---")
    donor.append(issue)
    donor.append("--- END ISSUE ---")
    donor.append("")
    donor.append("Please generate a complete test that can be used to reproduce the issue.")
    donor.append("")
    donor.append("The complete test should contain the following:")
    donor.append("1. Necessary imports.")
    donor.append("2. Real repository calls that exercise the issue described in the issue text through the actual public API operation chain.")
    donor.append(
        "3. A top-level literal assignment of the exact form OBLIGATIONS = {\"declared-id\": \"Behavior.test_method\", ...}."
    )
    donor.append(
        "4. A unittest.TestCase class whose declared methods match the OBLIGATIONS mapping exactly."
    )
    donor.append(
        "5. Assertions that consume actual observed behavior for every declared obligation and unaffected control."
    )
    donor.append("")
    donor.append("Adaptation from the original marker prompt and donor example:")
    donor.append("- Do not print Issue reproduced / Issue resolved / Other issues.")
    donor.append("- Use unittest assertions against observed results from real repository calls.")
    donor.append(
        "- Preserve the donor example's data flow generically: call a public API, capture the observed result, then assert on that actual result."
    )
    donor.append(
        "- If an obligation concerns isolation, shared state, propagation, or downstream effects, create distinct instances through the specified public API, change one through the required public setter or operation, and observe the other through the public API and downstream effects."
    )
    donor.append(
        "- Do not bypass the required public API path by writing internal state directly or by replacing a required setter or operation with internal attribute assignment."
    )
    donor.append(
        "- Attributes that are themselves the specified public API remain valid, but internal implementation fields are not substitutes for the required operation chain."
    )
    donor.append(
        "- Ordinary missing public dependencies should surface as execution errors; do not hide them."
    )
    donor.append(
        "- A missing required new API may be asserted only after a real existing repository call establishes actual repository interaction when appropriate."
    )
    donor.append("- Never monkeypatch, synthesize repository output, or convert unexpected exceptions into False.")
    donor.append("")
    donor.append(
        "Public issue and control obligations follow. Every obligation must be declared and checked by behavior:"
    )
    donor.append(stable_json(card))
    donor.append("")
    donor.append("Actual source excerpts follow:")
    donor.append(render_source_text(source_bundle))
    donor.append("")
    donor.append("Ensure the generated script reflects the issue described above.")
    donor.append(
        "Explain and exercise the actual repository calls, every declared obligation, unaffected controls, and state isolation/downstream effects when needed by the obligation text."
    )
    donor.append(
        "Use the source basis to identify the real public API path that should be called before asserting outcomes; do not imply a complete semantic proof."
    )
    donor.append("Wrap the complete unittest module in ```python ... ```.")
    return "\n".join(donor)


def build_repair_prompt(issue, card, source_bundle, prior_output, feedback):
    donor = []
    donor.append("Repair the previously generated unittest module.")
    donor.append("Use the same issue, obligations, and source basis.")
    donor.append("The previous attempt was not admitted.")
    donor.append("Bounded feedback:")
    donor.append(stable_json(feedback))
    donor.append("")
    donor.append("Previous model output:")
    donor.append(prior_output)
    donor.append("")
    donor.append("Issue:")
    donor.append(issue)
    donor.append("")
    donor.append("Public obligation card:")
    donor.append(stable_json(card))
    donor.append("")
    donor.append("Actual source excerpts:")
    donor.append(render_source_text(source_bundle))
    donor.append("")
    donor.append("Repair requirements:")
    donor.append(
        "- Keep the same unittest-module format and a top-level literal OBLIGATIONS mapping with every declared id exactly once."
    )
    donor.append(
        "- Preserve real repository interaction and the issue's actual public API operation chain."
    )
    donor.append(
        "- Where the obligation is about isolation, shared state, propagation, or downstream effects, configure distinct instances through the specified public API, invoke the required public setter or operation on one instance, and observe the other through the public API and downstream effects."
    )
    donor.append(
        "- Do not repair by direct internal state writes, substitute helpers, monkeypatching, or replacing a required public operation with internal attribute assignment."
    )
    donor.append(
        "- Attributes that are themselves the specified public API remain valid; internal implementation fields are not substitutes."
    )
    donor.append(
        "- Preserve the donor example's generic data flow: make a real public API call, capture the observed result, and assert on that actual result with unittest assertions."
    )
    donor.append(
        "- If a required new API is missing, assert that failure only after real existing repository interaction; do not fabricate output and keep unexpected exceptions visible."
    )
    donor.append(
        "Return one repaired Python unittest module in the first ```python fenced block."
    )
    return "\n".join(donor)
