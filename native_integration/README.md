# Complete saved-team integration extension

This package records one fixed nine-cell extension of the already known AutoGen
`a21` source-filter serialization mechanism. It exercises a complete native team
configuration: construction, full `dump_component`, JSON-file write/read,
`BaseGroupChat.load_component`, actual local report generation, and a native
reviewer tool that independently checks the generated report against its CSV.
It adds integration depth and an application consequence, not another defect
discovery or a benchmark score. The earlier prospective study remains closed.

**The frozen global prerequisite flag is false.** All nine parent receipts report
complete collection and supported per-cell behavior predictions. However, the
unrestricted U scenario fails a separate frozen configuration assertion:
`patched_exports_declared_sources=false`, so `CONFIG_EQUIVALENCE.json` records
U as `MISMATCH` and `CLOSED.json` retains
`comparison_prerequisites_met=false`. The restricted T/C configurations are
`MATCH`. Do not replace these different dispositions with a blanket PASS.
No runner fix, new input, receipt rewrite or target rerun followed this result.

## Recorded observations

Each scenario ran once under D (direct original team), R (original export/load),
and P (new construction/export/load using the unchanged earlier a21 patch).
P regenerates the configuration with the patched serializer; it cannot recover
reviewer intent from an old JSON file that already omitted the restriction.
These are fresh configuration lifecycles, not conversation checkpoint/resume.

| Scenario | Report in all three procedures | D | R | P |
| --- | --- | --- | --- | --- |
| T: required reviewer, signed input, marker in an input note | Incorrect: two rows / 1950 cents; required three rows / 1750 | Review tool produces and delivers a discrepancy finding | Executor marker stops the team before reviewer invocation; finding absent | Review tool produces and delivers a discrepancy finding |
| C: required reviewer, positive input, no marker in notes | Correct: three rows / 2150 cents | Clean finding delivered | Clean finding delivered | Clean finding delivered |
| U: unrestricted stopping, exact T input | Same incorrect two-row / 1950-cent report | Stops at executor; review optional | Same | Same behavior; frozen configuration assertion fails |

The report defect is a deliberately planted positive-only row filter, not a new
framework defect or a model-generated mistake. All three T/U procedures leave
the report incorrect. The outcome is preservation or loss of the configured
review duty, not report repair or successful task completion. C changes both
the sign and marker condition; it is a normal-behavior control, not a one-variable
T/C causal comparison.

For each invoked review, the native provider actually receives the executor's
unchanged report-bearing message. Its finite response requests one
`review_csv_report` tool call and supplies no verdict. The tool reads the real
files, calculates the signed total, writes `review.json`, and returns that finding.
The collected result is linked to the same request, tool result, summary, final
`TaskResult`, and actual termination input. The first matched reviewer message
is `ToolCallExecutionEvent`, preceding `ToolCallSummaryMessage`; the full delta
is retained. R/T is skipped required review, not erroneous approval.

For U, the declared source restriction is `None`. Native component dumping omits
that null configuration field. The frozen assertion required the field to be
explicitly present, so it fails even though the recorded loaded condition is
unrestricted and all three runtime behaviors match the legal U prediction.
This later explanation does not turn the original assertion into a pass. The
global gate remains false; use the independent adjudication for the permitted
scope of T/C evidence and U runtime observations.

## Inspect the evidence

- [Protocol and predictions](experiments/native_decision_integration_v1/PROTOCOL.md)
  and [fixed scenarios](experiments/native_decision_integration_v1/scenarios.json).
- [Unchanged scientific runner](analysis/native_decision_integration_v1.py) and
  [unchanged a21 patch](patches/a21.patch).
- [Raw closure](observed/CLOSED.json) and
  [full configuration comparisons](observed/CONFIG_EQUIVALENCE.json).
- [Independent scientific adjudication](adjudication/ADJUDICATION.md) and
  [machine-readable checks](adjudication/ADJUDICATION.json):
  `SCOPED_T_C_SUPPORT_WITH_UNMET_FROZEN_GLOBAL_PREREQUISITE`, with no override
  of the original global gate.
- `observed/01_T_direct_original/` through `observed/09_U_reloaded_patched/`:
  every original observation, parent receipt, launch record, stdout and stderr.
- `observed/application/`: actual input, report, review finding when present,
  and saved team JSON when applicable. The same bytes are represented in each
  observation's artifact fields, subject to the disclosed path anonymization.
- `historical/freeze.json` and `historical/paths.json`: anonymized views of the
  original pre-execution seal and path identities, not runnable reproduction
  configuration.
- [Publication transformations](PUBLICATION_TRANSFORMS.json): original and
  published file digests, with separate embedded-artifact text digests.
- [Reused upstream dependencies](UPSTREAM_DEPENDENCIES.json): exact sibling
  archive, source-manifest, dependency and license identities.

## Anonymization and integrity

Only author-local root prefixes in copied evidence are replaced:
`/RESEARCH_ROOT` identifies the research repository, `/STUDY_ROOT` the prior
prospective workspace, and `/INTEGRATION_ROOT` this extension's execution tree.
Every copied file has both its original and published SHA-256 recorded. The
scientific runner, both CSV inputs, generator, scenario declaration and a21
patch are byte-identical to the executed versions. Protocol path references and
records containing local paths are explicitly identified as derived copies.

Existing hashes inside historical records are **not rewritten**. They bind the
original execution bytes, including original `team.json` paths. Where an embedded
artifact's text contains an anonymized path, `PUBLICATION_TRANSFORMS.json` records
its original recorded hash and the published text's hash separately. Result
booleans, failure flags, timestamps, message data, tool findings and numeric
outcomes retain their historical values. The original seal must not be used to
verify the modified public path strings as if they were original bytes.

This extension contains only public inputs and trusted study code. It releases
no private benchmark annotations, credentials, or paid-provider requests. It
contains no manuscript grading, acceptance target or paper-review opinions.

## Reproduce as a new user run

Use Linux, CPython 3.12, and the standard `patch` utility. This extension reuses
the existing `prospective/upstream/autogen.tar.gz`, pinned to
`027ecf0a379bcc1d09956d46d12d44a3ad9cee14`, and the sibling prospective dependency
requirements. Do not invoke the older 42-cell matrix to prepare this extension.
If that public environment is not already prepared, use its preparation command
from the artifact root:

```sh
python3.12 prospective/prepare.py --workspace /tmp/native-dependencies --install
```

That optional dependency setup accesses PyPI; the nine-cell target execution uses
no model service or network task command. It also prepares the sibling
smolagents source because the existing shared helper serves both earlier
frameworks. The integration runner only selects AutoGen. No installation or
target replay was performed to assemble this package.

Prepare an independent seal using the unchanged public runner and configurable
paths:

```sh
python3.12 native_integration/prepare.py \
  --source /tmp/native-dependencies/sources/autogen \
  --python /tmp/native-dependencies/venv/bin/python \
  --workspace /tmp/native-integration-reproduction
```

The helper verifies the complete pinned source and published input hashes,
creates a new path configuration and seal, and prints the exact command below.
It imports no AutoGen component and executes no target behavior. It does not
reuse the historical seal or change the scientific runner's U assertion.

```sh
/tmp/native-dependencies/venv/bin/python -B \
  native_integration/analysis/native_decision_integration_v1.py \
  --paths /tmp/native-integration-reproduction/paths.json \
  --freeze /tmp/native-integration-reproduction/freeze.json
```

The new workspace must not exist before preparation; its study/results
subdirectories must not exist before execution. The runner attempts the same
nine cells once, retaining failures and timeouts. Per-cell limits are 5 seconds
for the local command, 60 seconds for the native workflow, an 80-second worker
alarm and 90 seconds for the outer process group. No fixture changes or hidden
retries are permitted within a run. Keep new outputs separate from `observed/`.
A faithful reproduction should retain the U metadata mismatch rather than
silently treating it as repaired. Missing dependencies or observations are
inconclusive, never evidence of the predicted mechanism.

The preparation helper is new publication support code, validated statically;
it was not used for the historical execution. Original local execution facts
remain the sole original result record. This study does not measure live-model
competence, deployment prevalence, new-defect yield, guidance superiority,
aggregate benchmark gain or general serialization correctness.

Project-authored files use the artifact's MIT license. AutoGen code remains MIT
and its documentation remains CC BY 4.0; the reused archive and sibling
`prospective/upstream/autogen-LICENSE*` retain the upstream notices.
