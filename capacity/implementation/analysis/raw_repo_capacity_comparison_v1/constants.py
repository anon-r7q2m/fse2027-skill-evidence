"""Original immutable packages, new task identities and one finite allocation."""

from analysis.raw_repo_comparator_scored_v1.constants import (
    CALLS as CALLS,
    GENERATION_PACKAGE as GENERATION_PACKAGE,
    L_PATH as L_PATH,
    LN_PATH as LN_PATH,
    ORDER as ORDER,
    P_PATH as P_PATH,
    PN_PATH as PN_PATH,
    POLICIES as POLICIES,
    ROOT as ROOT,
    package_identities as package_identities,
)

PACKAGE = ROOT / "experiments/raw_repo_capacity_comparison_v1"
RESULTS = ROOT / "results_cache/raw_repo_capacity_comparison_v1"
TASK_COUNT, REPEAT_TASKS, REPEATS = 16, 4, 3
BLOCK_COUNT = TASK_COUNT + REPEAT_TASKS * (REPEATS - 1)
SOLVER_COUNT = BLOCK_COUNT * len(ORDER)
START_ALLOWANCE, MAX_REQUESTS = 2 * SOLVER_COUNT, SOLVER_COUNT * CALLS
HISTORICAL, CAP = 914, 1387
FIRST_RANK, LAST_RANK = 194, 500
REPEAT_SEED = "a2s-capacity-20260922-repeat-v1|"
LABEL = "CAPACITY_AWARE_16_TASK_COMPARISON_WITH_FIXED_RUN_VARIABILITY_PANEL"
HOST_POLICY = "CAPACITY_AWARE_ORIGINAL_AND_NAIVE_V1"
REVIEW = ROOT / "docs/reviews/next_effect_priority_20260922.md"
SCORER_ROOT = ROOT / "analysis/raw_repo_handoff_score_recovery_v1"
SCORER_SOURCES = tuple(
    str((SCORER_ROOT / name).relative_to(ROOT))
    for name in ("score_adapter.py", "scorer.py", "syntax_proof.py", "syntax_witness.py")
)
