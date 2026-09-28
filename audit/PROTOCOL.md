# FSE-Focused 7-Benchmark Hard Audit Protocol v1

Status: **FROZEN FOR INTERNAL EXECUTION**  
Date: 2026-08-03  
Scope: public, deterministic benchmark audit; no benchmark-solving runs
Audit scope ID: `agent2skill.fse_hard_audit.v1`

## Objective

For each FSE-relevant coding/software-engineering benchmark, establish what can be verified without treating an LLM
opinion as ground truth: the exact release and task universe, scoring atoms and
weights, evaluator and environment identity, required assets, known public
errata, deterministic integrity risks, and the remaining evidence needed for a
numeric Benchmark Validity Ceiling (BVC).

This audit is forward-only. It does not modify the frozen v1 candidate ledger
or the SWE-bench Verified M2 package.

The scope deliberately prioritizes seven complementary software-engineering
constructs: terminal engineering, curated/hard/multimodal repository repair,
feature development, multilingual issue resolution, and real-world freelance
engineering. General web, desktop, mobile, knowledge, and customer-service
agent benchmarks are excluded from this paper-facing audit.

## Benchmarks

1. `terminal_bench_2` — Terminal-Bench 2.0
2. `swe_bench_verified` — SWE-bench Verified
3. `swe_bench_pro` — SWE-bench Pro
4. `swe_bench_multimodal` — SWE-bench Multimodal
5. `featurebench` — FeatureBench
6. `multi_swe_bench` — Multi-SWE-bench
7. `swe_lancer` — SWE-Lancer

## Three-agent workflow

Each benchmark receives three logically separate roles:

1. **Primary analyst** — gathers official evidence and performs deterministic
   checks. Writes `benchmarks/<id>/primary.md` and
   `benchmarks/<id>/sources.jsonl`.
2. **Review agent** — reads the primary report, independently rechecks its most
   important sources and every numeric claim, searches for omissions and
   overclaims, and writes `benchmarks/<id>/review.md`. It must not silently edit
   the primary report.
3. **Final adjudicator** — reads both reports, resolves every disagreement, and
   writes `benchmarks/<id>/decision.md` plus
   `benchmarks/<id>/decision.json`. It may accept, narrow, or reject a claim,
   but may not invent a replacement fact.

The final adjudicator's authority is limited to the internal hard-audit state.
It cannot alone authorize a public blacklist or a task-level strict exclusion.

## Required audit dimensions

Every primary and final report must cover all dimensions below.

1. **Identity and release** — official name, repository/dataset, release/tag or
   commit, split, snapshot date, and supersession policy.
2. **Task universe** — task count, task IDs or atom identities, exclusions made
   by the official release, duplicates, and whether the denominator is frozen.
3. **Scoring** — scoring atom, per-atom maximum, weights, aggregation, partial
   credit, trial aggregation, and leaderboard normalization.
4. **Evaluator** — evaluator implementation and revision, oracle/reference
   dependencies, false-accept/false-reject risks, and replay readiness.
5. **Environment and assets** — images, websites, VMs, containers, credentials,
   external services, mutable state, and availability.
6. **Known quality evidence** — official errata, public papers/issues, existing
   candidate annotations, and deterministic counterexamples.
7. **Exposure and contamination** — public task visibility and known leakage;
   record separately from task quality.
8. **Current ceiling readiness** — whether a scoring manifest and task validity
   census are sufficient for `EXACT`, `INTERVAL`, or `TBD` BVC.
9. **Repair track** — what can be repaired without changing the construct, and
   what would require a new task identity or benchmark revision.
10. **Next checks** — the smallest evidence-producing actions that close the
    largest remaining uncertainty.

## Evidence policy

- Prefer official repositories, datasets, papers, documentation, release
  notes, and leaderboard definitions. Secondary sources are discovery aids.
- Every accepted numeric claim must cite a source URL/path and a frozen
  revision, retrieval date, or local content hash. If that is impossible, mark
  it `TBD` or `LIVE_UNFROZEN`.
- Recompute counts from task-level data when public data permits; otherwise
  label the value `OFFICIAL_REPORTED`, not independently reproduced.
- A local schema/hash/count check is deterministic evidence. An agent's prose
  judgment is not.
- Do not use solve frequency, model failure, harness incompatibility,
  availability failure, exposure, or one flaky run as task invalidity.
- Public candidate labels remain `CANDIDATE` until the strict evidence gate is
  satisfied. Absence of a known flag is not clearance.
- Private task-level annotations must not be copied into this directory.
- No paid API calls, credential reads, benchmark-solving runs, commits, pushes,
  Feishu updates, or public release are authorized by this protocol.

## Final status vocabulary

Each `decision.json` must use only these statuses:

- `FROZEN` — identity/denominator/contract is hash- or revision-bound.
- `PARTIAL` — material facts are verified, but named gaps remain.
- `LIVE_UNFROZEN` — only a mutable live source currently defines the fact.
- `TBD` — evidence is insufficient.
- `NOT_APPLICABLE` — the dimension does not apply, with a reason.

For BVC readiness:

- `EXACT` requires frozen scoring mass and complete authoritative validity
  adjudication.
- `INTERVAL` requires frozen scoring mass but permits explicitly bounded
  pending validity mass.
- `TBD` applies when scoring mass, denominator, or evidence binding is missing.

## Required final decision structure

`decision.md` must contain:

1. plain-language verdict;
2. accepted facts and evidence;
3. rejected or narrowed primary claims;
4. unresolved disagreements;
5. dimension status table;
6. candidate risks, explicitly not a blacklist;
7. current BVC statement;
8. prioritized next actions.

`decision.json` must contain at least:

```json
{
  "schema_version": "agent2skill.benchmark_hard_audit_decision.v1",
  "audit_scope_id": "agent2skill.fse_hard_audit.v1",
  "protocol_sha256": "<frozen protocol SHA-256>",
  "benchmark_id": "...",
  "as_of": "2026-08-03",
  "primary_report": "primary.md",
  "review_report": "review.md",
  "identity_status": "FROZEN|PARTIAL|LIVE_UNFROZEN|TBD|NOT_APPLICABLE",
  "universe_status": "FROZEN|PARTIAL|LIVE_UNFROZEN|TBD|NOT_APPLICABLE",
  "scoring_status": "FROZEN|PARTIAL|LIVE_UNFROZEN|TBD|NOT_APPLICABLE",
  "evaluator_status": "FROZEN|PARTIAL|LIVE_UNFROZEN|TBD|NOT_APPLICABLE",
  "environment_status": "FROZEN|PARTIAL|LIVE_UNFROZEN|TBD|NOT_APPLICABLE",
  "bvc_readiness": "EXACT|INTERVAL|TBD",
  "strict_blacklist_rate": null,
  "candidate_count": null,
  "candidate_denominator": null,
  "accepted_claims": [],
  "open_blockers": [],
  "next_actions": []
}
```

`strict_blacklist_rate` stays `null` unless a separately authorized strict
task-level adjudication has completed. Zero accepted exclusions with zero
review coverage is never reported as `0%`.
