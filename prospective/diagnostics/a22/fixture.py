"""Frozen a22 fixture. Do not run until every diagnostic arm is frozen.

The caller selects the complete native source via PYTHONPATH. This file does
not choose an original/patched arm, patch modules, or implement termination.
Run under an outer 120-second process timeout. The internal team timeout is
90 seconds and every native local command has a 5-second timeout.
"""

from __future__ import annotations

import argparse
import asyncio
import inspect
import json
import signal
import sys
import time
from pathlib import Path
from typing import Any


class ScriptProtocolError(RuntimeError):
    pass


def dump_message(message: Any) -> dict[str, Any]:
    return {
        "python_type": type(message).__name__,
        "data": message.model_dump(mode="json"),
    }


async def run_case(case: dict[str, Any], workdir: Path, report: dict[str, Any]) -> None:
    # All framework imports deliberately occur only when the root runs the CLI.
    from autogen_agentchat.agents import CodeExecutorAgent
    from autogen_agentchat.base import TaskResult
    from autogen_agentchat.conditions import MaxMessageTermination
    from autogen_agentchat.messages import (
        BaseAgentEvent,
        BaseChatMessage,
        CodeExecutionEvent,
        CodeGenerationEvent,
    )
    from autogen_agentchat.teams import RoundRobinGroupChat
    from autogen_ext.code_executors.local import LocalCommandLineCodeExecutor
    from autogen_ext.models.replay import ReplayChatCompletionClient

    frozen_input = case["input"]
    responses = tuple(frozen_input["model_responses"])

    class StrictScriptedClient(ReplayChatCompletionClient):
        """Only the provider is scripted; outputs depend solely on call index."""

        def __init__(self) -> None:
            super().__init__(list(responses))
            self.attempts: list[dict[str, Any]] = []
            self.responses_returned = 0
            self.exhaustion_attempted = False
            self.unexpected_call: str | None = None

        def reject(self, reason: str) -> None:
            self.unexpected_call = reason
            raise ScriptProtocolError(reason)

        async def create(self, messages: Any, **kwargs: Any) -> Any:
            ordinal = self.responses_returned
            attempt = {
                "ordinal": ordinal,
                "method": "create",
                "keyword_names": sorted(kwargs),
                "messages": [dump_message(message) for message in messages],
            }
            self.attempts.append(attempt)
            if ordinal >= len(responses):
                self.exhaustion_attempted = True
                raise ScriptProtocolError("script_exhausted")
            # Generation and reflection have distinct, source-traced call shapes.
            # Message contents are recorded but never select or alter a response.
            if ordinal % 2 == 0:
                if set(kwargs) != {"tools", "cancellation_token"}:
                    self.reject("unexpected_generation_keyword_shape")
                if kwargs["tools"] != [] or kwargs["cancellation_token"] is None:
                    self.reject("unexpected_generation_argument_values")
            elif kwargs:
                self.reject("unexpected_reflection_keyword_shape")
            response = await super().create(messages, **kwargs)
            self.responses_returned += 1
            attempt["returned_response_index"] = ordinal
            return response

        async def create_stream(self, *args: Any, **kwargs: Any) -> Any:
            self.attempts.append({"method": "create_stream", "keyword_names": sorted(kwargs)})
            self.reject("unexpected_streaming_call")
            if False:
                yield ""

    report["native_import_paths"] = {
        "CodeExecutorAgent": inspect.getfile(CodeExecutorAgent),
        "LocalCommandLineCodeExecutor": inspect.getfile(LocalCommandLineCodeExecutor),
        "RoundRobinGroupChat": inspect.getfile(RoundRobinGroupChat),
        "MaxMessageTermination": inspect.getfile(MaxMessageTermination),
        "ReplayChatCompletionClient": inspect.getfile(ReplayChatCompletionClient),
    }
    client = StrictScriptedClient()
    executor = LocalCommandLineCodeExecutor(
        work_dir=workdir,
        timeout=frozen_input["executor_timeout_seconds"],
        cleanup_temp_files=True,
    )
    agent = CodeExecutorAgent(
        "executor",
        code_executor=executor,
        model_client=client,
        model_client_stream=False,
        max_retries_on_error=0,
    )
    termination = MaxMessageTermination(**frozen_input["termination"])
    team = RoundRobinGroupChat(
        [agent],
        termination_condition=termination,
        max_turns=frozen_input["max_turns"],
        emit_team_events=False,
    )
    native_messages: list[Any] = []
    result: TaskResult | None = None

    async def collect() -> None:
        nonlocal result
        async for event in team.run_stream(task=frozen_input["task"]):
            if isinstance(event, TaskResult):
                result = event
            else:
                native_messages.append(event)

    try:
        await executor.start()
        await asyncio.wait_for(collect(), timeout=90)
        if result is None:
            raise RuntimeError("native_team_produced_no_TaskResult")
        report["run_status"] = "COMPLETED"
    except Exception as error:
        report["run_status"] = "INCONCLUSIVE"
        report["error"] = {"type": type(error).__name__, "message": str(error)}
    finally:
        report["provider"] = {
            "responses_provided": len(responses),
            "responses_returned": client.responses_returned,
            "responses_remaining": len(responses) - client.responses_returned,
            "script_exhausted": client.exhaustion_attempted,
            "unexpected_call": client.unexpected_call,
            "attempts": client.attempts,
        }
        report["native_stream"] = [dump_message(message) for message in native_messages]
        report["producer_facts"] = {
            "code_generation_events": [
                dump_message(message) for message in native_messages if isinstance(message, CodeGenerationEvent)
            ],
            "code_execution_events": [
                dump_message(message) for message in native_messages if isinstance(message, CodeExecutionEvent)
            ],
            "exit_codes": [
                message.result.exit_code for message in native_messages if isinstance(message, CodeExecutionEvent)
            ],
        }
        report["native_consumer"] = {
            "task_result_received": result is not None,
            "stop_reason": result.stop_reason if result is not None else None,
            "messages": [dump_message(message) for message in result.messages] if result is not None else None,
        }
        report["observed_counts"] = {
            "stream_messages": len(native_messages),
            "agent_events": sum(isinstance(message, BaseAgentEvent) for message in native_messages),
            "chat_messages": sum(isinstance(message, BaseChatMessage) for message in native_messages),
            "executor_final_texts": sum(
                isinstance(message, BaseChatMessage) and message.source == "executor" for message in native_messages
            ),
        }
        try:
            await executor.stop()
            await client.close()
        except Exception as error:
            report["run_status"] = "INCONCLUSIVE"
            report["cleanup_error"] = {"type": type(error).__name__, "message": str(error)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", required=True)
    parser.add_argument("--workdir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    started = time.monotonic()
    report: dict[str, Any] = {
        "case": args.case,
        "run_status": "INCONCLUSIVE",
        "python_executable": sys.executable,
        "workdir": str(args.workdir.resolve()),
        "diagnostic_execution_was_deferred": True,
    }

    # A POSIX hard bound also covers native import or cleanup stalls. A killed
    # process or missing report is INCONCLUSIVE; it cannot satisfy the oracle.
    if hasattr(signal, "SIGALRM"):
        signal.signal(signal.SIGALRM, signal.SIG_DFL)
        signal.alarm(115)
    try:
        prediction_path = Path(__file__).with_name("prediction.json")
        prediction = json.loads(prediction_path.read_text(encoding="utf-8"))
        matching = [case for case in prediction["cases"] if case["id"] == args.case]
        if len(matching) != 1:
            raise ValueError("unknown_or_nonunique_case")
        case = matching[0]
        if args.workdir.is_symlink():
            raise ValueError("workdir_must_not_be_a_symlink")
        workdir = args.workdir.resolve()
        if workdir.exists() and (not workdir.is_dir() or any(workdir.iterdir())):
            raise ValueError("workdir_must_be_a_new_or_empty_owned_directory")
        workdir.mkdir(parents=True, exist_ok=True)
        report["frozen_input"] = case["input"]
        asyncio.run(run_case(case, workdir, report))
    except Exception as error:
        report["run_status"] = "INCONCLUSIVE"
        report["error"] = {"type": type(error).__name__, "message": str(error)}
    report["elapsed_seconds"] = time.monotonic() - started
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if hasattr(signal, "SIGALRM"):
        signal.alarm(0)
    return 0 if report["run_status"] == "COMPLETED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
