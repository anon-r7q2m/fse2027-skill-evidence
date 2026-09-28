"""One nine-call clock with an exclusive pool-or-native editing decision."""

from analysis.automatic_extraction_v1.common import require
from analysis.raw_issue_feedback_entry_v2.budget import Budget as CapacityBudget
from analysis.raw_repo_localization_v1.budget import Budget as OriginalBudget

from .constants import HOST_POLICY


class Budget(OriginalBudget):
    def __init__(self, arm, **kwargs):
        super().__init__(arm, **kwargs)
        self.edit_path = None

    def select(self, path):
        require(self.arm in {"P", "LP"}, "only editor arms select a capacity route")
        CapacityBudget.select(self, path)

    def bind(self, name, client, stage):
        if self.arm in {"N", "L"}:
            return super().bind(name, client, stage)
        return CapacityBudget.bind(self, name, client, stage)

    def snapshot(self):
        return {**super().snapshot(), "host_policy": HOST_POLICY, "edit_path": self.edit_path}
