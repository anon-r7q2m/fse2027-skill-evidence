# What Does PASS Mean? Anonymous review artifact

This artifact accompanies **What Does PASS Mean? Evidence and Decisions in
Coding Agent Workflows**. It contains an unchanged generated SEARCH/REPLACE package,
its public parser replay, three bounded source-slice replay bundles, and
public audit reports. It also includes the fully released sixteen-task
comparison matrix and analysis. Finite executable cases support the stated observations;
they do not prove full-domain equivalence or reproduce benchmark scores.

## Run

The four entries below use CPython with its standard library. No network,
model service, Git service, database or container is needed. From this directory:

```sh
python3 -B reproduce_public.py
python3 -I -B principles/gp/replay.py
python3 -I -B principles/feedback/replay.py
python3 -I -B principles/pro/replay.py --output pro-replay-check.json
```

The parser and GP entries print their results. The feedback entry rewrites
`principles/feedback/result.json` and its generated `README.md`; replay a copy
if retaining the distributed record matters. The Pro command writes the
specified result file. `distribution-verification.json` records successful
runs of all four entries from a detached temporary copy. This packaging check
does not add experimental conditions or samples.

| Entry | What it executes | Evidence boundary |
|---|---|---|
| Public parser | 14 parser samples and four pinned donor-semantics examples | The unchanged package's parser and pure reference functions, without host or grading execution |
| GP | Six fixed conditions using four exact original selection functions | Recorded selection keys and receipts enter at a disclosed boundary; historical preservation checks and whole-file syntax are not rerun |
| Feedback | Eight conditions using original helper and caller methods on Base, B and V | Explicit ORM/database mocks; no complete Django execution; an equivalent direct-helper control detects the same regression |
| Pro | Six synthetic conditions using pinned scheduling, cache and reduction code | Constructed worker results and completion order; extra cache-owner fixture information; no real grading or concurrency race |

The 20 principles conditions reuse objects and synthetic controls. They are
not 20 independent tasks, a pooled detection rate or a benchmark improvement.
The planned GP factorial was cancelled before execution because scope use
could not be separated from a syntax gate. Feedback retains its initial
runner/result and one observer correction. These limitations and the normal
controls are part of the result, not omitted failed experiments.

## Additional source-path checks

`source_paths/` contains two fixed native paths and eight additional conditions,
with pre-execution protocols, all original results, exact public source and MIT
notices. SWE-agent path exposure is unknown and OpenHands was previously exposed;
these are not independent unseen-host validations. The source-path replay uses
an existing Python environment with Jinja2 and PyYAML (recorded: Python 3.12.3,
Jinja2 3.1.2, PyYAML 6.0.1):

```sh
python3 -B source_paths/replay.py --output source-path-replay-check
```

The output directory must have no existing per-host result files. See
[source-path scope and execution](source_paths/README.md) and the
[complete eight-condition report](source_paths/REPORT.md). Native methods are
executed with explicit runtime/model/state mocks, not a running agent service.

## Reading guide

Start with [claim-level evidence and coverage](CLAIM_EVIDENCE.md). New dated
records for all nine catalog classes and the six explanatory families are
under `records/`; public receipts are distinguished from executable replays.


- [Completed diagnostics](principles/REPORT.md), [fixed-case analysis](principles/case_analysis.md), and [study protocol](principles/study_protocol.json).
- Group-specific source boundaries, protocols and results: [GP](principles/gp/README.md), [feedback](principles/feedback/README.md), [Pro](principles/pro/README.md).
- [Historical evidence guide](EVIDENCE.md), [audit guide](audit/README.md), and retrospective evidence maps under `study/`.
- [Released capacity comparison](capacity/README.md): all 192 logical outcomes, original analysis, frozen design and execution aggregates. This is released benchmark data, separate from the 20 offline conditions; official grading is not rerun by the bundle.
- [Installed policies and original identity records](capacity/METHODS.md): task-selection inputs, fixed implementation definitions, stop records, and the 192-to-108 submission/grader mapping. `python3 -B capacity/summarize_outcomes.py` recomputes counts and exact paired tests from the released CSV, without a solver or grader.
- Minimal historical decision chains: [GP](witnesses/gp/README.md) and [feedback](witnesses/feedback/README.md). These supplement the local replay with original-record extracts; saved branch inputs are distinguished from the unbundled full provider-request comparison.
- Historical GP, feedback and PQ reports are under `principles/evidence/`. References from those reports into the research repository identify original evidence; this bundle does not reproduce every referenced study.

## Preserved code and provenance

The original `provenance.json` describes eleven unchanged files in the public
parser replay. All five files of generated package
`b276b81cbd303ae186cabb004855362d3c1f325649234baf9e10c7e66f623f77`
are retained. The declared parser adaptations include full-file nonempty
intervals, declared-path mapping, bounded UTF-8 sizes and a nonempty Python-file
domain. Four donor examples exercise repeated matches, reverse application,
unmatched-command skipping and boundary newlines. Downstream admission is
separate. The original record used CPython 3.13.14; the local candidate was
checked with CPython 3.13.11. Parsing the unchanged donor source emits a legacy
escape-sequence `SyntaxWarning` without changing the result.

Do not run `analysis/search_replace_source_v1.py` as a program: its historical
entry writes a one-time calibration result. The public replay loads only its
read-only reference definitions. New source slices and their provenance are
contained in the corresponding `principles/` group, with project-authored
wrappers and policy interventions distinguished from original functions.

## Release status

The authors approved anonymous publication of this curated review package on
September 28, 2026. Project-authored code and documents in this package are
provided under [MIT](LICENSE). Third-party material retains its own included
licenses and copyright notices; see [THIRD_PARTY.md](THIRD_PARTY.md). This grant
does not license the full research repository, benchmark datasets or restricted
records. The public review repository is
[anon-r7q2m/fse2027-skill-evidence](https://github.com/anon-r7q2m/fse2027-skill-evidence).

Public audit summaries describe scoped static triage across six benchmarks;
they neither release restricted individual annotations nor establish formal
blacklist authority. The bundle excludes complete model trajectories, independent
evaluator cases, private task annotations and account material. It is not a
full-host, full-database or official-score reproduction.
