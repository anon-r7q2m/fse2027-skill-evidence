#!/usr/bin/env python3
"""Prepare and replay eight fixed, public JSON-path source-slice conditions.

Preparation reads the five explicitly named public experiment artifacts and
pinned Django documentation/license. Replay is stdlib-only and offline. It
executes inspected AST-selected original methods, never a full Django module.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import shutil
import unittest
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace


COMMIT = "859a87d873ce7152af73ab851653b4e1c3ffea4c"
UPSTREAM = f"https://raw.githubusercontent.com/django/django/{COMMIT}"
MODULE_PATH = "django/db/models/fields/json.py"
ENTRY = "results_cache/raw_issue_feedback_effect_v2/live/192/entry"
INPUTS = {
    "source_view": f"{ENTRY}/B/host/source_view.json",
    "B_patch": f"{ENTRY}/B/host/snapshots/capture_002/agent.patch",
    "V_patch": f"{ENTRY}/V/host/snapshots/capture_006/agent.patch",
    "checker": f"{ENTRY}/checker/generated/script.py",
    "issue": "experiments/raw_issue_feedback_effect_v2/screen/192/public_issue.json",
}
METHODS = {
    "KeyTransform": ("__init__", "preprocess_lhs", "as_mysql"),
    "HasKeyLookup": ("as_sql", "as_mysql"),
}
CASE_NAMES = (
    "test_numeric_string_key_quoted",
    "test_non_numeric_string_key",
    "test_integer_index",
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def blob_id(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def dump(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def apply_recorded_patch(source: str, patch: str) -> str:
    """Apply the single inspected file diff exactly, including every context line."""
    lines = patch.splitlines(keepends=True)
    if patch.count("diff --git ") != 1:
        raise ValueError("Expected exactly one public source-file patch")
    if f"--- a/{MODULE_PATH}\n+++ b/{MODULE_PATH}\n" not in patch:
        raise ValueError("Unexpected patched path")
    identity = re.search(r"^index ([0-9a-f]{40})\.\.([0-9a-f]{40})", patch, re.M)
    if identity is None or blob_id(source.encode()) != identity[1]:
        raise ValueError("Recorded patch does not bind the captured base source")
    original = source.splitlines(keepends=True)
    output: list[str] = []
    position = 0
    index = 0
    while index < len(lines):
        match = re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", lines[index])
        if match is None:
            index += 1
            continue
        start = int(match[1]) - 1
        if start < position:
            raise ValueError("Overlapping patch hunks")
        output.extend(original[position:start])
        position = start
        removed = added = 0
        index += 1
        while index < len(lines) and not lines[index].startswith("@@ "):
            line = lines[index]
            if not line or line[0] not in " +-":
                raise ValueError("Unsupported patch line")
            if line[0] in " -":
                if position >= len(original) or original[position] != line[1:]:
                    raise ValueError("Patch context mismatch")
                position += 1
                removed += 1
            if line[0] in " +":
                output.append(line[1:])
                added += 1
            index += 1
        if (removed, added) != (int(match[2] or 1), int(match[4] or 1)):
            raise ValueError("Patch hunk lengths differ")
    output.extend(original[position:])
    result = "".join(output)
    if blob_id(result.encode()) != identity[2]:
        raise ValueError("Reconstructed candidate does not match recorded Git blob")
    return result


def extract_slice(source: str) -> tuple[str, list[dict]]:
    """Keep original method bytes; omit unrelated class methods and module setup."""
    lines = source.splitlines(keepends=True)
    parts = ["# Exact source-method excerpts; globals and class bases are supplied by replay.py.\n"]
    provenance = []

    def append(node: ast.AST, name: str) -> None:
        segment = "".join(lines[node.lineno - 1 : node.end_lineno])
        parts.append(segment + "\n")
        provenance.append(
            {
                "symbol": name,
                "start_line": node.lineno,
                "end_line": node.end_lineno,
                "sha256": digest(segment.encode()),
            }
        )

    tree = ast.parse(source)
    function = next(
        n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "compile_json_path"
    )
    append(function, function.name)
    for name, methods in METHODS.items():
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == name)
        parts.append(lines[cls.lineno - 1])
        if name == "HasKeyLookup":
            attribute = next(
                n
                for n in cls.body
                if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == "logical_operator" for t in n.targets)
            )
            append(attribute, "HasKeyLookup.logical_operator")
        for method in methods:
            node = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == method)
            append(node, f"{name}.{method}")
    return "\n".join(parts), provenance


def fixtures() -> list[dict]:
    fixed = []
    for snapshot in ("Base", "B", "V"):
        fixed.append(
            {
                "id": f"{snapshot}_original",
                "snapshot": snapshot,
                "mode": "original_checker",
                "expected_statuses": ["PASS" if snapshot == "V" else "FAIL", "PASS", "PASS"],
                "expected_outputs": [
                    '$."1111"' if snapshot == "V" else "$[1111]",
                    '$."foo"',
                    "$[3]",
                ],
                "control_count": 2,
                "issue_proxy_count": 1,
            }
        )
        fixed.append(
            {
                "id": f"{snapshot}_production_path",
                "snapshot": snapshot,
                "mode": "production_path",
                "expected_statuses": ["PASS", "FAIL" if snapshot == "V" else "PASS"],
                "expected_outputs": ['$."foo"', '$."3"' if snapshot == "V" else "$[3]"],
                "control_count": 2,
                "issue_proxy_count": 0,
            }
        )
    fixed.extend(
        [
            {
                "id": "V_equivalent_helper",
                "snapshot": "V",
                "mode": "equivalent_helper",
                "expected_statuses": ["PASS", "FAIL"],
                "expected_outputs": ['$."foo"', '$."3"'],
                "control_count": 2,
                "issue_proxy_count": 0,
            },
            {
                "id": "B_legal_lookup_adaptation",
                "snapshot": "B",
                "mode": "legal_lookup",
                "expected_statuses": ["PASS", "PASS"],
                "expected_outputs": ['$."1111"', '$."foo"'],
                "control_count": 2,
                "issue_proxy_count": 0,
            },
        ]
    )
    return fixed


def prepare(repo: Path, artifact: Path) -> None:
    """Freeze expected observations before any source-slice method is executed."""
    if (artifact / "protocol.json").exists():
        raise FileExistsError("The frozen feedback protocol already exists")
    source_dir = artifact / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    data = {name: (repo / path).read_bytes() for name, path in INPUTS.items()}
    view = json.loads(data["source_view"])
    public = json.loads(data["issue"])["public_row"]
    if view["base_commit"] != COMMIT or public["base_commit"] != COMMIT:
        raise ValueError("Pinned public source revision mismatch")
    base = next(f["content"] for f in view["files"] if f["path"] == MODULE_PATH)
    sources = {"Base": base}
    for name in ("B", "V"):
        sources[name] = apply_recorded_patch(base, data[f"{name}_patch"].decode())
    identities = {}
    for name, source in sources.items():
        sliced, locations = extract_slice(source)
        (source_dir / f"{name}.py").write_text(sliced)
        identities[name] = {
            "full_module_sha256": digest(source.encode()),
            "git_blob": blob_id(source.encode()),
            "slice": f"source/{name}.py",
            "segments": locations,
        }
    (source_dir / "original_checker.py").write_bytes(data["checker"])
    for name in ("B", "V"):
        (source_dir / f"{name}.patch").write_bytes(data[f"{name}_patch"])
    downloaded = {}
    for key, upstream_path in {
        "license": "LICENSE",
        "documentation": "docs/topics/db/queries.txt",
    }.items():
        url = f"{UPSTREAM}/{upstream_path}"
        with urllib.request.urlopen(url, timeout=30) as response:
            downloaded[key] = {"url": url, "bytes": response.read()}
    (artifact / "LICENSE-Django.txt").write_bytes(downloaded["license"]["bytes"])
    doc = downloaded["documentation"]["bytes"].decode().splitlines()
    anchor = next(
        i
        for i, line in enumerate(doc)
        if "If the key is an integer, it will be interpreted" in line
    )
    excerpt = "\n".join(doc[anchor : anchor + 5]) + "\n"
    (source_dir / "documented_index_obligation.txt").write_text(excerpt)
    (source_dir / "public_requirement.txt").write_text(
        public["problem_statement"].splitlines()[0]
        + "\n\nThe public example requires has_key='1111' to find an object key.\n"
        + "This replay does not certify all has_key/has_keys/has_any_keys repairs.\n"
    )
    shutil.copyfile(Path(__file__), artifact / "replay.py")
    protocol = {
        "schema": "skill-reuse-principles-feedback-v1",
        "frozen_at_utc": datetime.now(UTC).isoformat(),
        "status": "FROZEN_BEFORE_OFFLINE_REPLAY",
        "instance_id": "django__django-15503",
        "fixture_limit": 8,
        "fixture_unit": "one snapshot and check policy; not an independent task",
        "source_revision": COMMIT,
        "source_url": f"{UPSTREAM}/{MODULE_PATH}",
        "source_objects": identities,
        "input_provenance": {
            name: {"repository_relative_path": INPUTS[name], "sha256": digest(value)}
            for name, value in data.items()
        },
        "documentation": {
            "url": downloaded["documentation"]["url"],
            "full_file_sha256": digest(downloaded["documentation"]["bytes"]),
            "excerpt_start_line": anchor + 1,
            "excerpt_end_line": anchor + 5,
            "interpretation": "Integer key transforms must preserve array-index semantics. This public lookup-specific issue does not authorize changing that documented behavior.",
        },
        "license": {
            "django": "BSD-3-Clause; retained in LICENSE-Django.txt",
            "url": downloaded["license"]["url"],
            "note": "B/V are recorded modifications of the BSD-licensed source. Newly authored replay/metadata remain project-author material; no repository-wide license is inferred.",
        },
        "execution_boundary": {
            "kind": "EXACT_AST_SELECTED_METHODS_WITH_EXPLICIT_MOCKS",
            "real_methods": [
                "compile_json_path",
                "KeyTransform.__init__",
                "KeyTransform.preprocess_lhs",
                "KeyTransform.as_mysql",
                "HasKeyLookup.as_sql",
                "HasKeyLookup.as_mysql",
            ],
            "mocked": [
                "Transform.__init__: stores lhs only",
                "PostgresOperatorLookup.process_lhs: compiles mock column",
                "compiler.compile: COLUMN to SQL COLUMN with no parameters",
                "connection.vendor: mysql",
            ],
            "not_executed": [
                "full Django imports",
                "ORM query resolution",
                "database execution",
                "SQLite/Oracle backends",
                "LLM",
                "Docker",
                "official scoring",
            ],
        },
        "assertion_roles": {
            "original_numeric_string": "FAULTY_PROXY_OBSERVATION_ONLY; not an issue-correctness ground truth",
            "original_controls": [
                "direct helper ['foo'] -> $.\"foo\"",
                "direct helper [3] -> $[3]",
            ],
            "production_controls": [
                "original KeyTransform('foo', COLUMN).as_mysql -> $.\"foo\"",
                "original KeyTransform(3, COLUMN).as_mysql -> $[3]",
            ],
            "equivalent_helper_controls": [
                "direct helper ['foo'] -> $.\"foo\"",
                "direct helper ['3'] -> $[3]",
            ],
            "legal_lookup_controls": [
                "B HasKeyLookup RHS '1111' -> $.\"1111\"",
                "B HasKeyLookup RHS 'foo' -> $.\"foo\"",
            ],
        },
        "interpretation_rules": [
            "All three compared preservation policies use exactly two controls; only the original checker additionally has the separately labelled faulty issue assertion.",
            "Original full-checker rejection of Base/B is not evidence of failure of the public issue or of the array-index preservation obligation.",
            "Legal adaptation is certified only for the two exercised SQL-path constructions, not the complete candidate or issue.",
            "If equivalent direct-helper controls detect the same V regression, the path aids control derivation, not unique or general superiority.",
            "FAIL means an executed assertion is false; UNKNOWN means missing source, an execution exception, or missing evidence.",
            "No benchmark score, population rate, or new independent confirmation follows from these exposed fixtures.",
        ],
        "fixtures": fixtures(),
        "files_sha256": {},
    }
    protocol["files_sha256"] = {
        str(path.relative_to(artifact)): digest(path.read_bytes())
        for path in sorted(artifact.rglob("*"))
        if path.is_file()
    }
    destination = repo / "experiments/skill_reuse_principles_v1/feedback_protocol.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError("Refusing to overwrite the experiment protocol")
    dump(destination, protocol)
    shutil.copyfile(destination, artifact / "protocol.json")
    dump(
        artifact / "preparation.json",
        {
            "status": "FROZEN_NOT_EXECUTED",
            "protocol_sha256": digest(destination.read_bytes()),
            "fixture_conditions": 8,
        },
    )
    print(
        json.dumps(
            {
                "status": "FROZEN_NOT_EXECUTED",
                "conditions": 8,
                "protocol_sha256": digest(destination.read_bytes()),
            }
        )
    )


class MockTransform:
    """Explicit substitute for the unrelated Django expression constructor."""

    def __init__(self, lhs):
        self.lhs = lhs


class MockCompiler:
    def compile(self, value):
        if value != "COLUMN":
            raise ValueError("Only the frozen column boundary is supported")
        return "COLUMN", []


class MockLookup:
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs

    def process_lhs(self, compiler, connection):
        return compiler.compile(self.lhs)


def namespace(artifact: Path, snapshot: str) -> dict:
    path = artifact / "source" / f"{snapshot}.py"
    environment = {
        "__name__": "inspected_django_slice",
        "json": json,
        "Transform": MockTransform,
        "PostgresOperatorLookup": MockLookup,
    }
    exec(compile(ast.parse(path.read_text()), str(path), "exec"), environment)
    return environment


def run_condition(artifact: Path, fixture: dict) -> dict:
    environment = namespace(artifact, fixture["snapshot"])
    original = environment["compile_json_path"]
    calls = []

    def observed_helper(keys, *args, **kwargs):
        output = original(keys, *args, **kwargs)
        calls.append(
            {
                "keys": keys,
                "key_types": [type(key).__name__ for key in keys],
                "args": list(args),
                "kwargs": kwargs,
                "output": output,
            }
        )
        return output

    environment["compile_json_path"] = observed_helper
    compiler = MockCompiler()
    connection = SimpleNamespace(vendor="mysql")
    observations = []

    def observe(name, role, action, expected):
        start = len(calls)
        try:
            actual = action()
            status = "PASS" if actual == expected else "FAIL"
            detail = {"actual": actual, "expected": expected}
        except Exception as error:
            status = "UNKNOWN"
            detail = {"exception": type(error).__name__, "message": str(error)}
        observations.append(
            {"name": name, "role": role, "status": status, **detail, "helper_calls": calls[start:]}
        )

    mode = fixture["mode"]
    if mode == "original_checker":
        checker = artifact / "source/original_checker.py"
        tree = ast.parse(checker.read_text())
        behavior = next(
            node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Behavior"
        )
        environment["unittest"] = unittest
        exec(
            compile(ast.Module(body=[behavior], type_ignores=[]), str(checker), "exec"), environment
        )
        for number, name in enumerate(CASE_NAMES):
            start = len(calls)
            try:
                case = environment["Behavior"](name)
                getattr(case, name)()
                status, detail = "PASS", {}
            except AssertionError as error:
                status, detail = "FAIL", {"assertion": str(error)}
            except Exception as error:
                status, detail = (
                    "UNKNOWN",
                    {"exception": type(error).__name__, "message": str(error)},
                )
            observations.append(
                {
                    "name": name,
                    "role": "faulty_issue_proxy" if number == 0 else "control",
                    "status": status,
                    **detail,
                    "helper_calls": calls[start:],
                }
            )
    elif mode == "production_path":
        for key, expected in (("foo", '$."foo"'), (3, "$[3]")):
            observe(
                f"KeyTransform({key!r}).as_mysql",
                "control",
                lambda key=key: environment["KeyTransform"](key, "COLUMN").as_mysql(
                    compiler, connection
                )[1][-1],
                expected,
            )
    elif mode == "equivalent_helper":
        for key, expected in (("foo", '$."foo"'), ("3", "$[3]")):
            observe(
                f"compile_json_path([{key!r}])",
                "control",
                lambda key=key: observed_helper([key]),
                expected,
            )
    elif mode == "legal_lookup":
        for key, expected in (("1111", '$."1111"'), ("foo", '$."foo"')):
            observe(
                f"HasKeyLookup(rhs={key!r}).as_mysql",
                "authorized_lookup_control",
                lambda key=key: environment["HasKeyLookup"]("COLUMN", key).as_mysql(
                    compiler, connection
                )[1][-1],
                expected,
            )
    else:
        raise ValueError("Unfrozen condition mode")
    statuses = [item["status"] for item in observations]
    outputs = [
        item["actual"]
        if "actual" in item
        else item["helper_calls"][-1]["output"]
        if item["helper_calls"]
        else None
        for item in observations
    ]
    controls = [item for item in observations if item["role"] != "faulty_issue_proxy"]
    return {
        "id": fixture["id"],
        "snapshot": fixture["snapshot"],
        "mode": mode,
        "observations": observations,
        "control_status": "UNKNOWN"
        if any(o["status"] == "UNKNOWN" for o in controls)
        else "FAIL"
        if any(o["status"] == "FAIL" for o in controls)
        else "PASS",
        "expected_observations_match": statuses == fixture["expected_statuses"]
        and outputs == fixture["expected_outputs"],
    }


def replay(artifact: Path) -> int:
    protocol_path = artifact / "protocol.json"
    protocol = json.loads(protocol_path.read_text())
    if protocol["fixtures"] != fixtures() or len(protocol["fixtures"]) != 8:
        raise ValueError("Condition list differs from the frozen eight")
    correction_path = artifact / "implementation_fix.json"
    correction = json.loads(correction_path.read_text()) if correction_path.exists() else None
    for relative, expected in protocol["files_sha256"].items():
        if relative == "replay.py" and correction is not None:
            if (
                correction["frozen_protocol_sha256"] != digest(protocol_path.read_bytes())
                or correction["original_runner_sha256"] != expected
                or digest((artifact / "replay.initial.py").read_bytes()) != expected
            ):
                raise ValueError("Implementation correction does not bind the original replay")
            expected = correction["replacement_runner_sha256"]
        if digest((artifact / relative).read_bytes()) != expected:
            raise ValueError(f"Frozen source/artifact integrity mismatch: {relative}")
    rows = [run_condition(artifact, fixture) for fixture in protocol["fixtures"]]
    by_id = {row["id"]: row for row in rows}
    clean = (
        "Base_original",
        "Base_production_path",
        "B_original",
        "B_production_path",
        "B_legal_lookup_adaptation",
    )
    unknown = sum(item["status"] == "UNKNOWN" for row in rows for item in row["observations"])
    result = {
        "schema": "skill-reuse-principles-feedback-result-v1",
        "protocol_sha256": digest(protocol_path.read_bytes()),
        "implementation_fix": correction,
        "executed_at_utc": datetime.now(UTC).isoformat(),
        "execution_kind": protocol["execution_boundary"]["kind"],
        "fixture_conditions": len(rows),
        "fixture_condition_is_not_independent_task": True,
        "all_frozen_observations_match": all(row["expected_observations_match"] for row in rows),
        "unknown_assertions": unknown,
        "known_regression_detection": {
            mode: {
                "detected": int(by_id[name]["control_status"] == "FAIL"),
                "missed": int(by_id[name]["control_status"] == "PASS"),
                "unknown": int(by_id[name]["control_status"] == "UNKNOWN"),
                "denominator": "one reused V source object",
            }
            for mode, name in {
                "original_direct_controls": "V_original",
                "production_path_controls": "V_production_path",
                "equivalent_direct_controls": "V_equivalent_helper",
            }.items()
        },
        "nonregressing_obligation_conditions": {
            "count": len(clean),
            "false_rejections": sum(by_id[name]["control_status"] == "FAIL" for name in clean),
            "unknown": sum(by_id[name]["control_status"] == "UNKNOWN" for name in clean),
            "not_a_whole_patch_correctness_label": True,
        },
        "conclusion": "Production-path controls and equally small equivalent direct-helper controls detect the same V array-index regression; the original two direct controls miss it. The real path supplies the relevant input transformation, not a unique testing capability. The B scalar lookup adaptation is retained on two exercised paths.",
        "benchmark_gain_claim": False,
        "independent_confirmation": False,
        "rows": rows,
    }
    dump(artifact / "result.json", result)
    lines = [
        "# Feedback source-slice replay",
        "",
        "This is an offline, exposed-case diagnostic with eight fixture conditions, not eight tasks.",
        "Exact original method bodies are selected by AST and run with explicit mock boundaries.",
        "No full Django module, ORM query, database, model, container, or official scorer is executed.",
        "",
        "Run from any directory after copying this entire folder: `python3 /path/to/feedback/replay.py`.",
        "Python 3.12+ standard library only; replay performs no network access and requires no repository.",
        "",
        "| Condition | Two controls | Original issue proxy | Frozen observations match |",
        "|---|---|---|---|",
    ]
    for row in rows:
        proxies = [
            item["status"] for item in row["observations"] if item["role"] == "faulty_issue_proxy"
        ]
        lines.append(
            f"| {row['id']} | {row['control_status']} | {proxies[0] if proxies else 'not run'} | {row['expected_observations_match']} |"
        )
    lines.extend(
        [
            "",
            "The original checker's numeric-string issue assertion is a faulty proxy observation, not ground truth.",
            "Original checker conditions contain three assertions: one proxy and exactly two controls.",
            "The three preservation policies are compared on their two controls only.",
            "The normal/authorized-adaptation condition has two checks of B's scalar has-key SQL paths.",
            "Passing those paths does not establish B's complete issue correctness.",
            "",
            "One implementation correction is recorded in implementation_fix.json. The initial result and replay are retained. It corrects a reducer comparing a helper's root-free substring against the final SQL-path parameter; source, assertions, fixtures and expected observations remain unchanged.",
            "",
            result["conclusion"],
            "",
            f"Unknown assertions: {unknown}. False rejections among five nonregressing obligation conditions: {result['nonregressing_obligation_conditions']['false_rejections']}; those conditions reuse Base/B and are not independent observations.",
            "",
            "## Source and boundaries",
            "",
            f"Django base revision: `{COMMIT}`. `protocol.json` records original source hashes, exact segment locations, recorded B/V patch identities, public documentation, frozen expected observations and file hashes.",
            "`source/*.py` contains only compile_json_path; KeyTransform constructor, preprocess_lhs, as_mysql; and HasKeyLookup as_sql/as_mysql with its original logical_operator. Class headers/method bodies retain original source bytes.",
            "Transform construction, column compilation, parent lookup processing and a MySQL vendor object are explicitly mocked. The real KeyTransform string conversion, original preprocess method and original as_mysql call into the original helper execute. Full ORM resolution and database semantics remain unassessed.",
            "The original generated checker is retained byte-for-byte; only its inspected Behavior class is executed with compile_json_path bound to each source slice. Its Django import is not executed.",
            "",
            "## Scope and licensing",
            "",
            "This is retrospective diagnostic validation, not held-out confirmation, a population rate, or evidence of benchmark gain. SQLite/Oracle execution, every lookup variant, and complete task correctness remain unassessed.",
            "Django excerpts and recorded modifications retain the BSD-3-Clause notice in LICENSE-Django.txt. The new replay and metadata are project-author material; this package does not infer a repository-wide release license. Public release permissions remain with the authors.",
            "No private annotations, hidden tests, solver request bodies, credentials, or official scoring artifacts are included.",
        ]
    )
    (artifact / "README.md").write_text("\n".join(lines) + "\n")
    print(
        json.dumps(
            {
                key: result[key]
                for key in (
                    "fixture_conditions",
                    "all_frozen_observations_match",
                    "unknown_assertions",
                    "known_regression_detection",
                    "nonregressing_obligation_conditions",
                )
            },
            indent=2,
        )
    )
    return 0 if result["all_frozen_observations_match"] and unknown == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", nargs="?", choices=("prepare", "run"), default="run")
    parser.add_argument("--artifact", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--repo", type=Path)
    args = parser.parse_args()
    if args.command == "prepare":
        if args.repo is None:
            parser.error("prepare requires --repo")
        prepare(args.repo.resolve(), args.artifact.resolve())
        return 0
    return replay(args.artifact.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
