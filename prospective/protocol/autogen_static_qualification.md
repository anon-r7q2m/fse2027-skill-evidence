# AutoGen 静态资格审查

日期：2026-09-29。只读审查盲化包 `case_u`、`case_v` 的 `prediction.json`、`fixture.py`、`intervention.patch`，冻结 AutoGen 原始源码及相关公开文档/测试，以及 `PROTOCOL.md`。没有运行、导入或测试目标/fixture，没有应用补丁、联网、模型调用、Docker 或 benchmark，没有改写预测。

审查者未构造这两包；未读取 allocation、原 diagnostics 或论文。此前参与过项目论文/证据工作，因此不声称项目历史零暴露。本轮标签隐藏，但正文、类名、文件内代号和分析写法可能泄露路线；不据此推断标签，也不声称完全盲化。以下都是静态资格判断，没有行为结果。

路径约定：`U/`、`V/` 分别为 `/STUDY_ROOT/qualification/case_u/`、`case_v/`；`A/` 为 `/STUDY_ROOT/sources/autogen/python/`；`AC/` 为 `A/packages/autogen-agentchat/src/autogen_agentchat/`；`CORE/` 为 `A/packages/autogen-core/src/autogen_core/`；`EXT/` 为 `A/packages/autogen-ext/src/autogen_ext/`；`P` 为本目录 `PROTOCOL.md`。

| 包 | 结论 | 已有公开义务支持的有限命题 |
|---|---|---|
| `case_u` | **QUALIFIED** | `TextMentionTermination` 配置往返丢失明确指定的 `sources`，使不符合来源资格的 executor 消息提前终止原生 team |
| `case_v` | **QUALIFIED** | 原生生成/执行事件出现在输出流，却未进入响应的 `inner_messages`；配置 `include_agent_event=True` 的 team 终止计数因此少计并多运行一轮 |

**未发现必须先改冻结 fixture、预测或补丁才能执行的 API/wiring 阻碍。** 资格依赖根所声明的完整 source copy、清洁环境、owned workdir 和超时执行条件。下面保留的局限不是要求增加样本或改写预言。

## case_u

**义务独立、具体，并非把任意 marker 解释为成功。** `AC/conditions/_terminations.py:115–126` 公开规定 `sources` 限制哪些发送者的消息可触发；`CORE/_component_config.py:135–146` 公开规定配置应能创建与原实例配置相符的组件，并可 dump/load。`sources` 属于配置而非一次运行的 `_terminated` 状态。原 schema 只有 `text`，`_to_config` 和 `_from_config` 也只传 `text`（`_terminations.py:107–108,150–155`）；实际 consumer 又以 `_sources is None` 表示不限制来源（`132–144`）。由此能够静态推出被冻结的“来源限制在序列化边界丢失”机制，不需观察结果后另造义务。

**fixture 通过完整原生配置与 team 消费链。** `U/fixture.py:141–158` 实际执行 `dump_component().model_dump(mode="json")`、`TerminationCondition.load_component`，将恢复对象交给真实 `RoundRobinGroupChat`。CORE 的 loader 支持字典，并调用 schema 与 `_from_config`（`_component_config.py:241–244,272–303`）；所用公共 provider 位于默认可信命名空间内（`256–269`）。team manager 在原生响应后取得 `inner_messages` 和 chat message、应用终止条件，随后决定是否选择下一 speaker（`AC/teams/_group_chat/_base_group_chat_manager.py:135–164,195–227`）。最终结果由原生输出队列生成 `TaskResult.stop_reason`（`_base_group_chat.py:539–564`），fixture 捕获该对象和真实消息顺序（`U/fixture.py:163–175`）。不是调用一个复制的 termination helper 后自行宣布 team 已停。

触发任务中的代码拼接 `"REVIEW_" + "STOP"`，原任务文本不含连续 `REVIEW_STOP`（`U/prediction.json:107–132`；fixture `18–35,159`）。真正含 marker 的第一条应是 exit-0 子进程的 executor 输出。于是 original 的 `[user, executor]`、0 provider call 与 patched 的 `[user, executor, reviewer]`、1 provider call 区分的是“谁被允许触发”，不是 marker 文案或模型是否正确（prediction `69–103`）。初始任务也会经过 termination（manager `104–129`），该字符串设计排除了在执行前意外命中这个入口。

**本机执行记录仍来自原生 executor。** `U/fixture.py:68–80` 使用观察子类，调用 `super().execute_code_blocks`、复制返回对象供记录、把同一对象返回给 agent，没有替换执行逻辑或伪造 exit code。`CodeBlock`/`CodeResult` 是 dataclass（`CORE/code_executor/_base.py:18–31`），`asdict` 的使用相符。原生 executor 写入 owned workdir，再通过当前 Python 启动真正子进程，捕获退出码/stdout/stderr（`EXT/code_executors/local/__init__.py:391–442,458–474`）。agent 在其后可能原地格式化非零输出（`AC/agents/_code_executor_agent.py:717–727`），所以保留格式化前的复制有实际用途。这一观察包装应在报告中披露，但不能称为替代/mock executor；冻结脚本的实际计算和退出仍完全由原实现执行。

**固定 provider 与控制合法。** 无模型的 executor 路径执行来自指定 `user` 的代码，并产生原生 TextMessage（`_code_executor_agent.py:530–544,677–685`）。reviewer 才使用一个固定响应；`U/fixture.py:85–139` 只按 replay 序号返回内容，检查 SystemMessage、user/executor 两个 UserMessage 及 kwargs，禁用 streaming，额外调用/耗尽为 `INCONCLUSIVE`。原生 AssistantAgent 的调用是 messages 加 tools、cancellation_token、json_output（`AC/agents/_assistant_agent.py:1085–1114`），与 frozen client 参数相符；ReplayClient 默认不生成 thought/tool calls（`EXT/models/replay/_replay_chat_completion_client.py:130–184`），不存在预期外模型分支。零次调用意味着合法未消费固定后缀，不是脚本耗尽。

三个案例均至多一个固定 provider 响应、`max_turns=4`、单命令 5 秒。成功控制和 exit-7 控制都没有 executor marker；都允许 reviewer 发出 marker 后终止（`U/prediction.json:150–239`）。exit 7、错误输出和 reviewer 终止同时发生是预先声明的合法控制，不能记为“非零退出后错误接受”或任务成功。

**补丁保持义务。** `U/intervention.patch:3–24` 在 schema 增加可选 `sources`，dump 时复制列表，load 时传回构造器；原文件已导入 `List`（`AC/conditions/_terminations.py:3`）。原有 `None` 默认、substring 匹配和来源检查不变，没有更换条件或把 trigger 从输入中删除。静态 hunk 与冻结原文相符。它只能保存今后正确导出的来源限制，不能恢复历史配置中已被丢掉的数据，也没有证明所有 Component 配置的往返正确性（prediction `275–280` 已声明）。

## case_v

**公开义务支持事件纳入，而不支持响应中途硬中断。** `AC/conditions/_terminations.py:62–68` 明确表示 `include_agent_event=True` 时计数 `BaseAgentEvent`；`AC/messages.py:457–487` 将两种 code 事件定义为该类型。公开教程 `A/docs/src/user-guide/agentchat-user-guide/tutorial/termination.ipynb:13,21–25` 明确以自上次调用以来的 delta，在每个 agent 完成响应后一次检查全部消息。`AC/base/_chat_agent.py:19–21,57–61` 也描述 `inner_messages` 及 inner message stream。本案的预言正是第一次完整响应结束后的 4 条：user task、generation event、execution event、executor TextMessage（`V/prediction.json:26–55`）。它没有要求事件一出现就取消尚未完成的 response，也没有把 token chunk 当成另一条完成消息。

**输出流与终止输入确实是两条原生路径。** CodeExecutorAgent 创建 `inner_messages=[]`，向 stream yield generation/execution event，但原文没有把这两个对象 append 到该列表（`AC/agents/_code_executor_agent.py:546,602–624`）。最终 reflection Response 转发此列表（`666–675,886–892`）。container 将 yield 的事件发往输出主题，却单独把最终 Response 交给 manager（`AC/teams/_group_chat/_chat_agent_container.py:131–149,167–174`）。manager 的 GroupChatMessage handler 只入输出队列（`_base_group_chat_manager.py:263–265`）；其 termination delta 则来自 `Response.inner_messages` 加 final chat message（`139–159`）。因此“输出可见”本身不等于“termination 收到了”；这是需要用冻结原生运行验证的具体缺口，而不是 fixture 内重新实现计数得到的结论。

在源码路径成立且无额外事件时，原始 termination 先计 task=1，再按每轮 final chat 加 1；两轮后只有 3，随后 `max_turns=2` 的合法 fallback 生效（manager `200–227`）。补丁使第一轮 delta 增加两个事件，累计达到 4。`MaxMessageTermination` 在 `include_agent_event=False` 时仍只计 BaseChatMessage（`_terminations.py:83–90`），故两个 chat-only 控制应保留 count-two 终止。错误位置是完整响应的事件表示遗漏，不能把较后发生的 max-turns fallback 本身叫作非法行为。

**fixture 的原生 consumer 与 provider shape 相符。** `V/fixture.py:97–139` 使用原生 `CodeExecutorAgent`、`LocalCommandLineCodeExecutor`、`RoundRobinGroupChat`、`MaxMessageTermination`，直接迭代 `team.run_stream` 并保留 TaskResult；`153–176` 同时保存 native stream、execution result、计数和 native stop reason。代码生成调用带 `tools=[]` 与非空 cancellation token，reflection 调用只带 messages（`_code_executor_agent.py:821,866`），与 frozen client 偶数/奇数调用检查一致（fixture `65–89`）。ReplayClient 顺序消费固定文本；无内容、exit status、source variant 分支。`max_retries_on_error=0` 确保非零执行后也不插入 retry/JSON 请求（源码 `627–648`）。fixture 的 kwargs 检查不是通用 Model API 验证器；本次原生具体调用形状足以匹配，任何实际意外调用仍须按冻结 oracle 作 `INCONCLUSIVE`。

两个触发分别 exit 0/7，冻结四个响应、`max_turns=2`；两控制使用对应相同脚本，只预先改变终止配置为 chat-only/count-two（`V/prediction.json:64–442`）。提前停止时可以不消费最后两个响应。非零触发/控制预期的 execution event output 是 agent 格式化后的输出（`_code_executor_agent.py:723–725`），不是未加工 stdout；fixture 没有声称另行捕获原始子进程管道。exit code 和实际执行证据来自原生 CodeResult，不应把固定 reflection 文本当作独立验证结果。

**补丁足以检验冻结路径，不扩大合同。** `V/intervention.patch:3–21` 把两个既有事件对象放入同一个 `inner_messages` 列表，仍按原顺序 yield，最终原生 Response 自动转交 manager；不修改 termination 计数、阈值、回合数、执行代码或 provider。列表在对应路径已存在，hunk 与原文相符，没有缺失符号或语法依赖。它只覆盖冻结的非 streaming、单代码块、无重试分支；不能据此宣布所有 retry、no-code、streaming 分支或全部事件都已修复（prediction `444–470` 已保留此范围）。

## 联合执行前的具体约束

1. **没有发现须修复的冻结 API 阻断。** RoundRobinGroupChat 支持单 participant 和 `emit_team_events=False`，调度为按 participant 列表轮转（`AC/teams/_group_chat/_round_robin_group_chat.py:72–82,242–265`）；两 fixture 均在真正执行前 `await executor.start()`，结束时 `stop()`。这些设置不需要改写输入。依赖可导入性未测试；导入失败只能记可行性/`INCONCLUSIVE`，不能用另一已安装版本顶替。
2. **联合矩阵不能叠加或改脚本。** U 补丁只影响 TextMentionTermination 配置；V 使用 MaxMessageTermination。V 补丁在有 model client 的执行分支；U 的 executor 走无 model client 分支并提前返回。因此两包静态上可在 original、U-only、V-only 三份独立源码上消费同一案例的原脚本，未见必须按 variant 调整内容的理由。此处没有宣称交叉控制已通过；实际运行须保留完整 7 个冻结输入来源和每份变体身份（P:92–94）。
3. **安全边界来自可信固定命令和根执行器。** 两包本机命令仅做整数计算、print、assert 或 `SystemExit(7)`；没有 pip、网络、外部模型、个人路径或 shell 注入。默认 `functions=[]` 使 executor 不进入依赖安装设置路径（`EXT/code_executors/local/__init__.py:190–195,336–339`）；Python 命令使用 `sys.executable`、cwd 为 owned workdir，并继承调用进程环境（`396–433`）。须持续使用根所声明且在 smol 审查中只读核对的 clean explicit environment 与 owned process group；不能直接继承个人交互环境。两 fixture 已拒绝 workdir symlink/非空目录（`U/fixture.py:207–212`；`V/fixture.py:213–218`），但 output 路径仍由执行方保证在 owned tree 内。
4. **超时与采集状态不代表支持。** U 是 command 5 秒、async 75 秒、alarm 110 秒；V 是 command 5 秒、team 90 秒、alarm 115 秒；仍要求外层不超过 120 秒。V 的硬 alarm 可能留下缺失报告，必须是 `INCONCLUSIVE`。U 的 `OBSERVED`、V 的 `COMPLETED` 只说明收集完成；必须另检 source origins、调用数/shape、真实代码/exit/output、消息序列及 TaskResult。provider exhaustion、timeout、缺少 native execution/TaskResult 或捕获异常均不能算发现或修复。U 还明确保持 `evaluation_status=UNEVALUATED`（fixture `186–198`）。
5. **不得把终止当作成功或升级计数。** U 的来源资格与 V 的预算计数是不同义务；非零退出后按规则终止是合法控制。两个 V 触发是同一机制的两个输入，不是两次独立发现。static qualification、原始错误决策、干预成功、控制保持和外推限制要分别判定；若需 wiring 修复，仅按 P:100–106 记录允许的 import/API/harness 变化，不改 frozen oracle。

两案可在上述既定条件下进入协议 G3。此结论不等于运行通过、benchmark 增益或论文评分；本审查没有请求新样本、替换 target 或扩大研究。
