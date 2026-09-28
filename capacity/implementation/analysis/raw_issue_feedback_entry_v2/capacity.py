"""Check the unchanged parser's initial complete-text bound before sampling."""

from analysis.automatic_extraction_v1.common import require
from analysis.same_base_selection_v2.contracts import MAX_TEXT_BYTES

POLICY = "CAPACITY_GATED_LP_V2"


def admission(view):
    rows = []
    if view["status"] == "SOURCE_VIEW_READY":
        require(bool(view["files"]), "ready input cannot have an empty selected file set")
        for row in view["files"]:
            before = row["content"]
            after = "\n" + "\n".join(before.splitlines()) + "\n"
            a, b = len(before.encode("utf-8")), len(after.encode("utf-8"))
            rows.append(
                {
                    "path": row["path"],
                    "before_bytes": a,
                    "initial_after_bytes": b,
                    "paired_bytes": a + b,
                    "individually_feasible": a + b <= MAX_TEXT_BYTES,
                }
            )
        reason = (
            "ALL_SELECTED_FILES_EXCEED_PAIRED_LIMIT"
            if all(not row["individually_feasible"] for row in rows)
            else None
        )
    elif view["status"] == "P_INPUT_LIMIT" and view["selected_files"]:
        reason = "COMPLETE_P_INPUT_LIMIT"
    else:
        reason = None
    return {
        "host_policy": POLICY,
        "source_status": view["status"],
        "paired_limit_bytes": MAX_TEXT_BYTES,
        "files": rows,
        "reason": reason,
        "path": "native_capacity_fallback" if reason else "original_P",
    }
