"""Complete pinned mini with the raw host's input and absolute resource limits."""

import asyncio
import copy
from pathlib import Path
import time

from analysis.automatic_extraction_v1.common import digest, file_sha, require, write_once
from analysis.gr_generated_effect_v1.capture import (
    BUNDLE_FILES,
    capture_runtime,
    strict_final_capture,
    validate_bundle,
)
from analysis.mini_swe_capped_v1.adapter import require_execution_eligible
from analysis.mini_swe_capped_v1.bridge import (
    AdmissionClock,
    REMOTE_WORKER,
    TimeExceeded,
    run_complete_mini,
    stop_message,
)
from analysis.mini_swe_capped_v1.configuration import capped_configuration
from analysis.mini_swe_capped_v1 import process_boundary
from analysis.mini_swe_capped_v1.runtime import runtime_identity
from analysis.source_first_selection_v2.host import Host as WorkspaceHost

ROOT = Path(__file__).resolve().parents[2]
CALLS, SOLVE_SECONDS, FINALIZATION_SECONDS = 9, 1500, 300


def raw_configuration(policy):
    require(
        policy["calls_per_start"] == CALLS
        and policy["request_timeout_seconds"] == 300
        and policy["input_token_limit"] == 65536
        and policy["output_token_limit"] == 8192,
        "common raw-repository limits required",
    )
    result = capped_configuration(policy)
    result["agent"]["wall_time_limit_seconds"] = SOLVE_SECONDS
    return result


class RawClock(AdmissionClock):
    """The bridge installs this check at the last pre-dispatch boundary too."""

    def __init__(self, policy, *, clock=time.monotonic):
        self.request_seconds = policy["request_timeout_seconds"]
        super().__init__(SOLVE_SECONDS, drain_seconds=FINALIZATION_SECONDS, clock=clock)

    def check(self, stage):
        super().check(stage)
        if stage in {"before_dispatch", "dispatch_admitted"}:
            if self.clock() + self.request_seconds > self.end:
                self.events.append(
                    {"stage": stage, "reason": "FULL_REQUEST_TIMEOUT_UNAVAILABLE", "overrun": 0}
                )
                raise TimeExceeded(stop_message("ADMISSION_TIME_LIMIT"))

    def final_remaining(self):
        remaining = self.drain_end - self.clock()
        require(remaining > 0, "common model-free finalization deadline exhausted")
        return remaining


async def execute_raw_mini(issue, environment, client, logs, *, interpreter, clock=None):
    require(type(issue) is str and bool(issue.strip()), "original public issue required")
    config = raw_configuration(client.policy)
    clock = clock or RawClock(client.policy)
    result = await run_complete_mini(
        issue,
        environment,
        client,
        config,
        logs,
        seconds=SOLVE_SECONDS,
        clock=clock,
        interpreter=interpreter,
    )
    eligibility = require_execution_eligible(logs, client)
    return result, eligibility, clock


class MiniHost(WorkspaceHost):
    """One owned raw-repository path, complete native loop, original final tree."""

    def __init__(self, *, config, **kwargs):
        super().__init__(identities={}, **kwargs)
        self.config = copy.deepcopy(config)
        self.client = self.clock = self.solver = self.runtime = None

    async def setup(self):
        self.solver = self.factory(self.logs / "environment", "raw-mini")
        await self.solver.start(force_build=False)
        self.runtime = await capture_runtime(self.solver, file_sha(self.capture_script))
        result = await self.solver.exec(
            "git rev-parse HEAD HEAD^{tree}", cwd="/testbed", timeout_sec=15
        )
        require(
            result.return_code == 0
            and result.stdout.splitlines()
            == [self.config["base_commit"], self.config["base_tree"]],
            "mini must start at the shared pinned repository",
        )
        clean = await self.solver.exec("git status --porcelain", cwd="/testbed", timeout_sec=15)
        require(
            clean.return_code == 0 and not (clean.stdout or "").strip(),
            "mini clean base required",
        )
        await self.solver.upload_file(
            ROOT / "analysis/mini_swe_capped_v1/command_worker.py", REMOTE_WORKER
        )
        self.processes = await process_boundary.baseline(
            self.solver, self.runtime["executable"], self.logs
        )

    async def run(self, *, client):
        require(not self.started, "complete mini path cannot restart")
        require(not client.records and client.pending is None, "fresh mini account required")
        require(
            self.config["scope"] in {"REAL_RAW_REPOSITORY_COMPARISON", "PUBLIC_SCRIPTED_CONTROL"},
            "explicit raw-repository scope required",
        )
        configuration = raw_configuration(client.policy)
        self.started, self.client = True, client
        output = failure = None
        started = time.monotonic()
        try:
            await asyncio.wait_for(self.setup(), timeout=300)
            self.clock = RawClock(client.policy)
            write_once(
                self.logs / "installation.json",
                {
                    "runtime": runtime_identity(),
                    "configuration": configuration,
                    "raw_issue_sha256": digest(self.config["issue"]),
                    "human_task_card": False,
                    "solve_end": self.clock.end,
                    "total_end": self.clock.drain_end,
                    "request_policy": client.policy,
                    "base_commit": self.config["base_commit"],
                    "base_tree": self.config["base_tree"],
                },
            )
            result, eligibility, _ = await execute_raw_mini(
                self.config["issue"],
                self.solver,
                client,
                self.logs,
                interpreter=self.runtime["executable"],
                clock=self.clock,
            )
            await asyncio.wait_for(
                process_boundary.final_boundary(
                    self.solver, self.runtime["executable"], self.processes, self.logs
                ),
                timeout=self.clock.final_remaining(),
            )
            await strict_final_capture(
                self.solver,
                self.logs,
                base_commit=self.config["base_commit"],
                runtime=self.runtime,
                timeout_seconds=self.clock.final_remaining(),
            )
            folder = self.logs / "final_capture"
            bundle = validate_bundle(folder, self.config["base_commit"])
            self.clock.final_remaining()
            output = {
                "status": "PREFIX_ENDPOINTS_FROZEN",
                "prefix": "Hmini",
                "terminal_status": result["exit_status"],
                "policies": {
                    "Hmini": {
                        "status": "COMPLETE_MINI_FINAL_WORKTREE",
                        "selection": {"snapshot_ref": bundle["final_tree"]},
                        "publication": {
                            **bundle,
                            "original_capture": str(folder),
                            "original_bundle_hashes": {
                                name: file_sha(folder / name) for name in BUNDLE_FILES
                            },
                            "run_id": self.config["run_id"],
                            "recapture": False,
                        },
                    }
                },
                "requests": len(client.records),
                "usage": copy.deepcopy(client.usage),
                "score_eligibility": eligibility,
                "official_scores": None,
            }
            write_once(self.logs / "endpoints.json", output)
        except BaseException as exc:
            failure = type(exc).__name__
            raise
        finally:
            errors = []
            for environment in reversed(self.environments):
                try:
                    await asyncio.wait_for(environment.stop(delete=True), timeout=120)
                except BaseException as exc:
                    errors.append(type(exc).__name__)
            write_once(
                self.logs / "cleanup.json",
                {
                    "cleanup_confirmed": not errors,
                    "errors": errors,
                    "workers": [],
                    "environments": [environment.record for environment in self.environments],
                },
            )
            write_once(
                self.logs / "trajectory.json",
                {
                    "failure_type": failure,
                    "native": client.snapshot(),
                    "terminal_status": output["terminal_status"]
                    if output
                    else "EXECUTION_INCOMPLETE",
                    "elapsed_seconds": time.monotonic() - started,
                    "official_scores": None,
                },
            )
            if errors:
                raise RuntimeError("RAW_MINI_CLEANUP_UNCONFIRMED") from None
        return output
