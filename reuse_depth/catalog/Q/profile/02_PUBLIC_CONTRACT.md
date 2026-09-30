# Public ABI: sweagent_chooser_v1

Implement `handle(event, state) -> {"state": object, "effects": [one effect]}`.
Raise `ValueError("PROTOCOL_REJECTED: ...")` for malformed protocol or incorrect
lifecycle. JSON-only persistent state; no filesystem, network, model, subprocess,
host, or donor imports. Standard library and declared own modules only.

Manifest: schema_version=1, profile=`sweagent_chooser_v1`,
entrypoint=`mechanism:handle`, modules=[your module basenames],
capabilities=[`chooser_request`, `chooser_selection`]. At most eight modules,
1 MiB/module, 4 MiB/package. Event/state/effect each <=3 MiB; combined worker
input <=8 MiB. Never truncate source, messages or candidate patch silently.

## Events

All have exactly `kind`, `run_id` (nonempty <=256 chars), `base_snapshot_ref`
(40 lowercase hex) plus the fields listed below. Empty initial state required.

`begin_choice`: additionally `problem_statement` (string), `candidates` (0..4
rows). Each row has exactly:

```
{"sample_index": positive int, "request_id": nonempty string,
 "snapshot_ref": 40 lowercase hex, "exit_status": string,
 "patch": string or null,
 "files": [{"path": repository-relative path, "content": full modified text,
            "hunks": [{"target_start": nonnegative int,
                       "target_length": nonnegative int}, ...]}, ...]}
```

Sample indices are increasing, unique, <=4, and need not be contiguous. IDs and
file paths are unique; candidate request_id is nonempty and <=256 characters.
There are at most 64 file rows, in unified-diff order. Paths are 1..4096
characters, canonical repository-relative POSIX paths with no backslash,
control character (code point <32 or 127), empty component, `.` or `..`
component, or `.git`, `.hg`, `.svn` component. Only modified existing
text files are in scope. Hunk coordinates come from a generic diff parser; full
text is candidate-matched. Empty/null patch has no files. Source syntax failures,
added/deleted/renamed files and missing candidate text are outside this profile;
host must stop before invoking, never fabricate or omit context.

`model_response`: additionally `request_id`, `status`, `text`; status is one of
`completed`, `incomplete`, `failed`, `unknown`. Text is a string only for completed,
otherwise null. ID must match the one outstanding chooser request.

`get_best`: no additional fields; legal only after SELECTED, EMPTY or UNAVAILABLE
selection. Return the same cached selection effect, issue no model request.
Repeated begin or response, get_best while waiting, another run/base, invalid
types/keys and mismatched receipt ID must be rejected.

## Required mechanism semantics

Use the supplied unchanged `Chooser` source and fixed YAML templates.
For nonempty candidate pool:

1. If >=2 rows have exit_status exactly `submitted`, retain only those rows;
   otherwise retain every row. Preserve order and original sample identity.
2. Format each retained row. Null patch or `len(patch)>5000` uses the literal
   `Solution invalid.`; this is display only and **does not remove eligibility**.
   For other patches, compute edited_files30 using supplied `PatchFormatter`:
   per hunk start=max(1,target_start-30), stop=target_start+target_length+30,
   merge overlapping/touching intervals; include numbered lines, omission markers
   and `[File: path]` headings exactly as donor executes. The donor's below-omitted
   count is `len(lines)-last_stop`; preserve it even where it appears unusual.
   Empty patch uses `Empty. No edited files found.` for edited_files30.
3. Render fixed donor system/instance/submission templates byte-for-byte as
   Jinja2 3.1.6 default Template does. The package may implement these particular
   templates with standard-library string assembly; generic template support is
   not required. No package code or target implementation is supplied.
4. Emit one chooser_request. On completed text parse the last regex `\d+`
   anywhere in the response, int-convert it; no digit/int conversion error means
   local index 0. An out-of-range local index falls back to local index 0.
   Map that zero-based filtered index to the original sample_index/snapshot_ref.
   Do not edit, normalize, vote, validate semantics or replace the selected patch.
5. Cache the resulting selection for get_best. Empty initial pool emits EMPTY
   immediately without a query. A non-completed receipt emits UNAVAILABLE,
   with null selected identity, and does not retry or fallback. This last rule
   intentionally replaces the donor's unbound-response exception/outer fallback.

## Effects

Each effect has exactly `kind`, `run_id`, `base_snapshot_ref` plus:

- chooser_request: `request_id` = run_id + `/chooser/1`, `messages` (exact donor
  system/user pair), `candidate_indices` (filtered original sample indices).
- chooser_selection: `status` (`SELECTED`, `EMPTY`, `UNAVAILABLE`),
  `sample_index`, `snapshot_ref`, `candidate_indices`. SELECTED has original
  identity; EMPTY has null index and base snapshot; UNAVAILABLE both null.
  EMPTY indices=[]; other indices retain the request's filtered roster.

State internals are not prescribed. No extra effect fields are permitted.
Official labels, benchmark tests and hidden cases are never inputs. All model
effects are interpreted/charged by the host; handle itself makes no model call.
