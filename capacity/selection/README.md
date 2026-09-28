# Existing selection records, projected for release

All JSON files are new field projections. `_release` records export time and source paths; original experiment timestamps remain separate fields. Full original byte SHA-256 values are in [PROVENANCE.json](../implementation/PROVENANCE.json). A redacted projection does not have the original file's digest.

* `ranking_rule.json` gives the pinned dataset revision, ranking seed, exact ranking function, and legacy exclusion rule.
* `ranked_roster.json` preserves all 476 ranked IDs and their recorded rank hashes, plus the 24 legacy IDs. The new `rank` column is the 1-based original array position. Difficulty is omitted.
* `predecessor_exclusions.json` exposes the immediate predecessor's excluded and selected IDs.
* `frozen_selection_rule.json` retains the current 217 exclusions, 16 selected rank/ID objects, four repeat IDs, original creation time, and parent/dataset digests.
* `task_manifest.json` binds those 16 IDs to repository/base commits and issue/decision digests, without issue contents.
* `screen_freeze_records.json` contains only rule/time and decision fields from the 16 original screen records.
* `schedule.json` retains 24 task/repeat blocks, 192 ordered slots, runtime digests, and package identities. Runtime paths and task text are omitted.
* `freeze_chain.json` retains selected original launch/score bindings and local timestamps, omitting commands, processes, and account details.

The 217 recorded exclusions are exactly the predecessor's exclusions plus its eight selected IDs. Relative to "legacy 24 plus the first 193 ranked IDs," the actual set contains `sympy__sympy-11870` and omits `pydata__xarray-2905`. The published set is the actual record; this release does not invent a historical reason for that difference. The selected capacity IDs nevertheless match original ranks 194–209. `last_position=500` in the rule is the search-window bound, not the last selected rank.

Source implementations for selection and repeat ordering are under [implementation/analysis/raw_repo_capacity_comparison_v1](../implementation/analysis/raw_repo_capacity_comparison_v1). These records expose the recorded selection process, without certifying all exposure outside that process.
