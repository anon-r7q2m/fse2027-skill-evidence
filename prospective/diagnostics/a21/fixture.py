"""Frozen static diagnostic fixture. Execute only after the root freezes all arms.

The root selects original/patched packages through PYTHONPATH. This file does not
alter sys.path, patch the termination consumer, or make any network/API calls.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import signal
import time
from dataclasses import asdict
from pathlib import Path


MARKER = "REVIEW_STOP"
MODEL_RESPONSES = ["Recorded the execution outcome; REVIEW_STOP."]
REVIEWER_SYSTEM = "Record the execution outcome, then end this review."
TASK_PREFIX = "Execute the supplied local Python block once, then let reviewer record the result.\n"
CASES = {
    "trigger_source_lost": {
        "kind": "trigger",
        "code": 'value = 2 + 2\nprint("calculation", value)\nprint("REVIEW_" + "STOP")\n',
    },
    "control_success": {
        "kind": "control",
        "code": 'value = 2 + 2\nassert value == 4\nprint("calculation", value)\n',
    },
    "control_execution_failure": {
        "kind": "control",
        "code": 'import sys\nprint("check failed intentionally", file=sys.stderr)\nraise SystemExit(7)\n',
    },
}


class Inconclusive(Exception):
    pass


async def run_case(case_id: str, workdir: Path, facts: dict) -> None:
    # Imports deliberately use the root-selected complete native packages.
    import autogen_agentchat.agents._code_executor_agent as agent_module
    import autogen_agentchat.conditions._terminations as termination_module
    import autogen_agentchat.teams._group_chat._round_robin_group_chat as team_module
    import autogen_core
    import autogen_ext.code_executors.local as local_module
    from autogen_agentchat.agents import AssistantAgent, CodeExecutorAgent
    from autogen_agentchat.base import TaskResult, TerminationCondition
    from autogen_agentchat.conditions import TextMentionTermination
    from autogen_agentchat.teams import RoundRobinGroupChat
    from autogen_core.models import SystemMessage, UserMessage
    from autogen_ext.code_executors.local import LocalCommandLineCodeExecutor
    from autogen_ext.models.replay import ReplayChatCompletionClient

    facts["source_origins"] = {
        name: module.__file__
        for name, module in {
            "autogen_core": autogen_core,
            "code_executor_agent": agent_module,
            "termination": termination_module,
            "round_robin_group_chat": team_module,
            "local_command_line_executor": local_module,
        }.items()
    }

    class RecordedLocalExecutor(LocalCommandLineCodeExecutor):
        """Observation only: call the native method and return its same object."""

        async def execute_code_blocks(self, code_blocks, cancellation_token):
            record = {
                "code_blocks": [asdict(block) for block in code_blocks],
                "native_result_before_agent_formatting": None,
            }
            facts["producer_calls"].append(record)
            result = await super().execute_code_blocks(code_blocks, cancellation_token)
            # Copy before CodeExecutorAgent formats nonzero-exit output in place.
            record["native_result_before_agent_formatting"] = asdict(result)
            return result

    class FixedClient(ReplayChatCompletionClient):
        """Finite provider script; validation never chooses the response text."""

        async def create(
            self,
            messages,
            *,
            tools=(),
            tool_choice="auto",
            json_output=None,
            extra_create_args=None,
            cancellation_token=None,
        ):
            call = {
                "method": "create",
                "messages": [message.model_dump(mode="json") for message in messages],
                "tools_count": len(tools),
                "tool_choice": str(tool_choice),
                "json_output": None if json_output is None else str(json_output),
                "extra_create_args": dict(extra_create_args or {}),
            }
            facts["provider_calls"].append(call)
            if self._current_index >= len(MODEL_RESPONSES):
                facts["script_exhaustion_error"] = True
                raise Inconclusive("Frozen provider response list exhausted by an extra call")
            shape_ok = (
                len(messages) == 3
                and isinstance(messages[0], SystemMessage)
                and isinstance(messages[1], UserMessage)
                and messages[1].source == "user"
                and isinstance(messages[2], UserMessage)
                and messages[2].source == "executor"
                and all(isinstance(message.content, str) for message in messages)
                and not tools
                and tool_choice == "auto"
                and json_output is None
                and not extra_create_args
            )
            if not shape_ok:
                facts["unexpected_provider_call"] = True
                raise Inconclusive("Provider call shape differs from the frozen allowed shape")
            response = await super().create(
                messages,
                tools=tools,
                tool_choice=tool_choice,
                json_output=json_output,
                extra_create_args=extra_create_args or {},
                cancellation_token=cancellation_token,
            )
            facts["responses_consumed"] = self._current_index
            call["response"] = response.model_dump(mode="json")
            return response

        async def create_stream(self, *args, **kwargs):
            facts["provider_calls"].append({"method": "create_stream"})
            facts["unexpected_provider_call"] = True
            raise Inconclusive("Streaming is outside the frozen provider call shape")
            yield  # Keep the async-generator interface; this statement is unreachable.

    configured = TextMentionTermination(MARKER, sources=["reviewer"])
    serialized = configured.dump_component().model_dump(mode="json")
    restored = TerminationCondition.load_component(serialized)
    facts["configuration"] = {
        "requested": {"text": MARKER, "sources": ["reviewer"]},
        "serialized_component": serialized,
        "restored_sources_observation": getattr(restored, "_sources", "attribute_missing"),
    }
    client = FixedClient(MODEL_RESPONSES)
    executor = RecordedLocalExecutor(timeout=5, work_dir=workdir, cleanup_temp_files=False)
    agent = CodeExecutorAgent("executor", code_executor=executor, sources=["user"])
    reviewer = AssistantAgent(
        "reviewer",
        model_client=client,
        system_message=REVIEWER_SYSTEM,
        model_client_stream=False,
    )
    team = RoundRobinGroupChat([agent, reviewer], termination_condition=restored, max_turns=4)
    task = TASK_PREFIX + "```python\n" + CASES[case_id]["code"] + "```"
    facts["task"] = task
    await executor.start()
    try:
        async for item in team.run_stream(task=task):
            if isinstance(item, TaskResult):
                facts["consumer"] = {
                    "task_result_received": True,
                    "stop_reason": item.stop_reason,
                    "messages": [message.model_dump(mode="json") for message in item.messages],
                }
            else:
                facts["native_stream_messages"].append(item.model_dump(mode="json"))
    finally:
        await executor.stop()
        await client.close()
    if not facts["consumer"]["task_result_received"]:
        raise Inconclusive("Native team produced no TaskResult")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", required=True, choices=sorted(CASES))
    parser.add_argument("--workdir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    started = time.monotonic()
    facts = {
        "case": args.case,
        "collection_status": "INCONCLUSIVE",
        "evaluation_status": "UNEVALUATED",
        "producer_calls": [],
        "provider_calls": [],
        "native_stream_messages": [],
        "consumer": {"task_result_received": False, "stop_reason": None, "messages": []},
        "frozen_model_responses": MODEL_RESPONSES,
        "responses_consumed": 0,
        "script_exhaustion_error": False,
        "unexpected_provider_call": False,
        "limits": {"command_timeout_seconds": 5, "async_timeout_seconds": 75, "alarm_seconds": 110, "max_turns": 4},
    }

    def alarm_handler(signum, frame):
        raise TimeoutError("Fixture exceeded its 110 second wall-clock guard")

    signal.signal(signal.SIGALRM, alarm_handler)
    signal.alarm(110)
    try:
        if args.workdir.is_symlink():
            raise Inconclusive("Owned workdir must not be a symlink")
        workdir = args.workdir.resolve()
        if workdir.exists() and any(workdir.iterdir()):
            raise Inconclusive("Owned workdir must be new or empty")
        workdir.mkdir(parents=True, exist_ok=True)
        facts["workdir"] = str(workdir)
        asyncio.run(asyncio.wait_for(run_case(args.case, workdir, facts), timeout=75))
        if facts["script_exhaustion_error"] or facts["unexpected_provider_call"]:
            raise Inconclusive("Provider contract violation")
        facts["collection_status"] = "OBSERVED"
    except Exception as exc:
        facts["collection_status"] = "INCONCLUSIVE"
        facts["exception"] = {"type": type(exc).__name__, "message": str(exc)}
    finally:
        signal.alarm(0)
        facts["elapsed_seconds"] = time.monotonic() - started
        facts["responses_remaining"] = len(MODEL_RESPONSES) - facts["responses_consumed"]
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(facts, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
