"""Preserve original grades; score a proven candidate-induced syntax stop as unresolved."""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

GRADER_ID = "agent2skill_swebench_verified_candidate_syntax_v1"
PROOF_STATUS = "CANDIDATE_INDUCED_SYNTAX_FAILURE_VERIFIED"
PYTHON = "/opt/miniconda3/envs/testbed/bin/python"


def load_original(path=None):
    path = Path(path) if path is not None else Path(__file__).with_name("portable_original.py")
    name = "a2s_syntax_recovery_original_grader"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def collect_proof(metadata_path, log_path):
    script = Path(__file__).with_name("syntax_proof.py")
    process = subprocess.run(
        [
            PYTHON,
            "-I",
            "-B",
            str(script),
            "--metadata",
            str(metadata_path),
            "--log",
            str(log_path),
            "--artifact-dir",
            "/a2s-out",
            "--repo",
            "/testbed",
            "--verifier-root",
            str(Path(log_path).parent),
        ],
        env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"},
        cwd="/tests",
        capture_output=True,
        timeout=45,
        check=False,
    )
    if process.returncode != 0 or process.stderr:
        return None
    return json.loads(process.stdout)


def grade_instance(original, metadata, raw_log, *, patch_is_none=False, proof_provider=None):
    result = original.grade_instance(
        metadata, raw_log, model_patch=None if patch_is_none else original._PATCH_PRESENT
    )
    result["grader_id"] = GRADER_ID
    result["adaptations"] = ["verified_candidate_syntax_empty_status_map_v1"]
    result["classification_basis"] = "ORIGINAL_PORTABLE_RULES"
    if (result.get("error") or {}).get("code") != "EMPTY_STATUS_MAP":
        return result
    try:
        proof = proof_provider() if proof_provider is not None else None
        if not (
            isinstance(proof, dict)
            and proof.get("status") == PROOF_STATUS
            and proof.get("python_executable") == PYTHON
            and proof.get("base_compiles") is True
            and proof.get("candidate_compiles") is False
            and proof.get("same_exception_site") is True
            and proof.get("candidate_executed_by_probe") is False
            and proof.get("exception_class") in {"SyntaxError", "IndentationError", "TabError"}
        ):
            return result
        official = result["official_report"][result["instance_id"]]
        if official["resolved"] is not False or official["patch_successfully_applied"] is not True:
            return result
        statuses = official["tests_status"]
        result.update(
            valid_for_scoring=True,
            classification="unresolved",
            reward=0,
            resolved=False,
            status_map={},
            metrics={
                "fail_to_pass": original.compute_fail_to_pass(statuses),
                "pass_to_pass": original.compute_pass_to_pass(statuses),
                "resolution_status": original.get_resolution_status(statuses),
            },
            error=None,
            classification_basis=PROOF_STATUS,
            syntax_evidence=proof,
        )
    except Exception:
        # Unestablished attribution keeps the original invalid result.
        return result
    return result


def main(argv=None):
    original = load_original()
    args = original.build_parser().parse_args(argv)
    try:
        metadata = json.loads(Path(args.metadata).read_text())
        raw_log = Path(args.log).read_text()
        report = grade_instance(
            original,
            metadata,
            raw_log,
            patch_is_none=args.patch_is_none,
            proof_provider=lambda: collect_proof(args.metadata, args.log),
        )
    except (OSError, UnicodeError, ValueError) as exc:
        report = original._base_report(None, None)
        report["grader_id"] = GRADER_ID
        report["error"] = {
            "code": "INPUT_READ_ERROR",
            "message": type(exc).__name__,
            "bad_codes": [],
        }
    original._write_output(args.output, report)
    return 0 if report["valid_for_scoring"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
