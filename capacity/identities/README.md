# Task, submission, grader, and recorded outcome identities

These new projections connect existing records; they are not a new score release or rerun. See [METHODS.md](../METHODS.md) and [PROVENANCE.json](../implementation/PROVENANCE.json) for source files, source-byte hashes, and transformations.

| File | Contents |
|---|---|
| `policy_outcomes.csv` | 192 logical rows: cell, task, policy, repeat, base, submitted final tree, representative score cell, grader ID, scope hash, and original reward. |
| `task_contracts.json` | 16 task/base contracts with original task-file modes/hashes, grader ID and image identities; no test contents. |
| `grader_sources.json` | Original scoring-source map used in the equivalence key. |
| `score_scopes.json` | 108 original representative scopes, selected-capture identities, existing consumption records, and representative rewards. Shared task/source maps are referenced rather than repeated. |
| `reward_commit_records.json` | 108 existing commit-marker records and their source paths. No evaluation log, request, response, or private test body. |
| `primary_stage_dispositions.json` | 128 primary path observations for discovery/localization, pre-edit routing, editing stop status/reason, solver terminal status, and stage request counts. |

Join `policy_outcomes.csv.score_cell` to `score_scopes.json.rows[].cell_id`. Join `task_contract_id` to `task_contracts.json.tasks`. All scopes use `grader_sources.json`. The equivalence key includes task, base, final tree, task-file identities and scoring-source identities. It does not group by reward. The CSV's `scored_patch_sha256` identifies the score representative's patch, not every member's own capture. `shared_score=True` denotes reuse of a representative score.

Scope-file byte digests remain separate from reward-commit object self-digests. `reward_commit_artifact_sha256` links to the commit's `artifact_sha256`; the latter hashes the object without that field, using sorted compact UTF-8 JSON plus a trailing newline. The commit's per-file `commitment_sha256` fields retain their original semantics; no key was read or released. A hash by itself cannot let a public reader recreate an omitted original file.

The primary stop table keeps distinct stage observations. Capacity reasons describe a prospective route decision; they are not task-failure labels. Pipeline stop reasons exported from the original policy summaries are `NO_SELECTION`, `OUTSIDE_P_FILE_DOMAIN`, or null. A null does not mean a successful repair. Terminal statuses do not replace the separate benchmark reward. No failure stage or free-text cause was invented when a field was absent.

The original consumed records explicitly limit replay/restoration guarantees; those fields are retained. This release verifies record identity and joins, not complete repository restoration or independent score execution.

The frozen grader variant permits a verified candidate-syntax exception, described in [METHODS.md](../METHODS.md). The later [grading witnesses](../score_witnesses/README.md) add a privacy-scoped projection of all 108 original reports: the exception was applied zero times. The original identity records here remain unchanged. Do not infer classification from zero reward. The new projection also retains all sixteen primary LnPn first-stop records; submitted patch text and raw test logs remain withheld.
