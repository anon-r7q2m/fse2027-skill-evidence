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
