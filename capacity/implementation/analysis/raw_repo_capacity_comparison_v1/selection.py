"""Freeze the complete method and ID-only panel before reading new public issues."""

import argparse
from datetime import datetime, timezone

from analysis.automatic_extraction_v1.common import file_sha, parse_json, require, write_once
from analysis.raw_repo_confirmation_v1.selection import reader

from .allocation import read as read_allocation
from .constants import FIRST_RANK, LAST_RANK, PACKAGE, ROOT, TASK_COUNT
from .schedule import choose_ids, repeat_panel


def method_bindings():
    prior = parse_json(
        (ROOT / "experiments/raw_repo_handoff_scored_v1/launch_manifest.json").read_bytes()
    )
    paths = {ROOT / name for name in prior["bindings"] if name.endswith(".py")}
    for folder in (
        "raw_repo_capacity_comparison_v1",
        "raw_issue_feedback_entry_v2",
        "raw_repo_confirmation_v1",
        "raw_issue_feedback_effect_v1",
    ):
        paths.update((ROOT / "analysis" / folder).glob("*.py"))
    for folder in ("L_PATH", "P_PATH", "LN_PATH", "PN_PATH"):
        from . import constants

        paths.update(p for p in getattr(constants, folder).iterdir() if p.is_file())
    for name in prior["bindings"]:
        if name.endswith(".py"):
            require(file_sha(ROOT / name) == prior["bindings"][name], "frozen host changed")
    return {str(p.relative_to(ROOT)): file_sha(p) for p in sorted(paths)}


def freeze():
    read_allocation()
    prior_path = ROOT / "experiments/raw_issue_feedback_effect_v2/selection_rule.json"
    prior = parse_json(prior_path.read_bytes())
    ranking = ROOT / prior["prior_ranking"]
    require(file_sha(ranking) == prior["prior_ranking_sha256"], "original ranking changed")
    excluded = set(prior["excluded_ids"]) | {r["instance_id"] for r in prior["selected_ids"]}
    require(
        len(excluded) == 217 and prior["last_position"] == FIRST_RANK - 1, "all exposures excluded"
    )
    require(not (PACKAGE / "screen").exists(), "IDs must precede issue access")
    ids = choose_ids(parse_json(ranking.read_bytes())["ranked"], excluded)
    rule = {
        "status": "ALL_TASK_AND_REPEAT_IDS_FROZEN_BEFORE_ISSUES",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        **{
            k: prior[k]
            for k in (
                "dataset",
                "revision",
                "parquet_sha256",
                "prior_ranking",
                "prior_ranking_sha256",
            )
        },
        "allowed_dataset_columns": ["instance_id", "repo", "base_commit", "problem_statement"],
        "excluded_ids": sorted(excluded),
        "selected_ids": ids,
        "repeat_ids": repeat_panel([r["instance_id"] for r in ids]),
        "start_position": FIRST_RANK,
        "last_position": LAST_RANK,
        "required_tasks": TASK_COUNT,
        "post_selection_replacement": False,
        "selection": "FIRST_16_UNEXPOSED_IDS_NO_CONTENT_FILTER",
        "design_sha256": file_sha(PACKAGE / "DESIGN.md"),
        "predecessor_rule_sha256": file_sha(prior_path),
        "method_bindings": method_bindings(),
        "model_requests": 0,
        "benchmark_starts": 0,
    }
    write_once(PACKAGE / "selection_rule.json", rule)
    return {"status": rule["status"], "selected": ids, "repeat_ids": rule["repeat_ids"]}


def checked_rule():
    rule = parse_json((PACKAGE / "selection_rule.json").read_bytes())
    require(rule["design_sha256"] == file_sha(PACKAGE / "DESIGN.md"), "pre-exposure design changed")
    require(rule["method_bindings"] == method_bindings(), "pre-exposure method changed")
    ranking = ROOT / rule["prior_ranking"]
    require(
        file_sha(ranking) == rule["prior_ranking_sha256"]
        and rule["selected_ids"]
        == choose_ids(parse_json(ranking.read_bytes())["ranked"], rule["excluded_ids"])
        and rule["repeat_ids"] == repeat_panel([r["instance_id"] for r in rule["selected_ids"]]),
        "pre-exposure ID-only panel changed",
    )
    return rule


def select():
    rule = checked_rule()
    selected, ranks = [], []
    previous = reader.PACKAGE
    reader.PACKAGE = PACKAGE
    try:
        while len(selected) < TASK_COUNT:
            result = reader.next_issue()
            require(
                result.get("status") != "FIXED_SCREEN_WINDOW_EXHAUSTED", "fixed window exhausted"
            )
            rank = result["rank"]
            ranks.append(rank)
            if result.get("status") == "EXCLUDED_PRIOR_EXPOSURE":
                continue
            row, folder = result["public_row"], PACKAGE / "screen" / f"{rank:03d}"
            expected = rule["selected_ids"][len(selected)]
            require(
                set(row) == set(rule["allowed_dataset_columns"])
                and {"rank": rank, "instance_id": row["instance_id"]} == expected,
                "public issue must belong to the already frozen ID roster",
            )
            write_once(
                folder / "decision.json",
                {
                    "status": "COMPATIBLE",
                    "disposition": "PRESELECTED_ID_NO_CONTENT_FILTER",
                    **expected,
                    "environment_ready": None,
                    "behavior_executed": False,
                },
            )
            selected.append(
                {
                    "rank": rank,
                    **{k: row[k] for k in ("instance_id", "repo", "base_commit")},
                    "public_issue_path": str((folder / "public_issue.json").relative_to(ROOT)),
                    "public_issue_sha256": file_sha(folder / "public_issue.json"),
                    "decision_path": str((folder / "decision.json").relative_to(ROOT)),
                    "decision_sha256": file_sha(folder / "decision.json"),
                }
            )
    finally:
        reader.PACKAGE = previous
    value = {
        "status": "SIXTEEN_ORIGINAL_PUBLIC_ISSUES_FIXED",
        "stage": "raw_repo_capacity_comparison_v1",
        "rule_sha256": file_sha(PACKAGE / "selection_rule.json"),
        "selected": selected,
        "repeat_ids": rule["repeat_ids"],
        "screened_ranks": ranks,
        "score_exposed": False,
        "behavior_executed": False,
        "model_requests": 0,
        "benchmark_starts": 0,
    }
    write_once(PACKAGE / "selection.json", value)
    return {"status": value["status"], "tasks": len(selected), "repeat_ids": rule["repeat_ids"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("freeze", "select"))
    print(globals()[parser.parse_args().mode]())
