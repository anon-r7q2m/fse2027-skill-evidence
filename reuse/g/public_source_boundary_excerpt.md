## 1. Deliverable, visibility, and source boundary

Submit exactly three UTF-8 Python source files, `native_logs.py`,
`compatibility.py`, and `mechanism.py`. The entry point is
`mechanism.handle(event, state) -> {"state": ..., "effects": [...]}`.
All three files are replaceable package code. Helpers, algorithms, and private
state are implementation choices. The runtime must not import an existing G
implementation or supply parsed test states, inventory selection, obligation
judgments, or G feedback as a host capability.

The package owns raw-log parsing, actual base-PASSED inventory construction,
validation/freezing of supplied classifications, candidate interpretation,
trigger decisions, and substantive feedback. The host owns snapshot capture,
explicit projection, isolated command execution, resource enforcement, raw
receipts, and message transport. No live model call belongs inside the package.

Both methods receive the same exported public target, source, dependency
information, event/result specification, public examples, and public feedback.
They do not receive the old L3 package, its fixture module or internal state
traces, another method's submissions, hidden cases or answers, official repair
answers, or private annotations. Public expected behavior in this specification
and new public examples is intentionally visible. Neither generation context
may browse the surrounding repository to obtain excluded implementations.

The source is Agentless commit
`5ce5888b9f149beaace393957a55ea8ee46c9f71`: relevant inventory, selector,
regression execution and reranking code. Its requirements do not pin the
historical SWE-bench dependency. Revision
`726c5461e2ef52d83cf1ea2107870a8bb3328d57` is a named grading compatibility
example, not recovery of the exact original dependency stack.

Declared adaptations are complete inventory retention; externally supplied
evidence-linked three-state obligations; strict actual PASSED and execution
completeness; package-owned native parsers; original-test projection onto an
independent complete candidate copy; and feedback inside the repair loop in
place of offline ranking. The source/adaptation account is evaluated separately
from code execution. These adaptations are not called unchanged donor behavior.
