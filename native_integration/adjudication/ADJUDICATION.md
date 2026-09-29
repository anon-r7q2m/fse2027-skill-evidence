# Native decision integration v1: independent result adjudication

Date: 2026-09-29. Adjudicator: `score_witness_plan`.

**Disposition: scoped T/C evidence is supported; the frozen global prerequisite
remains unmet.** All nine cells completed and matched their local behavioral
predictions. T and C each have a passing frozen R/P configuration comparison.
U has observed legal behavior but a failed frozen configuration assertion, so
this is not an all-controls-pass or full-prespecified-matrix success.

The machine-readable record is [ADJUDICATION.json](ADJUDICATION.json). Original
observations, receipts and failed flags remain unchanged under
`results_cache/native_decision_integration_v1/`. No target was rerun, no runner
was repaired, and no failed gate was overridden during this adjudication.

## What was checked

The root froze eight inputs and an upstream manifest of 1,837 files at
`2026-09-29T15:57:27.703732+00:00`, then executed the prescribed matrix once.
I independently read all nine raw observations, launch records and parent wait
receipts; all nine parent receipts record return code 0 without timeout.

This audit used standard-library file/JSON/CSV reads, arithmetic, source-text
inspection and hashing. It did not import AutoGen or the runner, construct/load a
team, execute the application, call a model/provider, run a grader or container,
or alter original experiment files. I was the pre-execution static reviewer,
not a fresh manuscript reviewer, and this adjudication has no acceptance score.

The following checks were recomputed from source records, not accepted merely
from the runner's `SUPPORTED` flags:

- All eight frozen input hashes and all nine freeze/path/source bindings match.
  The upstream source and original copy each match all 1,837 frozen file hashes.
  The patched copy has the same inventory, differs in only `_terminations.py`,
  and matches exactly the three changes in the unchanged prior a21 patch.
- Each cell executed exactly the frozen application program once with exit code
  0. Its actual code file, output, input CSV, report, saved JSON where present,
  and finding where present match their observation records and hashes.
- The original stream and final `TaskResult` message sequences agree. All 23
  observed termination calls returned; no observer errors, incomplete calls or
  worker exceptions were recorded. Each cell has one actual native stop.
- Five actual replay-provider requests invoked five native review-tool calls.
  Each request's tool name, call ID and arguments match the fixed request. The
  actual provider input contains the unchanged executor report message.
- All five findings equal an independent signed-row/count computation over the
  actual input and report. Tool result, finding file and summary agree as JSON;
  request/result links agree, and that summary occurs in both the final result
  and actual termination input. No finding exists in the other four cells.
- Full R/P configuration comparisons were independently reconstructed using only
  the two frozen substitutions. Their recorded T=`MATCH`, C=`MATCH`,
  U=`MISMATCH` results, including U's single failed assertion, are reproduced.

Native replay requests are deterministic scripted requests, not external model
calls. Nine local cell completions and nine local prediction matches are not
benchmark scores or nine independent discoveries.

## Observed application behavior

D is direct original execution; R is original full-team JSON export/load; P is
new full-team JSON export/load under the unchanged a21 patch. A finding is
reported only when its complete delivery chain was verified.

| Scenario | Procedure | Effective source restriction | Actual review calls | Delivered finding | Report correct? | Actual stop message | Required review met? |
| --- | --- | --- | ---: | --- | --- | --- | --- |
| T | D | reviewer | 1 | requires correction | No | reviewer tool execution event | Yes |
| T | R | none | 0 | absent | No | executor text | No |
| T | P | reviewer | 1 | requires correction | No | reviewer tool execution event | Yes |
| C | D | reviewer | 1 | consistent | Yes | reviewer tool execution event | Yes |
| C | R | none | 1 | consistent | Yes | reviewer tool execution event | Yes |
| C | P | reviewer | 1 | consistent | Yes | reviewer tool execution event | Yes |
| U | D | none | 0 | absent | No | executor text | Not required |
| U | R | none | 0 | absent | No | executor text | Not required |
| U | P | none | 0 | absent | No | executor text | Not required |

T's unchanged application program produced two rows totaling 1,950 cents instead
of the CSV's three signed rows totaling 1,750 cents. D and P actually detected and
reported this discrepancy; they did not repair the report. R stopped on the
executor's note marker before the reviewer was called. That is skipped required
review, not evidence that a reviewer wrongly approved the report.

C produced the correct three rows totaling 2,150 cents, and all three procedures
delivered a consistent finding. R still lost the source restriction; this input
simply did not trigger an early executor stop. C establishes this normal behavior,
not universal policy preservation or a one-variable causal contrast with T.

U used the same input and program bytes as T while declaring unrestricted
stopping and optional review. All three procedures actually stopped on executor
text, legally under that declaration. Their reports remain incorrect. The U
observations are retained with the failed configuration assertion below.

## Failed frozen assertion: retain, explain, do not repair

The exact failed check is U's `patched_exports_declared_sources`. It requires both
that the `sources` field be present in P's exported termination configuration and
that its value equal the declaration. In U the declaration is `None`; the field
is absent in both R and P, making that frozen presence requirement false.

The fixed native serialization source explains this specific observation:

```text
autogen-core/src/autogen_core/_component_config.py:179
obj_config = self._to_config().model_dump(exclude_none=True)
```

The unchanged a21 patch defines `sources: List[str] | None = None`, exports the
current `None` into that configuration model, and loads `config.sources` into the
condition. Native dumping therefore omits the None-valued field; native loading
restores its default `None`. All three U consumers were actually observed with
`sources=None`. Every other full-configuration field compared equal after the
exact owned-work-directory substitution; no additional difference is concealed.

This is a post-execution diagnosis of an overly strict study assertion. The
pre-execution static review also missed the distinction between absent optional
fields and explicitly present nulls. It is not a new AutoGen defect, an amendment
to the frozen criterion, or permission to replace the failed result with a pass.

The following original facts are preserved:

```text
U.config.status = MISMATCH
U.config.patched_exports_declared_sources = false
CLOSED.comparison_prerequisites_met = false
```

The adjudicated global gate is also **false**, with no override. T and C support
their individually matched, complete observed contrasts. U is described only as
observed legal behavior with an unmet frozen assertion. The complete matrix must
not be described as having passed all prespecified prerequisites. This scoped
interpretation is explicitly qualified after execution, not relabeled as an
unqualified confirmatory success.

## Defensible claim and limits

In this fixed full-team configuration lifecycle, original loading discarded a
declared reviewer restriction and stopped a report workflow before its functioning
deterministic review tool was invoked. Direct execution and a newly serialized
team under the known patch delivered the discrepancy finding. The normal-input
comparison completed review in all three procedures. These T/C comparisons pass
their own frozen configuration checks, while the optional-review U comparison
retains a failed null-field presence assertion and the global gate remains unmet.

This extension supplies application-chain evidence for the already known a21
mechanism. It measures neither production prevalence, live-model judgment,
general serialization correctness, report repair, aggregation/scaling benefit,
nor benchmark improvement. It does not recover already saved lossy JSON. All
earlier experiments and discovery counts remain closed; new independent defect
discoveries, live provider API calls and benchmark scores are each zero.

