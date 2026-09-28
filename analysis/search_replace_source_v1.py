"""One source-only calibration of pinned Agentless SEARCH/REPLACE semantics."""

import ast
from collections import OrderedDict
from contextlib import redirect_stdout
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
POSTPROCESS = ROOT / (
    "experiments/reproduction_regression_v1/sources/agentless/agentless/util/postprocess_data.py"
)
REPAIR = ROOT / (
    "results_cache/agentless_candidate_acquisition_source_v1/public/agentless/repair/repair.py"
)
OUTPUT = ROOT / "results_cache/search_replace_source_v1/calibration.json"
PIN = "5ce5888b9f149beaace393957a55ea8ee46c9f71"
SOURCE_HASHES = {
    POSTPROCESS: "9ddd0f53dbdf696d4d4726d0f05f92073db7795cb62b441dbeb5f66146d05462",
    REPAIR: "5bbd34d00a214624a7c01b44f96990dbe2cdb9ba60709b2571936eeb00b6bac7",
}
FUNCTIONS = {
    "check_syntax",
    "remove_empty_lines",
    "check_code_differ_by_just_empty_lines",
    "extract_python_blocks",
    "split_edit_multifile_commands",
    "parse_diff_edit_commands",
}


def donor():
    sources = {}
    for path, expected in SOURCE_HASHES.items():
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError("Pinned source differs: " + str(path.relative_to(ROOT)))
        sources[path] = raw.decode("utf-8")
    nodes = [
        node
        for node in ast.parse(sources[POSTPROCESS]).body
        if isinstance(node, ast.FunctionDef) and node.name in FUNCTIONS
    ]
    if {node.name for node in nodes} != FUNCTIONS:
        raise ValueError("Missing pure donor definition")
    namespace = {"ast": ast, "re": re, "OrderedDict": OrderedDict}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(POSTPROCESS), "exec"), namespace)
    prompt_name = "repair_prompt_combine_topn_cot_diff"
    prompt_node = next(
        node
        for node in ast.parse(sources[REPAIR]).body
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == prompt_name for t in node.targets)
    )
    return (
        namespace,
        ast.literal_eval(prompt_node.value),
        {node.name: [node.lineno, node.end_lineno] for node in nodes},
    )


def sample(edits):
    blocks = [
        "### sample.py\n<<<<<<< SEARCH\n" + old + "\n=======\n" + new + "\n>>>>>>> REPLACE"
        for old, new in edits
    ]
    return "```python\n" + "\n".join(blocks) + "\n```"


def fixtures():
    # Observations are fixed before source execution; raw source bytes are retained.
    return [
        {
            "id": "ordinary_indented",
            "before": "def value():\n    return 1\n",
            "edits": [("    return 1", "    return 2")],
            "expect": "admit_with_replacement",
        },
        {
            "id": "no_match",
            "before": "value = 1\n",
            "edits": [("missing = 1", "missing = 2")],
            "expect": "reject_blank_only",
        },
        {
            "id": "repeated_matches",
            "before": "value = 1\nmarker = 0\nvalue = 1\n",
            "edits": [("value = 1", "value = 2")],
            "expect": "both_matches",
        },
        {
            "id": "reverse_commands",
            "before": "value = 1\nmarker = 0\nvalue = 2\n",
            "edits": [("value = 1", "value = 2"), ("value = 2", "value = 3")],
            "expect": "reverse_original_matches",
        },
        {
            "id": "partial_miss",
            "before": "value = 1\n",
            "edits": [("value = 1", "value = 2"), ("missing = 0", "missing = 1")],
            "expect": "admit_with_replacement",
        },
        {
            "id": "boundary_newlines",
            "before": "first = 1\nlast = 1",
            "edits": [("first = 1", "first = 2"), ("last = 1", "last = 2")],
            "expect": "literal_boundary_newlines",
        },
        {
            "id": "declared_interval_only",
            "before": "value = 1\nmarker = 0\nvalue = 1\n",
            "intervals": [[3, 3]],
            "edits": [("value = 1", "value = 2")],
            "expect": "only_interval_match",
        },
        {
            "id": "invalid_syntax",
            "before": "def value():\n    return 1\n",
            "edits": [("    return 1", "    return (")],
            "expect": "reject_syntax",
        },
        {
            "id": "blank_only",
            "before": "value = 1\n",
            "edits": [("value = 1", "value = 1\n")],
            "expect": "reject_blank_only",
        },
        {
            "id": "empty_interval_source_defect",
            "before": "value = 1\n",
            "intervals": [],
            "edits": [("value = 1", "value = 2")],
            "expect": "excluded_source_exception",
        },
    ]


def observation(row):
    expected = row["expect"]
    if expected == "excluded_source_exception":
        return row.get("exception", {}).get("type") == "UnboundLocalError"
    if "exception" in row:
        return False
    after = row["after"]
    if expected == "admit_with_replacement":
        return (
            row["admitted"] and "return 2" in after
            if row["id"] == "ordinary_indented"
            else (row["admitted"] and "value = 2" in after)
        )
    if expected == "reject_blank_only":
        return row["syntax_valid"] and row["blank_only"] and not row["admitted"]
    if expected == "both_matches":
        return row["admitted"] and after.count("value = 2") == 2 and "value = 1" not in after
    if expected == "reverse_original_matches":
        return row["admitted"] and after == "\nvalue = 2\nmarker = 0\nvalue = 3\n"
    if expected == "literal_boundary_newlines":
        return row["admitted"] and after == "\nfirst = 2\nlast = 2\n"
    if expected == "only_interval_match":
        return row["admitted"] and after == "value = 1\nmarker = 0\nvalue = 2\n"
    if expected == "reject_syntax":
        return not row["syntax_valid"] and not row["admitted"]
    raise ValueError("Unknown predeclared observation")


def run():
    if OUTPUT.exists():
        raise FileExistsError("Calibration is single-use; retain its original result")
    ns, prompt_template, spans = donor()
    rows = []
    for case in fixtures():
        row = dict(case)
        row["raw_output"] = sample(case["edits"])
        row["intervals"] = case.get("intervals", [[1, len(case["before"].splitlines())]])
        log = io.StringIO()
        try:
            with redirect_stdout(log):
                blocks = ns["extract_python_blocks"](row["raw_output"])
                groups = ns["split_edit_multifile_commands"](blocks, diff_format=True)
                # A declared path mapping replaces only the donor wrapper's eval.
                if set(groups) != {"'sample.py'"}:
                    raise ValueError("Fixture commands escaped the declared path")
                after = ns["parse_diff_edit_commands"](
                    groups["'sample.py'"], case["before"], [tuple(x) for x in row["intervals"]]
                )
                row.update(
                    after=after,
                    syntax_valid=ns["check_syntax"]([after]),
                    blank_only=ns["check_code_differ_by_just_empty_lines"](
                        [after], [case["before"]]
                    ),
                )
                row["admitted"] = row["syntax_valid"] and not row["blank_only"]
        except Exception as exc:
            row["exception"] = {"type": type(exc).__name__, "message": str(exc)}
        row["stdout"] = log.getvalue()
        row["observation_matches"] = observation(row)
        rows.append(row)
    prompt = prompt_template.format(
        problem_statement="Change value() to return 2.",
        repair_relevant_file_instruction="Below is the declared complete file.",
        content="### sample.py\n" + rows[0]["before"],
    )
    passed = all(row["observation_matches"] for row in rows)
    result = {
        "status": "SOURCE_CALIBRATED" if passed else "SOURCE_OBSERVATION_MISMATCH",
        "utc": datetime.now(timezone.utc).isoformat(),
        "scope": "PUBLIC_SYNTHETIC_SOURCE_ONLY_NOT_GENERATED_PACKAGE_OR_GAIN",
        "donor_commit": PIN,
        "source_bindings": {str(p.relative_to(ROOT)): h for p, h in SOURCE_HASHES.items()},
        "source_function_spans": spans,
        "fixture_count": len(rows),
        "supported_cases": 9,
        "excluded_domain_probes": 1,
        "model_requests": 0,
        "benchmark_starts": 0,
        "scorer_starts": 0,
        "containers_started": 0,
        "new_mechanisms": 0,
        "prompt_preview": prompt,
        "adaptations": [
            "declared path mapping replaces wrapper eval",
            "synthetic complete-file context; no localization inference",
            "pure original functions only; no donor SDK initialization or Git operations",
        ],
        "rows": rows,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    print(
        json.dumps(
            {
                key: value
                for key, value in result.items()
                if key
                not in {
                    "source_bindings",
                    "source_function_spans",
                    "prompt_preview",
                    "rows",
                    "adaptations",
                }
            }
        )
    )
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    run()
