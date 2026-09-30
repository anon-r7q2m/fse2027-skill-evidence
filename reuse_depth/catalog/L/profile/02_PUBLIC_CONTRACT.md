# Localization-only public ABI

Profile `localization_only_v1`, entrypoint `mechanism:handle`, Python 3.13 with
the existing pinned libcst 1.9.0 isolation profile. `handle(event, state)` is a
pure JSON state transition returning exactly `{"state": {...}, "effects": [effect]}`.
Exactly one effect per invocation. No network, credentials, shell, workspace
writes, runtime imports of the donor repository or model calls inside the package.
Declared modules are `mechanism.py` and mechanically inherited `donor_logic.py`.
The latter is the unchanged helper from the frozen source-repaired L package;
its repair helpers exist but must never be called by this endpoint.

Every event and effect has `kind`, `run_id` (nonempty string, <=256 UTF-8 bytes),
`base_commit` and `base_snapshot_ref` (40 lowercase hex characters). All except
`begin` also have a nonempty unique `request_id`. Receipts must match the
currently pending request, identities and stage. Reject repeated begin,
out-of-order/foreign receipts and post-terminal callbacks with
`ValueError("PROTOCOL_REJECTED: ...")`. Extra event/effect keys are invalid.
State is empty only at begin; subsequent state includes `progress` as below.
Other state fields belong to the package. Validate without changing input objects.

## Events

* `begin`: additionally `issue`, `tracked_paths`, `config`. The issue is the
  unchanged public issue (<=100,000 bytes). Paths are lexicographically sorted,
  unique, normalized repository-relative paths (<=30,000). Config equals the
  exported `CONFIG` in `contracts.py` exactly. No requirement card, selected
  files, target answer or manually supplied position is present.
* `files_ready`: additionally `request_id`, `files`. One to three ordered
  `{path,status,content,mode}` rows correspond exactly to `read_files.paths`.
  Status is `available`, `missing`, `non_utf8` or `unavailable`. Available rows
  contain full immutable UTF-8 content (<=256 KiB each, <=512 KiB total) and
  `100644`/`100755`; other rows contain null content/mode. Empty content or
  Python syntax unsupported by the parser terminates with the corresponding
  source status. Do not normalize stored raw source or its line endings.
* `model_result`: additionally `request_id`, `stage`, `status`, `text`,
  `input_tokens`, `query_id`. Stage is `file`, `related` or `fine`.
  Status `completed` has text (possibly empty, <=1 MiB) and a positive integer
  query_id. `context_limit` is a local full-request preflight rejection: null
  text/query_id, no provider call. `output_failed` has null text and a positive
  query_id: a completed, fully charged output could not be consumed. Input
  tokens is a nonnegative integer. Unknown usage, provider identity failure
  and exogenous infrastructure errors are NOT output_failed; the host stops.

## Effects and progression

* `model_request`: additionally `request_id`, `stage`, `prompt` (<=1 MiB).
  Preserve the donor file prompt, compressed related skeleton and numbered
  fine context. Use immutable original AST/line structure separately from
  donor model-visible text. Each stage uses a fresh model context; the host
  uses its fixed model/reasoning configuration and an empty system prompt.
  Fine rendering follows related-map response order (use those paths as the
  helper's `file_names`, not original selected order). Only outer `.strip()`
  is an allowed prompt normalization; internal content/whitespace is preserved.
* `read_files`: additionally `request_id`, `paths`; one immutable batch after
  the completed file response. File selection uses donor exact path matching,
  then takes the first three results BEFORE stable deduplication for the read.
* `localization_handoff`: additionally `request_id`, `status`, `message` and
  every progress field below. Stop here; never emit repair/apply/edit effects.

File has at most one actual request, related at most two, fine at most two.
File->related->fine order is mandatory. An invalid related/fine response retries
that stage once; the same donor at-least-one-resolvable-location predicate is
used, not an invented all-files-valid requirement. The inherited empty `line:`
token recovery is an explicit adaptation. Repeated invalid related/fine outputs
end as EMPTY_RELATED_LOCALIZATION/EMPTY_FINE_LOCALIZATION. Related failure does
not start an ungrounded fine or repair request. A context_limit drops only the
last path from the current related/fine view roster and retries without charging
a model request, stopping at one remaining path if still overlong. The fine
roster includes all related-map entries, including appended empty entries,
matching the donor's `coarse_locs.popitem()` ordering. Removing an empty entry
can leave the prompt unchanged; the roster still shrinks. This changes only
the view roster, not the original selected paths or saved raw maps. File
context rejection cannot shrink the repository by a host relevance heuristic.
An output_failed receipt ends immediately as MODEL_OUTPUT_FAILED.
The request and shared clock ceilings include all stages and local work.

Normal statuses are LOCALIZED, EMPTY_FILE_LOCALIZATION,
EMPTY_RELATED_LOCALIZATION, EMPTY_FINE_LOCALIZATION, EMPTY_FINE_CONTEXT,
CONTEXT_LIMIT, SOURCE_UNAVAILABLE, SOURCE_SYNTAX_UNSUPPORTED,
MODEL_OUTPUT_FAILED. These are local process dispositions, not solve scores.

## Explicit progress and location mapping

Every returned state includes `progress` with exactly these six fields, initially
empty lists. Update it at each completed callback; normal handoff contains the
same values. The host copies it without parsing donor model text.

* `donor_found_files`: exact parsed file output truncated to three, retaining
  duplicates/order. This is the bounded top-three list, not a claim to retain
  donor's complete untruncated `found_files`; full raw model output is logged.
* `selected_files`: stable unique paths from `donor_found_files`.
* `related_locations`, `fine_locations`: ordered `{path,locations:[strings]}`
  rows from donor parsing, including empty/unrecognized location text. Keep
  response appearance order and the donor's appended empty selected paths.
* `locations`: resolved `{path,start,end}` rows from the FIRST `line_locs`
  return of `transfer_arb_locs_to_locs`, iterating the fine map in its order.
  Call it with the original structure, separately reconstructed display text,
  `context_window=0, loc_interval=True, fine_grain_only=False`. Do not substitute
  its second, expanded/clamped context interval return. Retain raw integer
  ranges, duplicates and ordering, including out-of-file integers: the P
  exporter rejects invalid ranges instead of silently fixing them.
* `localized_files`: fine-map ordered paths with at least one returned line
  range. Paths with empty/unrecognized fine locations stay in the above lists
  and native context, but do not enter this list. No host reranking or repair
  success is involved in that selection.

LOCALIZED means at least one donor-resolved fine location exists. It does not
mean all coordinates are admissible to P or correct for the issue. This
projection is grounded in donor `construct_topn_file_context`'s nonempty
line-location branch; exposing exact line_locs for this host is a declared ABI
adaptation. No fallback whole-file locations may be invented for L_loc.

L's native continuation receives all six fields, status/reason and access to
its original search/read/edit tools. LP supplies complete immutable files for
`localized_files` and these exact `locations` to the unchanged P ABI. Invalid
ranges, >64 ranges or P's 256 KiB aggregate limit produce a declared empty-base
pipeline outcome for ordinary scoring. These P limits never constrain L's
native continuation. Do not delete invalid ranges to obtain a passing view.

If the shared budget expires, the host returns LOCALIZATION_BUDGET_STOP with
the LAST completed and validated progress, recording its reason and all actual
requests. Late or unprocessed model text is never promoted into progress.
Pending/unknown/exogenous requests prohibit continuation. Local failures do not
reset the clock, create free model requests or erase spent tokens.
