#!/usr/bin/env python3
"""Frozen static diagnostic fixture; execute only after the study freeze.

Import selection belongs to the caller (normally PYTHONPATH=/selected/src).
This fixture never substitutes the parser, executor, checker dispatcher, or run loop.
"""

import argparse
import json
import os
from pathlib import Path
import signal
import sys
import time


class ScriptProtocolError(RuntimeError):
    pass


def plain(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (list, tuple)):
        return [plain(item) for item in value]
    if isinstance(value, dict):
        return {str(key): plain(item) for key, item in value.items()}
    if hasattr(value, "dict"):
        return plain(value.dict())
    return {"type": type(value).__name__, "repr": repr(value)}


def install_environment_guards():
    # remote_executors.py imports python-dotenv and calls load_dotenv at import.
    # Current python-dotenv honors this flag; the audit hook prevents any read
    # if a dependency ignores it. No framework operation is replaced.
    os.environ["PYTHON_DOTENV_DISABLED"] = "1"
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    os.environ["DO_NOT_TRACK"] = "1"
    sys.dont_write_bytecode = True

    def guard(event, args):
        if event in {"socket.connect", "socket.connect_ex", "socket.getaddrinfo", "subprocess.Popen", "os.system"}:
            raise PermissionError("Fixture prohibits network access and external commands")
        if event == "open" and args and isinstance(args[0], (str, bytes, os.PathLike)):
            name = Path(os.fsdecode(args[0])).name
            if name == ".env" or name.startswith(".env."):
                raise PermissionError("Fixture prohibits reading dotenv files")

    sys.addaudithook(guard)


def run_native_case(case, record):
    import smolagents
    from smolagents.agents import CodeAgent
    from smolagents.memory import ActionStep
    from smolagents.models import ChatMessage, MessageRole, Model
    from smolagents.monitoring import TokenUsage

    class FrozenModel(Model):
        def __init__(self, script):
            super().__init__(model_id="static-diagnostic-frozen-provider")
            self.script = script
            self.cursor = 0
            self.calls = []
            self.unexpected_calls = []
            self.script_exhausted = False

        def generate(self, *args, **kwargs):
            event = {
                "call_index": len(self.calls) + 1,
                "positional_count": len(args),
                "kwargs": plain(kwargs),
                "messages": plain(args[0]) if args else None,
            }
            self.calls.append(event)
            if self.cursor >= len(self.script):
                self.script_exhausted = True
                event["protocol_error"] = "SCRIPT_EXHAUSTED"
                raise ScriptProtocolError("SCRIPT_EXHAUSTED")
            entry = self.script[self.cursor]
            shape_ok = (
                len(args) == 1
                and isinstance(args[0], list)
                and all(isinstance(message, ChatMessage) for message in args[0])
                and kwargs == entry["allowed_kwargs"]
            )
            if not shape_ok:
                event["protocol_error"] = "UNEXPECTED_CALL_SHAPE"
                self.unexpected_calls.append(event["call_index"])
                raise ScriptProtocolError("UNEXPECTED_CALL_SHAPE")
            # Only the call index selects a response. Runtime messages, source
            # paths, intervention status, and previous results are not selectors.
            self.cursor += 1
            event["response_index"] = self.cursor
            event["response_content"] = entry["content"]
            return ChatMessage(
                role=MessageRole.ASSISTANT,
                content=entry["content"],
                token_usage=TokenUsage(input_tokens=0, output_tokens=0),
            )

    checks = []

    def exact_answer(final_answer, memory, agent):
        accepted = isinstance(final_answer, str) and final_answer == case["validator_expected"]
        checks.append(
            {
                "candidate": plain(final_answer),
                "candidate_type": type(final_answer).__name__,
                "returned_boolean": accepted,
                "agent_step_number": agent.step_number,
                "memory_step_count_at_check": len(memory.steps),
            }
        )
        return accepted

    model = FrozenModel(case["responses"])
    agent = CodeAgent(
        tools=[],
        model=model,
        final_answer_checks=[exact_answer],
        executor_type="local",
        executor_kwargs={"timeout_seconds": 10},
        code_block_tags=("<code>", "</code>"),
        max_steps=case["max_steps"],
        planning_interval=None,
        stream_outputs=False,
        verbosity_level=-1,
    )
    record["loaded_implementation"] = {
        "package_file": smolagents.__file__,
        "version": getattr(smolagents, "__version__", None),
        "agent_type": type(agent).__name__,
        "executor_type": type(agent.python_executor).__name__,
        "executor_timeout_seconds": agent.python_executor.timeout_seconds,
    }
    try:
        result = agent.run(case["task"], stream=False, return_full_result=True)
        record["native_return_type"] = type(result).__name__
        record["native_run_result"] = plain(result.dict())
        record["native_return_output_type"] = type(result.output).__name__
    except Exception as error:
        record["run_exception"] = {"type": type(error).__name__, "message": str(error)}
    finally:
        record["provider"] = {
            "calls": model.calls,
            "responses_consumed": model.cursor,
            "response_count": len(model.script),
            "script_exhausted": model.script_exhausted,
            "unexpected_calls": model.unexpected_calls,
        }
        record["checker_events"] = checks
        record["native_messages_after_run"] = plain(agent.write_memory_to_messages())
        record["native_action_steps"] = [
            {
                "step_number": step.step_number,
                "model_output": step.model_output,
                "code_action": step.code_action,
                "observations": step.observations,
                "action_output": plain(step.action_output),
                "is_final_answer": step.is_final_answer,
                "error": plain(step.error),
            }
            for step in agent.memory.steps
            if isinstance(step, ActionStep)
        ]
        record["producer_state"] = {
            name: plain(agent.python_executor.state[name])
            for name in ("answer", "final_answer_variable", "_print_outputs")
            if name in agent.python_executor.state
        }
        if model.script_exhausted or model.unexpected_calls:
            record["observation_status"] = "INCONCLUSIVE"
            record["inconclusive_reasons"].append("Frozen provider protocol was not followed")
        elif "run_exception" in record:
            record["observation_status"] = "INCONCLUSIVE"
            record["inconclusive_reasons"].append("Native run raised an unexpected exception")
        else:
            # OBSERVED describes collection only. No defect/fix verdict is filled in.
            record["observation_status"] = "OBSERVED"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", required=True)
    parser.add_argument("--workdir", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    prediction_path = Path(__file__).resolve().with_name("prediction.json")
    prediction = json.loads(prediction_path.read_text(encoding="utf-8"))
    cases = {case["id"]: case for case in prediction["cases"]}
    if args.case not in cases:
        parser.error("Unknown frozen case ID")
    workdir = Path(args.workdir).resolve()
    output = Path(args.output).resolve()
    workdir.mkdir(parents=True, exist_ok=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    os.chdir(workdir)
    started = time.monotonic()
    record = {
        "schema": "static_diagnostic_observation_v1",
        "case_id": args.case,
        "observation_status": "INCONCLUSIVE",
        "inconclusive_reasons": [],
        "python_executable": sys.executable,
        "python_optimization": sys.flags.optimize,
        "workdir": str(workdir),
        "frozen_input": cases[args.case],
    }

    def deadline(signum, frame):
        raise TimeoutError("Fixture exceeded its 110 second process budget")

    signal.signal(signal.SIGALRM, deadline)
    signal.alarm(110)
    try:
        install_environment_guards()
        if sys.flags.optimize:
            raise RuntimeError("Frozen diagnosis requires Python optimization level 0")
        run_native_case(cases[args.case], record)
    except Exception as error:
        record["observation_status"] = "INCONCLUSIVE"
        record["inconclusive_reasons"].append(type(error).__name__ + ": " + str(error))
    finally:
        signal.alarm(0)
        record["elapsed_seconds"] = time.monotonic() - started
        output.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0 if record["observation_status"] == "OBSERVED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
