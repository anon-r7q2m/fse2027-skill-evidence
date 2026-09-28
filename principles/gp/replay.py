"""Build and replay the bounded GP evidence slice without external execution.

Build reads only the named public trajectory and source package. Replay needs
only the resulting directory and uses four exact original selection functions.
The new confirmed-syntax-error exclusion is deliberately separate from them.
"""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys


PROTOCOL_PATH = Path("experiments/skill_reuse_principles_v1/gp_protocol.json")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def source_slice(source: str, names: list[str]) -> tuple[str, list[dict]]:
    definitions = {
        node.name: node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef)
    }
    parts, provenance = [], []
    for name in names:
        node = definitions[name]
        segment = ast.get_source_segment(source, node)
        if segment is None:
            raise ValueError(f"Source segment unavailable: {name}")
        parts.append(segment)
        provenance.append(
            {
                "function": name,
                "line_start": node.lineno,
                "line_end": node.end_lineno,
                "segment_sha256": digest(segment.encode()),
            }
        )
    return "\n\n\n".join(parts) + "\n", provenance


def historical_inputs(trajectory: dict, protocol: dict) -> dict:
    identity = protocol["source"]
    selection = trajectory["selection"]
    original = selection["p"]["state"]
    refs = [identity["early_snapshot"], identity["later_snapshot"]]
    if original["order"] != refs:
        raise ValueError("The recorded pool is not the frozen two-candidate order")
    pool = [copy.deepcopy(original["candidates"][ref]) for ref in refs]
    query = next(
        action
        for action in trajectory["actions"]
        if action["query_id"] == identity["syntax_error_query"]
    )
    diagnostic = query["result"]["stdout"]
    if "SyntaxError: invalid syntax" not in diagnostic or "line 418" not in diagnostic:
        raise ValueError("The frozen public syntax error is missing")
    additions = []
    for record in selection["content_receipts"]:
        if record["snapshot_ref"] not in refs:
            continue
        files = record["result"]["files"]
        if len(files) != 1 or files[0]["path"] != identity["modified_path"]:
            raise ValueError("Unexpected historical changed-file population")
        item = files[0]
        before, after = item["before_text"], item["after_text"]
        if not after.startswith(before):
            raise ValueError("The candidate is not the recorded exact suffix addition")
        additions.append(
            {
                "snapshot_ref": record["snapshot_ref"],
                "path": item["path"],
                "before_sha256": digest(before.encode()),
                "after_sha256": digest(after.encode()),
                "suffix_offset_characters": len(before),
                "exact_generated_suffix": after[len(before) :],
                "scope": "Generated suffix only; the unchanged Django file is not bundled",
            }
        )
    if [item["snapshot_ref"] for item in additions] != refs:
        raise ValueError("Historical generated additions are incomplete")
    projections = []
    for record in trajectory["sessions"]["G"]["events"]:
        event = record["event"]
        if event["kind"] != "execution_completed":
            continue
        receipt = event["receipt"]
        if receipt["snapshot_ref"] not in refs:
            continue
        decision = record["value"]["state"]["public"]["decision"]
        projections.append(
            {
                "snapshot_ref": receipt["snapshot_ref"],
                "projection": receipt["projection"],
                "recorded_preservation_passes": sum(
                    observation["observed"] == "PASSED"
                    for observation in decision["observations"].values()
                ),
                "recorded_preservation_status": decision["preserve_status"],
                "issue_fixed": decision["issue_fixed"],
                "evidence_level": "RECORDED_ORIGINAL_EXECUTION_NOT_RERUN",
            }
        )
    if len(projections) != 2:
        raise ValueError("The recorded candidate projection pair is incomplete")
    return {
        "state": {
            "flags": original["flags"],
            "base_snapshot_ref": original["base_snapshot_ref"],
        },
        "pool": pool,
        "current_snapshot_ref": selection["terminal_capture_ref"],
        "original_selection": selection["p"]["selection"],
        "recorded_syntax_observation": {
            "snapshot_ref": refs[0],
            "query_id": identity["syntax_error_query"],
            "return_code": query["result"]["return_code"],
            "path": identity["modified_path"],
            "line": 418,
            "message": "SyntaxError: invalid syntax",
            "evidence_level": "RECORDED_PUBLIC_EXECUTION",
        },
        "candidate_additions": additions,
        "projection_receipts": projections,
    }


README = """# GP: bounded local selection replay

This directory is self-contained. With CPython 3.10 or later, run:

```sh
python3 -B replay.py
```

The default command reads only files next to this script and prints JSON. It
does not invoke a model, subprocess, network, container, benchmark or scorer.
`python3 -B replay.py replay --output replay_result.json` optionally writes a
new report. The separate `build` subcommand is provenance extraction from the
research checkout; it is not required for public replay.

`original_selection_slice.py` contains four exact functions from the recorded
P package: candidate filtering by comparable preservation receipts, minimum
failure ranking, nonempty RAW/PY keys, voting and first-occurrence tie-break.
The recorded keys and receipts enter at that function boundary. Normalization,
snapshot transport, G execution and the full agent host are not rerun.

The historical pair reproduces original selection and applies a NEW exclusion
of the candidate with an already recorded public SyntaxError. The later
candidate's whole-file syntax remains unassessed in this small bundle. A
separate syntax illustration parses each exact generated suffix under the
declared synthetic class wrapper; that does not execute or certify a full
Django file. The original preservation PASS and projected-tree equality are
recorded evidence, not new test results. No task is newly graded.

Four additional conditions are explicitly synthetic: legitimate test-only
edits, a safe projection, unknown syntax after a size limit, and abstention
when all candidates have confirmed syntax errors. Synthetic normalization keys
are direct inputs at the ranker boundary, not newly generated donor outputs.
The new hard exclusion rejects only confirmed syntax failures; unknown remains
eligible for soft ranking with an unassessed label. This is not a syntax
correctness certificate. No empty-pool fallback may bypass a confirmed error.

The proposed scope-by-syntax factorial was cancelled before execution: scope
metadata has no distinct consumer action, and a syntax-based scope rule would
duplicate the syntax exclusion. This replay does not establish extra value for
generic scope tracking, benchmark gain or predictive generalization.

The protocol fixes six conditions. All are retained whatever their outcomes.
Source provenance and the output schema distinguish original records, exact
source replay, a new local policy, and synthetic controls. See provenance.json,
protocol.json, and THIRD_PARTY.md. No full trajectory, hidden test, private
annotation, unreleased score or credential is bundled.
"""


def build(repo: Path, out: Path) -> dict:
    protocol_bytes = (repo / PROTOCOL_PATH).read_bytes()
    protocol = json.loads(protocol_bytes)
    if len(protocol["fixtures"]) != 6:
        raise ValueError("The protocol must contain exactly six conditions")
    if (out / "inputs.json").exists():
        raise FileExistsError("Existing GP inputs are preserved; use another output directory")
    source_info = protocol["source"]
    trajectory_bytes = (repo / source_info["trajectory"]).read_bytes()
    mechanism_bytes = (repo / source_info["mechanism"]).read_bytes()
    for data, expected in (
        (trajectory_bytes, source_info["trajectory_sha256"]),
        (mechanism_bytes, source_info["mechanism_sha256"]),
    ):
        if digest(data) != expected:
            raise ValueError("Frozen original source binding mismatch")
    slice_text, functions = source_slice(mechanism_bytes.decode(), source_info["source_functions"])
    historical = historical_inputs(json.loads(trajectory_bytes), protocol)
    inputs = {
        "schema_version": "agent2skill.principles.gp_inputs.v1",
        "historical": historical,
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "protocol.json").write_bytes(protocol_bytes)
    (out / "original_selection_slice.py").write_text(slice_text, encoding="utf-8")
    write_json(out / "inputs.json", inputs)
    (out / "replay.py").write_bytes(Path(__file__).read_bytes())
    (out / "AGENTLESS_LICENSE.txt").write_bytes((repo / source_info["donor_license"]).read_bytes())
    (out / "README.md").write_text(README, encoding="utf-8")
    (out / "THIRD_PARTY.md").write_text(
        "# Source and license notice\n\n"
        "The original generated P package is source-guided by Agentless at the "
        f"pinned revision `{source_info['donor_revision']}`. The donor MIT notice "
        "is retained in AGENTLESS_LICENSE.txt. The four selection functions "
        "are exact excerpts from the research-generated package, not an "
        "assertion that the whole package or this project is donor-licensed. "
        "The project-authored script, generated snippets and other research "
        "materials still require the authors' release-license declaration. "
        "This is a local review candidate, not a public release.\n\n"
        "The syntax snippets contain only the model-generated appended lines. "
        "No original Django implementation/test body is copied. They are "
        "wrapped in an explicitly synthetic class for parsing only.\n",
        encoding="utf-8",
    )
    provenance = {
        "schema_version": "agent2skill.principles.gp_provenance.v1",
        "build_kind": "EXTRACTION_ONLY_NO_FIXTURE_EXECUTION",
        "original_source": source_info,
        "exact_source_functions": functions,
        "bundle_files": {
            name: digest((out / name).read_bytes())
            for name in (
                "protocol.json",
                "inputs.json",
                "original_selection_slice.py",
                "replay.py",
                "AGENTLESS_LICENSE.txt",
            )
        },
        "implementation_fix_passes": 0,
        "observed_outcomes_known_before_design": True,
        "new_prospective_validation": False,
    }
    write_json(out / "provenance.json", provenance)
    return {"status": "BUNDLE_BUILT_NOT_EXECUTED", "output": str(out), "conditions": 6}


def syntax_status(code: str | None, limit: int) -> dict:
    if code is None:
        return {"label": "unassessed", "reason": "SOURCE_NOT_AVAILABLE_OR_TEXT_SIZE_LIMIT"}
    if len(code.encode()) > limit:
        return {"label": "unassessed", "reason": "TEXT_SIZE_LIMIT"}
    try:
        ast.parse(code)
    except SyntaxError as error:
        return {"label": "violated", "reason": "SyntaxError", "line": error.lineno}
    return {"label": "supported", "reason": "COMPLETE_SYNTHETIC_FILE_AST_PARSE"}


def synthetic_inputs(fixture: dict, limit: int) -> tuple[dict, list, str, list, dict]:
    pool, syntax, projections = [], [], []
    normal_values = []
    for index, candidate in enumerate(fixture["candidates"]):
        code = candidate["code"]
        syntax.append(syntax_status(code, limit))
        key = ("RAW:" if candidate["key_kind"] == "raw" else "PY:") + candidate["id"]
        pool.append(
            {
                "snapshot_ref": candidate["id"],
                "key": key,
                "key_kind": candidate["key_kind"],
                "fallback_reason": candidate["fallback_reason"],
                "ordinal": index + 1,
                "reproduced": None,
                "g_first": {"comparable": True, "failure_count": 0},
            }
        )
        if code is not None:
            files = dict(fixture["base_files"])
            files[candidate["path"]] = code
            files.update(candidate.get("extra_files", {}))
            projected = dict(files)
            for name in fixture["replace_from_base"]:
                projected[name] = fixture["base_files"][name]
            projections.append({"original_files": files, "projected_files": projected})
        if fixture["id"] == "synthetic_safe_projection":
            namespace = {"__builtins__": {}}
            exec(compile(code, "<synthetic runtime>", "exec"), namespace)
            normal_values.append(namespace["value"]())
    projection = {
        "kind": "DECLARED_SYNTHETIC_MAP_NOT_ORIGINAL_G_EXECUTION",
        "projected_equal": (
            projections[0]["projected_files"] == projections[1]["projected_files"]
            if len(projections) == 2
            else None
        ),
        "restored_files": fixture["replace_from_base"],
        "normal_value_results": normal_values,
    }
    state = {
        "base_snapshot_ref": "synthetic_base",
        "flags": {"regression": True, "reproduction": False},
    }
    return state, pool, pool[-1]["snapshot_ref"], syntax, projection


def replay(bundle: Path) -> dict:
    provenance = load_json(bundle / "provenance.json")
    for name, expected in provenance["bundle_files"].items():
        if digest((bundle / name).read_bytes()) != expected:
            raise ValueError(f"Bundle input binding mismatch: {name}")
    protocol = load_json(bundle / "protocol.json")
    inputs = load_json(bundle / "inputs.json")
    source_text = (bundle / "original_selection_slice.py").read_text()
    namespace = {}
    exec(compile(source_text, "<exact original selection slice>", "exec"), namespace)
    choose = namespace["_choose_submission_effect"]
    historical = inputs["historical"]
    fixtures = protocol["fixtures"]
    if len(fixtures) != protocol["max_fixture_conditions"]:
        raise ValueError("Fixture count changed")
    additions = [
        {
            "snapshot_ref": item["snapshot_ref"],
            "scope": protocol["policy"]["suffix_syntax_scope"],
            "syntax": syntax_status(
                protocol["policy"]["suffix_syntax_wrapper"] + item["exact_generated_suffix"],
                protocol["policy"]["max_syntax_bytes"],
            ),
        }
        for item in historical["candidate_additions"]
    ]
    results = []
    for fixture in fixtures:
        is_historical = fixture["kind"].startswith("historical")
        if is_historical:
            state = copy.deepcopy(historical["state"])
            pool = copy.deepcopy(historical["pool"])
            current = historical["current_snapshot_ref"]
            syntax = [
                {"label": "violated", "reason": "RECORDED_PUBLIC_QUERY_14_SYNTAX_ERROR"},
                {"label": "unassessed", "reason": "WHOLE_FILE_NOT_REEXECUTED_IN_BUNDLE"},
            ]
            projection = {
                "kind": "RECORDED_ORIGINAL_EXECUTION_NOT_RERUN",
                "projected_equal": len(
                    {
                        item["projection"]["projected_tree"]
                        for item in historical["projection_receipts"]
                    }
                )
                == 1,
                "preservation_pass_counts": [
                    item["recorded_preservation_passes"]
                    for item in historical["projection_receipts"]
                ],
            }
        else:
            state, pool, current, syntax, projection = synthetic_inputs(
                fixture, protocol["policy"]["max_syntax_bytes"]
            )
        rejected = []
        admitted = []
        for candidate, status in zip(pool, syntax, strict=True):
            if fixture["policy"] != "original" and status["label"] == "violated":
                rejected.append(candidate["snapshot_ref"])
            else:
                admitted.append(candidate)
        if rejected and not admitted:
            effect = {
                "snapshot_ref": None,
                "mode": "abstain",
                "reason": "ALL_CANDIDATES_HAVE_CONFIRMED_SYNTAX_ERROR",
            }
        else:
            effect = choose(state, admitted, current)
        abstain = effect["snapshot_ref"] is None or effect["mode"].startswith("abstain")
        checks = {
            "selection": effect["snapshot_ref"] == fixture["expected_selected"],
            "rejection": rejected == fixture["expected_rejected"],
            "abstention": abstain == fixture["expected_abstain"],
            "syntax_labels": [item["label"] for item in syntax] == fixture["expected_syntax"],
        }
        if "expected_projected_equal" in fixture:
            checks["projection"] = (
                projection["projected_equal"] == fixture["expected_projected_equal"]
            )
        if fixture["id"] == "historical_original":
            checks["exact_original_effect"] = effect == historical["original_selection"]
            checks["recorded_projection"] = projection["projected_equal"] and projection[
                "preservation_pass_counts"
            ] == [4, 4]
            checks["suffix_parse_only"] = [item["syntax"]["label"] for item in additions] == [
                "violated",
                "supported",
            ]
        if fixture["id"] == "synthetic_safe_projection":
            checks["declared_value_property"] = projection["normal_value_results"] == [1, 1]
        results.append(
            {
                "fixture_id": fixture["id"],
                "kind": fixture["kind"],
                "policy": fixture["policy"],
                "selected_snapshot": effect["snapshot_ref"],
                "effect": effect,
                "rejected_candidates": rejected,
                "abstained": abstain,
                "syntax": dict(zip([item["snapshot_ref"] for item in pool], syntax, strict=True)),
                "projection": projection,
                "checks": checks,
                "expectations_met": all(checks.values()),
                "historical_hard_syntax_guarantee": "not_applicable" if is_historical else None,
                "issue_repair": "unassessed",
                "official_outcome": None,
            }
        )
    normal = [row for row in results if row["kind"] == "synthetic_normal_control"]
    return {
        "schema_version": "agent2skill.principles.gp_replay_result.v1",
        "status": "COMPLETED"
        if all(row["expectations_met"] for row in results)
        else "COMPLETED_WITH_COUNTEREXAMPLE_OR_IMPLEMENTATION_FAILURE",
        "h1_factorial": protocol["h1_factorial"],
        "implementation_fix_passes": provenance["implementation_fix_passes"],
        "fixture_conditions": len(results),
        "expectations_met": sum(row["expectations_met"] for row in results),
        "normal_control_candidates_rejected": sum(
            len(row["rejected_candidates"]) for row in normal
        ),
        "normal_control_candidates": 4,
        "normal_control_conditions": len(normal),
        "all_bad_abstention": results[-1]["abstained"],
        "historical_pair": {
            "original_selection": results[0]["selected_snapshot"],
            "new_local_policy_selection": results[1]["selected_snapshot"],
            "selection_changed": results[0]["selected_snapshot"] != results[1]["selected_snapshot"],
            "benchmark_effect": "NOT_MEASURED",
        },
        "generated_suffix_syntax_illustration": additions,
        "conditions": results,
        "boundaries": protocol["global_invariants"],
        "protocol_sha256": provenance["bundle_files"]["protocol.json"],
        "source_slice_sha256": provenance["bundle_files"]["original_selection_slice.py"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command")
    builder = subparsers.add_parser("build")
    builder.add_argument("--repo-root", type=Path, required=True)
    builder.add_argument("--out", type=Path, required=True)
    runner = subparsers.add_parser("replay")
    runner.add_argument("--bundle", type=Path, default=Path(__file__).resolve().parent)
    runner.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.command == "build":
        value = build(args.repo_root.resolve(), args.out.resolve())
    else:
        bundle = args.bundle if args.command else Path(__file__).resolve().parent
        value = replay(bundle)
        if args.command and args.output:
            write_json(args.output, value)
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0 if value.get("status") in ("BUNDLE_BUILT_NOT_EXECUTED", "COMPLETED") else 1


if __name__ == "__main__":
    sys.exit(main())
