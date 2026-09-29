# s11 static diagnosis: smolagents

Status: **PREDICTION, not executed**. One primary prediction, two trigger inputs,
two controls and one candidate local intervention are frozen in this directory.
No benchmark result, live-model result, score or measured intervention effect is
claimed.

The prediction is that `fix_final_answer_code` changes literal string data while
trying to rename a variable, causing the native final-answer validation path to
reject an otherwise correct source-level result. The validator correctly rejects
the corrupted value; the defect is in the earlier adaptation. Exhausting the
configured step limit is the observable consequence, not independently a defect.

## Public obligation and independently decidable fact

- `src/smolagents/agents.py:287` calls `final_answer_checks` a
  “List of validation functions to run before accepting a final answer.” Its
  following lines specify the final answer, memory and agent arguments and a
  boolean return value.
- `src/smolagents/local_python_executor.py:335-336` says the adaptation replaces
  “variable assignments to final_answer with final_answer_variable” while
  “preserving function calls to final_answer().”
- `README.md:232` says: “Actions are now Python code snippets. Hence, tool calls
  will be performed as Python function calls.”
- The pinned native constant evaluator at
  `src/smolagents/local_python_executor.py:1461-1463` handles `ast.Constant` by
  returning `expression.value`. `FinalAnswerTool.forward`, at
  `src/smolagents/default_tools.py:89-90`, returns its argument.

These obligations do not require every wrong answer to be retried indefinitely.
They do establish a concrete, independently decidable distinction between a
variable identifier and the contents of a harmless string literal. The fixture's
exact-answer predicate is an application configuration implementing each explicit
echo task, not a new assertion presented as a framework promise.

## Complete producer-to-consumer path

1. `CodeAgent.run` installs the real tools, including the native `FinalAnswerTool`,
   in the native local executor. The public check is supplied with its actual
   `(final_answer, memory, agent)` calling convention.
2. `CodeAgent._step_stream` calls `Model.generate`, parses the returned code block,
   and passes the code through `fix_final_answer_code`. Only this model interface
   is scripted. The parser, helper and executor remain native.
3. The existing helper searches the entire source text with an assignment regex
   and then substitutes matches in the entire text. It does not exclude string
   tokens. The resulting code is recorded as native `ActionStep.code_action`.
4. `LocalPythonExecutor.__call__` invokes the complete native
   `evaluate_python_code`. Assignments, string constants, print calls and the
   `final_answer` tool execute there. The latter raises the native
   `FinalAnswerException`, which produces a native final `CodeOutput`.
5. `_step_stream` creates a native `ActionOutput` from that result. The run loop
   invokes `_validate_final_answer`; only after it succeeds does it set
   `returned_final_answer` and `ActionStep.is_final_answer`.
6. `run(..., return_full_result=True)` returns the actual native `RunResult`,
   including its `state` and output. If the single allowed action was rejected,
   the native limit handler requests the fixed fallback and sets an
   `AgentMaxStepsError`, resulting in `state="max_steps_error"`.

The result state is the accepting/terminating consumer evidence. The fixture
records native model messages, parsed action code, execution observations and
state, each actual check argument/boolean, action-final flags and the native
return value. It does not fill in a defect/fix verdict. Its `OBSERVED` status means
collection completed under the fixed provider protocol, and its process exit 0
has the same collection-only meaning.

## Frozen cases

All exact tasks, response texts, call shapes, maximum step counts and expected
facts are in `prediction.json`. Responses are selected by call index only. No
response is selected from runtime messages, error text, source path or variant.
The same fixture reads the same frozen inputs for original and patched sources.

| Case | Purpose | Expected original | Expected intervention |
| --- | --- | --- | --- |
| `t_literal_assignment_text` | A string contains `final_answer = 42`, but there is no assignment to that variable | Literal becomes `final_answer_variable = 42`; check false; native `max_steps_error` | Literal preserved; check true; native success |
| `t_literal_inside_real_assignment` | The intentionally repaired variable holds the string `final_answer` | Variable and literal both change; check false; native `max_steps_error` | Variable renamed, literal preserved; check true; native success |
| `c_successful_assignment_repair` | Preserve the helper's intended variable repair and ordinary acceptance | Repaired variable delivers `accepted`; success | Same |
| `c_execution_and_check_failure_recovery` | Preserve actual execution failure, false check and subsequent valid acceptance | `AgentExecutionError`, then rejected `rejected`, then accepted `accepted`; success | Same |

The first trigger is valid unambiguous code with an ordinary variable named
`answer`. There is no shadowed tool to fix. The second trigger exercises a real
identifier adaptation so that merely bypassing preprocessing is insufficient.
The success control also requires this adaptation: the native executor forbids
assigning to an existing static tool name. This requirement was traced in
`set_value` at `local_python_executor.py:794-805`.

The checking-failure control has three native action steps, within the common
limit of eight. Its first response deliberately raises a built-in `ValueError`.
Its second calls `final_answer("rejected")` and must fail the same public check.
Its third calls `final_answer("accepted")` and must succeed. It is legitimate for
the framework to record the first two errors and continue. This is not a claim
that an execution error should be accepted.

Every case has a frozen fallback suffix. It is unused following normal success.
Trigger scripts have two responses; the recovery-control script has four.
An unexpected call shape or script exhaustion is explicitly **INCONCLUSIVE**,
including when the native fallback handler catches the provider exception.

## Proposed local intervention

`intervention.patch` changes only `fix_final_answer_code` in
`src/smolagents/local_python_executor.py`. The original checkout was not edited.

The proposed helper parses source text to find actual `ast.Name` assignments and
direct `final_answer` calls. When adaptation is needed, it renames only Name
source spans that are not direct call targets. Back-to-front replacements keep
source positions stable. UTF-8 byte offsets match the AST's column convention;
the patch preserves formatting, string literal data, comments and attributes.
Syntactically invalid source is returned for native parsing/error handling.

This preserves the original tool integration and the checks and step limit. It
does not remove the checker, reinterpret failure as success or construct a
replacement executor. A small patch is not evidence of minimality. Existing
namespace collisions, general scope-aware renaming, dynamic rebinding and all
possible Python syntax are outside the asserted repair claim.

## Possible falsification

The prediction fails if either original trigger does not show the predicted
literal mutation in actual native action/producer/check evidence, or if the
native consumer does not take the predicted rejected/limit path. A fallback
string alone is insufficient evidence. If the original succeeds with the exact
literal under the frozen environment, the proposed failure chain is false.

The intervention fails if it does not deliver the intended unchanged string
through the actual checker and native success path, or if either control loses
its specified behavior. An exception, nonzero process exit or missing evidence
cannot establish a repair. If the intervention simply disables identifier
repair, the normal assignment-repair control is expected to reject it.

Missing dependencies, an unexpected provider call, exhaustion, guard-triggered
import failure, unavailable native implementations or process timeout are
inconclusive collection failures. They are not target defects or supported
findings. A source-checkout mismatch must be resolved using the root's selected
copy; `smolagents.__file__` is captured rather than inferred from the variant.

## Exposure and familiarity

I had general conceptual familiarity with smolagents/code agents, without a
recollection of this exact defect or patch. That is a self-report, not a guarantee
about training-data exposure. Workspace-level instructions and a general memory
summary were automatically present before assignment; no memory, manuscript,
study-result or sibling-output files were opened or used for this diagnosis.

Public upstream exposure relevant to the decision included:

- `tests/test_agents.py:501-521`: max-step tests explicitly expect an output and
  `AgentMaxStepsError`.
- `tests/test_agents.py:664-738`: final-answer tests, including a comment and
  assertion expecting an answer after state-based checks repeatedly fail.
  This is counterevidence to calling fallback output alone a bug.
- `tests/test_local_python_executor.py:2139-2175`: existing exact-text examples of
  variable repair, ordinary calls and object-attribute preservation. None of the
  displayed examples checks literal-data preservation.
- `docs/source/en/guided_tour.md:367-401`: termination description and public
  validator example. Its example signature differs from the implementation's
  current three-argument contract; the fixture follows the implementation and
  upstream tests, and does not diagnose that documentation discrepancy.
- `README.md:205-232` and
  `docs/source/en/tutorials/secure_code_execution.md:49-60`: public action and
  native-interpreter descriptions.

Additional static reads/searches were confined to `AGENTS.md`, `pyproject.toml`,
`src/smolagents/{__init__,agents,local_python_executor,models,memory,monitoring,
agent_types,default_tools,utils,remote_executors}.py`, those public documents and
the upstream test files. Nearby fake-model/test definitions and search hits in
other public docs/tests were exposed while locating these paths. No upstream
test, example, helper, framework import or fixture was executed.

One read-only `git rev-parse HEAD` attempt failed because the supplied tree has no
accessible Git metadata. The text version is `1.27.0.dev0`; no commit identity is
invented.

## Execution handoff, not an execution report

After the root freezes all required diagnostics, it can select either source copy
through `PYTHONPATH` and run, for example:

```bash
PYTHONPATH=/selected/smolagents/src /STUDY_ROOT/venv/bin/python /STUDY_ROOT/diagnostics/s11/fixture.py --case t_literal_assignment_text --workdir /owned/s11/run --output /owned/s11/run/observation.json
```

Keep `fixture.py` and `prediction.json` together. The CLI is identical for every
variant and case. Normal Python optimization level 0 is required; the native
checker uses `assert`, so optimized Python would describe another environment.
The fixture limits native snippets to 10 seconds and its process to 110 seconds;
the root should enforce the common overall limit of at most 120 seconds.

The complete native import includes an import-time `load_dotenv()` call in
`remote_executors.py`. The fixture sets `PYTHON_DOTENV_DISABLED=1`; a standard audit
hook additionally blocks dotenv file reads, networking and external commands.
It never obtains credentials or creates a provider client. These guards do not
replace framework behavior. A dependency that cannot import under these guards
must be reported as inconclusive.

Static validation is restricted to JSON/text parsing and `ast.parse` of source
text. Its success establishes syntax only. Timing and tool-call bounds are
recorded in the final handoff and `prediction.json`'s provenance field when the
files are sealed.
