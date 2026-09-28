# Bounded public source-path check: selection protocol

Frozen on 2026-09-28 before reading the selected native path behavior or
executing a fixture. This is a native source-path check, not a cross-host
transplantation, a blind independent sample, or a benchmark experiment.

## Selection rule

1. Prefer SWE-agent and OpenHands at their already pinned full source revisions.
2. SWE-agent object: the official default configured path from model output,
   through parsing/admission and tool execution, to the observation actually
   consumed by the next agent step.
3. OpenHands object: a tool action result through event/history processing to
   the next input of the default configured agent.
4. Qualification reads only public origin, pinned revision and license, local
   source completeness, entry/configuration metadata, and public prior-coverage
   records. It does not inspect the selected path's behavior or outcomes.
5. If either preferred host cannot be qualified, inventory local public donor
   hosts, sort canonical repository URLs, and take the first two qualified
   different hosts. Record exclusions. Do not select by a known defect.
6. Freeze exactly two object-consumer paths. No replacement after this freeze,
   and no third-case search. Prior exposure is judged at this specific path;
   unclear coverage is `exposure_unknown`, never independently unseen.

## Per-path protocol and stop rule

After freezing the objects, inspect their source paths, and before execution
freeze at most two obligations grounded in existing public documentation,
contract, or stated operation semantics. Record transformations, source slices,
mock boundaries, at most four conditions per path, and expected judgments
(`supported`, `violated`, `unknown`, or `not_applicable`). Include an ordinary
legal boundary and the actual transformed-input control. Compare existing
relevant public checks and the simplest direct test on that same input. Do not
invent an adaptation merely to add a condition.

Only existing local dependencies may be used. Native code slices or AST-loaded
methods with disclosed mocks are permitted. No installs, containers, model
calls, benchmark calls, commits, pushes, private annotations, or credentials.
New files stay within this document directory and
`results_cache/fse_source_path_check_20260928/`.

At most one limited fixture correction per path is allowed, preserving the
original output. Remaining uncertainty closes `unknown`. Preserve normal,
negative, legal, null, and unknown observations. Synthetic mutations cannot be
reported as native bugs. Do not claim debugging efficiency, independent
predictive generalization, or superiority over ordinary expert checks.

## Required outputs

Qualification/exclusion inventory and object freeze; two per-path protocols;
source-to-consumer maps; exact minimal public source and relevant test slices;
all condition outputs; direct-test comparison; and a concise report stating the
new knowledge or the resulting control decision, including a null conclusion.
