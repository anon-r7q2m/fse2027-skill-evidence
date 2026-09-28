"""Scored boundary over the frozen raw host methods and exact accepted packages."""

import asyncio
import copy
from pathlib import Path
import time

from analysis.aider_architect_entry_v1.bridge import combine_accounts
from analysis.automatic_extraction_v1.common import file_sha, parse_json, require, write_once
from analysis.gr_generated_effect_v1.capture import BUNDLE_FILES, validate_bundle
from analysis.localization_only_v1.adapter import Locator
from analysis.localization_issue_boundary_v1.boundary import validate_package
from analysis.raw_repo_localization_v1.host import Host as OriginalHost

from .constants import L_PATH, L_SHA, P_PATH, P_SHA, QUALIFICATION


def qualified_packages():
    from analysis.localization_only_v1.isolation import Program as LocatorProgram
    from analysis.same_base_selection_v2.isolation import Program as PoolProgram

    acceptance = parse_json((QUALIFICATION / "independent_acceptance.json").read_bytes())
    entry = parse_json((QUALIFICATION / "generated_entry/terminal.json").read_bytes())
    final = parse_json((QUALIFICATION / "generation/all_final_seal.json").read_bytes())["finals"][
        "direct"
    ]
    exited = parse_json((QUALIFICATION / "supervision/launcher_exited.json").read_bytes())
    require(
        acceptance["status"] == "INDEPENDENT_PASS"
        and acceptance["package_sha256"] == L_SHA
        and acceptance["passed"] == acceptance["cases"] == 8
        and acceptance["cleanup_confirmed"] is True
        and final["status"] == "FINAL_PACKAGE_SEALED"
        and acceptance["namespace"] == "localization_issue_boundary_v1"
        and acceptance["old_claim_reused"] is False
        and acceptance["old_hidden_suite_executed"] is False
        and final["public_status"] == "PUBLIC_BOUNDARY_PASS"
        and final["package_sha256"] == L_SHA
        and final["human_candidate_code_repairs"] == 0
        and exited["return_code"] == 0,
        "new issue-boundary repair and independent acceptance required",
    )
    require(
        entry["status"] == "LONG_ISSUE_ACTUAL_ENTRY_PASS"
        and entry["cleanup_confirmed"] is True
        and entry["parent_wait_return_code"] == 0
        and len(entry["entries"]) == 2
        and {r["arm"] for r in entry["entries"]} == {"L", "LP"}
        and all(
            r["package_sha256"] == L_SHA and r["cleanup_confirmed"] and r["issue_utf8_bytes"] > 256
            for r in entry["entries"]
        ),
        "same-package L and LP actual entries required",
    )
    require(
        LocatorProgram(L_PATH).identity == L_SHA and PoolProgram(P_PATH).identity == P_SHA,
        "qualified package bytes changed",
    )
    require(
        validate_package(L_PATH) == final["ast_boundary"] == acceptance["ast_boundary"],
        "unchanged localization implementation outside issue validation required",
    )
    return {"L": L_SHA, "P": P_SHA}


class Host(OriginalHost):
    async def run(self, arm, *, client_factory, program=None, locator=None):
        require(not self.started and arm in {"N", "P", "L", "LP"}, "new raw repository run")
        require((arm in {"P", "LP"}) == (program is not None), "P only for pool arms")
        require(not program or program.identity == P_SHA, "unchanged original P package required")
        require((arm in {"L", "LP"}) == (locator is not None), "locator only for L arms")
        require(self.config.get("scope") == "REAL_RAW_REPOSITORY_COMPARISON", "real scope required")
        qualified_packages()
        require(
            locator is None or isinstance(locator, Locator) and locator.program.identity == L_SHA,
            "only the exact qualified localization package may enter the scored path",
        )
        self.started, self.client_factory = True, client_factory
        output = failure = None
        started = time.monotonic()
        try:
            await asyncio.wait_for(self.setup(arm), timeout=300)
            repository = await self.localize(arm, locator) if arm != "N" else None
            snapshot, policy, terminal = (
                await self.pool(repository, program) if program else await self.native()
            )
            self.budget.require_known()
            total = combine_accounts(
                {name: client.snapshot() for name, client in self.clients.items()}
            )
            require(total["requests"] == self.budget.used(), "all actual requests must be bound")
            folder = Path(snapshot["directory"])
            require(
                validate_bundle(folder, self.config["base_commit"]) == snapshot["bundle"]
                and snapshot["snapshot_ref"] == policy["selection"]["snapshot_ref"],
                "original selected capture differs",
            )
            policy["publication"] = {
                **snapshot["bundle"],
                "original_capture": str(folder),
                "original_bundle_hashes": {name: file_sha(folder / name) for name in BUNDLE_FILES},
                "run_id": self.config["run_id"],
                "recapture": False,
            }
            output = {
                "status": "PREFIX_ENDPOINTS_FROZEN",
                "prefix": arm,
                "terminal_status": terminal,
                "policies": {arm: policy},
                **total,
                "budget": self.budget.snapshot(),
                "discovery": self.discovery,
                "official_scores": None,
            }
            self.budget.check("before_endpoint_write")
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
            workers = copy.deepcopy(program.records) if program else []
            if locator is not None and hasattr(locator, "program"):
                workers.extend(copy.deepcopy(locator.program.records))
            if any(row.get("cleanup_confirmed") is not True for row in workers):
                errors.append("WORKER_CLEANUP_UNCONFIRMED")
            self.cleanup = {
                "cleanup_confirmed": not errors,
                "errors": errors,
                "environments": [environment.record for environment in self.environments],
                "workers": workers,
            }
            write_once(self.logs / "cleanup.json", self.cleanup)
            write_once(
                self.logs / "trajectory.json",
                {
                    "failure_type": failure,
                    "terminal_status": output["terminal_status"]
                    if output
                    else "EXECUTION_INCOMPLETE",
                    "score_eligibility": self.score_eligibility,
                    "loop": self.loop_result,
                    "delivery": self.broker.delivery.snapshot() if self.broker else None,
                    "host_failures": self.broker.host_failures if self.broker else [],
                    "clients": {name: c.snapshot() for name, c in self.clients.items()},
                    "controllers": {name: c.snapshot() for name, c in self.controls.items()},
                    "sampling": self.sampling.snapshot() if self.sampling else None,
                    "budget": self.budget.snapshot() if self.budget else None,
                    "elapsed_seconds": time.monotonic() - started,
                    "official_scores": None,
                },
            )
            if errors:
                raise RuntimeError("RAW_REPOSITORY_CLEANUP_UNCONFIRMED") from None
        return output
