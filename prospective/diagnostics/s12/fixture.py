"""Frozen static diagnostic; execute only after the root freezes all records."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time


def encode(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): encode(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [encode(item) for item in value]
    if hasattr(value, "dict") and callable(value.dict):
        return encode(value.dict())
    return {"type": type(value).__name__, "repr": repr(value)}


def write_json(path, data):
    path.write_text(json.dumps(encode(data), indent=2, ensure_ascii=False) + "\n")


def worker(case, output_path):
    facts = {
        "case_id": case["id"],
        "harness_status": "INCONCLUSIVE",
        "python_optimization": sys.flags.optimize,
        "python_executable": sys.executable,
        "script_exhausted": False,
        "unexpected_calls": [],
        "model_calls": [],
        "checker_calls": [],
        "consumer": None,
        "native_steps": [],
        "native_messages": [],
        "exception": None,
    }
    model = None
    agent = None
    result = None
    try:
        if sys.flags.optimize != case["input"]["python_optimization"]:
            raise RuntimeError("Worker optimization does not match the frozen case")

        import smolagents.agents as agents_module
        import smolagents.local_python_executor as executor_module
        from smolagents.agents import CodeAgent
        from smolagents.memory import ActionStep, FinalAnswerStep
        from smolagents.models import ChatMessage, MessageRole, Model

        facts["implementation"] = {
            "agents_module": str(Path(agents_module.__file__).resolve()),
            "executor_module": str(Path(executor_module.__file__).resolve()),
        }

        class FrozenScriptViolation(RuntimeError):
            pass

        class FixedModel(Model):
            def __init__(self, responses):
                super().__init__(model_id="frozen-local-provider")
                self.responses = list(responses)
                self.next_response = 0

            def generate(self, *args, **kwargs):
                call = {
                    "ordinal": len(facts["model_calls"]) + 1,
                    "positional_arguments": encode(args),
                    "keyword_arguments": encode(kwargs),
                }
                facts["model_calls"].append(call)
                allowed = (
                    len(args) == 1
                    and isinstance(args[0], list)
                    and all(isinstance(message, ChatMessage) for message in args[0])
                    and kwargs == {
                        "stop_sequences": ["Observation:", "Calling tools:", "</code>"]
                    }
                )
                if not allowed:
                    facts["unexpected_calls"].append(call["ordinal"])
                    raise FrozenScriptViolation("Unexpected native provider call shape")
                if self.next_response >= len(self.responses):
                    facts["script_exhausted"] = True
                    raise FrozenScriptViolation("Frozen provider response list exhausted")
                content = self.responses[self.next_response]
                self.next_response += 1
                call["response_index"] = self.next_response - 1
                call["response_content"] = content
                return ChatMessage(role=MessageRole.ASSISTANT, content=content)

        def accept_42(final_answer, memory, agent):
            accepted = final_answer == "42"
            facts["checker_calls"].append({
                "answer": encode(final_answer),
                "answer_type": type(final_answer).__name__,
                "step_number": agent.step_number,
                "returned": accepted,
            })
            return accepted

        def observe_final_answer(step, agent):
            facts.setdefault("native_final_answer_steps", []).append(encode(step.dict()))

        model = FixedModel(case["input"]["responses"])
        agent = CodeAgent(
            tools=[],
            model=model,
            max_steps=case["input"]["max_steps"],
            planning_interval=None,
            executor_type="local",
            executor_kwargs={"timeout_seconds": 2},
            stream_outputs=False,
            use_structured_outputs_internally=False,
            final_answer_checks=[accept_42],
            step_callbacks={FinalAnswerStep: observe_final_answer},
            return_full_result=True,
            verbosity_level=-1,
        )
        facts["implementation"]["executor_class"] = (
            type(agent.python_executor).__module__ + "." + type(agent.python_executor).__qualname__
        )
        result = agent.run(case["input"]["task"], stream=False, return_full_result=True)
        facts["consumer"] = {
            "entry": "CodeAgent.run(stream=False, return_full_result=True)",
            "return_type": type(result).__name__,
            "native_run_state": result.state,
            "returned_output": encode(result.output),
        }
        facts["harness_status"] = "OBSERVED"
    except Exception as error:
        facts["exception"] = {"type": type(error).__name__, "message": str(error)}
    finally:
        if model is not None:
            facts["responses_consumed"] = model.next_response
            facts["responses_available"] = len(model.responses)
        if agent is not None:
            try:
                facts["native_steps"] = encode(agent.memory.get_full_steps())
                facts["native_messages"] = encode(agent.write_memory_to_messages())
                facts["producer_facts"] = {
                    "candidate_in_native_executor_state": encode(agent.python_executor.state.get("candidate")),
                    "action_steps": [
                        {
                            "step_number": step.step_number,
                            "code_action": step.code_action,
                            "observations": step.observations,
                            "action_output": encode(step.action_output),
                            "native_is_final_answer": step.is_final_answer,
                            "native_error": None if step.error is None else {
                                "type": type(step.error).__name__,
                                "message": str(step.error),
                            },
                        }
                        for step in agent.memory.steps if isinstance(step, ActionStep)
                    ],
                }
            except Exception as error:
                facts["capture_exception"] = {"type": type(error).__name__, "message": str(error)}
                facts["harness_status"] = "INCONCLUSIVE"
        if facts["unexpected_calls"] or facts["script_exhausted"]:
            facts["harness_status"] = "INCONCLUSIVE"
        write_json(output_path, facts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True)
    parser.add_argument("--workdir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    sys.dont_write_bytecode = True
    manifest = json.loads(Path(__file__).with_name("prediction.json").read_text())
    cases = {case["id"]: case for case in manifest["cases"]}
    if args.case not in cases:
        parser.error("Unknown frozen case")
    case = cases[args.case]
    workdir = args.workdir.resolve()
    output_path = args.output.resolve()
    workdir.mkdir(parents=True, exist_ok=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if args.worker:
        os.chdir(workdir)
        worker(case, output_path)
        return

    started = time.monotonic()
    facts = {"case_id": args.case, "harness_status": "INCONCLUSIVE"}
    # Inherit the root-selected PYTHONPATH; alter only interpreter optimization.
    child_env = os.environ.copy()
    child_env["PYTHONOPTIMIZE"] = str(case["input"]["python_optimization"])
    child_env["PYTHONDONTWRITEBYTECODE"] = "1"
    with tempfile.TemporaryDirectory(prefix="s12_fixture_", dir=workdir) as child_directory:
        child_output = Path(child_directory) / "worker_facts.json"
        command = [
            sys.executable, "-B", str(Path(__file__).resolve()),
            "--case", args.case, "--workdir", str(workdir),
            "--output", str(child_output), "--worker",
        ]
        try:
            completed = subprocess.run(
                command, cwd=workdir, env=child_env, capture_output=True,
                text=True, timeout=10, check=False,
            )
            if child_output.exists():
                facts = json.loads(child_output.read_text())
            facts["worker_process"] = {
                "exit_status": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
                "timeout_seconds": 10,
            }
            if completed.returncode != 0:
                facts["harness_status"] = "INCONCLUSIVE"
        except subprocess.TimeoutExpired as error:
            facts["worker_process"] = {
                "timed_out": True, "timeout_seconds": 10,
                "stdout": encode(error.stdout), "stderr": encode(error.stderr),
            }
        except Exception as error:
            facts["launcher_exception"] = {"type": type(error).__name__, "message": str(error)}
    facts["elapsed_seconds"] = time.monotonic() - started
    write_json(output_path, facts)


if __name__ == "__main__":
    main()
