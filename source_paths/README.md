# Review bundle: two native source-path checks

Read `REPORT.md`, then `SELECTION_PROTOCOL.md`, `QUALIFICATION_AND_FREEZE.md`,
the two per-path protocols, and `SOURCE_CONSUMER_MAP.md`.

- `public_source/`: exact pinned public files and MIT licenses.
- `public_source_manifest.json`: original public tree blob identities; no
  author-machine path or private annotations.
- `replay.py`: unchanged native method bodies loaded through Python AST with
  the mock boundaries declared in the protocols.
- `results/attempt_0/`: complete initial results and source-method registry;
  no fixture correction occurred. The registry identifies loaded methods,
  not full code or branch coverage.

Run from this directory with an existing Python 3.10+ environment containing
PyYAML and Jinja2:

```bash
python3 -B replay.py --output replay-output
```

The recorded execution used the existing system Python because the project
venv lacked Jinja2. Nothing was installed. The replay refuses to overwrite
per-host output files. It does not call a real model, execute shell commands,
start containers, run benchmark workers, or fetch source. It is not the native
upstream test suite or a complete agent reproduction.

SWE-agent's exact object-consumer path exposure is unknown; OpenHands' path
was previously exposed. These source-informed controls frozen before fixture
execution are not independent unseen-object or cross-host validation. More
precisely, source selection and all conditions were fixed before their fixture
execution, while expected judgments were informed by reading the selected
source. See the protocols for that ordering.
