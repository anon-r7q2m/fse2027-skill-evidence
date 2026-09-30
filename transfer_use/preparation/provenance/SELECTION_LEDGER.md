# Fixed roster and display provenance

Prepared 2026-09-29 before any analyst output. This is a purposive, bounded set,
not a systematic census or a random sample. The selection phase sought outside
framework materials that permit action, retained legal behavior, evidence limits,
and conditional or multiple-contributor reasoning. These intentions are not
analyst labels and are not placed in the input directory.

| Unit | Public origin | Analyst source pin | Pin relation and retained limitation |
|---|---|---|---|
| E1 | PydanticAI issue 6277 | `b5f43e4cc4c7d6ae2d7f76007dede1d8ca00c204` | Base of the final merged change, after the initial report; original report says `main`, not this SHA. Actual input bytes are preserved. The version's public `end_strategy` contract has scope wording that requires adjudication, not an assumed native-output obligation. |
| E2 | PydanticAI issue 6968 | `577a8e94b500999727cbf61fef569755a889f1ce` | Last main commit before the issue creation timestamp, not a reporter-attested revision. Original code is partial and remains partial. |
| E3 | LangGraph issue 6792 | `a7a27dd43a4229c2ca09ac065a6a39e4ce083063` | Tag 1.0.8 matches the reported package version. The text says an outer entrypoint was invoked; pasted calls target the inner entrypoint. Both remain unchanged. No actual invocation is inferred or repaired. |
| E4 | LangGraph 1.0.8 `interrupt` documentation example | `a7a27dd43a4229c2ca09ac065a6a39e4ce083063` | A documented operation, not an incident. It shares source and API family with E3 and contributes no independent runtime observation. |

The roster was fixed before packet assembly. Earlier exploratory candidates
PydanticAI 4830/4831 were not retained because the route was narrowed to the four
above; they are not failures in a measured denominator. AutoGen 8086 was excluded
from this transfer roster because the same framework and configuration boundary
had already been studied. AutoGen 7837/7933/8088 serve prior-art correction for
the earlier a21 case, not transfer units. Search results not promoted to candidates
are not represented as an exhaustive screened population. No substitutions or
further framework search are allowed after this roster choice.

## Input/resolution separation

`../input/` contains only neutral factual presentations, public example/code or
output blocks, unmodified selected source modules and pinned documentation,
licenses, and attribution. It has no issue title/labels/open-closed status, PR
resolution, post-fix tests, manuscript, review score, reference answer, or this
ledger. The source references in attribution are origins, not permission to browse.

Issue summaries are authored neutral paraphrases. Full issue prose has not been
copied into the package. `E1_ISSUE_METADATA.json` through `E3_ISSUE_METADATA.json`
record the public issue API URL, metadata, complete body hash at acquisition, and
code-fence extraction locations/hashes. `issue_code/` retains the original public
code/output blocks, including blocks withheld from analysts because they expose
the report author's explanation or suggested fix.

`SOURCE_FILES.json` records every complete upstream module/document/license,
pin, URL, byte length and SHA-256. The files are unchanged. An initial request for
E2 `docs/capabilities.md` returned 404; the pinned tree has
`docs/capabilities/custom.md`, which was retrieved. E1's `_tool_execution.py` and
`agent/__init__.py` were added during pre-freeze completeness review at the same
E1 pin. An attempted E1 `_deferred.py` request returned 404 because that module
does not exist at this pin; E1's retained `tools.py` contains the corresponding
types. No E2 module was substituted into E1.

`PRESENTATION_TRANSFORMS.json` records exact display transformations:

- E1: use the original minimal-example code block, remove all comments and
  display-only print expressions, and remove its conditional branch whose only
  effect was printing a verdict. Original line positions are preserved with blank
  lines. Other characters, operation ordering, model response strings, global
  counters, tool/configuration declarations and calls are unchanged. Static
  `ast.parse` verifies only that this presentation remains syntactically parseable;
  it is not a target run or a claim of reproduction.
- E2: original code and reported-value blocks copied byte for byte.
- E3: original code and the two reported output blocks copied byte for byte.
- E4: the existing fenced Python example is extracted from the pinned `interrupt`
  docstring. Python string escapes and indentation are decoded for display. No
  behavior or trace is added. The unmodified full source remains available.

`resolution_only/E1_final/` retains the final merged implementation and tests with
its license. `E1_FINAL_PR.json` and `E3_PROPOSED_PR.json` preserve public state and
commit metadata. E1's final code differs from the PR prose regarding plain text;
the raw final source is kept, not a harmonized narrative. E3's proposed PR remains
unmerged and cannot establish the actual report's invocation. These materials are
reference-side evidence; details absent from analyst-visible materials must not
become mandatory hidden grading facts.

## Licensing and release boundary

PydanticAI and LangGraph source/docs are covered by their retained upstream MIT
licenses and attribution. Issue authors are credited for their public code/output
excerpts; the repository licenses are not represented as explicit issue-author
license grants. This is an internal preparation package, not a new publication or
license relicensing action. Any later public artifact must preserve this distinction
or distribute a URL/extraction recipe for material without an explicit grant.

## Status

No target program, dependency import, model, benchmark scorer or container was
run in preparation. The input snapshot manifest records file bytes before
reference reconciliation; it does not authorize dispatch. Root must freeze the
final prompt, method projection, input files, both separately written first
references and combined admissible-action set before either analysis context.
