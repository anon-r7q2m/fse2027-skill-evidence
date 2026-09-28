#!/usr/bin/python3
"""Execute the two frozen public source slices; never run tools or a model."""
from __future__ import annotations

import argparse
import ast
import asyncio
import copy
import json
import logging
import re
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from shlex import quote
from types import SimpleNamespace as NS

import yaml
from jinja2 import Template


BASE = Path(__file__).resolve().parent
SOURCE = BASE / "public_source"
SLICES = []


class Quiet:
    def __getattr__(self, name):
        return lambda *args, **kwargs: None


class Record(NS):
    def model_copy(self, *, deep=False, update=None):
        obj = copy.deepcopy(self) if deep else copy.copy(self)
        for key, value in (update or {}).items():
            setattr(obj, key, value)
        return obj


def native_class(path, class_name, method_names, env):
    tree = ast.parse(path.read_text())
    cls = next(x for x in tree.body if isinstance(x, ast.ClassDef) and x.name == class_name)
    methods = [copy.deepcopy(x) for x in cls.body if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef)) and x.name in method_names]
    assert {x.name for x in methods} == set(method_names)
    for method in methods:
        SLICES.append({"path": str(path.relative_to(BASE)), "symbol": f"{class_name}.{method.name}", "start": method.lineno, "end": method.end_lineno})
    generated = ast.ClassDef(name=class_name, bases=[], keywords=[], body=methods, decorator_list=[])
    module = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), generated], type_ignores=[])
    exec(compile(ast.fix_missing_locations(module), str(path), "exec"), env)
    return env[class_name]


def native_functions(path, names, env):
    tree = ast.parse(path.read_text())
    nodes = [copy.deepcopy(x) for x in tree.body if isinstance(x, ast.FunctionDef) and x.name in names]
    assert {x.name for x in nodes} == set(names)
    for node in nodes:
        SLICES.append({"path": str(path.relative_to(BASE)), "symbol": node.name, "start": node.lineno, "end": node.end_lineno})
    module = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), *nodes], type_ignores=[])
    exec(compile(ast.fix_missing_locations(module), str(path), "exec"), env)


class FormatError(Exception):
    def __init__(self, message, error_code, **kwargs):
        super().__init__(message)
        self.error_code = error_code
        self.extra = kwargs


class StopAfterCapture(Exception):
    pass


class Step(Record):
    def __init__(self, **kwargs):
        super().__init__(output="", thought="", action="", observation="", query=[], state={},
                         tool_calls=None, tool_call_ids=[], thinking_blocks=[], extra_info={},
                         done=False, submission=None, exit_status=None, execution_time=0)
        self.__dict__.update(kwargs)


def text_of(content):
    if isinstance(content, str):
        return content
    return "".join(x["text"] if isinstance(x, dict) else x.text for x in content)


def run_swe_agent():
    root = SOURCE / "swe_agent"
    logging.TRACE = 5
    env = dict(json=json, re=re, quote=quote, Template=Template, copy=copy, time=time,
               asyncio=asyncio, logging=logging, FunctionCallingFormatError=FormatError,
               StepOutput=Step, BashAction=lambda **kwargs: Record(**kwargs),
               CommandTimeoutError=type("CommandTimeoutError", (Exception,), {}),
               _BlockedActionError=type("BlockedAction", (Exception,), {}),
               _TotalExecutionTimeExceeded=type("TotalExecutionTimeExceeded", (Exception,), {}),
               _RetryWithOutput=type("RetryWithOutput", (Exception,), {}),
               _RetryWithoutOutput=type("RetryWithoutOutput", (Exception,), {}),
               _ExitForfeit=type("ExitForfeit", (Exception,), {}),
               RETRY_WITH_OUTPUT_TOKEN="<<RETRY_WITH_OUTPUT>>",
               RETRY_WITHOUT_OUTPUT_TOKEN="<<RETRY_WITHOUT_OUTPUT>>",
               EXIT_FORFEIT_TOKEN="<<EXIT_FORFEIT>>")
    native_functions(root / "sweagent/tools/utils.py", ["_should_quote"], env)
    Parser = native_class(root / "sweagent/tools/parsing.py", "FunctionCallingParser", ["_parse_tool_call", "__call__"], env)
    Handler = native_class(root / "sweagent/tools/tools.py", "ToolHandler", ["parse_actions", "should_block_action", "check_for_submission_cmd"], env)
    RuntimeEnv = native_class(root / "sweagent/environment/swe_env.py", "SWEEnv", ["communicate"], env)
    native_functions(root / "sweagent/agent/history_processors.py", ["_get_content_text", "_clear_cache_control", "_set_cache_control"], env)
    Processor = native_class(root / "sweagent/agent/history_processors.py", "CacheControlHistoryProcessor", ["__call__"], env)
    Agent = native_class(root / "sweagent/agent/agents.py", "DefaultAgent",
                         ["forward", "handle_action", "handle_submission", "add_step_to_history", "_get_format_dict", "_add_templated_messages_to_history", "_append_history", "messages"], env)
    config = yaml.safe_load((root / "config/default.yaml").read_text())["agent"]
    templates = Record(**config["templates"], max_observation_length=100000,
                       next_step_truncated_observation_template="Observation: {{observation[:max_observation_length]}}<response clipped>")
    parser = Parser()
    command = Record(name="bash", end_name=None, invoke_format="{command}",
                     arguments=[Record(name="command", required=True, argument_format="{{value}}")])
    filter_config = Record(blocklist=["vim", "vi", "emacs", "nano", "nohup", "gdb", "less", "tail -f", "python -m venv", "make"],
                           blocklist_standalone=["python", "python3", "ipython", "bash", "sh", "/bin/bash", "/bin/sh", "nohup", "vi", "vim", "emacs", "nano", "su"],
                           block_unless_regex={"radare2": r"\b(?:radare2)\b.*\s+-c\s+.*", "r2": r"\b(?:radare2)\b.*\s+-c\s+.*"})
    processor = Processor()
    processor.last_n_messages, processor.last_n_messages_offset, processor.tagged_roles = 2, 0, ["user", "tool"]

    def new_agent(runtime, model):
        tools = Handler()
        tools.config = Record(parse_function=parser, commands=[command], filter=filter_config,
                              execution_timeout=30, total_execution_timeout=1800,
                              max_consecutive_execution_timeouts=3, command_docs="", env_variables={})
        tools.guard_multiline_input = lambda action: action
        tools.get_state = lambda **kwargs: {}
        runtime_env = RuntimeEnv()
        runtime_env.logger, runtime_env.deployment, runtime_env.repo = Quiet(), Record(runtime=runtime), None
        a = Agent()
        a.name, a.logger, a._chook = "main", Quiet(), Quiet()
        a.tools, a.model, a._env = tools, model, runtime_env
        a.templates, a.history_processors = templates, [processor]
        a.history = [{"role": "system", "content": "Fixed local source-path fixture.", "agent": "main"}]
        a._problem_statement = Record(get_problem_statement=lambda: "Fixed public-path check", get_extra_fields=lambda: {})
        a._action_sampler, a._always_require_zero_exit_code = None, False
        a._total_execution_time, a._n_consecutive_timeouts = 0, 0
        return a

    conditions = [("S-A", "true", "", 0, 1), ("S-B", "false", "", 1, 1),
                  ("S-C", "printf 'error\\n'; false", "error\n", 1, 1), ("S-D", "true", None, None, 2)]
    rows = []
    for cid, cmd, output, status, number in conditions:
        calls = [{"id": f"call-{i}", "function": {"name": "bash", "arguments": json.dumps({"command": cmd})}} for i in range(number)]
        response = {"message": "Run the fixed command.", "tool_calls": calls}
        runtime_calls = []

        async def run_in_session(action):
            runtime_calls.append(vars(action))
            return Record(output=output, exit_code=status)

        queries = []

        def query(messages):
            queries.append(copy.deepcopy(messages))
            if len(queries) > 1:
                raise StopAfterCapture()
            return copy.deepcopy(response)

        runtime = Record(run_in_session=run_in_session)
        a = new_agent(runtime, Record(query=query))
        row = {"id": cid, "model_response": response, "runtime_output": output, "runtime_exit_code": status}
        try:
            step = a.forward(a.messages)
        except FormatError as error:
            row.update(parser_error=error.error_code, runtime_calls=runtime_calls,
                       S1="supported" if error.error_code == "multiple" and not runtime_calls else "violated",
                       S2="not_applicable", consumer_message=None)
            try:
                parser(response, [command])
            except FormatError as direct:
                row["direct_parser_error"] = direct.error_code
                row["direct_check_same_judgment"] = direct.error_code == error.error_code
        else:
            a.add_step_to_history(step)
            final = a.messages
            try:
                a.forward(final)
            except StopAfterCapture:
                pass
            consumer = text_of(queries[-1][-1]["content"])
            identity_ok = queries[-1][-1].get("tool_call_ids") == ["call-0"]
            actual_action = runtime_calls[0]["command"] if runtime_calls else None
            success_asserted = "ran successfully" in consumer
            s2 = "violated" if success_asserted and status != 0 else "supported"
            direct = new_agent(runtime, Record(query=lambda history: None))
            direct.add_step_to_history(copy.deepcopy(step))
            direct_text = text_of(direct.messages[-1]["content"])
            row.update(parsed_action=step.action, runtime_calls=runtime_calls,
                       returned_observation=step.observation, consumer_message=consumer,
                       consumer_tool_call_ids=queries[-1][-1].get("tool_call_ids"),
                       success_asserted=success_asserted,
                       S1="supported" if actual_action == cmd and identity_ok else "violated", S2=s2,
                       direct_rendered_message=direct_text,
                       direct_check_same_judgment=(direct_text == consumer),
                       status_visible_to_renderer=False)
        rows.append(row)
    return {"host": "SWE-agent", "revision": "3ea751c087f32b16e039a2233dd6eefecef325d5", "exposure": "unknown",
            "conditions": rows, "upstream_tests_inspected_not_executed": ["tests/test_agent.py::test_function_calling", "tests/test_agent.py::test_show_no_output_template", "tests/test_parsing.py::test_function_calling_parser"],
            "native_runtime_executed": False, "model_called": False}


class Event(Record):
    hidden = False


class Action(Event):
    pass


class Observation(Event):
    pass


class CmdRunAction(Action):
    pass


class MessageAction(Action):
    pass


class SystemMessageAction(Action):
    pass


@dataclass
class TextContent:
    text: str


@dataclass
class Message:
    role: str
    content: list = field(default_factory=list)
    tool_calls: list | None = None
    tool_call_id: str | None = None
    name: str | None = None

    def model_copy(self, *, update):
        obj = copy.copy(self)
        for key, value in update.items():
            setattr(obj, key, value)
        return obj


@dataclass
class View:
    events: list


@dataclass
class Condensation:
    action: object


def run_openhands():
    root = SOURCE / "openhands"
    env = dict(logger=Quiet(), Action=Action, Observation=Observation, CmdRunAction=CmdRunAction,
               MessageAction=MessageAction, SystemMessageAction=SystemMessageAction,
               Message=Message, TextContent=TextContent, View=View, Condensation=Condensation,
               EventSource=Record(USER="user"), check_tools=lambda tools, config: tools)
    for name in ["AgentDelegateAction", "AgentThinkAction", "IPythonRunCellAction", "FileEditAction", "FileReadAction", "BrowseInteractiveAction", "BrowseURLAction", "MCPAction", "AgentFinishAction"]:
        env[name] = type(name, (Action,), {})
    Formatter = native_class(root / "openhands/events/observation/commands.py", "CmdOutputObservation", ["to_agent_observation"], env)
    class CmdObservation(Observation, Formatter):
        pass
    env["CmdOutputObservation"] = CmdObservation
    native_functions(root / "openhands/events/serialization/event.py", ["truncate_content"], env)
    Memory = native_class(root / "openhands/memory/conversation_memory.py", "ConversationMemory",
                          ["process_events", "_process_action", "_process_observation", "_filter_unmatched_tool_calls", "_apply_user_message_formatting", "_ensure_system_message", "_ensure_initial_user_message"], env)
    Agent = native_class(root / "openhands/agenthub/codeact_agent/codeact_agent.py", "CodeActAgent", ["step", "_get_initial_user_message", "_get_messages"], env)
    Controller = native_class(root / "openhands/controller/agent_controller.py", "AgentController", ["_on_event"], env)
    rows = []
    for cid, status, kind in [("O-A", 0, "complete"), ("O-B", 1, "complete"), ("O-C", 0, "partial"), ("O-D", 1, "orphan")]:
        initial = MessageAction(source="user", content="Run the fixed command.", image_urls=[])
        events = [SystemMessageAction(source="agent", content="Fixed local source-path fixture."), initial]
        ids = ["call-a", "call-b"] if kind == "partial" else ["call-orphan" if kind == "orphan" else "call-a"]
        response = Record(id="response-a", choices=[Record(message=Record(role="assistant", content="", tool_calls=[Record(id=i) for i in ids]))])
        metadata = Record(tool_call_id=ids[0], function_name="execute_bash", model_response=response)
        if kind != "orphan":
            events.append(CmdRunAction(source="agent", command="true" if status == 0 else "false", tool_call_metadata=metadata))
        obs = CmdObservation(content="", command="true" if status == 0 else "false", source="environment", tool_call_metadata=metadata,
                             metadata=Record(prefix="", suffix="", working_dir=None, py_interpreter_path=None, exit_code=status))
        events.append(obs)
        state = Record(history=[], get_last_user_message=lambda: initial, to_llm_metadata=lambda **kwargs: {})
        controller = Controller()
        controller.state_tracker = Record(add_history=lambda event: state.history.append(event))

        async def no_op(event):
            return None

        controller._handle_action = controller._handle_observation = no_op
        controller.should_step = lambda event: False
        controller.log = lambda *args, **kwargs: None
        controller.get_agent_state = lambda: "fixture_ingestion"
        for event in events:
            asyncio.run(controller._on_event(event))
        config = Record(enable_som_visual_browsing=False)
        memory = Memory()
        memory.agent_config, memory.prompt_manager = config, Record(get_system_message=lambda: "Fixed local source-path fixture.")
        captured = []
        llm = Record(config=Record(max_message_chars=10000), vision_is_active=lambda: False,
                     is_caching_prompt_active=lambda: False, format_messages_for_llm=lambda messages: copy.deepcopy(messages),
                     completion=lambda **kwargs: captured.append(kwargs["messages"]) or "fixed-response")
        agent = Agent()
        agent.name, agent.pending_actions, agent.tools = "CodeActAgent", deque(), []
        agent.prompt_manager, agent.conversation_memory, agent.llm = memory.prompt_manager, memory, llm
        agent.condenser = Record(condensed_history=lambda state: View(events=state.history))
        agent.response_to_actions = lambda response: ["STOP_AFTER_CAPTURE"]
        agent.step(state)
        actual = captured[0]
        direct = memory.process_events(copy.deepcopy(state.history), copy.deepcopy(initial), max_message_chars=10000, vision_is_active=False)

        def serial(messages):
            return [{"role": m.role, "text": text_of(m.content), "tool_call_ids": [c.id for c in m.tool_calls] if m.tool_calls else [], "tool_call_id": m.tool_call_id} for m in messages]

        actual_rows, direct_rows = serial(actual), serial(direct)
        tool_messages = [m for m in actual_rows if m["role"] == "tool"]
        calls = [i for m in actual_rows for i in m["tool_call_ids"]]
        tool_ids = [m["tool_call_id"] for m in tool_messages]
        is_complete = kind == "complete"
        o1 = "not_applicable"
        if is_complete:
            o1 = "supported" if len(tool_messages) == 1 and f"exit code {status}" in tool_messages[0]["text"] and tool_ids == ["call-a"] else "violated"
        o2 = "supported" if ((calls == tool_ids == ["call-a"]) if is_complete else not calls and not tool_ids) else "violated"
        rows.append({"id": cid, "boundary": kind, "runtime_exit_code_supplied_by_fixture": status,
                     "original_content": obs.content, "native_formatted_observation": obs.to_agent_observation(),
                     "history_event_types": [type(e).__name__ for e in state.history], "consumer_messages": actual_rows,
                     "O1": o1, "O2": o2, "direct_messages": direct_rows, "direct_check_same_judgment": actual_rows == direct_rows,
                     "native_scheduler_reachability": "unknown" if not is_complete else "not_executed"})
    return {"host": "OpenHands", "revision": "34bf9c2579ca5a25e452583eed38c6c0e45cebd6", "exposure": "previously_exposed",
            "conditions": rows, "upstream_test_implementation": "not_locally_available_not_inspected_or_executed",
            "native_runtime_executed": False, "model_called": False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for name, run in [("swe_agent", run_swe_agent), ("openhands", run_openhands)]:
        path = args.output / f"{name}.json"
        if path.exists():
            raise RuntimeError(f"Refusing to overwrite {path.name}")
        try:
            result = run()
            result["execution_status"] = "completed"
        except Exception as error:
            result = {"execution_status": "fixture_error", "error_type": type(error).__name__, "error": str(error)}
        path.write_text(json.dumps(result, indent=2) + "\n")
        print(name, result["execution_status"])
    (args.output / "executed_slices.json").write_text(json.dumps(SLICES, indent=2) + "\n")


if __name__ == "__main__":
    main()
