"""Replay public parser examples and four pinned donor semantics cases.

This is a local, deterministic illustration, not the original full evaluator,
host qualification, independent evaluation, or benchmark scoring procedure.
"""

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import runpy
import sys


sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT / (
    "results_cache/search_replace_transfer_v1/generation/direct/final_package"
)


def main():
    spec = importlib.util.spec_from_file_location(
        "accepted_search_replace_parser", PACKAGE / "edit_parser_pkg.py"
    )
    parser = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parser)
    suite = json.loads(
        (ROOT / "experiments/search_replace_transfer_v1/public_suite.json").read_text()
    )
    assert suite["visibility"] == "PUBLIC"
    assert suite["schema"] == "p2_search_replace_parser_v1"

    sample_count = 0
    for case in suite["cases"]:
        for index, sample in enumerate(case["samples"]):
            try:
                files = parser.parse_sample_text(sample["text"], case["files"])
                status = "parsed"
            except parser.ParseError:
                files, status = [], "parse_failed"
            assert status == sample["expected_status"], (case["id"], index, "status")
            assert files == sample.get("expected_files", []), (case["id"], index, "files")
            sample_count += 1

    reference = runpy.run_path(
        str(ROOT / "analysis/search_replace_source_v1.py"),
        run_name="public_source_reference",
    )
    donor, _, _ = reference["donor"]()
    selected = {
        "repeated_matches", "reverse_commands", "partial_miss", "boundary_newlines"
    }
    matched = []
    for case in reference["fixtures"]():
        if case["id"] not in selected:
            continue
        text = reference["sample"](case["edits"])
        before = case["before"]
        with contextlib.redirect_stdout(io.StringIO()):
            blocks = donor["extract_python_blocks"](text)
            groups = donor["split_edit_multifile_commands"](blocks, diff_format=True)
            expected = donor["parse_diff_edit_commands"](
                groups["'sample.py'"], before, [(1, len(before.splitlines()))]
            )
        actual = parser.parse_sample_text(
            text, [{"path": "sample.py", "content": before}]
        )
        assert actual == [{"path": "sample.py", "before": before, "after": expected}]
        matched.append(case["id"])

    assert set(matched) == selected
    print(json.dumps({
        "scope": "PUBLIC_PARSER_DEMO_ONLY",
        "python_version": sys.version.split()[0],
        "public_case_groups": len(suite["cases"]),
        "public_samples_passed": sample_count,
        "source_semantics_cases_passed": matched,
        "benchmark_scores_reproduced": False,
        "independent_evaluation_reproduced": False,
        "host_execution_reproduced": False,
    }, indent=2))


if __name__ == "__main__":
    main()
