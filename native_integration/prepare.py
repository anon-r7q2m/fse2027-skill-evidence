"""Prepare a new user reproduction seal without importing or running AutoGen."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shlex
import sys


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_manifest(root):
    result = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if any(part in {".git", "__pycache__", ".pytest_cache"} for part in relative.parts):
            continue
        if path.is_symlink():
            raise RuntimeError(f"Unsupported source symlink: {relative}")
        if path.is_file() and path.suffix not in {".pyc", ".pyo"}:
            result[str(relative)] = digest(path)
    return result


def write_once(path, value):
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source", required=True, type=Path, help="Prepared pinned AutoGen source directory"
    )
    parser.add_argument(
        "--python", required=True, type=Path, help="Prepared CPython 3.12 venv interpreter"
    )
    parser.add_argument(
        "--workspace", required=True, type=Path, help="New reproduction control directory"
    )
    args = parser.parse_args()
    if sys.version_info[:2] != (3, 12):
        parser.error("Use CPython 3.12, matching the recorded runtime")
    bundle = Path(__file__).resolve().parent
    workspace = args.workspace.resolve()
    source = args.source.resolve()
    # Do not resolve the interpreter symlink out of its virtual environment.
    python = Path(os.path.abspath(args.python))
    if workspace.exists() or workspace.is_relative_to(bundle) or workspace.is_relative_to(source):
        raise RuntimeError("Choose a new workspace outside the published bundle and upstream source")
    if not python.is_file():
        raise RuntimeError("The prepared interpreter does not exist")

    dependencies = json.loads((bundle / "UPSTREAM_DEPENDENCIES.json").read_text())
    for item in dependencies["dependencies"]:
        if digest(bundle / item["path_from_bundle"]) != item["sha256"]:
            raise RuntimeError("A reused public dependency changed: " + item["path_from_bundle"])
    expected_source = json.loads(
        (bundle.parent / "prospective/upstream/autogen_source_manifest.json").read_text()
    )
    actual_source = source_manifest(source)
    if actual_source != expected_source:
        raise RuntimeError("Prepared source differs from the pinned complete public snapshot")

    protocol = bundle / "experiments/native_decision_integration_v1"
    runner = bundle / "analysis/native_decision_integration_v1.py"
    patch = bundle / "patches/a21.patch"
    scientific_inputs = [runner, patch] + [
        protocol / name
        for name in (
            "PROTOCOL.md",
            "scenarios.json",
            "input_trigger.csv",
            "input_control.csv",
            "report_generator.py",
        )
    ]
    publication = json.loads((bundle / "PUBLICATION_TRANSFORMS.json").read_text())
    published_hashes = {
        item["published_path"]: item["published_sha256"] for item in publication["files"]
    }
    for path in scientific_inputs:
        if digest(path) != published_hashes[str(path.relative_to(bundle))]:
            raise RuntimeError("A published scientific input changed: " + path.name)

    workspace.mkdir(parents=True, exist_ok=False)
    paths = {
        "repo": str(bundle),
        "protocol": str(protocol),
        "study": str(workspace / "study"),
        "output": str(workspace / "results"),
        "source": str(source),
        "python": str(python),
        "patch": str(patch),
    }
    paths_file = workspace / "paths.json"
    freeze_file = workspace / "freeze.json"
    write_once(paths_file, paths)
    write_once(
        freeze_file,
        {
            "study": "native_decision_integration_v1",
            "status": "FROZEN_FOR_EXECUTION",
            "run_purpose": "NEW_USER_REPRODUCTION_NOT_ORIGINAL_EXECUTION",
            "frozen_at": datetime.now(timezone.utc).isoformat(),
            "paths": paths,
            "files": {str(path): digest(path) for path in scientific_inputs + [paths_file]},
            "source_root": str(source),
            "source_commit": dependencies["commit"],
            "source_files": actual_source,
            "python": str(python),
            "matrix_cells": 9,
            "new_target_executions_before_freeze": 0,
            "preparation_helper_sha256": digest(Path(__file__)),
            "publication_transform_manifest_sha256": digest(bundle / "PUBLICATION_TRANSFORMS.json"),
            "historical_metadata_failure_retained_in_runner": True,
        },
    )
    print("Prepared a new user reproduction. No target was imported or executed.")
    print(
        shlex.join(
            [
                str(python),
                "-B",
                str(runner),
                "--paths",
                str(paths_file),
                "--freeze",
                str(freeze_file),
            ]
        )
    )


if __name__ == "__main__":
    main()
