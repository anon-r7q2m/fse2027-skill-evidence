# P2 SEARCH/REPLACE variant: public behavior contract

Variant `p2_search_replace_full_file_v1`; transport profile
`same_base_selection_v2`. Source: Agentless commit
`5ce5888b9f149beaace393957a55ea8ee46c9f71`, CoT diff-format path.
The parent package remains immutable; this contract does not amend its
line-coordinate contract or reuse its behavior qualification for new code.

## Exactly two generated replacements

Return exactly two FOUR-backtick blocks:

- `python mechanism.py`: only `def _build_prompt(event: dict) -> tuple[str, str]`.
  Keep this exact signature, use imports already available in the parent, and
  return `(instructions, user_prompt)`. Inline any necessary file rendering;
  the parent's `_render_files` includes display line numbers and is unsuitable.
- `python edit_parser_pkg.py`: the complete replacement module, including
  `class ParseError(ValueError)` and `parse_sample_text(text, base_files)`.
  Standard library imports and private helpers are allowed. Do not import
  Agent2Skill, the donor checkout or a prewritten target implementation.

The assembler inserts only the original model bytes. All other bytes, including
the manifest and the rest of mechanism.py, admission_pkg.py and normalize_pkg.py,
must match the parent. No other file, import or function replacement is allowed.

## Prompt and input domain

Every sample receives identical complete issue text, declared paths, full
original file content without inserted display line numbers, original file
modes and supplied locations. Supplied locations remain context; the editing
interval for each declared file is exactly
`[(1, len(before.splitlines()))]`. The model does not output line coordinates.
All files are existing nonempty UTF-8 Python files; reject zero-line files
before generating sample requests. Do not silently fall into the donor's
empty-interval branch. File discovery/localization is not part of this target.

The prompt must explain precise SEARCH/REPLACE syntax, exact indentation,
declared paths, independent same-base commands, and all the restrictions below.
It must not instruct `edit_file(` calls or numbered-line edits. Require one
complete `python` fence, with one to 64 commands. Each command has an explicit
`### <declared path>` line, `<<<<<<< SEARCH`, one or more original lines,
`=======`, replacement lines (possibly empty), and `>>>>>>> REPLACE`.
Only whitespace may occur outside the fence or between commands.

## Parsing and source semantics

`parse_sample_text` returns sorted per-file `{path, before, after}` objects,
with complete original and resulting text, including files whose commands
did not match. It raises `ParseError` for malformed syntax, domain and resource
rejection. The existing caller turns that into one `parse_failed` sample.

For conforming commands, preserve the actual donor behavior:

1. Group by declared path in first-appearance order and deduplicate exact
   repeated commands within each file, retaining their first occurrence.
   File output ordering is sorted as in the parent host ABI.
2. Use the complete file as one nonempty interval. Reconstruct the donor's
   context with leading and trailing `\n`, using `before.splitlines()`.
3. Find applicable commands against that original context before applying
   changes; then apply those commands in reverse order, checking each match
   against the then-current context.
4. Search and replacement are bounded by `\n`. Use Python `str.replace`
   semantics for all nonoverlapping matches in the context. Do not require
   a unique occurrence or reject text overlaps using the old coordinate rules.
5. A command that does not match is skipped; others may still apply. Preserve
   source newline reconstruction literally, including no-match results.
6. Do not reject invalid Python or blank-only changes in the parser. Return
   their raw after text; unchanged downstream admission owns these decisions.

Explicit profile restrictions/adaptations:

- Direct declared-path mapping replaces the source wrapper's `eval`.
  Reject undeclared paths; never evaluate model text or access the filesystem.
- Reject incomplete markers, an empty SEARCH, missing per-command headers,
  nested/extra fences and extra nonwhitespace text. Structural marker strings
  cannot appear as standalone lines inside a search/replacement payload.
- Reject the donor's special ellipsis forms: SEARCH exactly `...`, or SEARCH
  or REPLACE starting with `...\n`. Ordinary literal `...` inside code or
  strings is allowed. No fuzzy matching, guessed indentation or repair loop.
- Bound the aggregate UTF-8 bytes of `before` plus `after` over returned files
  to 256 KiB. Compute potential growth before allocating each replacement;
  reject overflow via `ParseError`, keeping other sample slots intact.
  The same limit applies to intermediate materialized after text. Malformed
  or out-of-domain samples are not worker failures; actual interpreter,
  transport, cleanup and host errors remain execution stops.
- Input base files, command count and output sizes must respect the inherited
  public ABI. Do not shrink, truncate or partially return an oversized sample.

The parser need not print donor diagnostic stdout, since stdout is not part of
the package's declared effects. Source output bytes inside the domain must be
preserved. No-match and syntax-invalid output must not be silently fixed.

## Downstream and evidence

Do not change sample identity/order/multiplicity, four callbacks, admission,
normalization, tie-breaking, original-tree publication or request limits.
R checks are outside this package. Source behavior, local integration and
benchmark outcomes remain distinct. No benchmark improvement is presumed.
