"""One original thirty-two-path execution with shared budgets and no score exposure."""

import argparse
import asyncio
import copy
from dataclasses import dataclass
import fcntl
import os
from pathlib import Path
import tempfile

from analysis.automatic_extraction_v1.common import file_sha, parse_json, require, write_once
from analysis.aider_architect_comparison_v1.workflow import start_accounting as original_accounting
from analysis.measurement_entry.process import check_process, process_identity, run_process
from analysis.measurement_entry.public import runtime_environment
from analysis.reproduction_regression_v1.environment_witness import setup_environment
from analysis.raw_repo_localization_prospective_v1.workflow import validate_accounts

from .constants import (
    CALLS,
    CAP,
    HISTORICAL,
    L_PATH,
    LN_PATH,
    LABEL,
    P_PATH,
    PN_PATH,
    GENERATION_PACKAGE,
    PACKAGE,
    POLICIES,
    PREDECESSOR,
    PREVIOUS_RESULTS,
    QUALIFICATION,
    RESULTS,
    ROOT,
    package_identities,
)
from .host import Host, NaiveHost, MiniHost, qualified_packages
from .dispatch import client_type
from .inputs import validate_schedule
from .selection import predecessor_closed

LAUNCH = PACKAGE / "launch_manifest.json"
LIVE = RESULTS / "live"
STATUS = "FROZEN_FOUR_TASK_HANDOFF_EIGHT_ARM"


def allocate():
    predecessor_closed()
    qualified_packages()
    close = parse_json((QUALIFICATION / "generation/allocation_close.json").read_bytes())
    require(
        close["requests_used"] + close["retired_slots_after_close"] == 411
        and close["cumulative_cap"] == 411
        and close["unallocated_requests"] == 0,
        "repair allocation must be closed",
    )
    value = {
        "status": "FINITE_EIGHT_ARM_RAW_COMPARATOR_ALLOCATION",
        "historical_starts": HISTORICAL,
        "new_start_allowance": 64,
        "max_solver_starts": 32,
        "max_scorer_starts": 32,
        "max_new_model_requests": 288,
        "benchmark_cap": CAP,
        "previous_cap": 764,
        "cap_increase": 46,
        "automatic_retries": 0,
        "authorization": "PERSISTENT_USER_CONTINUE_AND_FINITE_INCREASE_AUTHORIZATION",
        "prior_completion_sha256": file_sha(PREVIOUS_RESULTS / "completion_summary.json"),
        "extraction": {
            "used": close["requests_used"],
            "retired": close["retired_slots_after_close"],
            "cap": 411,
            "new_requests": 0,
        },
        "exposure": LABEL,
        "old_solver_endpoints_reused": False,
    }
    write_once(PACKAGE / "allocation.json", value)
    return value


def freeze():
    from .scoring import checked_plan

    predecessor_closed()
    qualified_packages()
    allocation = parse_json((PACKAGE / "allocation.json").read_bytes())
    schedule = parse_json((PACKAGE / "schedule.json").read_bytes())
    validate_schedule(schedule)
    checks = parse_json((RESULTS / "boundary_checks.json").read_bytes())
    plan = checked_plan()
    require(
        allocation["historical_starts"] == HISTORICAL
        and allocation["new_start_allowance"] == 64
        and allocation["benchmark_cap"] == CAP
        and allocation["old_solver_endpoints_reused"] is False
        and checks["status"] == "PASS"
        and checks["model_requests"] == 0
        and plan["max_scorer_starts"] == 32,
        "finite successor allocation and seam checks required",
    )
    predecessor_manifest = PREDECESSOR / "launch_manifest.json"
    bindings = dict(parse_json(predecessor_manifest.read_bytes())["bindings"])
    for name, sha in bindings.items():
        require(file_sha(ROOT / name) == sha, "frozen predecessor bytes changed: " + name)
    generation = parse_json((GENERATION_PACKAGE / "generation_manifest.json").read_bytes())
    for name, sha in generation["bindings"].items():
        require(name not in bindings or bindings[name] == sha, "inconsistent shared dependency")
        bindings[name] = sha
    paths = [
        predecessor_manifest,
        PREVIOUS_RESULTS / "completion_summary.json",
        PREVIOUS_RESULTS / "live/all_terminal.json",
        PREVIOUS_RESULTS / "scores/all_terminal.json",
        PREVIOUS_RESULTS / "scores/reconciliation.json",
        PREVIOUS_RESULTS / "scores/supervision/launcher_exited.json",
        PREVIOUS_RESULTS / "supervision/launcher_exited.json",
        *PACKAGE.glob("*.json"),
        PACKAGE / "DESIGN.md",
        *(PACKAGE / "runtime").glob("*.json"),
        RESULTS / "boundary_checks.json",
        RESULTS / "recorded_entry/terminal.json",
        RESULTS / "input_preflight.json",
        RESULTS / "preparation/import_qualification.json",
        RESULTS / "preparation/import_preflight/terminal.json",
        RESULTS / "preparation/scope.json",
        RESULTS / "preparation/build_terminal.json",
        *(PACKAGE / "screen").glob("*/*.json"),
        *(RESULTS / "preparation/import_preflight").glob("*/identity.json"),
        QUALIFICATION / "acceptance_attestation.json",
        QUALIFICATION / "independent_acceptance.json",
        QUALIFICATION / "generated_entry/terminal.json",
        QUALIFICATION / "generation/all_final_seal.json",
        QUALIFICATION / "generation/allocation_close.json",
        QUALIFICATION / "generation_supervision/launcher_exited.json",
        QUALIFICATION / "generated_entry/using_provided.json",
        QUALIFICATION / "public_mini_entry/terminal.json",
        GENERATION_PACKAGE / "generation_manifest.json",
        GENERATION_PACKAGE / "generation_review.json",
        ROOT / "docs/reviews/raw_repo_handoff_scored_v1_design_20260921.md",
        ROOT / "docs/reviews/raw_repo_handoff_scored_v1_implementation_20260921.md",
        ROOT / "tests/analysis/test_raw_repo_handoff_scored_v1.py",
    ]
    for namespace in ("raw_repo_handoff_scored_v1", "raw_repo_discovery_handoff_v1"):
        paths.extend((ROOT / "analysis" / namespace).glob("*.py"))
    for folder in (L_PATH, P_PATH, LN_PATH, PN_PATH):
        paths.extend(p for p in folder.iterdir() if p.is_file())
    paths.extend(ROOT / name for name in plan["sources"])
    bindings.update({str(p.relative_to(ROOT)): file_sha(p) for p in paths if p != LAUNCH})
    value = {
        "status": STATUS,
        "historical_starts": HISTORICAL,
        "benchmark_cap": CAP,
        "max_solver_starts": 32,
        "max_scorer_starts": 32,
        "max_new_model_requests": 288,
        "policy_sha256": file_sha(PACKAGE / "policy.json"),
        "schedule_sha256": file_sha(PACKAGE / "schedule.json"),
        "packages": package_identities(),
        "bindings": bindings,
        "automatic_retries": 0,
        "exposure": LABEL,
        "old_solver_endpoints_reused": False,
        "closed_extraction_allocation": parse_json(
            (QUALIFICATION / "generation/allocation_close.json").read_bytes()
        ),
    }
    write_once(LAUNCH, value)
    return {"status": STATUS, "sha256": file_sha(LAUNCH), "bindings": len(bindings)}


def inspect():
    manifest = parse_json(LAUNCH.read_bytes())
    policy = parse_json((PACKAGE / "policy.json").read_bytes())
    schedule = parse_json((PACKAGE / "schedule.json").read_bytes())
    require(
        manifest["status"] == STATUS
        and manifest["policy_sha256"] == file_sha(PACKAGE / "policy.json")
        and manifest["schedule_sha256"] == file_sha(PACKAGE / "schedule.json")
        and manifest["packages"] == package_identities()
        and manifest["max_new_model_requests"] == 288
        and manifest["historical_starts"] == HISTORICAL
        and manifest["benchmark_cap"] == CAP
        and manifest["exposure"] == LABEL
        and manifest["old_solver_endpoints_reused"] is False
        and policy["calls_per_start"] == CALLS
        and policy["execution_scope"] == "REAL_GROUNDED",
        "frozen allocation changed",
    )
    predecessor_closed()
    validate_schedule(schedule)
    for name, sha in manifest["bindings"].items():
        path = ROOT / name
        require(
            not name.startswith("/")
            and ".." not in Path(name).parts
            and ".env" not in path.name
            and not {"hidden", "evaluator_only", "_evaluation_private"}.intersection(path.parts)
            and not path.is_symlink()
            and file_sha(path) == sha,
            "frozen input changed: " + name,
        )
    return manifest, policy, schedule


def reviewed():
    value = parse_json((PACKAGE / "launch_review.json").read_bytes())
    require(
        value["status"] == "GO_RAW_HANDOFF_SCORED_V1_LIVE"
        and value["launch_manifest_sha256"] == file_sha(LAUNCH),
        "specific live review required",
    )


def start_accounting(slots, root=LIVE, historical=HISTORICAL):
    return original_accounting(slots, root=root, historical=historical)


def allowed_roles(prefix):
    samples = {f"sample{i}" for i in range(1, 5)}
    return {
        "N": {"native"},
        "L": {"localization", "native"},
        "P": {"discovery", *samples},
        "LP": {"localization", *samples},
        "Ln": {"localization", "native"},
        "Pn": {"discovery", *samples},
        "LnPn": {"localization", *samples},
        "Hmini": {"mini"},
    }[prefix]


def role_policy(policy, prefix, role, calls):
    require(role in allowed_roles(prefix), "unassigned stage")
    if role in {"discovery", "localization"}:
        require(calls == 5, "fixed discovery ceiling")
    elif role.startswith("sample"):
        require(calls == 1, "one request per original sample")
    elif role == "mini":
        require(calls == CALLS, "complete mini shared allowance")
    else:
        require(
            calls == 9 if prefix == "N" else 4 <= calls <= 9,
            "native receives remaining shared calls",
        )
    return {**copy.deepcopy(policy), "calls_per_start": calls}


@dataclass(frozen=True)
class Permit:
    manifest_sha256: str
    slot: dict
    process: dict
    role: str
    calls: int

    def verify(self, policy):
        require(file_sha(LAUNCH) == self.manifest_sha256, "launch identity changed")
        _, common, schedule = inspect()
        reviewed()
        require(
            policy == role_policy(common, self.slot["prefix"], self.role, self.calls)
            and self.slot in schedule["slots"]
            and process_identity(os.getpid()) == self.process
            and not (LIVE / "all_terminal.json").exists(),
            "immutable stage permit changed",
        )
        root = LIVE / self.slot["cell_id"]
        require(
            parse_json((root / "child_begin.json").read_bytes())["process"] == self.process
            and not (root / "child_finished.json").exists(),
            "original stage no longer active",
        )
        created = parse_json((root / "stages" / (self.role + ".json")).read_bytes())
        require(
            created["policy"] == policy
            and created["role"] == self.role
            and created["calls"] == self.calls,
            "creation-time policy differs",
        )


async def run_host(host, prefix, client_factory, program, locator):
    if prefix == "Hmini":
        return await host.run(client=client_factory("mini", CALLS))
    kwargs = {"client_factory": client_factory, "program": program, "locator": locator}
    if prefix in {"Ln", "Pn", "LnPn"}:
        kwargs["qualification"] = qualified_packages
    return await host.run(prefix, **kwargs)


async def child(cell_id):
    os.umask(0o022)
    setup_environment()
    _, policy, schedule = inspect()
    reviewed()
    matches = [s for s in schedule["slots"] if s["cell_id"] == cell_id]
    require(len(matches) == 1, "unallocated path")
    slot, root = matches[0], LIVE / cell_id
    launch = parse_json((root / "launch.json").read_bytes())
    require(
        launch["manifest_sha256"] == file_sha(LAUNCH)
        and launch["parent"] == process_identity(os.getppid()),
        "original path parent required",
    )
    birth = process_identity(os.getpid())
    write_once(root / "child_begin.json", {"process": birth, "slot": slot})
    require(file_sha(slot["runtime"]) == slot["runtime_sha256"], "runtime changed")
    config = parse_json(Path(slot["runtime"]).read_bytes())
    prefix = slot["prefix"]
    config = {**config, "run_id": config["run_id"] + "-" + prefix}
    from analysis.localization_only_v1.adapter import Locator
    from analysis.localization_only_v1.isolation import Program as LocatorProgram
    from analysis.same_base_selection_v2.isolation import Program as PoolProgram
    from analysis.raw_repo_comparators_v1.isolation import Program as NaiveProgram
    from analysis.raw_repo_comparators_v1.locator import Locator as NaiveLocator
    from analysis.validated_selection_entry_v1.environment import environment_factory

    target = root / "entry/prefixes" / prefix
    factory, absent = environment_factory(
        target, **{k: config[k] for k in ("image", "base_commit", "base_tree", "capture_script")}
    )
    host_type = (
        MiniHost if prefix == "Hmini" else NaiveHost if prefix in {"Ln", "Pn", "LnPn"} else Host
    )
    host = host_type(
        logs=target,
        environment_factory=factory,
        cleanup_check=absent,
        capture_script=config["capture_script"],
        config=config,
    )
    program = (
        PoolProgram(P_PATH, records_dir=target / "P_workers") if prefix in {"P", "LP"} else None
    )
    locator_program = (
        LocatorProgram(L_PATH, records_dir=target / "L_workers") if prefix in {"L", "LP"} else None
    )
    locator = Locator(locator_program, target / "localization") if locator_program else None
    if prefix in {"Pn", "LnPn"}:
        program = NaiveProgram(PN_PATH, role="Pn", records_dir=target / "Pn_workers")
    if prefix in {"Ln", "LnPn"}:
        locator_program = NaiveProgram(LN_PATH, role="Ln", records_dir=target / "Ln_workers")
        locator = NaiveLocator(locator_program, target / "localization")
    clients, policies = {}, {}

    def client_factory(role, calls):
        require(role not in clients, "fresh stage only")
        if role != "mini":
            require(host.budget is not None, "native stages start after setup only")
        if role == "native":
            require(
                calls == CALLS - host.budget.used(), "native allowance must equal actual remainder"
            )
        actual = role_policy(policy, prefix, role, calls)
        policies[role] = actual
        write_once(
            root / "stages" / (role + ".json"),
            {
                "role": role,
                "calls": calls,
                "policy": actual,
                "requests_already_used": 0 if role == "mini" else host.budget.used(),
                "common_budget": None if role == "mini" else host.budget.snapshot(),
            },
        )
        cls = client_type(role)
        client = cls(
            actual, root / "requests" / role, Permit(file_sha(LAUNCH), slot, birth, role, calls)
        )
        clients[role] = client
        return client

    failure, output = None, None
    try:
        output = await run_host(host, prefix, client_factory, program, locator)
        discovery = getattr(host, "discovery", None) or {}
        write_once(
            root / "stage_observation.json",
            {
                "prefix": prefix,
                "submit_actions": sum(
                    action.get("name") == "submit_files" for action in discovery.get("actions", [])
                ),
                "nonempty_selected_files": bool(
                    discovery.get("selected_files") or discovery.get("localized_files")
                ),
                "source_view_status": (getattr(host, "view", None) or {}).get("status"),
                "editor_requests": sum(
                    len(client.records)
                    for name, client in clients.items()
                    if name.startswith("sample")
                ),
            },
        )
    except BaseException as exc:
        failure = type(exc).__name__
        raise
    finally:
        cleanup = getattr(host, "cleanup", None)
        if cleanup is None and (target / "cleanup.json").is_file():
            cleanup = parse_json((target / "cleanup.json").read_bytes())
        write_once(
            root / "usage.json",
            {
                "accounts": {name: c.snapshot() for name, c in clients.items()},
                "stage_policies": policies,
                "failure_type": failure,
                "cleanup_confirmed": bool(cleanup and cleanup["cleanup_confirmed"]),
                "actual_gateway_fee": "TBD",
            },
        )
    require(
        output["status"] == "PREFIX_ENDPOINTS_FROZEN" and cleanup["cleanup_confirmed"],
        "path incomplete",
    )
    write_once(
        root / "child_finished.json",
        {
            "status": "PREFIX_COMPLETE",
            "process": birth,
            "endpoints_sha256": file_sha(target / "endpoints.json"),
        },
    )


def consume(slot, process):
    root = LIVE / slot["cell_id"]
    birth = check_process((root / "process/process.json").read_bytes(), process)["process"]
    finished = parse_json((root / "child_finished.json").read_bytes())
    path = root / "entry/prefixes" / slot["prefix"]
    trajectory = parse_json((path / "trajectory.json").read_bytes())
    endpoints = parse_json((path / "endpoints.json").read_bytes())
    usage = parse_json((root / "usage.json").read_bytes())
    cleanup = parse_json((path / "cleanup.json").read_bytes())
    require(
        parse_json((root / "child_begin.json").read_bytes())["process"] == birth
        and finished["process"] == birth
        and finished["status"] == "PREFIX_COMPLETE"
        and finished["endpoints_sha256"] == file_sha(path / "endpoints.json")
        and trajectory["failure_type"] is None
        and usage["cleanup_confirmed"] is True
        and usage["failure_type"] is None
        and cleanup["cleanup_confirmed"] is True
        and all(r["cleanup_confirmed"] for r in cleanup["workers"] + cleanup["environments"])
        and set(endpoints["policies"]) == set(POLICIES[slot["prefix"]]),
        "original path evidence incomplete",
    )
    common = parse_json((PACKAGE / "policy.json").read_bytes())
    config = parse_json(Path(slot["runtime"]).read_bytes())
    config = {**config, "run_id": config["run_id"] + "-" + slot["prefix"]}
    if slot["prefix"] in {"Ln", "Pn", "LnPn"}:
        from analysis.raw_repo_comparators_v1.naive_consumer import consume as naive_consume

        identities = package_identities()
        names = {"Ln": ("Ln",), "Pn": ("Pn",), "LnPn": ("Ln", "Pn")}[slot["prefix"]]
        checked = naive_consume(
            path,
            arm=slot["prefix"],
            config=config,
            policy=common,
            request_root=root / "requests",
            expected_packages={name: identities[name] for name in names},
        )
        requests, totals = checked["requests"], checked["usage"]
        require(trajectory["clients"] == usage["accounts"], "naive request accounts differ")
    elif slot["prefix"] == "Hmini":
        from analysis.raw_repo_comparators_v1.mini_consumer import consume as mini_consume

        checked = mini_consume(
            path, config=config, policy=common, request_root=root / "requests/mini"
        )
        requests, totals = checked["requests"], checked["usage"]
        require(usage["accounts"] == {"mini": trajectory["native"]}, "mini request account differs")
    else:
        requests, totals = validate_accounts(
            slot["prefix"],
            usage["accounts"],
            usage["stage_policies"],
            trajectory,
            endpoints,
            common,
        )
        require(trajectory["clients"] == usage["accounts"], "host and request accounts differ")
    for name, account in usage["accounts"].items():
        for number, record in enumerate(account["records"], 1):
            commit = parse_json(
                (root / "requests" / name / f"request_{number:02d}/commit.json").read_bytes()
            )
            require(
                all(commit.get(k) == v for k, v in record.items()),
                "original committed ledger differs",
            )
        creation = parse_json((root / "stages" / (name + ".json")).read_bytes())
        require(
            creation["policy"]
            == usage["stage_policies"][name]
            == role_policy(common, slot["prefix"], name, creation["calls"]),
            "stage creation identity changed",
        )
    policy = endpoints["policies"][slot["prefix"]]
    require(
        policy["publication"]["run_id"] == config["run_id"]
        and policy["publication"]["base_commit"] == config["base_commit"],
        "per-arm original publication identity",
    )
    if policy["status"] == "DECLARED_PIPELINE_EMPTY_BASE":
        require(
            policy["publication"]["final_tree"] == config["base_tree"]
            and policy["publication"]["patch_bytes"] == 0,
            "actual base, not invented zero score, required",
        )
    write_once(
        root / "consumed.json",
        {
            "status": "PREFIX_VALID",
            "slot": slot,
            "endpoints_sha256": finished["endpoints_sha256"],
            "accounts": usage["accounts"],
            "process": process,
            "official_scores": None,
        },
    )
    return {
        "slot": slot,
        "endpoint_path": str(path / "endpoints.json"),
        "endpoint_sha256": finished["endpoints_sha256"],
        "requests": requests,
        "usage": totals,
    }


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
        completed, failure = [], None
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
                with tempfile.TemporaryDirectory(prefix="a2s-raw-prefix-") as config:
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
                completed.append(consume(slot, process))
                print(slot["cell_id"] + " PREFIX_VALID", flush=True)
            require(len(completed) == 32, "whole block required")
        except BaseException as exc:
            failure = type(exc).__name__
            raise
        finally:
            write_once(
                LIVE / "all_terminal.json",
                {
                    "status": "ALL_THIRTY_TWO_PREFIXES_VALID"
                    if failure is None
                    else "PREFIX_BLOCK_INVALID",
                    "failure_type": failure,
                    "completed": completed,
                    "starts": start_accounting(schedule["slots"]),
                    "new_model_requests": sum(r["requests"] for r in completed),
                    "request_count_scope": "VALID_PREFIXES_ONLY; ALL_USAGE_PRESERVED_PER_PREFIX",
                    "resource_status": "ALL_PREFIX_CLEANUP_CONFIRMED"
                    if failure is None
                    else "UNCONFIRMED_FOR_INCOMPLETE_PREFIX; SEE_OWNED_REGISTRATIONS",
                    "scores_released": False,
                    "retry_allowed": False,
                },
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("allocate", "freeze", "inspect", "launch", "child"))
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
        print(globals()[args.mode]())
