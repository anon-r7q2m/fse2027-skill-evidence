# GP: bounded local selection replay

This directory is self-contained. With CPython 3.10 or later, run:

```sh
python3 -B replay.py
```

The default command reads only files next to this script and prints JSON. It
does not invoke a model, subprocess, network, container, benchmark or scorer.
`python3 -B replay.py replay --output replay_result.json` optionally writes a
new report. The separate `build` subcommand is provenance extraction from the
research checkout; it is not required for public replay.

`original_selection_slice.py` contains four exact functions from the recorded
P package: candidate filtering by comparable preservation receipts, minimum
failure ranking, nonempty RAW/PY keys, voting and first-occurrence tie-break.
The recorded keys and receipts enter at that function boundary. Normalization,
snapshot transport, G execution and the full agent host are not rerun.

The historical pair reproduces original selection and applies a NEW exclusion
of the candidate with an already recorded public SyntaxError. The later
candidate's whole-file syntax remains unassessed in this small bundle. A
separate syntax illustration parses each exact generated suffix under the
declared synthetic class wrapper; that does not execute or certify a full
Django file. The original preservation PASS and projected-tree equality are
recorded evidence, not new test results. No task is newly graded.

Four additional conditions are explicitly synthetic: legitimate test-only
edits, a safe projection, unknown syntax after a size limit, and abstention
when all candidates have confirmed syntax errors. Synthetic normalization keys
are direct inputs at the ranker boundary, not newly generated donor outputs.
The new hard exclusion rejects only confirmed syntax failures; unknown remains
eligible for soft ranking with an unassessed label. This is not a syntax
correctness certificate. No empty-pool fallback may bypass a confirmed error.

The proposed scope-by-syntax factorial was cancelled before execution: scope
metadata has no distinct consumer action, and a syntax-based scope rule would
duplicate the syntax exclusion. This replay does not establish extra value for
generic scope tracking, benchmark gain or predictive generalization.

The protocol fixes six conditions. All are retained whatever their outcomes.
Source provenance and the output schema distinguish original records, exact
source replay, a new local policy, and synthetic controls. See provenance.json,
protocol.json, and THIRD_PARTY.md. No full trajectory, hidden test, private
annotation, unreleased score or credential is bundled.
