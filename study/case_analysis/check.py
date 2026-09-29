"""Read-only reference and record checks; no target imports or execution."""

import json
from functools import lru_cache
from pathlib import Path
import tarfile


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def require(condition, message):
    if not condition:
        raise ValueError(message)


def pointer(value, path):
    require(path == "" or path.startswith("/"), f"Invalid JSON Pointer: {path}")
    for token in path.split("/")[1:]:
        token = token.replace("~1", "/").replace("~0", "~")
        value = value[int(token)] if isinstance(value, list) else value[token]
    return value


@lru_cache(maxsize=None)
def read_text(path, member=None):
    source = (ROOT / path).resolve()
    require(source.is_relative_to(ROOT), f"Reference outside artifact: {path}")
    if member is None:
        return source.read_text(encoding="utf-8")
    with tarfile.open(source) as archive:
        item = archive.getmember(member)
        require(item.isfile(), f"Archive member is not a regular file: {member}")
        return archive.extractfile(item).read().decode("utf-8")


def resolve(reference):
    text = read_text(reference["path"], reference.get("member"))
    if "fields" in reference:
        value = json.loads(text)
        return {name: pointer(value, path) for name, path in reference["fields"].items()}
    if "pointer" in reference:
        return pointer(json.loads(text), reference["pointer"])
    if "lines" in reference:
        start, end = reference["lines"]
        lines = text.splitlines(keepends=True)
        require(1 <= start <= end <= len(lines), f"Bad line range: {reference}")
        return "".join(lines[start - 1 : end])
    return text


def evidence_refs(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "evidence":
                yield from child
            else:
                yield from evidence_refs(child)
    elif isinstance(value, list):
        for child in value:
            yield from evidence_refs(child)


def main():
    inputs = json.loads((HERE / "case_inputs.json").read_text())
    analysis = json.loads((HERE / "case_analysis.json").read_text())
    facts = {row["id"]: row for row in inputs["facts"]}
    require(len(facts) == len(inputs["facts"]), "Duplicate fact ID")
    ids = {row["case_id"] for row in inputs["cases"]}
    require(len(ids) == len(inputs["cases"]) == 6, "Expected six analysis units")
    require(ids == {row["case_id"] for row in analysis["cases"]}, "Case IDs differ")
    for fact in facts.values():
        require(
            fact["availability"] in {"PUBLIC_RAW", "PUBLIC_PROJECTION", "REPORTED_ONLY"},
            "Unknown availability",
        )
        require(resolve(fact["reference"]) == fact["value"], f"Changed source: {fact['id']}")
    for case in inputs["cases"]:
        require(set(case["fact_ids"]) <= facts.keys(), f"Unknown input fact: {case['case_id']}")
        for unavailable in case["unavailable_inputs"]:
            resolve(unavailable["reference"])
    require(set(evidence_refs(analysis)) <= facts.keys(), "Unknown analysis premise")
    for case in analysis["cases"]:
        require(
            case["obligations"] and case["hypotheses"] and case["correction"],
            "Missing analysis field",
        )
        require(
            all(x["authority"] in {"JUSTIFIED", "ASSUMED", "UNKNOWN"} for x in case["obligations"]),
            "Unknown authority code",
        )
        require(
            all(
                x["status"] in {"SUPPORTED", "CONTRADICTED", "UNRESOLVED"}
                for x in case["hypotheses"]
            ),
            "Unknown hypothesis status",
        )
        correction = case["correction"]
        if "recorded_reference" in correction:
            require(
                resolve(correction["recorded_reference"]) == correction["recorded_value"],
                "Changed correction record",
            )

    def value(name):
        return facts[name]["value"]

    pool = value("gp.pool")
    receipts = value("gp.projection_receipts")
    require(len(pool) == len(receipts) == 2, "GP pair count")
    require(len({row["snapshot_ref"] for row in pool}) == 2, "GP originals differ")
    require(
        len({row["projection"]["projected_tree"] for row in receipts}) == 1,
        "GP projection equality",
    )
    require(
        [row["recorded_preservation_passes"] for row in receipts] == [4, 4],
        "GP preservation counts",
    )
    require(len({row["key"] for row in pool}) == 2, "GP two distinct keys")
    require(
        value("gp.original_selection")["snapshot_ref"] == pool[0]["snapshot_ref"],
        "GP first selection",
    )
    require(
        value("feedback.v_direct")["observation_2_helper_calls"][0]["keys"] == [3],
        "Direct helper integer input",
    )
    require(
        value("feedback.v_production")["observation_1_helper_calls"][0]["keys"] == ["3"],
        "Production helper string input",
    )
    require(
        value("feedback.v_production")["observation_1_actual"] == '$."3"', "V production output"
    )
    require(value("feedback.b_production")["observation_1_actual"] == "$[3]", "B production output")
    for prefix in ["a21", "a22"]:
        original, changed = value(prefix + ".trigger_original"), value(prefix + ".trigger_changed")
        require(
            original["frozen_responses"] == changed["frozen_responses"],
            "Native scripted inputs differ",
        )
        require(original["termination"] == changed["termination"], "Requested termination differs")
    require(
        value("a21.trigger_original")["producer_output"]
        == value("a21.trigger_changed")["producer_output"],
        "a21 producer output differs",
    )
    require(
        value("a21.trigger_original")["responses_consumed"] == 0
        and value("a21.trigger_changed")["responses_consumed"] == 1,
        "a21 response counts",
    )
    require(
        value("a22.trigger_original")["observed_counts"]["agent_events"] == 4
        and value("a22.trigger_changed")["observed_counts"]["agent_events"] == 2,
        "a22 event counts",
    )
    full, subset = value("pro.full_inputs"), value("pro.subset_inputs")
    full_result, subset_result = value("pro.full_result"), value("pro.subset_result")
    require(full["predictions"] == subset["predictions"], "Pro paired predictions differ")
    require(
        full_result["results"] == subset_result["results"] == {"case_a": True}, "Pro paired results"
    )
    require(
        full_result["overall_accuracy"] == subset_result["overall_accuracy"] == 1.0,
        "Pro original means",
    )
    require(
        set(full_result["results"]) != set(full["claim"]["ids"]),
        "Pro full coverage mismatch absent",
    )
    require(
        set(subset_result["results"]) == set(subset["claim"]["ids"]), "Pro subset coverage mismatch"
    )
    print(f"REFERENCE_AND_RECORD_CHECKS_PASS: {len(ids)} analysis units; {len(facts)} facts")
    print("No normative judgment, target execution, or benchmark reproduction was validated.")


if __name__ == "__main__":
    main()
