# GP local replay: source ranking and a new syntax exclusion

Status: **COMPLETED**, six fixed conditions, six matching their declared
expectations. This is one retrospective historical candidate pair plus four
synthetic conditions, not six independent task observations. No model,
benchmark, Docker, network, scorer or original-artifact mutation occurred.

## The factorial question stops with a negative design outcome

`H1 = CANCELLED_NOT_OPERATIONALLY_DISTINCT` was fixed before execution. A scope
annotation without a changed consumer is metadata; a scope policy that simply
rejects known syntax errors duplicates the local syntax exclusion. We did not
invent a separate treatment or claim extra utility for generic scope tracking.

## Actual local results

| Fixed condition | Selection | Confirmed-error exclusions | Abstention |
|---|---|---:|---|
| Historical original source ranking | Earlier `508c251e...` | 0 | No |
| Same recorded pool, new syntax exclusion | Later `befc36e3...` | 1 | No |
| Synthetic legitimate test-only pool | First valid test-only candidate | 0 | No |
| Synthetic safe projection | First candidate; both declared value checks return 1 | 0 | No |
| Synthetic `TEXT_SIZE_LIMIT` / unknown syntax | First candidate, explicitly `unassessed` | 0 | No |
| Synthetic all-confirmed-error pool | No candidate | 2 | Yes |

The original replay reproduces the complete recorded selection effect:
`pool=2`, `comparable=2`, `eligible=2`, `winning_votes=1`,
`minimum_failures=0`, `reason=MAJORITY_VOTE`. The exact original function slice
retains comparable-receipt filtering, RAW/Python keys, vote counts and the
first-occurrence tie-break. Keys and failure summaries are recorded inputs;
normalization is not rerun.

The new local policy is a **hard exclusion of confirmed syntax errors before
the original soft ranking**. Its historical exclusion uses the already recorded
public query-14 `SyntaxError` on the earlier candidate. It does not classify
`TEXT_SIZE_LIMIT`, absent syntax evidence, or test-only changes as errors.
Unknown candidates remain eligible with an explicit `unassessed` label; this
policy does not certify that every admitted candidate is syntactically valid.
The historical policy never promised this new exclusion and is not relabeled
invalid. The all-error condition tests the new wrapper's abstention, not donor
source fidelity.

Across the two synthetic normal-control pools, **0 of 4 candidates are rejected**.
This is a fixed control count, not an estimated general false-positive rate.
There is one explicit synthetic uncertainty condition and one all-error
abstention condition. No other fixture was added after execution.

## Evidence levels and limits

- **Exact source replay:** four unchanged functions from P package
  `5f70bae4b1b6732fd16a06e8802fdb6628fdcb6d68e240ba434477e202da6e93`,
  applied to the original recorded ranker inputs. Full host transport and
  package normalization are outside this replay boundary.
- **Recorded original execution:** both preservation receipts are 4/4 PASS;
  both projected trees equal the base; `issue_fixed` remains null. Original
  G/Django tests are not rerun. Equality of these receipts does not mean the
  selector's complete inputs are equal: RAW/Python keys and order differ.
- **New syntax illustration:** exact model-generated additions, placed under
  a declared synthetic class wrapper, respectively raise `SyntaxError` and
  parse. This reproduces the local malformed-plus-sign phenomenon, not a
  full-file syntax certificate or Django test result. The local policy uses
  the original recorded error, not this smaller illustration as a substitute.
- **New local policy:** removing the candidate with a confirmed error changes
  this fixed pool's selection. The later candidate remains unassessed for
  whole-file syntax in this bundle and was not newly scored. No lost solve,
  gained solve, general selection advantage or prediction result follows.
- **Synthetic controls:** demonstrate limited behavior of the new exclusion.
  Their safe projection is an explicit file-map operation, not a reexecution
  of the historical G implementation.

## Reproduction and validation

From any working directory, using only this directory and CPython 3.10+:

```sh
python3 -B replay.py
```

The initial execution ran with `/tmp` as the working directory and passed all
six expected observations on its first run. `implementation_fix_passes=0`.
Ruff check and format check passed for the authored replay script; the bundled
original selection source remains an exact slice, without formatting edits.
See `replay_result.json`, `provenance.json` and `SCHEMA.md`.

The repository extraction step is separate from replay:

```sh
python3 -B analysis/skill_reuse_principles_v1/gp_replay.py build \
  --repo-root . --out <new-empty-output-directory>
```

This is a local artifact candidate. The donor notice is included; the authors'
release-license declaration for project-authored materials remains separate.
No full trajectory or unchanged Django source body is bundled.
