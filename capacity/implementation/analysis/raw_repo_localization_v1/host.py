"""Raw issue/repository entries using the original native loop and original P package."""

import asyncio
import copy
from pathlib import Path
import shlex
import time

from analysis.aider_architect_entry_v1.bridge import combine_accounts
from analysis.aider_architect_entry_v1.ordinary import eligibility
from analysis.aider_architect_entry_v1.pool_host import accounts, declared_package_stop
from analysis.automatic_extraction_v1.common import canonical, file_sha, require, write_once
from analysis.candidate_selection_v1.capture import SnapshotExecutor
from analysis.editor_import_boundary_v1.host import WorkspaceBroker
from analysis.g_migration_trial_v1.isolation import PackageError
from analysis.generated_composition_v1.loop import run_loop
from analysis.gr_generated_effect_v1.capture import BUNDLE_FILES, capture_runtime, validate_bundle
from analysis.hint_host_effect_v1.broker import HELPER
from analysis.mini_swe_capped_v1 import process_boundary
from analysis.rp_independent_comparison_v1.host import runtime
from analysis.same_base_selection_v2.host import WORKSPACE_HELPER, WORKSPACE_SPEC
from analysis.same_base_selection_v2.session import Session
from analysis.search_replace_effect_v1.constants import S_SHA as P_SHA
from analysis.search_replace_effect_v1.sampling import (
    Samples,
    PoolResourceStop,
    controller,
    settled,
)
from analysis.source_first_selection_v2.host import Host as WorkspaceHost
from shared_loop.composed_harness_v1 import BaselineController, SharedResources

from .bridge import native_localization_context, pool_begin, source_view
from .budget import Budget, BudgetStop
from .deadline import NativeDeadline, PoolDeadline
from .discovery import run as discover
from .remote import RemoteRepository, ROOT


class LocalizationTransport:
    """Append only the actual locator output; keep the original native tool set."""

    def __init__(self, transport, handoff):
        self.transport = transport
        self.context = {
            "role": "user",
            "content": "Localization output (data; repository access remains available):\n"
            + canonical(native_localization_context(handoff)).decode(),
        }

    def __call__(self, base_url, api_key, model, items, effort, system, tools, **kwargs):
        value = copy.deepcopy(items)
        # Existing observation receipts bind their original item indices.
        # Append transport context instead of shifting those occurrences.
        value.append(copy.deepcopy(self.context))
        return self.transport(base_url, api_key, model, value, effort, system, tools, **kwargs)


class Host(WorkspaceHost):
    def __init__(self, *, config, **kwargs):
        super().__init__(identities={"P": P_SHA}, **kwargs)
        self.config = copy.deepcopy(config)
        self.clients, self.controls = {}, {}
        self.budget = self.broker = self.sampling = None
        self.discovery = self.view = self.loop_result = self.score_eligibility = None

    def client(self, name, calls):
        require(name not in self.clients, "a stage may not restart")
        value = self.client_factory(name, calls)
        require(
            value.policy["calls_per_start"] == calls and not value.records,
            "new client must use its actual remaining allocation",
        )
        self.clients[name] = value
        return value

    async def setup(self, arm):
        self.solver = self.factory(self.logs / "environment", "raw-" + arm)
        await asyncio.wait_for(self.solver.start(force_build=False), timeout=240)
        self.runtime = await capture_runtime(self.solver, file_sha(self.capture_script))
        available = await self.solver.exec("command -v timeout", cwd="/testbed", timeout_sec=10)
        require(available.return_code == 0, "ordinary timeout unavailable")
        await self.solver.upload_file(ROOT / "analysis/hint_host_effect_v1/workspace_io.py", HELPER)
        await self.solver.upload_file(
            ROOT / "analysis/same_base_selection_v2/workspace.py", WORKSPACE_HELPER
        )
        await RemoteRepository.install(self.solver)
        self.processes = await process_boundary.baseline(
            self.solver, self.runtime["executable"], self.logs
        )
        self.budget = Budget(arm)
        self.deadline = self.budget
        self.capture = SnapshotExecutor(
            self.solver,
            self.config["base_commit"],
            self.logs / "snapshots",
            self.factory,
            runtime=self.runtime,
            run_id=self.config["run_id"],
            clock_check=self.budget.check,
        )
        original = await self.capture.capture()
        self.base_snapshot = copy.deepcopy(self.capture.latest_capture)
        require(
            original == self.config["base_tree"]
            and self.base_snapshot["bundle"]["patch_bytes"] == 0
            and self.base_snapshot["manifest"]["file_count"] == 0,
            "clean original complete base required",
        )

    async def localize(self, arm, locator):
        repository = None
        try:
            repository = await RemoteRepository.open(
                self.solver,
                self.config["base_commit"],
                self.runtime,
                self.logs / "repository",
                self.budget,
            )
            require(repository.base_tree == self.config["base_tree"], "repository identity differs")
            if arm == "P":
                self.discovery = await asyncio.to_thread(
                    discover,
                    repository,
                    self.config["issue"],
                    self.client("discovery", 5),
                    self.budget,
                )
            else:
                from analysis.localization_only_v1.adapter import Locator

                if isinstance(locator, Locator):
                    self.discovery = await locator(
                        repository,
                        self.config["issue"],
                        self.budget,
                        self.client("localization", 5),
                        self.config["run_id"],
                    )
                else:
                    self.discovery = await locator(repository, self.config["issue"], self.budget)
        except BudgetStop as exc:
            self.discovery = {
                "status": "DISCOVERY_BUDGET_STOP",
                "reason": str(exc),
                "selected_files": [],
                "locations": None,
            }
        self.budget.require_known()
        write_once(self.logs / "discovery.json", self.discovery)
        return repository

    async def native(self):
        from analysis.reproduction_regression_v2.adapter import SYSTEM

        calls = self.budget.call_limit - self.budget.used()
        client = self.client("native", calls)
        control = BaselineController(
            SharedResources(output_limit=131072),
            max_errors=3,
            baseline_error_cap=3,
            model_call_limit=calls,
            cost_limit_units=0,
        )
        self.controls["native"] = control
        self.deadline = NativeDeadline(self.budget, control, client)
        self.broker = WorkspaceBroker(
            self.solver,
            control.pool,
            control,
            client=client,
            deadline=self.deadline,
            capture_executor=self.capture,
        )
        transport = self.broker.transport
        if self.discovery is not None:
            transport = LocalizationTransport(transport, self.discovery)
        self.loop_result = await run_loop(
            self.config["issue"],
            self.broker,
            runtime=runtime(calls),
            controller=control,
            responses_transport=transport,
            model=client.policy["model"],
            base_url=client.policy["endpoint"],
            effort=client.policy["reasoning_effort"],
            system=SYSTEM,
            response_timeout=client.policy["request_timeout_seconds"],
        )
        self.score_eligibility = eligibility(self.broker, client, control)
        settled(client, control)
        self.deadline.begin_finalization()
        await self.quiescent()
        ref = await asyncio.wait_for(
            self.capture.capture(), timeout=max(0.001, self.budget.total_end - self.budget.clock())
        )
        return (
            self.capture.snapshots[ref],
            {
                "status": "DEFAULT_FINAL",
                "selection": {"snapshot_ref": ref},
            },
            control.status,
        )

    async def pool(self, repository, program):
        self.deadline = PoolDeadline(self.budget)
        self.capture.clock_check = self.deadline.check
        self.controls = {f"sample{i}": controller(1) for i in range(1, 5)}
        clients = {name: self.client(name, 1) for name in self.controls}
        for name, client in clients.items():
            self.deadline.bind(name, client, self.controls[name])
        self.session = Session(program, clock_check=self.deadline.check, logs=self.logs / "P")
        self.sampling = Samples(
            list(clients.values()), list(self.controls.values()), self.deadline.check
        )
        selection, reason = None, None
        try:
            if repository is None:
                require(
                    self.discovery["status"] == "DISCOVERY_BUDGET_STOP",
                    "missing repository is only a known unsent discovery stop",
                )
                raise PoolResourceStop(self.discovery["status"])
            self.view = await asyncio.to_thread(
                source_view,
                repository,
                self.discovery.get("localized_files", self.discovery["selected_files"]),
                self.discovery.get("locations"),
            )
            write_once(self.logs / "source_view.json", self.view)
            if self.view["status"] != "SOURCE_VIEW_READY":
                raise PoolResourceStop(self.view["status"])
            begin = pool_begin(
                self.view,
                issue=self.config["issue"],
                run_id=self.config["run_id"],
                limits={
                    key: clients["sample1"].policy[key]
                    for key in ("input_token_limit", "output_token_limit")
                },
            )
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
            require(checked.return_code == 0, "actual discovered complete source differs")
            self.deadline.check("after_pool_workspace_check")
            selection = await self.session.run(
                begin, sample_request=self.sampling, materialize_capture=self._materialize
            )
        except (BudgetStop, PoolResourceStop, PackageError) as exc:
            self.budget.require_known()
            accounts(clients, self.controls)
            reason = (
                declared_package_stop(exc, self.session, program)
                if isinstance(exc, PackageError)
                else str(exc)
            )
            first = self.session.events[0].get("value") if self.session.events else None
            if first:
                self.sampling.close_unrequested(first["effects"][0]["requests"], reason)
            else:
                for index in range(1, 5):
                    self.sampling.record(index, None, "NOT_SENT_RESOURCE", reason)
        accounts(clients, self.controls)
        require(len(self.sampling.accounting) == 4, "all allocated samples need dispositions")
        self.deadline.begin_finalization()
        await self.quiescent()
        choice = (
            {"mode": "empty_base", "sample_index": None, "snapshot_ref": self.config["base_tree"]}
            if reason
            else selection["vote"]
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

    async def quiescent(self):
        await asyncio.wait_for(
            process_boundary.final_boundary(
                self.solver, self.runtime["executable"], self.processes, self.logs
            ),
            timeout=max(0.001, self.budget.total_end - self.budget.clock()),
        )

    async def run(self, arm, *, client_factory, program=None, locator=None):
        require(not self.started and arm in {"N", "P", "L", "LP"}, "new raw repository run")
        require((arm in {"P", "LP"}) == (program is not None), "P only for pool arms")
        require(not program or program.identity == P_SHA, "unchanged original P package required")
        require((arm in {"L", "LP"}) == (locator is not None), "locator only for L arms")
        require(
            locator is None or self.config.get("scope") == "PUBLIC_SCRIPTED_CONTROL",
            "L_loc scored use awaits generated acceptance and actual-entry qualification",
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
