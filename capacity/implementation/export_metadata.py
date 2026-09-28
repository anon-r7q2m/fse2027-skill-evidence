"""Export selected existing records without importing or executing experiment code.

New release utility, not part of the historical experiment. Requires an explicitly
provided source checkout. Reads only the named metadata and source-code files;
never opens requests, responses, trajectory files, private annotations or secrets.
"""

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--capacity-output", required=True, type=Path)
    args = parser.parse_args()
    root, out = args.source_root.resolve(), args.capacity_output.resolve()
    exported = datetime.now(timezone.utc).isoformat()
    source_records, release_records = {}, []
    checks = {}
    exp = "experiments/raw_repo_capacity_comparison_v1/"
    res = "results_cache/raw_repo_capacity_comparison_v1/"

    def sha(raw):
        return hashlib.sha256(raw).hexdigest()

    def raw_source(name):
        path = root / name
        assert not path.is_symlink() and path.is_file()
        raw = path.read_bytes()
        source_records[name] = {"source_path": name, "source_sha256": sha(raw)}
        return raw

    def read(name):
        return json.loads(raw_source(name))

    def only(value, fields):
        return {key: value[key] for key in fields.split() if key in value}

    def clean(value):
        if isinstance(value, dict):
            return {clean(k): clean(v) for k, v in value.items()}
        if isinstance(value, list):
            return [clean(v) for v in value]
        if isinstance(value, str):
            value = value.replace(str(root) + "/", "")
            assert "/Data/" not in value and "/home/" not in value
        return value

    def write_json(name, data, sources, description):
        assert name.startswith(("selection/", "identities/", "implementation/"))
        payload = {
            "_release": {
                "kind": "NEW_FIELD_PROJECTION_OF_EXISTING_RECORDS",
                "exported_utc": exported,
                "source_paths": sources,
                "description": description,
                "historical_registration": False,
            },
            **clean(data),
        }
        raw = (json.dumps(payload, indent=2, ensure_ascii=False) + "\n").encode()
        target = out / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("wb") as handle:
            handle.write(raw)
        release_records.append({"release_path": name, "release_sha256": sha(raw),
                                "source_paths": sources, "transformation": description})

    rule = read(exp + "selection_rule.json")
    chosen = read(exp + "selection.json")
    ranking_path = rule["prior_ranking"]
    ranking = read(ranking_path)
    ranking_rule_path = "experiments/submit_review_host_effect_v1/selection_rule.json"
    ranking_rule = read(ranking_rule_path)
    predecessor_path = "experiments/raw_issue_feedback_effect_v2/selection_rule.json"
    predecessor = read(predecessor_path)
    schedule = read(exp + "schedule.json")
    plan = read(exp + "scoring_plan.json")
    launch = read(exp + "launch_manifest.json")
    seal = read(res + "scores/frozen_endpoints.json")
    reconciled = read(res + "scores/reconciliation.json")
    executed = read(res + "execution_summary.json")

    assert source_records[ranking_path]["source_sha256"] == rule["prior_ranking_sha256"]
    assert source_records[predecessor_path]["source_sha256"] == rule["predecessor_rule_sha256"]
    assert source_records[exp + "selection_rule.json"]["source_sha256"] == chosen["rule_sha256"]
    assert source_records[exp + "scoring_plan.json"]["source_sha256"] == seal["score_plan_sha256"]
    assert set(rule["excluded_ids"]) == set(predecessor["excluded_ids"]) | {
        row["instance_id"] for row in predecessor["selected_ids"]}
    assert [r["instance_id"] for r in rule["selected_ids"]] == [
        r["instance_id"] for r in ranking["ranked"][193:209]]
    for row in ranking["ranked"]:
        assert sha(ranking_rule["seed"].encode() + b"\0" + row["instance_id"].encode()) == row["rank_sha256"]
    assert ranking["ranked"] == sorted(ranking["ranked"], key=lambda r: (r["rank_sha256"], r["instance_id"]))
    repeat_order = sorted([r["instance_id"] for r in rule["selected_ids"]],
        key=lambda ident: (sha(("a2s-capacity-20260922-repeat-v1|" + ident).encode()), ident))
    assert repeat_order[:4] == rule["repeat_ids"]
    checks["selection"] = {"ranked_ids": len(ranking["ranked"]),
        "excluded_ids": len(rule["excluded_ids"]), "selected_ids": len(chosen["selected"]),
        "predecessor_union_matches": True, "selected_ranks_194_to_209_match": True,
        "all_rank_hashes_recomputed": True, "repeat_hash_selection_matches": True}

    write_json("selection/ranking_rule.json", only(ranking_rule,
        "dataset_id dataset_revision parquet_sha256 seed ranking excluded_roster selection_exclusions frozen_before_roster_projection"),
        [ranking_rule_path], "Whitelist projection; original ranking specification.")
    write_json("selection/ranked_roster.json", {
        **only(ranking, "population_count ranked_count rule_sha256 excluded_roster_sha256 excluded_ids"),
        "ranked": [{"rank": i, **only(row, "instance_id repo rank_sha256")}
                   for i, row in enumerate(ranking["ranked"], 1)]}, [ranking_path],
        "Difficulty omitted. The rank column is the original array position, 1-based.")
    write_json("selection/predecessor_exclusions.json", only(predecessor,
        "status excluded_ids selected_ids last_position prior_ranking prior_ranking_sha256"),
        [predecessor_path], "Whitelist projection of the immediate predecessor roster.")
    write_json("selection/frozen_selection_rule.json", only(rule,
        "status created_utc dataset revision parquet_sha256 prior_ranking prior_ranking_sha256 excluded_ids selected_ids repeat_ids start_position last_position required_tasks post_selection_replacement selection design_sha256 predecessor_rule_sha256 model_requests benchmark_starts"),
        [exp + "selection_rule.json"], "Original rule fields; historical created_utc is retained separately from export time.")
    write_json("selection/task_manifest.json", {
        **only(chosen, "status rule_sha256 screened_ranks repeat_ids score_exposed model_requests benchmark_starts behavior_executed"),
        "selected": [only(row, "rank instance_id repo base_commit decision_sha256 public_issue_sha256")
                     for row in chosen["selected"]]}, [exp + "selection.json"],
        "Issue bodies and local paths are omitted.")
    screen_rows, screen_sources = [], []
    for row in chosen["selected"]:
        prefix = exp + "screen/" + str(row["rank"]) + "/"
        begin, decision = read(prefix + "begin.json"), read(prefix + "decision.json")
        assert begin["selection_rule_sha256"] == chosen["rule_sha256"]
        screen_rows.append({"begin": only(begin, "created_utc rank selection_rule_sha256"),
                            "decision": only(decision, "rank instance_id status disposition behavior_executed")})
        screen_sources += [prefix + "begin.json", prefix + "decision.json"]
    write_json("selection/screen_freeze_records.json", {"rows": screen_rows}, screen_sources,
               "Only freeze times and dispositions; no issue text or difficulty.")
    write_json("selection/schedule.json", {
        **only(schedule, "status package_identities repeat_ids"),
        "tasks": [only(r, "rank instance_id repo base_commit decision_sha256 public_issue_sha256")
                  for r in schedule["tasks"]],
        "blocks": [only(r, "block_id instance_id rank repeat_index runtime_sha256 task_position")
                   for r in schedule["blocks"]],
        "slots": [only(r, "block_id cell_id instance_id number prefix rank repeat_index runtime_sha256 task_position")
                  for r in schedule["slots"]]}, [exp + "schedule.json"],
        "Frozen slot order and identities; runtime paths and task text omitted.")

    chain_paths = [res + "live/started.json", res + "supervision/manifest.json",
        res + "supervision/launcher_started.json", res + "supervision/launcher_exited.json",
        res + "scores/started.json", res + "scores/supervision/manifest.json",
        res + "scores/supervision/launcher_started.json", res + "scores/all_terminal.json"]
    chain_rows = []
    for name in chain_paths:
        item = read(name)
        projected = only(item, "schema phase scope_path scope_sha256 manifest_sha256 score_plan_sha256 seal_sha256 utc status launcher_started_sha256 return_code")
        if name.endswith("scores/all_terminal.json"):
            projected["actual_starts"] = item["starts"]["actual_starts"]
            projected["completed_count"] = len(item["completed"])
        chain_rows.append({"source_path": name, "record": projected})
    assert read(res + "live/started.json")["manifest_sha256"] == source_records[exp + "launch_manifest.json"]["source_sha256"]
    assert read(res + "scores/started.json")["seal_sha256"] == source_records[res + "scores/frozen_endpoints.json"]["source_sha256"]
    assert read(res + "scores/supervision/manifest.json")["scope_sha256"] == source_records[res + "scores/frozen_endpoints.json"]["source_sha256"]
    bindings = {name: value for name, value in launch["bindings"].items()
                if name in {exp + suffix for suffix in ("DESIGN.md", "policy.json", "selection_rule.json",
                    "selection.json", "schedule.json", "scoring_plan.json")}}
    write_json("selection/freeze_chain.json", {"launch": {
        **only(launch, "status policy_sha256 schedule_sha256 packages automatic_retries old_solver_endpoints_reused"),
        "bindings": bindings}, "records": chain_rows},
        [exp + "launch_manifest.json", *chain_paths],
        "Selected local chronology and digest links, not external preregistration or independent timestamps.")

    policy_name = exp + "policy.json"
    policy = read(policy_name)
    assert source_records[policy_name]["source_sha256"] == launch["policy_sha256"]
    write_json("implementation/policy.json", only(policy,
        "model accepted_response_models reasoning_effort calls_per_start input_token_limit output_token_limit request_timeout_seconds execution_scope input_estimator tokenizer_encoding tokenizer_version stage_id"),
        [policy_name], "Explicit whitelist; endpoint, credential_mode and all transport/account details omitted.")
    naive_name = "results_cache/raw_repo_comparators_v1/generation/all_final_seal.json"
    naive = read(naive_name)
    write_json("implementation/naive_package_seal.json", {"status": naive["status"],
        "finals": {name: only(value, "role status package_sha256 package_files attempts selected_attempt source_access human_code_repairs public_status")
                   for name, value in naive["finals"].items()}}, [naive_name],
        "Package identities and selected-attempt provenance; no generation request or response.")

    task_fields = "instance_id repo rank base_commit task_name task_files environment_images projection_sha256 grader_id"
    write_json("identities/task_contracts.json", {
        **only(plan, "status run_kind adaptation grader_id"),
        "tasks": {key: only(value, task_fields) for key, value in plan["tasks"].items()}},
        [exp + "scoring_plan.json"], "Sixteen task/base/grader contracts; task contents and local task paths omitted.")
    write_json("identities/grader_sources.json", {"grader_id": plan["grader_id"], "sources": plan["sources"]},
        [exp + "scoring_plan.json"], "Exact existing source path-to-digest map used by the score equivalence key.")
    scope_rows, commits, scope_sources = [], [], []
    scopes = {}
    rewards = {row["cell_id"]: row["reward"] for row in reconciled["rows"]}
    for slot in seal["unique_slots"]:
        cell = slot["cell_id"]
        base = res + "scores/" + cell + "/"
        scope_name, consumed_name = base + "scope.json", base + "consumed.json"
        scope, consumed = read(scope_name), read(consumed_name)
        assert source_records[scope_name]["source_sha256"] == slot["scope_sha256"] == consumed["scope_sha256"]
        assert scope["sources"] == plan["sources"]
        assert scope["task_files"] == plan["tasks"][scope["instance_id"]]["task_files"]
        assert scope["grader_id"] == plan["grader_id"] == consumed["score"]["grader_id"]
        assert scope["base_commit"] == scope["selected_capture"]["base_commit"] == plan["tasks"][scope["instance_id"]]["base_commit"]
        assert consumed["score"]["selected_capture"] == scope["selected_capture"]
        record = only(scope, "cell_id block_id instance_id repo rank repeat_index policy_name base_commit grader_id environment_images projection_sha256 score_plan_sha256 config_sha256 bundle_sha256 selected_capture")
        record.update(scope_sha256=slot["scope_sha256"], task_contract_id=scope["instance_id"],
                      grader_sources_file="grader_sources.json", reward=rewards[cell],
                      consumption=only(consumed["score"], "status grader_id instance_id selected_capture config_sha256 task_checksum task_bindings_sha256 task_projection_sha256 metadata_sha256 terminal_sha256 reward_commit_artifact_sha256 score_eligible score_release scoring_content_scope replay_and_restore"))
        scope_rows.append(record)
        scopes[cell] = record
        scope_sources += [scope_name, consumed_name]
        trial_path = Path(scope["trial_path"])
        assert trial_path.is_relative_to(root / res / "scores")
        commit_name = str((trial_path / "verifier/reward_commit.json").relative_to(root))
        commit = read(commit_name)
        assert commit["artifact_sha256"] == consumed["score"]["reward_commit_artifact_sha256"]
        unsigned_commit = {k: v for k, v in commit.items() if k != "artifact_sha256"}
        canonical_commit = json.dumps(unsigned_commit, ensure_ascii=False, sort_keys=True,
            separators=(",", ":"), allow_nan=False).encode() + b"\n"
        assert sha(canonical_commit) == commit["artifact_sha256"]
        commits.append({"score_cell": cell, "source_path": commit_name,
                        "record": only(commit, "schema_version artifact_type artifact_sha256 commit_marker_written_last publication_order files")})
    assert len(scope_rows) == 108
    write_json("identities/score_scopes.json", {
        **only(seal, "status score_plan_sha256 live_terminal_sha256 official_scores_exposed max_actual_scorer_starts"),
        "rows": scope_rows}, [res + "scores/frozen_endpoints.json", *scope_sources],
        "108 existing scopes and score-consumption identities. Repeated task_files and sources are losslessly referenced in adjacent files.")
    write_json("identities/reward_commit_records.json", {"rows": commits},
        [row["source_path"] for row in commits],
        "Original commit metadata only. commitment_sha256 fields are retained as named, not relabeled plain file SHA-256.")

    sealed_rows = {row["cell_id"]: row for row in seal["policies"]}
    csv_rows = []
    for row in reconciled["rows"]:
        raw = sealed_rows[row["cell_id"]]
        for key in "cell_id block_id instance_id policy repeat_index score_cell final_tree shared_score solver_status".split():
            assert row[key] == raw[key]
        scope = scopes[row["score_cell"]]
        task = plan["tasks"][row["instance_id"]]
        assert row["instance_id"] == scope["instance_id"]
        assert row["final_tree"] == scope["selected_capture"]["final_tree"]
        assert row["reward"] == scope["reward"]
        csv_rows.append({**only(row, "cell_id block_id instance_id policy repeat_index final_tree score_cell shared_score solver_status reward"),
            "base_commit": task["base_commit"], "grader_id": task["grader_id"],
            "task_contract_id": row["instance_id"], "score_scope_sha256": scope["scope_sha256"],
            "scored_patch_sha256": scope["selected_capture"]["patch_sha256"]})
    assert len(csv_rows) == 192 and len({r["score_cell"] for r in csv_rows}) == 108
    with (out / "outcomes.csv").open(newline="") as handle:
        public_rows = list(csv.DictReader(handle))
    expected_public = {(r["instance_id"], r["policy"], int(r["repeat_index"])): r for r in public_rows}
    assert len(expected_public) == len(csv_rows)
    for row in csv_rows:
        public = expected_public[(row["instance_id"], row["policy"], row["repeat_index"])]
        assert float(public["reward"]) == float(row["reward"])
        assert public["score_cell"] == row["score_cell"] and public["shared_score"] == str(row["shared_score"])
    csv_path = out / "identities/policy_outcomes.csv"
    with csv_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(csv_rows[0]))
        writer.writeheader()
        writer.writerows(csv_rows)
    release_records.append({"release_path": "identities/policy_outcomes.csv", "release_sha256": sha(csv_path.read_bytes()),
        "source_paths": [res + "scores/reconciliation.json", res + "scores/frozen_endpoints.json", exp + "scoring_plan.json"],
        "transformation": "Join existing reconciliation rows to sealed representative scope and task contract. scored_patch_sha256 belongs to score_cell, not necessarily the individual solver capture."})
    checks["identities"] = {"logical_rows": 192, "unique_scopes": 108, "scope_and_consumed_hashes_match": True,
        "reward_commit_self_digests_match_consumed": True, "all_reused_rewards_share_task_base_tree_and_grader": True,
        "existing_public_outcomes_unchanged_and_matched": True, "score_reexecution": False}

    primary = []
    primary_sources = [res + "execution_summary.json"]
    for row in executed["rows"]:
        if row["repeat_index"] != 1:
            continue
        arm, cell = row["prefix"], row["cell_id"]
        endpoint_name = res + "live/" + cell + "/entry/prefixes/" + arm + "/endpoints.json"
        endpoint = read(endpoint_name)
        disposition = endpoint["policies"][arm]
        assert endpoint["terminal_status"] == row["terminal_status"]
        item = only(row, "cell_id block_id instance_id prefix repeat_index status terminal_status discovery_status capacity_path capacity_reason requests editor_requests native_requests")
        item["policy_status"] = disposition["status"]
        item["pipeline_stop_reason"] = disposition.get("fallback_reason")
        item["recorded_endpoint_sha256"] = source_records[endpoint_name]["source_sha256"]
        item["stage_observations"] = [
            {"stage": "discovery_or_localization", "status": row["discovery_status"]},
            {"stage": "pre_edit_capacity_admission", "route": row["capacity_path"], "reason": row["capacity_reason"]},
            {"stage": "editing_pipeline", "status": disposition["status"], "stop_reason": disposition.get("fallback_reason")},
            {"stage": "solver_terminal", "status": row["terminal_status"]}]
        primary.append(item)
        primary_sources.append(endpoint_name)
    assert len(primary) == 128
    write_json("identities/primary_stage_dispositions.json", {"rows": primary}, primary_sources,
        "128 primary path status/stop fields only. Null means no reason in these fields, not proof of successful task resolution. No account records, model text, source views, traces, or annotations are exported.")
    checks["primary_dispositions"] = {"rows": 128, "raw_model_or_request_records_exported": False}

    package_dirs = {
        "L": "results_cache/localization_issue_boundary_v1/generation/direct/final_package",
        "P": "results_cache/search_replace_transfer_v1/generation/direct/final_package",
        "Ln": "results_cache/raw_repo_comparators_v1/generation/a2s/final_package",
        "Pn": "results_cache/raw_repo_comparators_v1/generation/direct/final_package"}
    package_files = {"L": ["mechanism.py", "donor_logic.py", "package.json"],
                     "P": ["mechanism.py", "admission_pkg.py", "edit_parser_pkg.py", "normalize_pkg.py", "package.json"],
                     "Ln": ["mechanism.py", "package.json"], "Pn": ["mechanism.py", "package.json"]}
    code_files = []
    for role, directory in package_dirs.items():
        code_files += [(directory + "/" + name, "implementation/packages/" + role + "/" + name)
                       for name in package_files[role]]
    modules = {
        "raw_repo_capacity_comparison_v1": ["constants", "host", "source", "budget", "roles", "schedule", "selection", "workflow"],
        "raw_issue_feedback_entry_v2": ["capacity", "context"],
        "raw_repo_localization_v1": ["host"],
        "raw_repo_localization_scored_v2": ["host"],
        "raw_repo_comparators_v1": ["host", "mini", "locator", "session"],
        "raw_repo_handoff_scored_v1": ["workflow"],
        "mini_swe_capped_v1": ["configuration", "runtime"],
        "raw_repo_handoff_score_recovery_v1": ["score_adapter", "scorer", "syntax_proof", "syntax_witness"]}
    for module, names in modules.items():
        code_files += [("analysis/" + module + "/" + name + ".py",
                        "implementation/analysis/" + module + "/" + name + ".py") for name in names]
    exact_copies = []
    for source_name, release_name in code_files:
        raw = raw_source(source_name)
        assert all(marker not in raw for marker in [b"/Data/", b"/home/"])
        binding = rule["method_bindings"].get(source_name)
        binding_record = exp + "selection_rule.json"
        if binding is None:
            binding = launch["bindings"].get(source_name)
            binding_record = exp + "launch_manifest.json"
        assert binding == sha(raw), (source_name, "not matched to original method binding")
        target = out / release_name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("wb") as handle:
            handle.write(raw)
        record = {"release_path": release_name, "release_sha256": sha(raw), "source_paths": [source_name],
                  "transformation": "BYTE_FOR_BYTE_COPY_FOR_INSPECTION_NOT_A_STANDALONE_EXECUTABLE",
                  "historical_binding_record": binding_record, "historical_binding_sha256": binding}
        release_records.append(record)
        exact_copies.append(record)
    excerpts = [("analysis/raw_repo_confirmation_v1/scoring.py", 237, 316, "score_equivalence_key.py.txt"),
                ("analysis/raw_repo_capacity_comparison_v1/scoring.py", 244, 279, "capacity_score_seal_wrapper.py.txt")]
    for source_name, first, after, name in excerpts:
        raw = raw_source(source_name)
        binding = plan["sources"][source_name]
        assert binding == sha(raw)
        excerpt = b"".join(raw.splitlines(keepends=True)[first - 1:after - 1])
        target = out / "implementation" / name
        with target.open("wb") as handle:
            handle.write(excerpt)
        release_records.append({"release_path": "implementation/" + name, "release_sha256": sha(excerpt),
            "source_paths": [source_name], "transformation": "VERBATIM_SOURCE_LINE_EXCERPT",
            "source_first_line": first, "source_last_line": after - 1,
            "historical_binding_record": exp + "scoring_plan.json", "historical_binding_sha256": binding})
    checks["code"] = {"byte_exact_files": len(exact_copies), "all_exact_copies_match_historical_binding": True,
                      "verbatim_excerpts": len(excerpts), "experiment_code_executed": False}
    write_json("implementation/extraction_checks.json", checks, [],
               "New structural/export checks, not model, benchmark, or experimental validation.")
    provenance = {"kind": "NEW_RELEASE_PROVENANCE_INDEX", "exported_utc": exported,
        "scope": "Selected existing records and implementation for audit, not complete reproduction or preregistration.",
        "source_records": list(source_records.values()), "release_files": release_records,
        "checks": checks}
    target = out / "implementation/PROVENANCE.json"
    with target.open("w") as handle:
        json.dump(clean(provenance), handle, indent=2)
        handle.write("\n")
    print(json.dumps({"exported_data_and_source_files": len(release_records) + 1, "checks": checks}))


if __name__ == "__main__":
    main()
