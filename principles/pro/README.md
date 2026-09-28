# Pinned Pro evaluator: six-condition offline replay

This is a synthetic diagnostic replay of the public standalone evaluator at
`ca10a60a5fcae51e6948ffe1485d4153d421e6c5`. It executes the original filtering,
result assignment, cache lookup, and final mean. It does **not** evaluate a real
task, patch, container, model, or leaderboard submission.

The first execution matched all six frozen expectations. The three
contract-consistent controls were retained. These counts describe this fixture
set, not an estimated detection rate, leaderboard error rate, or benchmark
validity result. No ordinary implementation-fix pass was used.

## Standalone execution

Copy this entire directory anywhere, then run with CPython and no dependencies:

```sh
python3 -B replay.py --output replay-result.json
```

Replay uses temporary local files and makes no network calls. It neither imports
the repository nor imports the donor's optional Docker, Modal, pandas or tqdm
packages. Each fixture invokes the original orchestration once. The first run
used `/tmp` as its working directory while reading this bundle at its repository
location. A separate detached-copy distribution check is left to the integrating
agent; if performed, it is packaging verification, not another experimental
sample.

`result.json` retains the first execution. `inputs.json` is the exact frozen
protocol, including expected results and fixed completion order. The optional
output argument can write a new replay record without modifying either file.

## What is original and what is mocked

`source/swe_bench_pro_eval.py` contains unchanged public source bytes.
`source/original_slices.py` contains verbatim source ranges:

- `prepare_run`, lines 165–175, complete function;
- `eval_with_docker`, lines 358–364, the four original statements ending with
  the existing-cache return;
- `main`, lines 469–571, complete function, including its result dictionary,
  test-result interpretation, running means and final printed mean.

The builder verifies AST equality of the selected functions/prefix against the
pinned full source. Source and protocol bindings are checked before replay.
No authored replacement reducer supplies the reported original means: replay
parses the original `Overall accuracy` print and reads its original output JSON.

Explicit adapters replace only these boundaries:

1. A small input-frame adapter implements the operations needed for the unique
   synthetic JSONL rows. It is not a general pandas implementation.
2. A deterministic executor records submitted calls; `as_completed` returns the
   frozen order. Future results invoke the worker one at a time. There are no
   threads and no measured filesystem or scheduling race.
3. The original Docker cache prefix runs with a non-null inert SDK sentinel.
   A cache hit returns its real JSON through the original branch. An uncached
   call falls through to a worker that returns constructed test observations.
   No Docker API or later worker code executes.
4. A progress adapter records the strings computed by the original code.

The `docker` sentinel only allows entry through the original SDK-presence check;
it does not simulate container behavior. Original command-line parsing and
module-level imports are not executed. The original `eval` of test-name lists
receives fixed synthetic string literals created by this harness.

## Frozen conditions and observed decisions

All means below are synthetic worker-output means. A and B are invented IDs;
their patch strings are labels, not executable repairs.

| Fixture | Original result dictionary / mean | Fresh workers / cache hits | Proposed report consumer |
|---|---|---:|---|
| Missing B, claim full A+B | A=true / 1.0 | 1 / 0 | Abstain from the claimed full-population mean |
| Same input, explicit subset A | A=true / 1.0 | 1 / 0 | Publish the original subset mean 1.0 |
| Duplicate A, controlled PASS then FAIL | A=false / 0.0 | 2 / 0 | Abstain from a unique-submission report |
| Unique A+B, PASS then FAIL | A=true, B=false / 0.5 | 2 / 0 | Publish original full-population mean 0.5 |
| Same UID/prefix, cached patch differs | A=true / 1.0 | 0 / 1 | Request recomputation; publish no bound-input mean |
| Same UID/prefix, cached patch matches | A=true / 1.0 | 0 / 1 | Publish original mean 1.0 |

Every value and decision matched its frozen expected field in `result.json`.
The duplicate's original progress changes from 100% to 0% because the second
controlled completion replaces the first result at the same key. This
demonstrates dictionary overwrite under one specified order. It does not
measure real thread races or claim that the opposite order was tested.

The missing-ID pair deliberately keeps the evaluator input unchanged: the
same literal subset mean can support an explicitly scoped subset report while
not supporting a claim about the complete A+B population. Missing B is not
assigned a false outcome, and no new mean is calculated.

## The proposed consumer is a separate intervention

`proposed_report_consumer` is authored harness code, not an original function
or a submitted upstream fix. It is an actual publication decision that retains
the original mean only when the fixture's declared population, uniqueness and
known cache binding support that report. It otherwise abstains or requests
recomputation. These checks are ordinary local contract checks; this replay does
not establish an advantage over equivalent simple validation rules.

Cache ownership is **additional observer information supplied by the synthetic
fixture**. The legacy output JSON itself contains no patch binding. Its owner
must not be inferred from PASS, UID, prefix or file existence in a real run.
For the mismatch fixture, the unused fresh-worker observation is constructed;
it is not obtained by recomputation and is not reported as a new result.
Recomputation is requested but not executed. The original cached 1.0 remains in
the observation record and is never converted into a zero score.

Only patch identity is varied in this cache pair. Task, evaluator, parser,
container, runtime, and environment identity changes are not exercised here.
The matching control does not establish that the real cache has a complete
identity contract.

## Interpretation and limits

This is an instance check of consumer-relative evidence scope: a valid subset
calculation is not automatically a full-population score, and an output file
does not establish which changed input it grades. It also retains legitimate
subset and cache uses rather than rejecting all incomplete evidence.

The six fixtures are exposed, deliberately constructed cases. They establish
neither general prevention efficacy nor a new theory. They do not reproduce
grading accuracy, patch application, parser integration, Docker behavior, a live
leaderboard's intake policy, real cache-error frequency, task invalidity,
blacklist authority, or six-benchmark audit judgments. The audit's 4,989 units
are unrelated to the six-fixture denominator.

## Provenance, licensing, and repository build

`provenance.json` gives the immutable public URL, source hash, exact line ranges,
AST checks and protocol hash. Donor source and selected statements are MIT
licensed, Copyright (c) 2026 Scale AI, Inc; the unchanged notice is in
`source/LICENSE`. That donor license does not automatically license the
Agent2Skill-authored harness and protocol. Project-owner release licensing is
separate; no upload or publication was performed by this slice.

The repository-only preparation command copies the already frozen protocol,
extracts exact source statements and copies the replay program:

```sh
python3 -B analysis/skill_reuse_principles_v1/pro_replay.py --prepare
```

Preparation does not run the fixtures. The public pinned source and license
were acquired before fixture execution, after scoped local-source lookup found
no copy. `validation.json` records this slice's offline execution and lint;
detached-copy verification remains explicitly pending in that local record.
