"""Recompute reported counts and exact paired tests from released CSV records.

This reads existing outcomes only; it runs no solver or benchmark grader.
"""

import csv
import json
from collections import defaultdict
from math import comb
from pathlib import Path


def summarize(path):
    with path.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    outcomes = {}
    score_groups = defaultdict(list)
    for row in rows:
        key = (row["instance_id"], int(row["repeat_index"]), row["policy"])
        if key in outcomes or row["reward"] not in {"0", "1"}:
            raise ValueError("Duplicate logical outcome or nonbinary/missing reward")
        outcomes[key] = int(row["reward"])
        score_groups[row["score_cell"]].append(row)
    for group in score_groups.values():
        if len({(r["instance_id"], r["reward"]) for r in group}) != 1:
            raise ValueError("Inconsistent task/reward within a score cell")
    policies = ("N", "L", "P", "LP", "Ln", "Pn", "LnPn", "Hmini")
    tasks = sorted({t for t, repeat, _ in outcomes if repeat == 1})
    primary = {p: sum(outcomes[t, 1, p] for t in tasks) for p in policies}
    comparisons = []
    for policy in policies:
        if policy == "LP":
            continue
        wins = sum(outcomes[t, 1, "LP"] > outcomes[t, 1, policy] for t in tasks)
        losses = sum(outcomes[t, 1, "LP"] < outcomes[t, 1, policy] for t in tasks)
        n = wins + losses
        p_value = sum(comb(n, k) for k in range(wins, n + 1)) / 2**n
        comparisons.append({"control": policy, "lp_only": wins,
                            "control_only": losses, "one_sided_p": p_value})
    running = 0.0
    for rank, comparison in enumerate(sorted(comparisons, key=lambda x: x["one_sided_p"])):
        running = max(running, min(1.0, (len(comparisons) - rank) * comparison["one_sided_p"]))
        comparison["holm_p"] = running
    repeated = sorted({t for t, repeat, _ in outcomes if repeat > 1})
    repeats = {str(r): {p: sum(outcomes[t, r, p] for t in repeated)
                        for p in policies} for r in (1, 2, 3)}
    return {
        "scope": "Arithmetic over published outcomes; no new benchmark execution",
        "logical_rows": len(rows), "unique_score_cells": len(score_groups),
        "primary_tasks": len(tasks), "primary_solved": primary,
        "paired_comparisons": comparisons,
        "fixed_repeat_task_ids": repeated, "fixed_repeat_solved": repeats,
        "identity_limit": "This CSV check compares task/reward within score cells; "
                          "submission/grader identity is documented separately in identities/.",
    }


if __name__ == "__main__":
    print(json.dumps(summarize(Path(__file__).with_name("outcomes.csv")), indent=2))
