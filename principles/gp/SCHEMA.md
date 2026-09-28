# GP bundle schema and interpretation

All machine-readable files are UTF-8 JSON objects with a `schema_version`.
The fixed identifiers and source paths are provenance, not instructions to run
the original host or tests.

- `protocol.json` (`agent2skill.principles.gp_protocol.v1`) fixes six fixture
  conditions, source identities, exact source functions, expected outcomes,
  the new exclusion rule, the cancelled factorial and the one-fix-pass limit.
- `inputs.json` (`agent2skill.principles.gp_inputs.v1`) holds only the historical
  ranker state/pool, original selection, the public syntax-error observation,
  exact generated suffixes with source-content identities, and minimal recorded
  projection/preservation summaries. It contains no official grading output.
- `provenance.json` (`agent2skill.principles.gp_provenance.v1`) binds original
  source bytes and bundle input bytes and records function ranges and exact
  segment identities. `implementation_fix_passes` counts implementation fixes
  after fixture execution; the initial value is zero.
- `replay_result.json` (`agent2skill.principles.gp_replay_result.v1`) retains all
  six conditions. Each condition has an identifier, historical/synthetic kind,
  selected snapshot (string or null), source effect, exclusions, abstention,
  per-candidate syntax labels, projection evidence level, expected-observation
  checks, and their conjunction `expectations_met`.

`supported` concerns the declared finite syntax input only. `violated` requires
a concrete recorded or locally reproduced syntax error. `unassessed` means the
available input/evidence does not establish the property, including size-limited
or absent input. `not_applicable` records that the historical policy did not
promise the later hard syntax guarantee. No label is a task-validity disposition.

`official_outcome=null` and `benchmark_effect=NOT_MEASURED` are intentional: no
new official outcome is measured or attached to a locally changed selection.
Recorded preservation evidence is marked `RECORDED_ORIGINAL_EXECUTION_NOT_RERUN`.
The generated suffix illustration and the full original candidate have different
scope. A successful suffix parse does not certify the full candidate.

`expectations_met` verifies the fixture's announced local observation, not an
experimental benefit. The global `COMPLETED` status means all fixed checks
matched; a mismatch is retained as
`COMPLETED_WITH_COUNTEREXAMPLE_OR_IMPLEMENTATION_FAILURE`, with nonzero exit.
Normal-control rejection and abstention counts refer only to the named controls,
never a pooled empirical rate over real tasks.
