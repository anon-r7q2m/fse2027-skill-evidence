"""Build or run the six-fixture offline replay of the pinned Pro evaluator.

Original Python statements perform filtering, cache lookup and score reduction.
Adapters replace input-frame representation, completion order, and container work.
The proposed report consumer is separate from the original evaluator.
"""

from __future__ import annotations

import argparse
import ast
import contextlib
import hashlib
import io
import json
import os
import shutil
import tempfile
from pathlib import Path
from types import SimpleNamespace

REVISION = "ca10a60a5fcae51e6948ffe1485d4153d421e6c5"
SOURCE_HASH = "bb5d4c5486be296e464e695df3747064aaa3bb197394bc6d39980634afec2034"
SOURCE_URL = (
    "https://raw.githubusercontent.com/scaleapi/SWE-bench_Pro-os/"
    + REVISION
    + "/swe_bench_pro_eval.py"
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def prepare_bundle(bundle: Path) -> None:
    """Extract original statements without executing any fixture."""
    repo = Path(__file__).resolve().parents[2]
    protocol = repo / "experiments/skill_reuse_principles_v1/pro_protocol.json"
    raw = (bundle / "source/swe_bench_pro_eval.py").read_bytes()
    if sha256(raw) != SOURCE_HASH:
        raise ValueError("Pinned evaluator bytes do not match the frozen source")
    text = raw.decode()
    lines = text.splitlines(keepends=True)
    functions = {
        node.name: node for node in ast.parse(text).body if isinstance(node, ast.FunctionDef)
    }
    parts = []
    locations = []
    for name in ("prepare_run", "eval_with_docker", "main"):
        node = functions[name]
        end = node.body[3].end_lineno if name == "eval_with_docker" else node.end_lineno
        selected = "".join(lines[node.lineno - 1 : end])
        selected_node = ast.parse(selected).body[0]
        expected_node = ast.parse(ast.unparse(node)).body[0]
        if name == "eval_with_docker":
            expected_node.body = expected_node.body[:4]
        if ast.dump(selected_node) != ast.dump(expected_node):
            raise ValueError("Source-slice AST differs from the frozen function")
        parts.append(f"# Original lines {node.lineno}-{end}; {name}\n{selected}\n")
        locations.append(
            {
                "function": name,
                "start_line": node.lineno,
                "end_line": end,
                "selection": "first_four_statements"
                if name == "eval_with_docker"
                else "complete_function",
                "ast_equivalence": True,
            }
        )
    source_slice = "# MIT; Copyright (c) 2026 Scale AI, Inc. See source/LICENSE.\n\n" + "\n".join(
        parts
    )
    slice_path = bundle / "source/original_slices.py"
    slice_path.write_text(source_slice)
    shutil.copyfile(protocol, bundle / "inputs.json")
    shutil.copyfile(Path(__file__), bundle / "replay.py")
    write_json(
        bundle / "provenance.json",
        {
            "source_url": SOURCE_URL,
            "revision": REVISION,
            "source_sha256": SOURCE_HASH,
            "source_slice_sha256": sha256(slice_path.read_bytes()),
            "protocol_sha256": sha256(protocol.read_bytes()),
            "license": "MIT, Copyright (c) 2026 Scale AI, Inc",
            "license_url": SOURCE_URL.rsplit("/", 1)[0] + "/LICENSE",
            "license_sha256": sha256((bundle / "source/LICENSE").read_bytes()),
            "source_locations": locations,
            "source_acquisition": "Known public pinned URL; no matching source file found in scoped local evidence directories",
            "original_imports_executed": False,
            "original_worker_prefix": "Ends after cached-output return. An uncached call falls through to the explicitly mocked worker.",
            "authored_files_license": "Not inferred from the donor MIT license; project-owner release licensing remains separate.",
        },
    )


def worker_output(passed: bool) -> dict:
    """Construct synthetic test observations, never actual benchmark outcomes."""
    return {
        "tests": [
            {"name": "synthetic_f2p", "status": "PASSED" if passed else "FAILED"},
            {"name": "synthetic_p2p", "status": "PASSED"},
        ]
    }


class InputFrame:
    """Only the unique-row pandas operations used by these six fixtures."""

    def __init__(self, rows: list[dict]) -> None:
        self.loc = {row["instance_id"]: row for row in rows}
        if len(self.loc) != len(rows):
            raise ValueError("Synthetic raw rows must have unique IDs")
        self.index = self.loc.keys()

    def fillna(self, value: str) -> InputFrame:
        if value != "":
            raise ValueError("Unexpected original fillna argument")
        return self

    def set_index(self, column: str, *, drop: bool) -> InputFrame:
        if column != "instance_id" or drop:
            raise ValueError("Unexpected original index contract")
        return self


def read_json_frame(path: str, *, lines: bool) -> InputFrame:
    if not lines:
        raise ValueError("Only the frozen JSONL input branch is exercised")
    return InputFrame([json.loads(line) for line in Path(path).read_text().splitlines()])


def proposed_report_consumer(fixture: dict, original: dict, trace: list[dict]) -> dict:
    """An authored publication decision, NOT an original evaluator function."""
    ids = [prediction["instance_id"] for prediction in fixture["predictions"]]
    action = "publish_original_mean"
    reason = f"declared_{fixture['claim']['scope']}_population_supported"
    if len(ids) != len(set(ids)):
        action = "abstain_from_claimed_population_mean"
        reason = "duplicate_submission_identity"
    elif set(ids) != set(fixture["claim"]["ids"]):
        action = "abstain_from_claimed_population_mean"
        reason = "declared_population_not_covered"
    else:
        for event in trace:
            if event["source"] != "legacy_cache":
                continue
            cache = fixture["cache"]
            if cache is None:
                action = "request_recompute_without_publishing_cached_mean"
                reason = "cache_identity_unassessed"
                break
            if (
                cache["instance_id"] != event["instance_id"]
                or cache["prefix"] != event["prefix"]
                or cache["owner_patch"] != event["patch"]
            ):
                action = "request_recompute_without_publishing_cached_mean"
                reason = "externally_known_cache_patch_mismatch"
                break
    return {
        "consumer_action": action,
        "published_accuracy": original["overall_accuracy"]
        if action == "publish_original_mean"
        else None,
        "reason": reason,
    }


def run_fixture(fixture: dict, source_slice: str) -> dict:
    trace = []
    futures = []
    progress = []
    output = io.StringIO()

    class Future:
        def __init__(self, function, args, kwargs):
            self.function, self.args, self.kwargs = function, args, kwargs

        def result(self):
            return self.function(*self.args, **self.kwargs)

    class Executor:
        def __init__(self, *, max_workers):
            if max_workers != 2:
                raise ValueError("Unexpected worker limit")

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def submit(self, function, *args, **kwargs):
            future = Future(function, args, kwargs)
            futures.append(future)
            return future

    def as_completed(mapping):
        ordered = list(mapping)
        indices = fixture["completion_order"]
        if sorted(indices) != list(range(len(ordered))):
            raise ValueError("Completion order must be a permutation of submitted rows")
        return [ordered[index] for index in indices]

    class Progress:
        def __init__(self, iterable, *, total):
            self.iterable = iterable
            if len(iterable) != total:
                raise ValueError("Original progress count mismatch")

        def __iter__(self):
            return iter(self.iterable)

        def set_description(self, text):
            progress.append(text)

    def unused_runtime(*args, **kwargs):
        raise AssertionError("No nonlocal runtime is permitted")

    with tempfile.TemporaryDirectory(prefix="pro-offline-") as temporary:
        root = Path(temporary)
        rows = [
            {
                "instance_id": instance_id,
                "fail_to_pass": "['synthetic_f2p']",
                "pass_to_pass": "['synthetic_p2p']",
            }
            for instance_id in fixture["raw_ids"]
        ]
        raw_path = root / "raw.jsonl"
        raw_path.write_text("".join(json.dumps(row) + "\n" for row in rows))
        patch_path = root / "patches.json"
        write_json(patch_path, fixture["predictions"])
        args = SimpleNamespace(
            raw_sample_path=str(raw_path),
            patch_path=str(patch_path),
            output_dir=str(root),
            dockerhub_username="unused",
            scripts_dir="unused",
            num_workers=2,
            redo=False,
            block_network=True,
            docker_platform="linux/amd64",
            use_local_docker=True,
        )
        cache = fixture["cache"]
        if cache is not None:
            cache_path = root / cache["instance_id"] / (cache["prefix"] + "_output.json")
            cache_path.parent.mkdir(parents=True)
            write_json(cache_path, worker_output(cache["mock_pass"]))
        namespace = {
            "os": os,
            "json": json,
            "pd": SimpleNamespace(read_json=read_json_frame),
            "parse_args": lambda: args,
            "py_platform": SimpleNamespace(machine=lambda: "x86_64"),
            "concurrent": SimpleNamespace(
                futures=SimpleNamespace(ThreadPoolExecutor=Executor, as_completed=as_completed)
            ),
            "tqdm": Progress,
            "docker": object(),
            "eval_with_modal": unused_runtime,
        }
        exec(compile(source_slice, "source/original_slices.py", "exec"), namespace)
        original_cache_prefix = namespace["eval_with_docker"]

        def worker(patch, sample, *worker_args, **worker_kwargs):
            cached = original_cache_prefix(patch, sample, *worker_args, **worker_kwargs)
            event = {
                "instance_id": sample["instance_id"],
                "prefix": worker_kwargs["prefix"],
                "patch": patch,
                "source": "legacy_cache" if cached is not None else "mock_uncached_worker",
            }
            trace.append(event)
            if cached is not None:
                return cached
            matches = [
                item
                for item in fixture["predictions"]
                if (item["instance_id"], item["prefix"], item["patch"])
                == (event["instance_id"], event["prefix"], patch)
            ]
            if len(matches) != 1:
                raise ValueError("Mock worker identity is ambiguous")
            return worker_output(matches[0]["mock_pass"])

        namespace["eval_with_docker"] = worker
        with contextlib.redirect_stdout(output):
            namespace["main"]()
        printed = output.getvalue()
        score_lines = [
            line for line in printed.splitlines() if line.startswith("Overall accuracy:")
        ]
        if len(score_lines) != 1:
            raise ValueError("Original final reducer did not print exactly one mean")
        original = {
            "results": json.loads((root / "eval_results.json").read_text()),
            "overall_accuracy": float(score_lines[0].split(":", 1)[1].strip()),
            "scheduled": len(futures),
            "fresh_worker_calls": sum(item["source"] == "mock_uncached_worker" for item in trace),
            "cache_hits": sum(item["source"] == "legacy_cache" for item in trace),
            "progress": progress,
        }
    actual = original | proposed_report_consumer(fixture, original, trace)
    return {
        "fixture_id": fixture["id"],
        "control": fixture["control"],
        "expected": fixture["expected"],
        "actual": actual,
        "matches_expected": actual == fixture["expected"],
        "worker_trace_in_controlled_completion_order": trace,
        "original_stdout": printed,
    }


def replay(bundle: Path) -> dict:
    protocol = json.loads((bundle / "inputs.json").read_text())
    provenance = json.loads((bundle / "provenance.json").read_text())
    source_slice = (bundle / "source/original_slices.py").read_bytes()
    bindings = (
        sha256(source_slice) == provenance["source_slice_sha256"],
        sha256((bundle / "inputs.json").read_bytes()) == provenance["protocol_sha256"],
        sha256((bundle / "source/swe_bench_pro_eval.py").read_bytes()) == SOURCE_HASH,
    )
    if not all(bindings) or len(protocol["fixtures"]) != 6:
        raise ValueError("Frozen source/protocol binding or fixture limit failed")
    records = [run_fixture(fixture, source_slice.decode()) for fixture in protocol["fixtures"]]
    return {
        "scope": "SYNTHETIC_STANDALONE_ORCHESTRATION_REDUCTION_AND_CACHE_REPLAY",
        "source_revision": REVISION,
        "fixture_count": len(records),
        "matched_expectations": sum(record["matches_expected"] for record in records),
        "normal_controls_rejected": sum(
            record["control"] and record["actual"]["consumer_action"] != "publish_original_mean"
            for record in records
        ),
        "records": records,
        "limitations": protocol["limitations"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--prepare",
        action="store_true",
        help="Repository-only: build bundle before fixture execution",
    )
    parser.add_argument(
        "--output", type=Path, help="Optionally save the replay result; default prints only"
    )
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    bundle = (
        here
        if (here / "inputs.json").exists()
        else here.parents[1] / "results_cache/skill_reuse_principles_v1/pro"
    )
    if args.prepare:
        prepare_bundle(bundle)
        print("Prepared frozen standalone bundle; no fixtures executed")
        return
    result = replay(bundle)
    if args.output:
        write_json(args.output, result)
    print(json.dumps({key: value for key, value in result.items() if key != "records"}, indent=2))
    if result["matched_expectations"] != result["fixture_count"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
