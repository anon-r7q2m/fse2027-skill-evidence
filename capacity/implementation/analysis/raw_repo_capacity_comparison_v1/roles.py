"""Declared stage permissions for ordinary, pool, and capacity fallback paths."""

import copy

from analysis.automatic_extraction_v1.common import require
from analysis.raw_repo_handoff_scored_v1.workflow import allowed_roles as original_roles


def allowed_roles(prefix):
    roles = original_roles(prefix)
    return roles | ({"native"} if prefix in {"P", "LP", "Pn", "LnPn"} else set())


def role_policy(policy, prefix, role, calls):
    require(role in allowed_roles(prefix), "unassigned stage")
    if role in {"discovery", "localization"}:
        require(calls == 5, "fixed discovery ceiling")
    elif role.startswith("sample"):
        require(calls == 1, "one request per original sample")
    elif role == "mini" or prefix == "N":
        require(calls == 9, "common nine-request ceiling")
    else:
        require(4 <= calls <= 9, "native receives only the remaining allowance")
    return {**copy.deepcopy(policy), "calls_per_start": calls}
