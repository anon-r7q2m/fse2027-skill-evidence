"""ID-only selection and exact task/repeat/arm schedule, with no result inputs."""

import hashlib

from analysis.automatic_extraction_v1.common import require

from .constants import (
    BLOCK_COUNT,
    FIRST_RANK,
    LAST_RANK,
    ORDER,
    REPEAT_SEED,
    REPEAT_TASKS,
    REPEATS,
    SOLVER_COUNT,
    TASK_COUNT,
)


def choose_ids(ranking, excluded):
    selected = [
        {"rank": rank, "instance_id": ranking[rank - 1]["instance_id"]}
        for rank in range(FIRST_RANK, min(LAST_RANK, len(ranking)) + 1)
        if ranking[rank - 1]["instance_id"] not in set(excluded)
    ][:TASK_COUNT]
    require(
        len(selected) == len({t["instance_id"] for t in selected}) == TASK_COUNT,
        "fixed window must contain sixteen unique unexposed IDs",
    )
    return selected


def repeat_panel(task_ids):
    require(
        len(task_ids) == len(set(task_ids)) == TASK_COUNT,
        "sixteen distinct IDs required before repeat selection",
    )
    return sorted(
        task_ids,
        key=lambda ident: (hashlib.sha256((REPEAT_SEED + ident).encode()).hexdigest(), ident),
    )[:REPEAT_TASKS]


def blocks(tasks, repeat_ids):
    ids = [t["instance_id"] for t in tasks]
    require(
        len(tasks) == len(set(ids)) == len({t["rank"] for t in tasks}) == TASK_COUNT,
        "sixteen unique ordered tasks required",
    )
    require(repeat_ids == repeat_panel(ids), "repeat panel differs from the ID-only rule")
    return [
        {
            "instance_id": task["instance_id"],
            "rank": task["rank"],
            "task_position": position,
            "repeat_index": repeat,
            "block_id": f"{task['rank']}-r{repeat}",
        }
        for repeat in range(1, REPEATS + 1)
        for position, task in enumerate(tasks, 1)
        if repeat == 1 or task["instance_id"] in repeat_ids
    ]


def slots_for(block_rows):
    require(len(block_rows) == BLOCK_COUNT, "twenty-four task-repeat blocks required")
    slots = []
    for block in block_rows:
        offset = (block["task_position"] + block["repeat_index"] - 2) % len(ORDER)
        for arm in ORDER[offset:] + ORDER[:offset]:
            number = len(slots) + 1
            slots.append(
                {
                    **block,
                    "number": number,
                    "prefix": arm,
                    "cell_id": f"{number:03d}-{block['block_id']}-{arm}",
                }
            )
    return slots


def validate(value):
    expected = blocks(value["tasks"], value["repeat_ids"])
    actual = value["blocks"]
    require(
        len(actual) == BLOCK_COUNT
        and [{k: row[k] for k in expected[0]} for row in actual] == expected,
        "fixed task-repeat block identity or order changed",
    )
    require(
        len({row["runtime"] for row in actual}) == BLOCK_COUNT
        and len({row["runtime_sha256"] for row in actual}) == BLOCK_COUNT,
        "each task-repeat requires its own runtime identity",
    )
    require(
        len(value["slots"]) == SOLVER_COUNT and value["slots"] == slots_for(actual),
        "complete rotated schedule must retain all 192 fresh paths",
    )
