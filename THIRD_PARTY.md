# Third-party source

The two Agentless source files originate from
https://github.com/OpenAutoCoder/Agentless at revision
`5ce5888b9f149beaace393957a55ea8ee46c9f71`:

- `agentless/util/postprocess_data.py`
- `agentless/repair/repair.py`

Their original bytes are retained under the paths in `provenance.json`.
The complete MIT license, including Copyright (c) 2024 OpenAutoCoder, is at
`experiments/reproduction_regression_v1/sources/agentless/LICENSE`.
This notice applies to those donor files. It does not assert that the
Agent2Skill project as a whole has been released under MIT.

The replay uses the existing helper to compile six pure function definitions
from the pinned source AST. It does not import the donor modules wholesale or
require their datasets/model dependencies. Intentional transfer adaptations
are listed in `experiments/search_replace_transfer_v1/PUBLIC_CONTRACT.md`.

## Bounded principles replays

- `principles/gp/THIRD_PARTY.md` documents the generated selector slice and
  retains the pinned Agentless MIT notice in `AGENTLESS_LICENSE.txt`.
- `principles/feedback/source/` contains public Django source and patch
  variants. The full BSD 3-Clause notice is in
  `principles/feedback/LICENSE-Django.txt`; the group README identifies the
  pinned source and mocked execution boundary.
- `principles/pro/source/swe_bench_pro_eval.py` is the unchanged public
  evaluator at revision `ca10a60a5fcae51e6948ffe1485d4153d421e6c5`.
  `principles/pro/source/LICENSE` retains its MIT notice, and
  `principles/pro/provenance.json` identifies the original functions used.

These notices cover the indicated third-party material. Project-authored
wrappers and documents in this curated package are separately licensed by
`LICENSE`; each donor file retains its indicated original license.

## Supplementary native source paths

`source_paths/public_source/swe_agent/` and
`source_paths/public_source/openhands/` retain the exact public source files
at the pinned revisions in the source manifest. Both directories include their
original MIT LICENSE. The replay wrapper is project-authored and distinct from
the unchanged donor methods it loads.

## Original-record and installation supplements

The two GP candidate patches under `witnesses/gp/` modify public Django source;
the existing Django BSD notice in `principles/feedback/LICENSE-Django.txt`
continues to apply. Feedback supplements reuse the already bundled Django
source and patches.

The fixed capacity implementation includes project installation wrappers and
generated L/P/Ln/Pn packages. Agentless-derived L/P code retains the existing
Agentless MIT notice linked above; full package/source identities are in
`capacity/implementation/PROVENANCE.json`. Mini is a pinned dependency represented
by project wrappers and configuration, not a newly vendored upstream distribution.
