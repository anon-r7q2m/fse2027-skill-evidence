"""One fixed panel; failed HTTP paths remain missing without reopening transactions."""

import argparse
import asyncio
import fcntl
import os
from pathlib import Path
import tempfile

from analysis.automatic_extraction_v1.common import file_sha, parse_json, require, write_once
from analysis.aider_architect_comparison_v1.workflow import start_accounting as original_accounting
from analysis.editor_import_boundary_v1.host import rebound
from analysis.measurement_entry.process import process_identity, run_process
from analysis.measurement_entry.public import runtime_environment
from analysis.raw_repo_handoff_scored_v1 import workflow as original

from .allocation import read as read_allocation
from .constants import (
    CALLS,
    HOST_POLICY,
    LABEL,
    MAX_REQUESTS,
    PACKAGE,
    RESULTS,
    ROOT,
    SOLVER_COUNT,
    package_identities,
)
from .consumer import consume as consume_valid
from .host import Host, MiniHost, NaiveHost, qualified_packages
from .missing import consume as consume_missing
from .roles import role_policy
from .schedule import validate
from .selection import checked_rule

LAUNCH, LIVE = PACKAGE / "launch_manifest.json", RESULTS / "live"
STATUS = "FROZEN_16_TASK_CAPACITY_COMPARISON"


def freeze():
    from .scoring import checked_plan

    allocation, rule, plan = read_allocation(), checked_rule(), checked_plan()
    qualified_packages()
    checks = parse_json((RESULTS / "boundary_checks.json").read_bytes())
    entry = parse_json((RESULTS / "recorded_entry/terminal.json").read_bytes())
    require(
        checks["status"] == "PASS" and checks["model_requests"] == 0,
        "changed seams need zero-call checks",
    )
    require(
        entry["status"] == "RECORDED_CAPACITY_ENTRY_PASS"
        and entry["cleanup_confirmed"]
        and entry["real_model_requests"] == 0,
        "same production route must pass recorded entry",
    )
    schedule = parse_json((PACKAGE / "schedule.json").read_bytes())
    validate(schedule)
    bindings = dict(rule["method_bindings"])
    bindings.update(allocation["predecessor_bindings"])
    bindings.update(plan["sources"])
    paths = [
        *PACKAGE.glob("*.json"),
        PACKAGE / "DESIGN.md",
        *(PACKAGE / "runtime").glob("*.json"),
        *(PACKAGE / "screen").glob("*/*.json"),
        RESULTS / "boundary_checks.json",
        RESULTS / "recorded_entry/terminal.json",
        RESULTS / "input_preflight.json",
        RESULTS / "preparation/import_qualification.json",
        RESULTS / "preparation/import_preflight/terminal.json",
        RESULTS / "preparation/build_terminal.json",
        ROOT / "docs/reviews/raw_repo_capacity_implementation_20260922.md",
        ROOT / "tests/analysis/test_raw_repo_capacity_comparison_v1.py",
    ]
    bindings.update({str(p.relative_to(ROOT)): file_sha(p) for p in paths if p != LAUNCH})
    value = {
        "status": STATUS,
        "host_policy": HOST_POLICY,
        "exposure": LABEL,
        "historical_starts": allocation["historical_starts"],
        "benchmark_cap": allocation["benchmark_cap"],
        "max_solver_starts": SOLVER_COUNT,
        "max_scorer_starts": SOLVER_COUNT,
        "max_new_model_requests": MAX_REQUESTS,
        "packages": package_identities(),
        "policy_sha256": file_sha(PACKAGE / "policy.json"),
        "schedule_sha256": file_sha(PACKAGE / "schedule.json"),
        "bindings": bindings,
        "automatic_retries": 0,
        "old_solver_endpoints_reused": False,
    }
    write_once(LAUNCH, value)
    return {"status": STATUS, "sha256": file_sha(LAUNCH), "bindings": len(bindings)}


def inspect():
    manifest = parse_json(LAUNCH.read_bytes())
    allocation = read_allocation()
    policy = parse_json((PACKAGE / "policy.json").read_bytes())
    schedule = parse_json((PACKAGE / "schedule.json").read_bytes())
    require(
        manifest["status"] == STATUS
        and manifest["host_policy"] == HOST_POLICY
        and manifest["policy_sha256"] == file_sha(PACKAGE / "policy.json")
        and manifest["schedule_sha256"] == file_sha(PACKAGE / "schedule.json")
        and manifest["packages"] == package_identities()
        and manifest["max_solver_starts"] == manifest["max_scorer_starts"] == SOLVER_COUNT
        and manifest["max_new_model_requests"] == MAX_REQUESTS
        and manifest["historical_starts"] == allocation["historical_starts"]
        and manifest["benchmark_cap"] == allocation["benchmark_cap"]
        and manifest["old_solver_endpoints_reused"] is False
        and policy["calls_per_start"] == CALLS
        and policy["execution_scope"] == "REAL_GROUNDED",
        "frozen panel identity changed",
    )
    validate(schedule)
    for name, sha in manifest["bindings"].items():
        path = ROOT / name
        require(
            not Path(name).is_absolute()
            and ".." not in Path(name).parts
            and ".env" not in path.name
            and not path.is_symlink()
            and not {"hidden", "evaluator_only", "_evaluation_private"}.intersection(path.parts)
            and file_sha(path) == sha,
            "frozen input changed: " + name,
        )
    return manifest, policy, schedule


def reviewed():
    value = parse_json((PACKAGE / "launch_review.json").read_bytes())
    require(
        value["status"] == "GO_RAW_CAPACITY_COMPARISON_V1_LIVE"
        and value["launch_manifest_sha256"] == file_sha(LAUNCH),
        "specific launch review required",
    )


class Permit(original.Permit):
    verify = rebound(original.Permit.verify, {})


run_host = rebound(original.run_host, {"qualified_packages": qualified_packages})
child = rebound(original.child, {})
_context = {
    "PACKAGE": PACKAGE,
    "RESULTS": RESULTS,
    "LIVE": LIVE,
    "LAUNCH": LAUNCH,
    "inspect": inspect,
    "reviewed": reviewed,
    "Permit": Permit,
    "Host": Host,
    "NaiveHost": NaiveHost,
    "MiniHost": MiniHost,
    "role_policy": role_policy,
    "run_host": run_host,
}
child.__globals__.update(_context)
Permit.verify.__globals__.update(_context)


def start_accounting(slots, root=None, historical=None):
    return original_accounting(
        slots,
        root=LIVE if root is None else root,
        historical=read_allocation()["historical_starts"] if historical is None else historical,
    )


def consume(slot, process):
    root = LIVE / slot["cell_id"]
    if process.get("return_code") == 0:
        row = consume_valid(slot, process)
    else:
        row = consume_missing(
            root, slot, process, parse_json((PACKAGE / "policy.json").read_bytes())
        )
    write_once(root / "consumed.json", row)
    return row


def advance(rows, slot, process):
    row = consume(slot, process)
    require(
        row["status"] in {"PREFIX_VALID", "MISSING_CAPTURED_HTTP_TERMINAL"}, "unknown disposition"
    )
    rows.append(row)
    return row


def launch(scope):
    require(Path(scope).resolve() == LAUNCH, "fixed launch only")
    _, _, schedule = inspect()
    reviewed()
    from analysis.grounded_transfer_v1.ledger import GLOBAL_LEDGER

    with (GLOBAL_LEDGER.parent / "study.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        write_once(
            LIVE / "started.json",
            {"manifest_sha256": file_sha(LAUNCH), "parent": process_identity(os.getpid())},
        )
        rows, failure = [], None
        try:
            for slot in schedule["slots"]:
                root = LIVE / slot["cell_id"]
                write_once(
                    root / "launch.json",
                    {
                        "manifest_sha256": file_sha(LAUNCH),
                        "parent": process_identity(os.getpid()),
                        "slot": slot,
                    },
                )
                with tempfile.TemporaryDirectory(prefix="a2s-capacity-panel-") as config:
                    process = run_process(
                        [
                            str(ROOT / ".venv/bin/python"),
                            "-B",
                            "-m",
                            __package__ + ".workflow",
                            "child",
                            slot["cell_id"],
                        ],
                        cell=root / "process",
                        cwd=ROOT,
                        env=runtime_environment(config),
                        timeout=2400,
                    )
                row = advance(rows, slot, process)
                print(slot["cell_id"] + " " + row["status"], flush=True)
            require(len(rows) == SOLVER_COUNT, "all fixed path dispositions required")
        except BaseException as exc:
            failure = type(exc).__name__
            raise
        finally:
            write_once(
                LIVE / "all_terminal.json",
                {
                    "status": "ALL_192_SOLVER_DISPOSITIONS_CLOSED"
                    if failure is None
                    else "SOLVER_PHASE_STOPPED",
                    "failure_type": failure,
                    "completed": rows,
                    "starts": start_accounting(schedule["slots"]),
                    "new_model_requests": sum(r["requests"] for r in rows),
                    "unknown_usage_requests": sum(
                        r["usage"]["unknown_usage_requests"] for r in rows
                    ),
                    "request_count_scope": "ALL_CLOSED_VALID_AND_MISSING_PATHS; UNCLASSIFIED_FAILED_USAGE_PRESERVED",
                    "not_started": [
                        s["cell_id"]
                        for s in schedule["slots"]
                        if not (LIVE / s["cell_id"] / "launch.json").exists()
                    ],
                    "scores_released": False,
                    "retry_allowed": False,
                },
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("freeze", "inspect", "launch", "child"))
    parser.add_argument("scope", nargs="?")
    args = parser.parse_args()
    if args.mode == "launch":
        launch(args.scope)
    elif args.mode == "child":
        asyncio.run(child(args.scope))
    elif args.mode == "inspect":
        value, _, schedule = inspect()
        print({"status": value["status"], "paths": len(schedule["slots"])})
    else:
        print(freeze())
