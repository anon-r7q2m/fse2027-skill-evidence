"""New naive paths alongside the unchanged L/P host; no implicit package eligibility."""

import asyncio
import copy
from pathlib import Path
import shlex
import time

from analysis.aider_architect_entry_v1.bridge import combine_accounts
from analysis.aider_architect_entry_v1.pool_host import accounts, declared_package_stop
from analysis.automatic_extraction_v1.common import file_sha, require, write_once
from analysis.g_migration_trial_v1.isolation import PackageError
from analysis.gr_generated_effect_v1.capture import BUNDLE_FILES, validate_bundle
from analysis.raw_repo_localization_v1.bridge import source_view
from analysis.raw_repo_localization_v1.budget import BudgetStop
from analysis.raw_repo_localization_v1.deadline import PoolDeadline
from analysis.raw_repo_localization_v1.host import Host as OriginalHost
from analysis.raw_repo_localization_v1.remote import RemoteRepository
from analysis.same_base_selection_v2.host import WORKSPACE_HELPER, WORKSPACE_SPEC
from analysis.search_replace_effect_v1.sampling import Samples, PoolResourceStop, controller

from .contracts import validate_begin
from .locator import Locator
from .session import PoolSession

ARM_ROLES = {"Ln": "L", "Pn": "P", "LnPn": "LP"}


class NaiveHost(OriginalHost):
    """Functional package effects feed the same repository and submission machinery."""

    async def localize(self, arm, locator):
        if arm == "Pn":
            return await super().localize("P", None)
        repository = None
        try:
            repository = await RemoteRepository.open(
                self.solver,
                self.config["base_commit"],
                self.runtime,
                self.logs / "repository",
                self.budget,
            )
            require(repository.base_tree == self.config["base_tree"], "original repository tree")
            self.discovery = await locator(
                repository,
                self.config["issue"],
                self.budget,
                self.client("localization", 5),
                self.config["run_id"],
            )
        except BudgetStop as exc:
            self.discovery = {
                "status": "DISCOVERY_BUDGET_STOP",
                "reason": str(exc),
                "selected_files": [],
                "localized_files": [],
                "locations": [],
            }
        self.budget.require_known()
        write_once(self.logs / "discovery.json", self.discovery)
        return repository

    async def pool(self, repository, program):
        self.deadline = PoolDeadline(self.budget)
        self.capture.clock_check = self.deadline.check
        self.controls = {f"sample{i}": controller(1) for i in range(1, 5)}
        clients = {name: self.client(name, 1) for name in self.controls}
        for name, client in clients.items():
            self.deadline.bind(name, client, self.controls[name])
        self.session = PoolSession(program, clock_check=self.deadline.check, logs=self.logs / "Pn")
        self.sampling = Samples(
            list(clients.values()), list(self.controls.values()), self.deadline.check
        )
        selection = reason = None
        try:
            if repository is None:
                require(self.discovery["status"] == "DISCOVERY_BUDGET_STOP", "known discovery stop")
                raise PoolResourceStop(self.discovery["status"])
            self.view = await asyncio.to_thread(
                source_view,
                repository,
                self.discovery.get("localized_files", self.discovery["selected_files"]),
                self.discovery["locations"],
            )
            if self.view["status"] != "SOURCE_VIEW_READY":
                raise PoolResourceStop(self.view["status"])
            begin = {
                "kind": "begin",
                "run_id": self.config["run_id"],
                "base_commit": self.view["base_commit"],
                "base_snapshot_ref": self.view["base_snapshot_ref"],
                "issue": self.config["issue"],
                "files": copy.deepcopy(self.view["files"]),
                "locations": copy.deepcopy(self.view["locations"]),
                "limits": {
                    key: clients["sample1"].policy[key]
                    for key in ("input_token_limit", "output_token_limit")
                },
            }
            validate_begin(begin, "Pn")
            write_once(self.logs / "begin.json", begin)
            await self.solver.upload_file(self.logs / "begin.json", WORKSPACE_SPEC)
            self.deadline.check("before_pool_workspace_check")
            checked = await self.solver.exec(
                shlex.join(
                    [
                        self.runtime["executable"],
                        "-B",
                        WORKSPACE_HELPER,
                        "/testbed",
                        WORKSPACE_SPEC,
                        "--check",
                    ]
                ),
                cwd="/testbed",
                timeout_sec=45,
            )
            write_once(
                self.logs / "pool_source_check.json",
                {
                    "return_code": checked.return_code,
                    "stdout": checked.stdout,
                    "stderr": checked.stderr,
                },
            )
            require(checked.return_code == 0, "original input bytes/modes differ")
            self.deadline.check("after_pool_workspace_check")
            selection = await self.session.run(
                begin,
                sample_request=self.sampling,
                materialize_capture=self._materialize,
            )
        except (BudgetStop, PoolResourceStop, PackageError) as exc:
            self.budget.require_known()
            accounts(clients, self.controls)
            reason = (
                declared_package_stop(exc, self.session, program)
                if isinstance(exc, PackageError)
                else str(exc)
            )
            if self.session.requests:
                self.sampling.close_unrequested(self.session.requests, reason)
            else:
                for index in range(1, 5):
                    self.sampling.record(index, None, "NOT_SENT_RESOURCE", reason)
        accounts(clients, self.controls)
        require(len(self.sampling.accounting) == 4, "all sample slots have actual dispositions")
        self.deadline.begin_finalization()
        await self.quiescent()
        choice = (
            {"mode": "empty_base", "sample_index": None, "snapshot_ref": self.config["base_tree"]}
            if reason
            else selection
        )
        snapshot = (
            self.base_snapshot
            if choice["sample_index"] is None
            else self.session.captures[choice["sample_index"]]
        )
        return (
            snapshot,
            {
                "status": "DECLARED_PIPELINE_EMPTY_BASE"
                if reason
                else "ORIGINAL_GENERATED_SELECTION",
                "selection": choice,
                "fallback_reason": reason,
                "pool_selection": selection,
            },
            "KNOWN_PIPELINE_STOP" if reason else "SELECTION_COMPLETE",
        )

    async def run(self, arm, *, client_factory, program=None, locator=None, qualification=None):
        require(not self.started and arm in ARM_ROLES, "fresh declared naive arm")
        require((arm in {"Pn", "LnPn"}) == (program is not None), "editor only for pool arms")
        require(program is None or program.role == "Pn", "whole naive editor required")
        require((arm in {"Ln", "LnPn"}) == (locator is not None), "locator only for locating arms")
        require(
            locator is None or isinstance(locator, Locator) and locator.program.role == "Ln",
            "whole naive locator required",
        )
        observed = {
            **({"Pn": program.identity} if program else {}),
            **({"Ln": locator.program.identity} if locator else {}),
        }
        if self.config["scope"] != "PUBLIC_SCRIPTED_CONTROL":
            require(
                self.config["scope"] == "REAL_RAW_REPOSITORY_COMPARISON"
                and callable(qualification),
                "independent acceptance and same-package entry required",
            )
            qualified = qualification()
            require(
                all(qualified.get(k) == v for k, v in observed.items()),
                "qualified package identities",
            )
        self.started, self.client_factory = True, client_factory
        output = failure = None
        started = time.monotonic()
        try:
            await asyncio.wait_for(self.setup(ARM_ROLES[arm]), timeout=300)
            repository = await self.localize(arm, locator)
            snapshot, policy, terminal = (
                await self.pool(repository, program) if program else await self.native()
            )
            self.budget.require_known()
            total = combine_accounts(
                {name: client.snapshot() for name, client in self.clients.items()}
            )
            require(total["requests"] == self.budget.used(), "all actual requests bound")
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
                "implementations": observed,
                "policies": {arm: policy},
                **total,
                "budget": {**self.budget.snapshot(), "arm": arm, "stage_role": ARM_ROLES[arm]},
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
            if locator:
                workers.extend(copy.deepcopy(locator.program.records))
            if any(row.get("cleanup_confirmed") is not True for row in workers):
                errors.append("WORKER_CLEANUP_UNCONFIRMED")
            self.cleanup = {
                "cleanup_confirmed": not errors,
                "errors": errors,
                "environments": [e.record for e in self.environments],
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
