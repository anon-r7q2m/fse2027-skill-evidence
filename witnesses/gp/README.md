# GP: original-record witnesses for django__django-13925

These files supplement the existing local replay with field extracts from the
recorded run. No mechanism, checker, model, or benchmark was rerun to build them.

| Step | File | Connection to inspect |
|---|---|---|
| Two candidate patches | [candidates.json](candidates.json), [early patch](candidate_early.patch), [later patch](candidate_later.patch) | Original capture 14/17 manifests bind each patch SHA and tree. Both modify the public Django test file only. |
| What was actually checked | [checks.json](checks.json) | req-2/req-3 refer to different candidate trees, but both projected_tree fields name the same base tree. The replaced public test file is explicit. The recorded command/stdout describe the four preservation tests. |
| What P consumed and selected | [selection.json](selection.json) | Final package state binds order, ordinal, raw/Python key, fallback reason, and g_first request ID/failure count to each candidate. Its actual effect selects the early candidate. |
| Which package produced the output | [execution_bindings.json](execution_bindings.json) | Stage/P-worker package hashes agree; the worker output hash binds the original JSON stdout from which selection.json is projected. |
| What was published | [publication.json](publication.json) | The publication receipt has later as current_snapshot_ref and early as final_tree, with the same selection and original patch/manifest identities. |

The early tree is 508c251e5b694a2d7328145f19dd44f31ab16857; the later tree is
befc36e3265f789e28c1168e8ee6468c42631bb2. Both checks projected to
6403efc1a2b35c548b174165fd14e16c9d99396c. The pinned Django base commit is
0c42cdf0d2422f4c080e93594d5d15381d6e955e.

Each JSON record lists an original project-relative source path, its complete
source-file SHA-256, and exact RFC 6901 field paths. Fields not listed were
omitted. These JSON files are new projections, not byte-identical copies of the
original records. The two patch files are exact original bytes; their source
bindings are in candidates.json. No author-machine paths, account information,
model requests, or trajectories are included. Container/task paths inside the
recorded public command and stdout retain their original meaning.

The [existing ranker slice](../../principles/gp/original_selection_slice.py) and
[replay inputs](../../principles/gp/inputs.json) explain the deterministic selection
relation. The current supplements establish the recorded object/decision links;
they do not supply a complete runnable host environment. The original full
worker/request history is not included, and a source hash is an identity binding,
not independent authentication of a historical execution.

The historical query-14 SyntaxError remains the existing extracted observation
in the replay inputs and the [analysis report](../../principles/evidence/gp_diagnosis.md).
Its complete original trajectory was not opened during this extraction. The
early patch itself exposes the extra literal plus characters. The original
recorded ranker keeps a nonempty RAW fallback key eligible; its two single-vote
keys are tied and the earlier candidate wins. This is a selection/object-scope
case, not a measured lost solve: the later test-only candidate has no independently
measured official score here.

The patches modify Django code; see the existing
[Django license](../../principles/feedback/LICENSE-Django.txt).
