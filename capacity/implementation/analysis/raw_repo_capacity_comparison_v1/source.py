"""Validate actual selected ranges before choosing an editor by representation size."""

import copy

from analysis.automatic_extraction_v1.common import require
from analysis.localization_repair_v1.contracts import paths
from analysis.same_base_selection_v2.contracts import MAX_TEXT_BYTES


def source_view(repository, selected_files, locations=None):
    require(paths(selected_files, maximum=3, empty=True), "at most three selected paths")
    result = {
        "base_commit": repository.base_commit,
        "base_snapshot_ref": repository.base_tree,
        "selected_files": copy.deepcopy(selected_files),
        "range_origin": "whole_file" if locations is None else "locator",
        "files": [],
        "locations": [],
    }
    if not selected_files:
        return {**result, "status": "NO_SELECTION"}
    rows = repository.files(selected_files)
    require([row["path"] for row in rows] == selected_files, "source selection order changed")
    if any(row["status"] != "available" for row in rows):
        return {
            **result,
            "status": "SOURCE_UNAVAILABLE",
            "dispositions": [{"path": row["path"], "status": row["status"]} for row in rows],
        }
    if any(not row["path"].endswith(".py") or not row["content"].splitlines() for row in rows):
        return {**result, "status": "OUTSIDE_P_FILE_DOMAIN"}
    counts = {row["path"]: len(row["content"].splitlines()) for row in rows}
    if locations is None:
        locations = [{"path": path, "start": 1, "end": counts[path]} for path in selected_files]
    valid = (
        type(locations) is list
        and 1 <= len(locations) <= 64
        and all(
            type(row) is dict
            and set(row) == {"path", "start", "end"}
            and type(row["path"]) is str
            and row["path"] in counts
            and type(row["start"]) is int
            and type(row["end"]) is int
            and 1 <= row["start"] <= row["end"] <= counts[row["path"]]
            for row in locations
        )
        and {row["path"] for row in locations} == set(selected_files)
    )
    if not valid:
        return {**result, "status": "INVALID_LOCATOR_RANGES"}
    result["locations"] = copy.deepcopy(locations)
    if sum(len(row["content"].encode("utf-8")) for row in rows) > MAX_TEXT_BYTES:
        return {**result, "status": "P_INPUT_LIMIT"}
    result["files"] = sorted(
        [{key: row[key] for key in ("path", "content", "mode")} for row in rows],
        key=lambda row: row["path"],
    )
    return {**result, "status": "SOURCE_VIEW_READY"}
