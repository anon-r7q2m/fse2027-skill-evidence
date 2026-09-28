"""Same capacity policy with each editor's exact initial representation."""

import asyncio

from analysis.automatic_extraction_v1.common import file_sha, require, write_once
from analysis.editor_import_boundary_v1.host import rebound
from analysis.raw_issue_feedback_entry_v2.capacity import admission as original_admission
from analysis.raw_issue_feedback_entry_v2.context import WorkspaceBroker, attach, source_context
from analysis.raw_repo_comparators_v1.host import NaiveHost as OriginalNaive
from analysis.raw_repo_handoff_scored_v1.host import MiniHost as MiniHost, qualified_packages
from analysis.raw_repo_localization_scored_v2.host import Host as ScoredHost
from analysis.raw_repo_localization_v1.budget import BudgetStop
from analysis.raw_repo_localization_v1.host import Host as OriginalHost

from .budget import Budget
from .constants import HOST_POLICY
from .source import source_view


def admission(view, editor):
    require(editor in {"P", "Pn"}, "capacity decision needs an editor identity")
    result = original_admission(view)
    result.update(host_policy=HOST_POLICY, editor=editor)
    if editor == "Pn" and view["status"] == "SOURCE_VIEW_READY":
        for row in result["files"]:
            row["initial_after_bytes"] = row["before_bytes"]
            row["paired_bytes"] = 2 * row["before_bytes"]
            row["individually_feasible"] = row["paired_bytes"] <= result["paired_limit_bytes"]
        result["reason"] = (
            "ALL_SELECTED_FILES_EXCEED_PAIRED_LIMIT"
            if all(not row["individually_feasible"] for row in result["files"])
            else None
        )
        result["path"] = "native_capacity_fallback" if result["reason"] else "original_P"
    result["representation"] = "newline_normalized" if editor == "P" else "exact_original"
    return result


class CapacityRoute:
    setup = rebound(OriginalHost.setup, {"Budget": Budget})
    native = rebound(OriginalHost.native, {"WorkspaceBroker": WorkspaceBroker})
    editor = "P"

    async def pool(self, repository, program):
        require(self.budget.used("pool") == 0, "route decision precedes all editor requests")
        if repository is None:
            self.budget.select("original_P")
            return await super().pool(repository, program)
        try:
            view = await asyncio.to_thread(
                source_view,
                repository,
                self.discovery.get("localized_files", self.discovery["selected_files"]),
                self.discovery.get("locations"),
            )
        except BudgetStop as exc:
            self.budget.require_known()
            self.budget.select("original_P")
            write_once(self.logs / "capacity_clock_stop.json", {"reason": str(exc)})
            return await super().pool(repository, program)
        write_once(self.logs / "capacity_source_view.json", view)
        choice = admission(view, self.editor)
        choice.update(
            source_view_sha256=file_sha(self.logs / "capacity_source_view.json"),
            requests_already_used=self.budget.used(),
            remaining_requests=self.budget.call_limit - self.budget.used(),
            solve_end=self.budget.solve_end,
            total_end=self.budget.total_end,
        )
        write_once(self.logs / "capacity_admission.json", choice)
        self.budget.select(choice["path"])
        if choice["path"] == "original_P":
            return await super().pool(repository, program)
        self.view = view
        write_once(self.logs / "source_view.json", view)
        context = await source_context(
            self,
            {**self.discovery, "locations": view["locations"]},
            self.base_snapshot,
            self.logs / "native_context",
        )
        self.config["issue"] = attach(self.config["issue"], context)
        snapshot, policy, terminal = await self.native()
        policy.update(host_policy=HOST_POLICY, capacity_admission=choice)
        return snapshot, policy, terminal


class Host(CapacityRoute, ScoredHost):
    pass


class NaiveHost(CapacityRoute, OriginalNaive):
    editor = "Pn"


__all__ = ["Host", "NaiveHost", "MiniHost", "admission", "qualified_packages"]
