# Feedback: original-record witnesses for django__django-15503

This supplement preserves the small observation and endpoint chain for rank 192,
position 7. It extracts existing records only. No checker, model, local replay,
or benchmark was executed to create it.

| Step | File | Connection to inspect |
|---|---|---|
| Frozen proxy | [checker.json](checker.json) | The original card gives the three obligations; the seal binds card/script hashes. |
| B, U, V and the final selector | [endpoints.json](endpoints.json) | B and U share a tree/patch. U/V initial_ready records identify the same B starting tree before requests. The original post decisions select B for G_U and V for G_V. |
| Actual observation content | [observations.json](observations.json) | B numeric_key fails while both controls pass. The b_feedback record preserves the actual simplified feedback, including the assertion and traceback. V's same proxy cases pass. |
| Which tree/checker produced the observations | [check_receipts.json](check_receipts.json) | B/U/V behavior receipts bind request ID, exact before/after tree, script/card hashes, and execution status. |
| Feedback in saved continuation inputs | [prepared_feedback.json](prepared_feedback.json) | Exact substrings from V prepared/effective input records contain the saved b_feedback object; U's corresponding records contain no such marker. Offsets and source-field hashes are explicit. |
| Limited request-status evidence | [request_status.json](request_status.json) | First-request COMMIT metadata records number, purpose, body hash and status. It does not expose or establish actual body content. |
| Existing public code/patch identities | [public_source_bindings.json](public_source_bindings.json) | Original B/V patches and generated checker are byte-identical to the linked existing public artifact files. |

B tree: 3a83a2436f90d7f4a60d6ed684ec44a6500a1e42.
V tree: 6b6e44cd1f0860992dfd07e1f5b19e769241dc9b.
Pinned Django base commit: 859a87d873ce7152af73ab851653b4e1c3ffea4c.
The existing [checker](../../principles/feedback/source/original_checker.py),
[B patch](../../principles/feedback/source/B.patch), and
[V patch](../../principles/feedback/source/V.patch) are reused unchanged.

Each field projection records its original project-relative source path,
complete source-file SHA-256, and exact RFC 6901 field paths. Retained field
values are unchanged; omitted content is not represented. These projections
are not source-file bytes. Substring records separately identify the /issue
source field, offsets, exact text, and a deterministic equality check against
the saved feedback object. They are saved prepared/effective inputs, not raw
model requests. Source hashes identify omitted originals but cannot by
themselves independently authenticate an execution.

The actual first-request bodies and trajectories were not opened or included.
Therefore this supplement does not independently establish that feedback was
the sole transmitted input difference. The existing
[analysis report](../../principles/evidence/feedback_review.md) reports that
comparison; it remains analysis-level evidence. The saved construction records,
first-request status, and actual endpoint/checker records have the narrower
roles stated above. No encrypted reasoning, account information, author-machine
absolute paths, or hidden tests are included. Original container paths in the
public-checker traceback remain task-runtime paths.

The numeric-string assertion is preserved as the actual fallible proxy, not
endorsed as the correct JSON-path requirement. Passing it does not establish
correct KeyTransform integration. The endpoint records precede official scoring
and contain official_scores=null; they do not show an official solve or score
loss. This case does not estimate a general causal effect of feedback, and the
supplement does not provide a full host rerun.
