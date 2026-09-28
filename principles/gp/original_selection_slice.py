def _choose_submission_effect(state, pool, current_snapshot_ref):
    regression_enabled = state["flags"]["regression"]
    reproduction_enabled = state["flags"]["reproduction"]

    comparable = []
    for candidate in pool:
        g_first = candidate.get("g_first")
        if isinstance(g_first, dict) and g_first.get("comparable") is True:
            comparable.append(candidate)

    counts = {
        "pool": len(pool),
        "comparable": len(comparable),
        "eligible": 0,
        "winning_votes": 0,
        "minimum_failures": None,
    }

    if not pool:
        return _select_effect(
            snapshot_ref=current_snapshot_ref,
            mode="abstain_current",
            reason="EMPTY_POOL",
            counts=counts,
        )

    if regression_enabled:
        source = comparable
        if not source:
            return _select_effect(
                snapshot_ref=current_snapshot_ref,
                mode="abstain_current",
                reason="NO_COMPARABLE",
                counts=counts,
            )
    else:
        source = pool

    failure_counts = []
    for candidate in source:
        if regression_enabled:
            failure_counts.append(candidate["g_first"]["failure_count"])
        else:
            failure_counts.append(0)

    minimum_failures = min(failure_counts)
    counts["minimum_failures"] = minimum_failures

    minimum_group = []
    for candidate, failures in zip(source, failure_counts):
        if failures == minimum_failures:
            minimum_group.append(candidate)

    preferred_group = minimum_group
    used_reproduced_preference = False
    if reproduction_enabled:
        reproduced_group = [c for c in minimum_group if c.get("reproduced") is True]
        if reproduced_group:
            preferred_group = reproduced_group
            used_reproduced_preference = True

    eligible = [c for c in preferred_group if _candidate_has_nonempty_key(c)]
    if not eligible and used_reproduced_preference:
        eligible = [c for c in minimum_group if _candidate_has_nonempty_key(c)]
    if not eligible:
        eligible = [c for c in source if _candidate_has_nonempty_key(c)]

    counts["eligible"] = len(eligible)

    if eligible:
        winner = _majority_vote(eligible)
        counts["winning_votes"] = winner["winning_votes"]
        return _select_effect(
            snapshot_ref=winner["snapshot_ref"],
            mode="candidate",
            reason="MAJORITY_VOTE",
            counts=counts,
        )

    if any(c.get("key") == "" for c in source) and all(
        c.get("key") in ("", None) for c in source
    ):
        return _select_effect(
            snapshot_ref=state["base_snapshot_ref"],
            mode="empty_base",
            reason="ALL_KEYS_EMPTY",
            counts=counts,
        )

    return _select_effect(
        snapshot_ref=current_snapshot_ref,
        mode="abstain_current",
        reason="NO_COMPARABLE_KEYS",
        counts=counts,
    )


def _majority_vote(candidates):
    vote = {}
    first_index = {}
    first_snapshot = {}
    for index, candidate in enumerate(candidates):
        key = candidate["key"]
        vote[key] = vote.get(key, 0) + 1
        if key not in first_index:
            first_index[key] = index
            first_snapshot[key] = candidate["snapshot_ref"]

    best_key = None
    best_tuple = None
    for key in vote:
        score = (vote[key], -first_index[key])
        if best_tuple is None or score > best_tuple:
            best_tuple = score
            best_key = key

    return {
        "key": best_key,
        "snapshot_ref": first_snapshot[best_key],
        "winning_votes": vote[best_key],
    }


def _candidate_has_nonempty_key(candidate):
    return isinstance(candidate.get("key"), str) and candidate["key"] != ""


def _select_effect(snapshot_ref, mode, reason, counts):
    return {
        "kind": "select_submission_snapshot",
        "snapshot_ref": snapshot_ref,
        "mode": mode,
        "reason": reason[:256],
        "counts": {
            "pool": counts["pool"],
            "comparable": counts["comparable"],
            "eligible": counts["eligible"],
            "winning_votes": counts["winning_votes"],
            "minimum_failures": counts["minimum_failures"],
        },
    }
