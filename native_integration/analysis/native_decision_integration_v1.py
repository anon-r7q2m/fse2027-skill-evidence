"""Execute the separately frozen nine-cell saved-team integration study.

Only standard-library modules are imported before the verified worker boundary.
Do not invoke this script before independent code review and the root's freeze.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import dataclasses
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
import traceback


OLD_PATCH_SHA256 = "d2a2251069be3a83141e8d2fdaad814642e68a8abfc58f2cfde2d2644b69f269"
PATCHED_FILE = "python/packages/autogen-agentchat/src/autogen_agentchat/conditions/_terminations.py"
PROCEDURES = ("direct_original", "reloaded_original", "reloaded_patched")


@dataclasses.dataclass(frozen=True)
class Paths:
    repo: Path
    protocol: Path
    study: Path
    output: Path
    source: Path
    python: Path
    patch: Path

    @classmethod
    def read(cls, config_path: Path):
        raw = json.loads(config_path.read_text(encoding="utf-8"))
        if set(raw) != {field.name for field in dataclasses.fields(cls)}:
            raise RuntimeError("Path configuration must provide exactly the seven documented keys")
        if any(
            not isinstance(value, str) or not Path(value).is_absolute() for value in raw.values()
        ):
            raise RuntimeError("Path configuration requires explicit absolute paths")
        # Preserve the venv interpreter symlink: resolving it would select its base environment.
        paths = cls(
            **{
                key: Path(os.path.abspath(value)) if key == "python" else Path(value).resolve()
                for key, value in raw.items()
            }
        )
        if Path(__file__).resolve() != paths.repo / "analysis/native_decision_integration_v1.py":
            raise RuntimeError("Configured repository does not contain this runner")
        if paths.study.is_relative_to(paths.output) or paths.output.is_relative_to(paths.study):
            raise RuntimeError("Study and result directories must be disjoint")
        protected = (paths.protocol, paths.source, paths.python, paths.patch, config_path)
        for destination in (paths.study, paths.output):
            if destination == paths.repo or any(
                path.is_relative_to(destination) for path in protected
            ):
                raise RuntimeError("Owned destination contains a protected input")
            if destination.is_relative_to(paths.protocol) or destination.is_relative_to(
                paths.source
            ):
                raise RuntimeError("Owned destination lies within a protected input tree")
        return paths

    def as_dict(self) -> dict[str, str]:
        return {field.name: str(getattr(self, field.name)) for field in dataclasses.fields(self)}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_once(path: Path, value) -> None:
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def source_manifest(root: Path) -> dict[str, str]:
    result = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if any(part in {".git", "__pycache__", ".pytest_cache"} for part in relative.parts):
            continue
        if path.is_symlink():
            raise RuntimeError(f"Source snapshot contains an unsupported symlink: {relative}")
        if path.is_file() and path.suffix not in {".pyc", ".pyo"}:
            result[str(relative)] = digest(path)
    return result


def verify_freeze(freeze_path: Path, paths_file: Path, paths: Paths) -> dict:
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    if freeze.get("study") != "native_decision_integration_v1":
        raise RuntimeError("Wrong study freeze")
    if freeze.get("status") != "FROZEN_FOR_EXECUTION":
        raise RuntimeError("Study is not frozen for execution")
    required = {
        Path(__file__).resolve(),
        paths.protocol / "PROTOCOL.md",
        paths.protocol / "scenarios.json",
        paths.protocol / "input_trigger.csv",
        paths.protocol / "input_control.csv",
        paths.protocol / "report_generator.py",
        paths.patch,
        paths_file,
    }
    actual_paths = {Path(path).resolve() for path in freeze.get("files", {})}
    if actual_paths != required:
        raise RuntimeError("Freeze file set differs from the required study inputs")
    for path, expected in freeze["files"].items():
        if digest(Path(path)) != expected:
            raise RuntimeError(f"Frozen input changed: {Path(path).name}")
    if digest(paths.patch) != OLD_PATCH_SHA256:
        raise RuntimeError("The original a21 patch changed")
    if freeze.get("paths") != paths.as_dict():
        raise RuntimeError("Frozen path identities differ from the explicit configuration")
    if freeze.get("source_root") != str(paths.source):
        raise RuntimeError("Unexpected upstream source root")
    if freeze.get("python") != str(paths.python):
        raise RuntimeError("Unexpected dependency interpreter")
    if not freeze.get("source_files") or source_manifest(paths.source) != freeze["source_files"]:
        raise RuntimeError("Upstream source snapshot differs from the freeze")
    return freeze


async def review_csv_report(input_file: str, report_file: str, finding_file: str) -> str:
    """Read actual application artifacts and record signed-transaction consistency."""
    import csv
    import json
    from pathlib import Path

    if (input_file, report_file, finding_file) != ("input.csv", "report.json", "review.json"):
        raise ValueError("Review filenames differ from the frozen application")
    with Path(input_file).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    report = json.loads(Path(report_file).read_text(encoding="utf-8"))
    expected_rows = len(rows)
    expected_total = sum(int(row["amount_cents"]) for row in rows)
    finding = {
        "input_rows": expected_rows,
        "input_total_cents": expected_total,
        "report_rows": report["row_count"],
        "report_total_cents": report["total_cents"],
        "row_count_matches": report["row_count"] == expected_rows,
        "total_matches": report["total_cents"] == expected_total,
    }
    finding["consistent"] = finding["row_count_matches"] and finding["total_matches"]
    finding["verdict"] = "consistent" if finding["consistent"] else "requires_correction"
    finding["completion_marker"] = "REVIEW_COMPLETE"
    with Path(finding_file).open("x", encoding="utf-8") as handle:
        json.dump(finding, handle, sort_keys=True)
        handle.write("\n")
    return json.dumps(finding, sort_keys=True)


def message_record(message) -> dict:
    return {"native_type": type(message).__name__, "value": message.model_dump(mode="json")}


class NativeObserver:
    """Read native call/return frames; never replace a method or edit a frame."""

    def __init__(self, termination_code, executor_code, code_result_type):
        self.termination_code = termination_code
        self.executor_code = executor_code
        self.code_result_type = code_result_type
        self.termination_calls = []
        self.executor_results = []
        self.pending = {}
        self.errors = []

    def __call__(self, frame, event, arg):
        try:
            if frame.f_code is self.termination_code:
                if event == "call":
                    condition = frame.f_locals["self"]
                    index = len(self.termination_calls)
                    self.pending[id(frame)] = index
                    self.termination_calls.append(
                        {
                            "sources": None
                            if condition._sources is None
                            else list(condition._sources),
                            "marker": condition._termination_text,
                            "input_messages": [
                                message_record(item) for item in frame.f_locals["messages"]
                            ],
                            "returned": False,
                        }
                    )
                elif event == "return":
                    index = self.pending.pop(id(frame))
                    row = self.termination_calls[index]
                    row["returned"] = True
                    row["stop_message"] = None if arg is None else message_record(arg)
                    row["actual_matching_message"] = (
                        None if arg is None else message_record(frame.f_locals["message"])
                    )
                    row["actual_matching_text"] = None if arg is None else frame.f_locals["content"]
            elif frame.f_code is self.executor_code and event == "return":
                if isinstance(arg, self.code_result_type):
                    self.executor_results.append(
                        {
                            "code_blocks": [
                                dataclasses.asdict(item) for item in frame.f_locals["code_blocks"]
                            ],
                            "native_result": dataclasses.asdict(arg),
                        }
                    )
        except Exception as exc:
            self.errors.append({"type": type(exc).__name__, "message": str(exc)})


def make_environment(source: Path, temporary: Path, paths: Paths) -> dict[str, str]:
    return {
        "PATH": f"{paths.python.parent}:/usr/bin:/bin",
        "LANG": "C.UTF-8",
        "PYTHONPATH": os.pathsep.join(
            str(source / "python/packages" / package / "src")
            for package in ("autogen-core", "autogen-agentchat", "autogen-ext")
        ),
        "PYTHONNOUSERSITE": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHON_DOTENV_DISABLED": "1",
        "HF_HUB_OFFLINE": "1",
        "HF_HUB_DISABLE_TELEMETRY": "1",
        "OTEL_SDK_DISABLED": "true",
        "DO_NOT_TRACK": "1",
        "XDG_CACHE_HOME": str(paths.study / "cache"),
        "TMPDIR": str(temporary),
    }


async def native_workflow(launch: dict, facts: dict, paths: Paths) -> None:
    # This is the sole target-import boundary, reached only after freeze checks.
    import autogen_agentchat
    import autogen_core
    import autogen_ext.models.replay._replay_chat_completion_client as replay_module
    from autogen_agentchat.agents import AssistantAgent, CodeExecutorAgent
    from autogen_agentchat.base import TaskResult
    from autogen_agentchat.conditions import TextMentionTermination
    from autogen_agentchat.teams import BaseGroupChat, RoundRobinGroupChat
    from autogen_core import FunctionCall
    from autogen_core.code_executor import CodeResult
    from autogen_core.models import CreateResult, ModelFamily, RequestUsage
    from autogen_core.tools import FunctionTool
    from autogen_ext.code_executors.local import LocalCommandLineCodeExecutor
    from autogen_ext.models.replay import ReplayChatCompletionClient

    source = Path(launch["source"])
    modules = (autogen_agentchat, autogen_core, replay_module)
    origins = {module.__name__: str(Path(module.__file__).resolve()) for module in modules}
    if any(not Path(path).is_relative_to(source) for path in origins.values()):
        raise RuntimeError("Native import escaped the selected source copy")
    facts["source_origins"] = origins
    scenario = launch["scenario"]
    marker = launch["marker"]
    work = Path(launch["work"])
    code = (paths.protocol / "report_generator.py").read_text(encoding="utf-8")
    task = (
        (
            "Generate report.json from input.csv using the supplied block, then let the reviewer "
            "record whether every signed transaction is included in the row count and total.\n"
            if scenario["review_required"]
            else "Generate report.json from input.csv using the supplied block. This workflow "
            "allows any participant's completion marker to finish; review is optional.\n"
        )
        + "```python\n"
        + code
        + "```"
    )
    if marker in task:
        raise RuntimeError("Initial task contains the full completion marker")
    reply = CreateResult(
        finish_reason="function_calls",
        content=[
            FunctionCall(
                id="review-call-1",
                name="review_csv_report",
                arguments=json.dumps(
                    {
                        "input_file": "input.csv",
                        "report_file": "report.json",
                        "finding_file": "review.json",
                    },
                    sort_keys=True,
                ),
            )
        ],
        usage=RequestUsage(prompt_tokens=0, completion_tokens=0),
        cached=False,
    )
    client = ReplayChatCompletionClient(
        [reply],
        model_info={
            "vision": False,
            "function_calling": True,
            "json_output": False,
            "family": ModelFamily.UNKNOWN,
            "structured_output": False,
        },
    )
    executor = LocalCommandLineCodeExecutor(timeout=5, work_dir=work, cleanup_temp_files=False)
    producer = CodeExecutorAgent("executor", code_executor=executor, sources=["user"])
    tool = FunctionTool(
        review_csv_report,
        description="Read input.csv and report.json; write their consistency finding.",
    )
    reviewer = AssistantAgent(
        "reviewer",
        model_client=client,
        tools=[tool],
        system_message="Use review_csv_report to independently inspect the actual CSV and generated report.",
        model_client_stream=False,
        reflect_on_tool_use=False,
        max_tool_iterations=1,
        tool_call_summary_format="{result}",
    )
    condition = TextMentionTermination(marker, sources=scenario["sources"])
    team = RoundRobinGroupChat([producer, reviewer], termination_condition=condition, max_turns=4)
    facts["task"] = task
    facts["provider_script"] = reply.model_dump(mode="json")
    facts["declared_sources"] = scenario["sources"]
    if launch["procedure"] != "direct_original":
        exported = team.dump_component().model_dump(mode="json")
        write_once(work / "team.json", exported)
        read_back = json.loads((work / "team.json").read_text(encoding="utf-8"))
        facts["exported_team"] = read_back
        team = BaseGroupChat.load_component(read_back)
        # Obtain actual loaded instances for public lifecycle calls and read-only observation.
        producer = next(
            participant for participant in team._participants if participant.name == "executor"
        )
        reviewer = next(
            participant for participant in team._participants if participant.name == "reviewer"
        )
        executor = producer._code_executor
        condition = team._termination_condition
    effective_client = reviewer._model_client
    if not isinstance(effective_client, ReplayChatCompletionClient):
        raise RuntimeError("Loaded provider is not the native replay component")
    if not isinstance(executor, LocalCommandLineCodeExecutor):
        raise RuntimeError("Loaded executor is not the selected native local executor")
    if not isinstance(condition, TextMentionTermination):
        raise RuntimeError("Loaded condition is not the selected native condition")
    facts["effective_sources"] = None if condition._sources is None else list(condition._sources)
    facts["native_types"] = {
        name: f"{type(value).__module__}.{type(value).__name__}"
        for name, value in {
            "team": team,
            "executor_agent": producer,
            "executor": executor,
            "reviewer": reviewer,
            "provider": effective_client,
            "termination": condition,
        }.items()
    }
    observer = NativeObserver(
        TextMentionTermination.__call__.__code__,
        LocalCommandLineCodeExecutor.execute_code_blocks.__code__,
        CodeResult,
    )
    previous_profile = sys.getprofile()
    if previous_profile is not None:
        raise RuntimeError("An external profiler is already installed")
    await executor.start()
    try:
        sys.setprofile(observer)
        async for item in team.run_stream(task=task):
            if isinstance(item, TaskResult):
                facts["task_result"] = {
                    "stop_reason": item.stop_reason,
                    "messages": [message_record(message) for message in item.messages],
                }
            else:
                facts["stream"].append(message_record(item))
    finally:
        sys.setprofile(previous_profile)
        facts["termination_calls"] = observer.termination_calls
        facts["executor_results"] = observer.executor_results
        facts["observer_errors"] = observer.errors
        facts["observer_pending_calls"] = len(observer.pending)
        facts["provider_calls"] = [
            {
                "messages": [message_record(message) for message in call["messages"]],
                "tools": call["tools"],
                "json_output": call["json_output"],
                "extra_create_args": call["extra_create_args"],
                "cancellation_token_present": call["cancellation_token"] is not None,
            }
            for call in effective_client.create_calls
        ]
        await executor.stop()
        await effective_client.close()
        if effective_client is not client:
            await client.close()


def assess(launch: dict, facts: dict) -> None:
    scenario = launch["scenario"]
    work = Path(launch["work"])
    with (work / "input.csv").open(newline="", encoding="utf-8") as handle:
        inputs = list(csv.DictReader(handle))
    facts["input_data"] = (work / "input.csv").read_text(encoding="utf-8")
    facts["report"] = json.loads((work / "report.json").read_text(encoding="utf-8"))
    finding_path = work / "review.json"
    facts["review_finding"] = (
        json.loads(finding_path.read_text(encoding="utf-8")) if finding_path.exists() else None
    )
    facts["report_correct"] = facts["report"]["row_count"] == len(inputs) and facts["report"][
        "total_cents"
    ] == sum(int(row["amount_cents"]) for row in inputs)
    if (
        facts.get("task_result") is None
        or facts.get("observer_errors")
        or facts.get("observer_pending_calls")
        or len(facts.get("provider_calls", [])) > 1
        or len(facts.get("executor_results", [])) != 1
        or facts["executor_results"][0]["native_result"]["exit_code"] != 0
        or not facts.get("termination_calls")
        or any(not call.get("returned") for call in facts["termination_calls"])
    ):
        raise RuntimeError("Incomplete native observation or unexpected provider/executor behavior")
    tool_results = [
        result
        for item in facts["stream"]
        if item["native_type"] == "ToolCallExecutionEvent"
        for result in item["value"]["content"]
    ]
    if len(tool_results) > 1 or any(result.get("is_error") for result in tool_results):
        raise RuntimeError(
            "Native review exceeded the one-tool allowance or returned an execution error"
        )
    review_events = {
        kind: [item for item in facts["stream"] if item["native_type"] == kind]
        for kind in ("ToolCallRequestEvent", "ToolCallExecutionEvent", "ToolCallSummaryMessage")
    }
    executor_output = facts["executor_results"][0]["native_result"]["output"]
    receiving_messages = [
        message
        for call in facts["provider_calls"]
        for message in call["messages"]
        if message["value"].get("source") == "executor"
    ]
    received_report = (
        len(facts["provider_calls"]) == 1
        and any(
            message["value"].get("content") == executor_output for message in receiving_messages
        )
        and json.dumps(facts["report"], sort_keys=True) in executor_output
    )
    facts["reviewer_receiving_messages"] = receiving_messages
    facts["reviewer_received_executor_report"] = (
        received_report if facts["provider_calls"] else None
    )

    def decoded(text):
        try:
            return json.loads(text)
        except (TypeError, json.JSONDecodeError):
            return None

    expected_call = facts["provider_script"]["content"]
    request = review_events["ToolCallRequestEvent"]
    execution = review_events["ToolCallExecutionEvent"]
    summaries = review_events["ToolCallSummaryMessage"]
    finding = facts["review_finding"]
    expected_finding = {
        "input_rows": len(inputs),
        "input_total_cents": sum(int(row["amount_cents"]) for row in inputs),
        "report_rows": facts["report"]["row_count"],
        "report_total_cents": facts["report"]["total_cents"],
        "row_count_matches": facts["report"]["row_count"] == len(inputs),
        "total_matches": facts["report"]["total_cents"]
        == sum(int(row["amount_cents"]) for row in inputs),
        "consistent": facts["report_correct"],
        "verdict": "consistent" if facts["report_correct"] else "requires_correction",
        "completion_marker": launch["marker"],
    }
    delivery = {
        "reviewer_received_executor_report": received_report,
        "one_reviewer_request": len(request) == 1 and request[0]["value"]["source"] == "reviewer",
        "request_matches_fixed_call": len(request) == 1
        and request[0]["value"]["content"] == expected_call,
        "one_reviewer_execution": len(execution) == 1
        and execution[0]["value"]["source"] == "reviewer",
        "result_identity": len(tool_results) == 1
        and tool_results[0].get("call_id") == expected_call[0]["id"]
        and tool_results[0].get("name") == expected_call[0]["name"]
        and tool_results[0].get("is_error") is False,
        "result_matches_finding": finding is not None
        and len(tool_results) == 1
        and decoded(tool_results[0]["content"]) == finding,
        "finding_matches_artifacts": finding == expected_finding,
        "one_reviewer_summary": len(summaries) == 1
        and summaries[0]["value"]["source"] == "reviewer",
        "summary_links_request_and_result": len(summaries) == 1
        and summaries[0]["value"]["tool_calls"] == expected_call
        and summaries[0]["value"]["results"] == tool_results,
        "summary_matches_finding": finding is not None
        and len(summaries) == 1
        and decoded(summaries[0]["value"]["content"]) == finding,
        "summary_delivered_in_task_result": len(summaries) == 1
        and summaries[0] in facts["task_result"]["messages"],
        "summary_present_in_actual_termination_input": len(summaries) == 1
        and any(summaries[0] in call["input_messages"] for call in facts["termination_calls"]),
    }
    facts["finding_delivery_checks"] = delivery
    facts["finding_delivered"] = all(delivery.values())
    expected_review = scenario["id"] == "C" or (
        scenario["id"] == "T" and launch["procedure"] != "reloaded_original"
    )
    expected_sources = None if launch["procedure"] == "reloaded_original" else scenario["sources"]
    stops = [call for call in facts["termination_calls"] if call.get("stop_message") is not None]
    matches = {
        "effective_sources": facts["effective_sources"] == expected_sources,
        "report_rows": facts["report"]["row_count"] == scenario["expected_report_rows"],
        "report_total": facts["report"]["total_cents"] == scenario["expected_report_total_cents"],
        "provider_count": len(facts["provider_calls"]) == int(expected_review),
        "tool_count": len(tool_results) == int(expected_review),
        "finding_presence": (facts["review_finding"] is not None) == expected_review,
        "finding_delivery": facts["finding_delivered"] == expected_review,
        "one_native_stop": len(stops) == 1,
    }
    if len(stops) == 1:
        matches["stop_source"] = stops[0]["actual_matching_message"]["value"]["source"] == (
            "reviewer" if expected_review else "executor"
        )
    if expected_review and facts["review_finding"] is not None:
        finding = facts["review_finding"]
        matches["finding_input_rows"] = finding["input_rows"] == scenario["expected_input_rows"]
        matches["finding_input_total"] = (
            finding["input_total_cents"] == scenario["expected_input_total_cents"]
        )
        matches["finding_report_rows"] = finding["report_rows"] == facts["report"]["row_count"]
        matches["finding_report_total"] = (
            finding["report_total_cents"] == facts["report"]["total_cents"]
        )
        matches["finding_correctness"] = finding["consistent"] == facts["report_correct"]
    facts["review_obligation_fulfilled"] = (
        None if not scenario["review_required"] else facts["finding_delivered"]
    )
    facts["prediction_checks"] = matches
    facts["collection_status"] = "COMPLETE"
    facts["prediction_status"] = "SUPPORTED" if all(matches.values()) else "NOT_SUPPORTED"


def worker(launch_path: Path, paths_file: Path, paths: Paths) -> None:
    launch = json.loads(launch_path.read_text(encoding="utf-8"))
    freeze_path = Path(launch["freeze"])
    freeze = verify_freeze(freeze_path, paths_file, paths)
    if digest(freeze_path) != launch["freeze_sha256"]:
        raise RuntimeError("Launch freeze identity changed")
    source = Path(launch["source"])
    if source_manifest(source) != launch["source_files"]:
        raise RuntimeError("Selected source copy changed before worker launch")
    if launch["procedure"] not in PROCEDURES:
        raise RuntimeError("Unknown deployment procedure")
    if launch["paths_file"] != str(paths_file) or launch["paths"] != paths.as_dict():
        raise RuntimeError("Worker path configuration differs from its launch")
    if (
        not Path(launch["work"]).resolve().is_relative_to(paths.study)
        or not launch_path.is_relative_to(paths.output)
        or not source.resolve().is_relative_to(paths.study / "sources")
    ):
        raise RuntimeError("Worker paths escape the owned study")
    scenario_set = json.loads((paths.protocol / "scenarios.json").read_text(encoding="utf-8"))
    if (
        launch["scenario"] not in scenario_set["scenarios"]
        or launch["marker"] != scenario_set["marker"]
    ):
        raise RuntimeError("Launch scenario differs from the frozen scenario")
    if digest(Path(launch["work"]) / "input.csv") != digest(
        paths.protocol / launch["scenario"]["input"]
    ):
        raise RuntimeError("Application input changed")
    if any(
        (Path(launch["work"]) / name).exists()
        for name in ("report.json", "review.json", "team.json")
    ):
        raise RuntimeError("Worker application outputs already exist")
    facts = {
        "study": freeze["study"],
        "cell": launch["cell"],
        "scenario": launch["scenario"]["id"],
        "procedure": launch["procedure"],
        "collection_status": "INCONCLUSIVE",
        "prediction_status": "UNEVALUATED",
        "stream": [],
        "exceptions": [],
    }
    start = time.monotonic()

    def alarm_handler(signum, frame):
        raise TimeoutError("Frozen 80-second worker alarm reached")

    signal.signal(signal.SIGALRM, alarm_handler)
    signal.alarm(80)
    try:
        asyncio.run(asyncio.wait_for(native_workflow(launch, facts, paths), timeout=60))
        assess(launch, facts)
    except Exception as exc:
        facts["exceptions"].append(
            {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()}
        )
    finally:
        signal.alarm(0)
        facts["elapsed_seconds"] = time.monotonic() - start
        for name in ("input.csv", "report.json", "review.json", "team.json"):
            path = Path(launch["work"]) / name
            if path.is_file():
                facts.setdefault("artifact_files", {})[name] = {
                    "sha256": digest(path),
                    "text": path.read_text(encoding="utf-8"),
                }
        write_once(launch_path.parent / "observation.json", facts)
    print(
        json.dumps({key: facts[key] for key in ("cell", "collection_status", "prediction_status")})
    )


def compare_configurations(cells: dict, scenario: dict) -> dict:
    """Compare complete original/patched exports with only two precise substitutions."""
    result = {"scenario": scenario["id"], "status": "INCONCLUSIVE"}
    try:
        original_cell = cells["reloaded_original"]
        patched_cell = cells["reloaded_patched"]
        original = json.loads(json.dumps(original_cell["observation"]["exported_team"]))
        patched = json.loads(json.dumps(patched_cell["observation"]["exported_team"]))
        checks = {}
        restrictions = {}
        for name, exported, cell in (
            ("original", original, original_cell),
            ("patched", patched, patched_cell),
        ):
            participants = exported["config"]["participants"]
            if len(participants) != 2 or [item["config"]["name"] for item in participants] != [
                "executor",
                "reviewer",
            ]:
                raise RuntimeError("Unexpected participant structure in saved configuration")
            executor_config = participants[0]["config"]["code_executor"]["config"]
            checks[f"{name}_work_dir"] = executor_config["work_dir"] == cell["launch"]["work"]
            executor_config["work_dir"] = "<owned-cell-work-directory>"
            termination_config = exported["config"]["termination_condition"]["config"]
            restrictions[name] = {
                "present": "sources" in termination_config,
                "value": termination_config.get("sources"),
            }
            # Normalize only this exact decision field; keep every other sources field.
            termination_config["sources"] = scenario["sources"]
        checks["original_omits_termination_sources"] = not restrictions["original"]["present"]
        checks["patched_exports_declared_sources"] = (
            restrictions["patched"]["present"]
            and restrictions["patched"]["value"] == scenario["sources"]
        )
        checks["all_other_config_fields_equal"] = original == patched
        checks["same_declared_task_and_provider"] = all(
            cells[procedure]["observation"][field] == cells["direct_original"]["observation"][field]
            for procedure in PROCEDURES
            for field in ("task", "provider_script", "declared_sources")
        )
        result.update(
            {
                "status": "MATCH" if all(checks.values()) else "MISMATCH",
                "checks": checks,
                "observed_termination_sources": restrictions,
                "normalized_paths_only": [
                    "/config/participants/0/config/code_executor/config/work_dir",
                    "/config/termination_condition/config/sources",
                ],
                "normalized_full_config_sha256": {
                    name: hashlib.sha256(
                        json.dumps(value, sort_keys=True).encode("utf-8")
                    ).hexdigest()
                    for name, value in (("original", original), ("patched", patched))
                },
            }
        )
    except (KeyError, TypeError, ValueError, RuntimeError) as exc:
        result["error"] = {"type": type(exc).__name__, "message": str(exc)}
    return result


def run(freeze_path: Path, paths_file: Path, paths: Paths) -> None:
    freeze_path = freeze_path.resolve()
    freeze = verify_freeze(freeze_path, paths_file, paths)
    if paths.output.exists() or paths.study.exists():
        raise RuntimeError("Study/output already exists; this version cannot be rerun")
    paths.output.mkdir()
    paths.study.mkdir()
    write_once(
        paths.output / "STARTED.json",
        {
            "freeze_sha256": digest(freeze_path),
            "paths": paths.as_dict(),
            "unix_time": time.time(),
        },
    )
    sources = {}
    source_maps = {}
    for name in ("original", "patched"):
        path = paths.study / "sources" / name
        shutil.copytree(
            paths.source,
            path,
            ignore=shutil.ignore_patterns("__pycache__", ".git", ".pytest_cache"),
        )
        if name == "patched":
            result = subprocess.run(
                ["patch", "--batch", "--forward", "-p1", "-i", str(paths.patch)],
                cwd=path,
                env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"},
                capture_output=True,
                text=True,
                timeout=20,
                check=False,
            )
            write_once(
                paths.output / "patch_application.json",
                {
                    "return_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "patch_sha256": digest(paths.patch),
                },
            )
            if result.returncode != 0:
                raise RuntimeError("The unchanged a21 patch did not apply")
        observed = source_manifest(path)
        if set(observed) != set(freeze["source_files"]):
            raise RuntimeError("Source copy file inventory changed")
        changed = [key for key, value in observed.items() if value != freeze["source_files"][key]]
        if changed != ([PATCHED_FILE] if name == "patched" else []):
            raise RuntimeError("Unexpected target-source change")
        sources[name] = path
        source_maps[name] = observed
    scenarios = json.loads((paths.protocol / "scenarios.json").read_text(encoding="utf-8"))
    if scenarios["procedures"] != list(PROCEDURES) or [
        row["id"] for row in scenarios["scenarios"]
    ] != ["T", "C", "U"]:
        raise RuntimeError("The fixed nine-cell matrix changed")
    rows = []
    comparisons = []
    for scenario in scenarios["scenarios"]:
        scenario_cells = {}
        for procedure in PROCEDURES:
            verify_freeze(freeze_path, paths_file, paths)
            number = len(rows) + 1
            cell = f"{number:02d}_{scenario['id']}_{procedure}"
            cell_output = paths.output / cell
            work = paths.study / "work" / cell
            temporary = paths.study / "temporary" / cell
            for path in (cell_output, work, temporary):
                path.mkdir(parents=True)
            shutil.copyfile(paths.protocol / scenario["input"], work / "input.csv")
            source_name = "patched" if procedure == "reloaded_patched" else "original"
            launch = {
                "cell": cell,
                "scenario": scenario,
                "procedure": procedure,
                "marker": scenarios["marker"],
                "source": str(sources[source_name]),
                "source_files": source_maps[source_name],
                "work": str(work),
                "freeze": str(freeze_path),
                "freeze_sha256": digest(freeze_path),
                "paths_file": str(paths_file),
                "paths": paths.as_dict(),
            }
            launch_path = cell_output / "launch.json"
            write_once(launch_path, launch)
            with (
                (cell_output / "stdout.txt").open("xb") as stdout,
                (cell_output / "stderr.txt").open("xb") as stderr,
            ):
                child = subprocess.Popen(
                    [
                        str(paths.python),
                        "-B",
                        str(Path(__file__).resolve()),
                        "--paths",
                        str(paths_file),
                        "--worker",
                        str(launch_path),
                    ],
                    cwd=work,
                    env=make_environment(sources[source_name], temporary, paths),
                    stdout=stdout,
                    stderr=stderr,
                    start_new_session=True,
                )
                timed_out = False
                try:
                    return_code = child.wait(timeout=90)
                except subprocess.TimeoutExpired:
                    timed_out = True
                    os.killpg(child.pid, signal.SIGKILL)
                    return_code = child.wait()
            observation_path = cell_output / "observation.json"
            observation = (
                json.loads(observation_path.read_text(encoding="utf-8"))
                if observation_path.exists()
                else {}
            )
            scenario_cells[procedure] = {"launch": launch, "observation": observation}
            row = {
                "cell": cell,
                "return_code": return_code,
                "outer_timeout": timed_out,
                "collection_status": observation.get("collection_status", "INCONCLUSIVE"),
                "prediction_status": observation.get("prediction_status", "UNEVALUATED"),
            }
            if return_code != 0 or timed_out:
                row["collection_status"] = "INCONCLUSIVE"
                row["prediction_status"] = "UNEVALUATED"
            rows.append(row)
            write_once(cell_output / "receipt.json", row)
            print(json.dumps(row), flush=True)
        comparisons.append(compare_configurations(scenario_cells, scenario))
    write_once(paths.output / "CONFIG_EQUIVALENCE.json", {"comparisons": comparisons})
    unchanged = source_manifest(paths.source) == freeze["source_files"]
    copies_unchanged = all(source_manifest(sources[name]) == source_maps[name] for name in sources)
    write_once(
        paths.output / "CLOSED.json",
        {
            "study": "native_decision_integration_v1",
            "status": "FIXED_NINE_CELL_VERSION_CLOSED",
            "rows": rows,
            "original_source_unchanged": unchanged,
            "source_copies_unchanged": copies_unchanged,
            "configuration_comparisons": comparisons,
            "comparison_prerequisites_met": unchanged
            and copies_unchanged
            and all(item["status"] == "MATCH" for item in comparisons),
            "new_defect_discoveries": 0,
            "live_model_calls": 0,
            "benchmark_scores": 0,
            "interpretation": "Integration observations require independent adjudication; closure is not support.",
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--paths", required=True, type=Path, help="Explicit absolute root-path JSON"
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--freeze", type=Path, help="Run the fixed matrix after a root-created freeze"
    )
    mode.add_argument("--worker", type=Path, help="Internal single-cell launch receipt")
    args = parser.parse_args()
    paths_file = args.paths.resolve()
    paths = Paths.read(paths_file)
    if args.worker is not None:
        worker(args.worker.resolve(), paths_file, paths)
    else:
        run(args.freeze, paths_file, paths)


if __name__ == "__main__":
    main()
