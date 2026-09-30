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


## Prospective native-workflow archives

`prospective/upstream/smolagents.tar.gz` is the unchanged public repository
archive at 227ef5e49ddd82339295939072f0223249aa8d38, with its Apache-2.0
license, copyright notices and upstream third-party material preserved.
`prospective/upstream/autogen.tar.gz` is the unchanged public repository
archive at 027ecf0a379bcc1d09956d46d12d44a3ad9cee14, with the MIT code
license and all accompanying upstream notices/licenses preserved. AutoGen
`LICENSE-CODE` (MIT) and `LICENSE` (CC BY 4.0 for documentation) are both copied
adjacent to the archives, with distinct filenames. These materials are not
relicensed under the project-authored artifact MIT grant.


## September 30 source-to-skill supplement

`reuse/` adds pinned Agentless reranking and regression source excerpts at
`5ce5888b9f149beaace393957a55ea8ee46c9f71`, with the complete original MIT
notice at `reuse/licenses/Agentless-MIT.txt`. The generated selector and G
material is distinguished from donor excerpts in `reuse/PROVENANCE.json`.

Aider source files, public prompt templates and the bounded native factory
excerpt originate from `aider-ai/aider` at
`5dc9490bb35f9729ef2c95d00a19ccd30c26339c`. Its Apache-2.0 notice remains at
`reuse/licenses/Aider-Apache-2.0.txt`. These upstream materials are not
relicensed as project-authored MIT code. Generated target code, host-adapter
excerpts and newly authored inspection/provenance guides remain separately
identified in that provenance map.

## All-nine implementation and AP archival supplement

`reuse_depth/catalog/` contains unchanged selected generated target modules,
with original manifests where present and existing public profiles. It is
distinct from donor source and from the root project-authored MIT grant.
Donor-derived code/prompts retain pinned notices under `reuse_depth/licenses/`:
Agentless, Moatless, OpenHands, Trae and SWE-agent MIT; Aider Apache-2.0.
The Moatless/Trae notices were obtained from the exact pinned revisions and
their Git blob identities checked against the existing source trees.

`reuse_depth/aider_ap/` archives a project-authored synthetic fixture and
predetermined-response entry. The exact old patch and materialized source
belong to that fixture, not a benchmark or private annotation dataset. New
inspection guides/inventories and the static binding checker use the separate
project-authored MIT grant. Existing original bytes and small path projections
are identified in `reuse_depth/PROVENANCE.json`.
