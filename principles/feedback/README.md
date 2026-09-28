# Feedback source-slice replay

This is an offline, exposed-case diagnostic with eight fixture conditions, not eight tasks.
Exact original method bodies are selected by AST and run with explicit mock boundaries.
No full Django module, ORM query, database, model, container, or official scorer is executed.

Run from any directory after copying this entire folder: `python3 /path/to/feedback/replay.py`.
Python 3.12+ standard library only; replay performs no network access and requires no repository.

| Condition | Two controls | Original issue proxy | Frozen observations match |
|---|---|---|---|
| Base_original | PASS | FAIL | True |
| Base_production_path | PASS | not run | True |
| B_original | PASS | FAIL | True |
| B_production_path | PASS | not run | True |
| V_original | PASS | PASS | True |
| V_production_path | FAIL | not run | True |
| V_equivalent_helper | FAIL | not run | True |
| B_legal_lookup_adaptation | PASS | not run | True |

The original checker's numeric-string issue assertion is a faulty proxy observation, not ground truth.
Original checker conditions contain three assertions: one proxy and exactly two controls.
The three preservation policies are compared on their two controls only.
The normal/authorized-adaptation condition has two checks of B's scalar has-key SQL paths.
Passing those paths does not establish B's complete issue correctness.

One implementation correction is recorded in implementation_fix.json. The initial result and replay are retained. It corrects a reducer comparing a helper's root-free substring against the final SQL-path parameter; source, assertions, fixtures and expected observations remain unchanged.

Production-path controls and equally small equivalent direct-helper controls detect the same V array-index regression; the original two direct controls miss it. The real path supplies the relevant input transformation, not a unique testing capability. The B scalar lookup adaptation is retained on two exercised paths.

Unknown assertions: 0. False rejections among five nonregressing obligation conditions: 0; those conditions reuse Base/B and are not independent observations.

## Source and boundaries

Django base revision: `859a87d873ce7152af73ab851653b4e1c3ffea4c`. `protocol.json` records original source hashes, exact segment locations, recorded B/V patch identities, public documentation, frozen expected observations and file hashes.
`source/*.py` contains only compile_json_path; KeyTransform constructor, preprocess_lhs, as_mysql; and HasKeyLookup as_sql/as_mysql with its original logical_operator. Class headers/method bodies retain original source bytes.
Transform construction, column compilation, parent lookup processing and a MySQL vendor object are explicitly mocked. The real KeyTransform string conversion, original preprocess method and original as_mysql call into the original helper execute. Full ORM resolution and database semantics remain unassessed.
The original generated checker is retained byte-for-byte; only its inspected Behavior class is executed with compile_json_path bound to each source slice. Its Django import is not executed.

## Scope and licensing

This is retrospective diagnostic validation, not held-out confirmation, a population rate, or evidence of benchmark gain. SQLite/Oracle execution, every lookup variant, and complete task correctness remain unassessed.
Django excerpts and recorded modifications retain the BSD-3-Clause notice in LICENSE-Django.txt. The new replay and metadata are project-author material; this package does not infer a repository-wide release license. Public release permissions remain with the authors.
No private annotations, hidden tests, solver request bodies, credentials, or official scoring artifacts are included.
