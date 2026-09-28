# SWE-bench Pro Evaluator Semantics Follow-up — 2026-08-31

Status: `PINNED_STANDALONE_SEMANTICS_FROZEN_LIVE_CONTRACT_TBD`

This follow-up freezes the observable control-flow semantics of the official
standalone evaluator at commit
`ca10a60a5fcae51e6948ffe1485d4153d421e6c5`. It does not infer the live
leaderboard's intake, retry, rescore, or trial-aggregation policy.

## Source verification

- Evaluator URL:
  `https://raw.githubusercontent.com/scaleapi/SWE-bench_Pro-os/ca10a60a5fcae51e6948ffe1485d4153d421e6c5/swe_bench_pro_eval.py`
- Evaluator SHA-256:
  `bb5d4c5486be296e464e695df3747064aaa3bb197394bc6d39980634afec2034`
- Image helper URL:
  `https://raw.githubusercontent.com/scaleapi/SWE-bench_Pro-os/ca10a60a5fcae51e6948ffe1485d4153d421e6c5/helper_code/image_uri.py`
- Image helper SHA-256:
  `d1a858866dd2622c0e37986dd7b86698e5ea53546f30901d1bf0d6ba1b97384f`

Both hashes were re-fetched and verified on 2026-08-31.

## Frozen standalone semantics

| Area | Confirmed behavior | Consequence |
|---|---|---|
| Extra predictions | Prediction IDs absent from the supplied raw sample are warned about and removed before scheduling. | Extra IDs do not enter the final denominator. |
| Missing predictions | The evaluator schedules only supplied valid predictions and never inserts absent official tasks as `False`. | Missing official tasks disappear from the standalone mean. |
| Duplicate predictions | Duplicate IDs are not rejected. Futures run concurrently and write results into one dictionary keyed by task ID. | The last completed duplicate overwrites the earlier boolean; the winner is completion-order dependent. |
| Duplicate workspaces | Every run for one task shares the same `output_dir/task_id/workspace`; cache/output names add only `prefix`. | Duplicate jobs can race on workspace files, and equal-prefix jobs also race on cached output and patch snapshots. |
| Cache reuse | With `redo=false`, an existing `task_id/prefix_output.json` is reused without binding the patch, task row, evaluator, parser, run script, image, or runtime configuration. | A stale result can be accepted after an input or environment change. |
| Patch application | The generated shell script has no `set -e` and does not test the return code of `git reset`, `git checkout`, or `git apply`. | Setup, tests, and parsing may continue after patch-application failure. |
| Nonzero entry script | Modal and local-Docker paths log a nonzero entry-script/container status and still attempt to collect and score `output.json`. | Nonzero execution is not a typed terminal failure if parser output exists. |
| Error mapping | Returned `None`, malformed result processing, and caught exceptions become boolean `False`. | Patch failure, evaluator failure, image failure, and some infrastructure failures are conflated with an unresolved task. |
| Binary changes | Recognized binary diff sections are removed before evaluation. | Submitted binary modifications are outside the evaluated patch semantics. |
| Score reducer | Accuracy is `sum(eval_results.values()) / len(eval_results)`. | Weight is equal only over the unique result keys that survive the supplied run, not necessarily all 731 official tasks. |
| Environment identity | The helper produces a Docker Hub `repository:tag`; no digest is consumed. Network blocking and platform selection are optional, and local Docker has no explicit evaluator timeout. | Runtime bytes and platform/network policy are not frozen by this script. |

The empty-valid-prediction case is also not totalized: the final reducer divides
by `len(eval_results)`, which is zero when no valid patch is scheduled.

## Minimal fail-closed repair contract

1. Require exact set equality between submitted IDs and the frozen 731-task
   manifest before any job starts; reject missing, duplicate, and extra IDs.
2. Allocate a unique immutable run directory per submission row and bind every
   cached result to patch hash, task-row hash, evaluator hash, parser/run-script
   hashes, OCI digest, platform, network policy, and runtime configuration.
3. Stop immediately on reset, checkout, patch-apply, setup, test, parser, or
   container failure; do not parse a stale or partial output.
4. Record typed outcomes such as `RESOLVED`, `UNRESOLVED`, `INVALID_SUBMISSION`,
   `EVALUATOR_ERROR`, `INFRA_ERROR`, and `TIMEOUT`; freeze how each state enters
   the public score.
5. Compute the final score against the frozen manifest denominator and publish
   the retry, trial, rescore, and supersession rules separately.

## Remaining boundary

The pinned standalone evaluator semantics are now frozen. A separate follow-up
has resolved all 731 pinned tags to single-image manifest digests, but the live
leaderboard contract, end-to-end replay, and measured false-accept/false-reject
rates remain `TBD`. No task validity, strict exclusion, blacklist rate, BVC, or
model-performance claim follows from this artifact.
