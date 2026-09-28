"""Verifier-only proof that an original candidate introduced the logged syntax error."""

import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import sys


STATUS = "CANDIDATE_INDUCED_SYNTAX_FAILURE_VERIFIED"
PYTHON = "/opt/miniconda3/envs/testbed/bin/python"


def require(condition, code):
    if not condition:
        raise ValueError(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def blob(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def syntax(raw, name):
    try:
        compile(raw, name, "exec", dont_inherit=True)
    except SyntaxError as exc:
        return {"exception_class": type(exc).__name__, "line": exc.lineno}
    return None


def prove(metadata_path, log_path, artifact_dir, repo, verifier_root):
    """Read private evidence internally; return no source, test ID, line or message."""
    require(sys.executable == PYTHON, "TESTBED_INTERPRETER_REQUIRED")
    site_reader = runpy.run_path(str(Path(__file__).with_name("syntax_witness.py")))[
        "exception_site"
    ]
    raw_log = log_path.read_bytes()
    site = site_reader(raw_log.decode("utf-8"))
    require(site is not None, "UNIQUE_SYNTAX_SITE_REQUIRED")
    metadata_raw = metadata_path.read_bytes()
    metadata = json.loads(metadata_raw)
    manifest_raw = (artifact_dir / "capture_manifest.json").read_bytes()
    manifest = json.loads(manifest_raw)
    patch = (artifact_dir / "agent.patch").read_bytes()
    guard_raw = (verifier_root / "patch_validation.json").read_bytes()
    guard = json.loads(guard_raw)
    require(
        guard.get("status") == "PASS_PATCH_REPLAY"
        and guard.get("valid_execution") is True
        and guard.get("submission_disposition") == "scoreable"
        and guard.get("reason_code") is None
        and guard.get("base_commit") == manifest["base_commit"] == metadata["base_commit"]
        and guard.get("final_tree") == manifest["final_tree"]
        and guard.get("original_metadata_sha256") == sha(metadata_raw)
        and guard["v2_result"]["patch_sha256"] == manifest["patch"]["sha256"] == sha(patch),
        "ORIGINAL_REPLAY_IDENTITY_REQUIRED",
    )
    sidecar = (artifact_dir / "capture_manifest.json.sha256").read_text()
    require(sidecar == sha(manifest_raw) + "  capture_manifest.json\n", "MANIFEST_CHANGED")
    stages = verifier_root / "stages"
    for stage in ("setup", "install", "test_patch", "cleanup"):
        require((stages / (stage + ".rc")).read_text().strip() == "0", "STAGE_FAILED")
    test_rc = int((stages / "test_command.rc").read_text().strip())
    require(0 < test_rc < 126, "NORMAL_NONZERO_TEST_EXIT_REQUIRED")
    rows = [item for item in manifest["files"] if item["path"] == site["path"]]
    require(
        len(rows) == 1
        and rows[0]["change"] == "M"
        and site["path"] not in metadata["test_files"]
        and site["path"] not in guard["captured_test_path_overlap"],
        "MODIFIED_PRODUCTION_PYTHON_REQUIRED",
    )
    row = rows[0]
    target = repo / site["path"]
    require(
        repo.resolve() in target.resolve().parents
        and target.resolve() == target
        and target.is_file(),
        "REGULAR_PRODUCTION_FILE_REQUIRED",
    )

    def git(*args):
        return subprocess.check_output(
            ["git", "-C", str(repo), *args], stderr=subprocess.DEVNULL, timeout=15
        )

    require(git("rev-parse", "HEAD").decode().strip() == manifest["base_commit"], "BASE_CHANGED")
    before = git("show", manifest["base_commit"] + ":" + site["path"])
    after = target.read_bytes()
    require(
        len(before) == row["before"]["bytes"]
        and blob(before) == row["before"]["git_oid"]
        and len(after) == row["after"]["bytes"]
        and blob(after) == row["after"]["git_oid"]
        and sha(after) == row["after"]["content_sha256"],
        "BASE_OR_CANDIDATE_BYTES_CHANGED",
    )
    require(syntax(before, site["path"]) is None, "BASE_DOES_NOT_COMPILE")
    observed = syntax(after, site["path"])
    require(
        observed is not None and observed == {k: site[k] for k in ("exception_class", "line")},
        "CANDIDATE_SYNTAX_SITE_NOT_REPRODUCED",
    )
    return {
        "status": STATUS,
        "python_executable": sys.executable,
        "python_version": list(sys.version_info[:3]),
        "base_commit": manifest["base_commit"],
        "final_tree": manifest["final_tree"],
        "manifest_sha256": sha(manifest_raw),
        "patch_sha256": sha(patch),
        "metadata_sha256": sha(metadata_raw),
        "log_sha256": sha(raw_log),
        "patch_validation_sha256": sha(guard_raw),
        "path_sha256": sha(site["path"].encode()),
        "base_content_sha256": sha(before),
        "candidate_content_sha256": sha(after),
        "base_compiles": True,
        "candidate_compiles": False,
        "same_exception_site": True,
        "exception_class": observed["exception_class"],
        "candidate_executed_by_probe": False,
    }


def main():
    import argparse

    parser = argparse.ArgumentParser()
    for name in ("metadata", "log", "artifact-dir", "repo", "verifier-root"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    try:
        result = prove(args.metadata, args.log, args.artifact_dir, args.repo, args.verifier_root)
    except Exception:
        # No traceback, exception message, private source or hidden case is returned.
        print(json.dumps({"status": "CANDIDATE_SYNTAX_PROOF_UNAVAILABLE"}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
