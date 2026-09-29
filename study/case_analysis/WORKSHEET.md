# Analyze one obligation at its consumer

This packet reorganizes existing public evidence. It adds no experiment, outcome, preregistration, independent annotation, or estimated diagnostic accuracy. Its six analysis units are GP, feedback, AutoGen a21, AutoGen a22, and the two Pro population claims. The Pro pair reuses one computation; it is a contrast, not two independent discoveries.

Start with [case_inputs.json](case_inputs.json). It contains source excerpts, declared inputs and recorded observations, selected without copying fixture `expected` answers or authored causal labels. The complete older files remain linked and unchanged; their own expected answers are still visible. Read [case_analysis.json](case_analysis.json) afterward for the authors' reasoning. This separation enables disagreement with the inference; it is not a claim of blind analysis.

## Required input and decision record

Fill the following fields for **one obligation and one consumer action**. An entire agent is too broad a unit.

| Field | What to record |
| --- | --- |
| Consumer/action | Which operation consumes the information, and what selection, termination, repair or reporting decision follows? |
| Obligation/domain | State the property and applicable inputs. Cite a public requirement, API contract or explicit study contract. Do not infer authority from a passing check. |
| Boundary path | List relevant producer, transformation/configuration, delivery, check and consumer edges. Preserve parallel paths; do not invent a total order. |
| Available facts | Give exact source references and recorded values. Identify observations that were not captured or are not public. |
| Alternatives | For each explanation, state a discriminating observable, compare it with the record, and retain coexisting contributors. |
| Correction/control | Name the justified action, its tested or proposed status, and behavior that must remain legal. |
| Endpoint/limits | Report the observed local decision separately from task success and from unsupported generalization. |

Authority codes: `JUSTIFIED` means a cited requirement applies in this domain; `ASSUMED` means an unsupported assertion or a requirement newly imposed on an older system; `UNKNOWN` means the authority is unresolved. Separately use `ALLOWED_ADAPTATION` only when permission, changed domain and retained obligations are explicit. A new study rule may be justified for its diagnostic conditions without retroactively becoming the historical program's contract.

Evidence availability: `PUBLIC_RAW` means the specified public bytes, including an explicitly bounded source excerpt; `PUBLIC_PROJECTION` means retained fields from an existing record, not the complete original recording; `REPORTED_ONLY` means a public report without the underlying observation needed to independently substantiate the statement; `RESTRICTED` identifies unavailable material without providing a private path or its content. Availability does not itself establish truth or authority.

## Decision sequence

1. Establish the obligation before evaluating the check. An issue-specific object-key requirement does not automatically redefine every generic JSON-path call.
2. Trace the input that reaches the actual consumer. Record the earliest evidenced mismatch relevant to this obligation. A distinction lost on one path can coexist with admission, ranking and tie-breaking on another. Missing evidence is `UNKNOWN`, not evidence that an operation did not run.
3. Mark each explanation `SUPPORTED`, `CONTRADICTED` or `UNRESOLVED`, citing the premise IDs and discriminating observation. Preserve supported contributors even when one intervention bypasses them.
4. Choose the action below; require an existing intervention record before calling an action tested.

| Evidenced relation | Action |
| --- | --- |
| Unsupported predicate | Correct or narrow the requirement using independent authority before enforcing it. |
| Required configuration/invocation/delivery missing | Restore it at the demonstrated boundary; retain the intended consumer predicate. |
| Evidence addresses another object/property/population | Check the relevant object or narrow the claim, retaining lawful projections. |
| Correct input reaches an incorrect consuming rule | Correct that rule under the justified obligation. |
| Declared obligation satisfied, including permitted omission | Retain behavior. A desired extra property is a new requirement. |
| Authority or decisive observation unresolved | Withhold the defect/causal verdict and identify the missing evidence. |

For GP, a preservation receipt concerns restored tests, while selecting an original candidate also depends on RAW eligibility and first-occurrence voting. The optional new syntax exclusion rejects a confirmed syntax error; it does not certify the later candidate or outlaw test-only edits. For Pro, the same `case_a=true` mean 1.0 supports a declared subset `{case_a}` but does not establish a result for `{case_a, case_b}`. Withhold the unsupported full-population claim without assigning the missing case zero.

## Static checking

From the artifact root run `python3 -B study/case_analysis/check.py`. The standard-library checker resolves artifact-relative paths, RFC 6901 JSON Pointers and one-based inclusive text ranges (including an archive member without extraction). It compares the retained values and checks a few stated equality, count and population relations. It imports no target implementation, runs no replay and writes no file.

A successful check establishes references, shapes and these arithmetic relations. **It does not validate normative judgments, causal sufficiency, the authenticity of an omitted original, or completeness of any benchmark run.**
