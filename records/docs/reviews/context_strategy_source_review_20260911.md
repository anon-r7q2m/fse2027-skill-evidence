# 固定 Moatless / Trae 上下文策略源码审查

日期：2026-09-11。范围：下一来源策略选择；零模型请求、零 benchmark 启动。

## 决定

**NO：这两个固定来源中，没有找到可以直接替代当前 C、对通用 shell 观察进行完整语义压缩的 donor 机制。** Trae LakeView 是面向用户的轨迹注释，不在下一次 solver 请求中压缩上下文。Moatless 确有完整的消息历史选择代码，但它依赖类型化动作产生的摘要、文件状态和测试状态，不能只取其中的选择循环，再由宿主补写通用摘要器，却仍把整体称为 donor 策略。

若继续在这两个来源中做一次零调用筛查，唯一建议保留的条件候选是 **Moatless 的类型化观察摘要替换**：连同摘要生产者一起迁移 `MessageHistoryGenerator` 中“旧的大观察可用已有摘要，最后已执行节点保留原文”的规则。它比 `cleanup_context` 删除原语有更完整的来源边界，但目前尚不能承诺覆盖现有 shell 日志。不要因此启动模型或继续旧 G+C 效果块。

这是一项新的 L2 给定目标开发候选。原 Trae 两臂的 `BEHAVIOR_CARD_REJECTED` 和原 O3 的 `IndexError` 事实保持不变。

## 固定源码与入口

| 来源 | 固定 commit | 主要源码 |
|---|---|---|
| Trae | `e839e559ac61bdd0e057c375dd1dee391fee797d` | `trae_agent/utils/lake_view.py`；`utils/cli/simple_console.py`；`agent/base_agent.py` |
| Moatless | `011ead57a5c81664e9c45e07e1f50b17e695cc63` | `moatless/message_history/{message_history,compact,react_compact,summary}.py`；`actions/{view_code,run_tests}.py`；`agent/agent.py`；`node.py` |

路径与 Git blob 身份由 `results_cache/discovery_successor_v1/source_packs/{trae,moatless}/tree.json` 对应。已有正文从 blob cache 读取；缺失的相关公共文件从同一固定 commit 只读获取并核对 Git blob SHA，没有改写 source pack。

### Trae：LakeView 产物投向界面

- [`LakeView._agent_step_str`](https://github.com/bytedance/trae-agent/blob/e839e559ac61bdd0e057c375dd1dee391fee797d/trae_agent/utils/lake_view.py#L177) 仅拼接 `llm_response.content` 与工具调用名、参数，不读取 `tool_results`。它不足以从原始失败日志中提取必须保留的细节。
- [`create_lakeview_step`](https://github.com/bytedance/trae-agent/blob/e839e559ac61bdd0e057c375dd1dee391fee797d/trae_agent/utils/lake_view.py#L194) 调用步骤描述与标签提取，返回 `LakeViewStep(desc_task, desc_details, tags_emoji)`。描述 prompt 要求最多 10 / 30 词，标签来自固定集合；这不是 solver 上下文的信息保留契约。
- [`SimpleCLIConsole.update_status`](https://github.com/bytedance/trae-agent/blob/e839e559ac61bdd0e057c375dd1dee391fee797d/trae_agent/utils/cli/simple_console.py#L57) 启动后台显示任务；[`_create_lakeview_step_display`](https://github.com/bytedance/trae-agent/blob/e839e559ac61bdd0e057c375dd1dee391fee797d/trae_agent/utils/cli/simple_console.py#L222) 把上述字段放进 `Panel`，最终打印。
- [`BaseAgent._run_llm_step`](https://github.com/bytedance/trae-agent/blob/e839e559ac61bdd0e057c375dd1dee391fee797d/trae_agent/agent/base_agent.py#L209) 直接把消息交给 `_llm_client.chat`；工具结果经 `_tool_call_handler` 进入后续消息。上述路径没有把 LakeView 描述替换进 solver history。
- `extract_tag_in_step` 第 168–169 行先 `findall`，随后直接访问 `matched_tags[0]`；无匹配会抛 `IndexError`，不会到达第 173 行的 retry。步骤描述的重试循环是另一个函数，不能用它解释 tag 分支。

**适配边界：** 把 LakeView 的注释结果插入下一次请求、让它读取工具输出、决定何时触发以及哪些观察可替换，都会新增 donor 没有的策略。这样的系统可以另行研究，但不能作为本轮寻找的“完整 donor 上下文策略”通过。

### Moatless：真实影响 solver，但需要保留类型化依赖

[`ActionAgent._generate_actions`](https://github.com/aorwall/moatless-tools/blob/011ead57a5c81664e9c45e07e1f50b17e695cc63/moatless/agent/agent.py#L127) 将 `memory.generate_messages(node, workspace)` 的返回值直接传入 `completion_model.create_completion(messages=messages)`。这是实际模型输入路径。

**推荐筛查的精确边界：**

1. [`MessageHistoryGenerator._generate_unlimited_messages`](https://github.com/aorwall/moatless-tools/blob/011ead57a5c81664e9c45e07e1f50b17e695cc63/moatless/message_history/message_history.py#L307) 先寻找最后一个具有 `action_steps` 的节点；即使其后存在待执行节点，也能定位最后已执行节点。
2. [`_process_assistant_message`](https://github.com/aorwall/moatless-tools/blob/011ead57a5c81664e9c45e07e1f50b17e695cc63/moatless/message_history/message_history.py#L212) 保留动作与观察配对。只有旧节点、`max_tokens_per_observation` 非零、观察 token 数严格超过阈值且存在 `observation.summary` 时，才以摘要替换；否则保留原观察。最后已执行节点中的所有动作观察均保留原文。
3. 摘要是动作产物，不由上述 history generator 自行生成。[`ViewCode.execute`](https://github.com/aorwall/moatless-tools/blob/011ead57a5c81664e9c45e07e1f50b17e695cc63/moatless/actions/view_code.py#L219) 提供已查看 span 的摘要或重复查看说明；[`RunTests.execute`](https://github.com/aorwall/moatless-tools/blob/011ead57a5c81664e9c45e07e1f50b17e695cc63/moatless/actions/run_tests.py#L145) 分别生成带失败详情的完整输出与测试汇总 `summary`。

该策略的可检验收益假设是：已有可靠类型化摘要时，缩短已经送达的旧观察，同时让最近一次工具结果完整进入下一轮。它不自动保证旧失败详情永不丢失，也没有“rc 为 0 就可以删除”的规则。

**不能顺带迁移为既定正确行为的相邻代码：**

- `MessageHistoryGenerator._generate_token_limited_messages` 第 115–124 行按单条消息逆序装入预算，未按工具调用及响应成组选择，可能留下孤立响应。建议首次筛查使用 donor 本身支持的 `max_tokens=None` 配置，仅启用每观察阈值；宿主的整体请求 admission 仍独立保留。若以后修为成组裁剪，应单列适配。
- `CompactMessageHistoryGenerator.get_node_messages` 有最新文件去重、文件上下文重建、当前 diff 和测试失败详情等规则，依赖更大。它在同一节点的 `action_steps` 循环内重置 `actions` / `observations`，循环后才追加，不能假定全部动作保留。其原生 `generate_messages` 收集全部 tool calls，却只追加最后一个 tool response。`ReactCompactMessageHistoryGenerator` 的序列化避免了后一项问题，仍继承前一项问题。
- `SummaryMessageHistoryGenerator` 用轨迹索引判断“不是最后节点”。`Node.get_trajectory()` 包括当前待执行节点；在该入口中，最后已执行动作也可能被摘要。因此不能把它按注释概括为“保留最新原文”，更不能与基础 generator 的 last-executed 规则混用。

## 宿主适配必须声明的内容

| 项目 | donor 提供 | 当前宿主所需的明确变化 |
|---|---|---|
| 观察身份 | 类型化动作、节点和 `Observation` | 映射到真实工具调用、观察 ID 与实际投递状态；不能仅因 `eligible=true` 就认定已送达 |
| 压缩内容 | 动作生产者写好的 `summary` | 连同生产者及其类型化输入一起迁移；当前任意 shell stdout 不能自动获得同等摘要 |
| 最近观察 | 最后已执行节点全部观察保留原文 | 与真实下一次模型请求的消息序列对应；未送达结果和待 ACK 反馈保持完整 |
| 文件状态 | span/context 状态参与摘要 | 要么包内闭合状态依赖，要么将等价宿主能力列入适配；不能只根据文件名删除旧读取 |
| 预算 | 每观察 token 阈值；可选总 history 上限 | 固定计数器、输入阈值与整体 admission 的关系；配置变化与算法修正分别记录 |
| 失败信息 | typed tests 的完整输出和概要分离 | `pytest ... || true` 的外层 rc 不能代替语义失败判断；若缺少等价类型化信息，保留原文或拒绝适配 |

加入辅助模型对通用日志生成语义摘要，是新算法组成部分，需要自己的来源与计费记录。不能把它算成上述 donor 规则的零成本实现。

## 最小零调用判别案例

以下是下一步的案例设计，**本审查没有执行这些案例，也没有给出通过结论**。用新公共合成材料和固定 donor 执行对照，足以决定是否值得继续；无需重跑旧 benchmark。

| 案例 | 必须观察的判别点 |
|---|---|
| 两个已执行节点加一个待执行节点 | 旧观察超过阈值且有摘要才替换；最后已执行节点全部原文保留。阈值相等、摘要为空分别保持原文。它可区分基础 generator 与 `summary.py` 的不同语义。 |
| 同一节点两次工具调用，带不同结果 | 原动作/响应配对全部保留，进入下一请求；不能只核对摘要字符串。对 compact 分支直接按 donor 执行呈现实际缺口，不能暗改比较器让它通过。 |
| 一段仍包含必要事实的旧成功输出，加外层 rc0 的失败日志 | 无类型化摘要时保留原文；如果提供 donor 测试汇总，应如实显示哪些详情被丢失。若当前任务要求保留的关键事实不在摘要中，该候选在该域 NO，不临时手写 selector。 |
| 同文件旧版本、更新后的新版本与重复读取 | 只有来源定义的摘要/上下文状态可替代原文；不得把“同路径”当成内容等价。最新必要版本、版本变化与摘要引用必须可追踪。 |
| 压缩后仍超限，或没有可替代的旧摘要 | 不伪造压缩、预算节省或 ACK；由原整体 admission 如实拒绝/停止。检查实际下一次 solver 请求，计入新增前缀和机制反馈。 |

先验证这些案例能由当前宿主表达，并记录 donor 实际输出。如果必须新增一个通用语义摘要器才能让第三项成立，结论是**该来源不能闭合当前目标机制**。应另找真正把工具输出摘要反馈到 solver 的来源，而不是把 LakeView 显示层拼接成这样的实现。

## 本轮交付状态

固定来源的调用链与上述代码边界已核对；未形成新的自动包，未改变冻结行为卡、旧包或计分结果。当前推荐只到条件候选的零调用筛查；可执行迁移资格、宿主作用与真实增益均为 `TBD`。
