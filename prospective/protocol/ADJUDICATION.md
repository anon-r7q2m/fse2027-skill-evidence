# prospective_decision_v1 G4 独立裁定

裁定日期：2026-09-29。审查者 `adversarial_f38_artifact`。依据唯一 `execution_v1` 的全部 **42 份**既有原生运行记录、冻结盲化预测/fixture/patch、先前静态资格范围和原始源码；没有再次执行目标、fixture、测试或模型。

**有限行为结论：X/Y 为 `SUPPORTED_WITH_SCOPE`，U/V 为 `SUPPORTED`。** 6 个原始触发均出现冻结预言的模式，6 个对应自身补丁运行均出现预声明干预效果；同族对方补丁下的 6 个触发仍在；8 个不同控制输入在三份源码上的 **24 个控制运行**均保留冻结的适用行为。未发现行为层面的 `REFUTED`、`INCONCLUSIVE`、未触发或漏执行记录。这里是 4 份机制预言、14 个输入、42 个运行，不能把多个触发或控制当作独立发现。

这不是四项无条件“错误校验器决策”的计数：X 是前处理损坏正确常量，随后 checker 的拒绝正确；Y 的接受缺口仅在 `optimize=1`。U/V 的停止事件均不证明任务成功。普通/原则组别映射未提供、未读取，本报告不裁定方法优越性或组间增益。

逐项预期值、实际值、原始 JSON 字段路径、运行身份与摘要记录在 [G4_ADJUDICATION.json](/RESEARCH_ROOT/experiments/prospective_decision_v1/G4_ADJUDICATION.json)。原始证据根为 `/RESEARCH_ROOT/results_cache/prospective_decision_v1/execution_v1`；下表数字是该目录 `runs/` 下唯一运行名称的前缀，完整名称均在 JSON 的 `runs` 数组中。表格中 `fa`/`fav` 仅为显示缩写 `final_answer`/`final_answer_variable`，机器裁定和原记录保留完整原文；`T/F` 表示真实 checker 返回值。

## 四份预言的裁定

| 包及输入标识 | 原始触发 | 自身预声明干预 | 自身与同族对方的适用控制 | 裁定 |
|---|---:|---:|---:|---|
| X / `s11` | 2/2 | 2/2 | 4/4 控制输入的 original/自身补丁配对 | `SUPPORTED_WITH_SCOPE` |
| Y / `s12` | 1/1 | 1/1 | 4/4 控制输入的 original/自身补丁配对 | `SUPPORTED_WITH_SCOPE` |
| U / `a21` | 1/1 | 1/1 | 4/4 控制输入的 original/自身补丁配对 | `SUPPORTED` |
| V / `a22` | 2/2 | 2/2 | 4/4 控制输入的 original/自身补丁配对 | `SUPPORTED` |

X 的运行 001/004 在实际 `code_action`、executor state、观察及 checker 参数中同时出现改坏的常量，checker 返回 `False`，原生 action 未标 final，结果为 `max_steps_error` 和显式 fallback。自身补丁 002/005 保留常量、保留第二输入必需的变量改名，原生 checker 返回 `True`，第一 action 成为 final，返回精确答案。成功改名控制及执行失败→校验失败→成功恢复控制保留。对方补丁 003/006 没有修复常量问题。**这支持冻结的代码表示完整性缺陷及其工作流后果；它不支持“checker 收到正确值却拒绝”或“fallback 被报 success”。** 若只计严格 validator 的错误判断，X 必须排除；该解释范围已在行为运行前静态资格中保留，不能由本轮结果扩大。

Y 的运行 013 在 `python_optimization=1` 下真实执行出 `13`，checker 调用表为空，第一原生 action 无错误且为 final，`FinalAnswerStep` 和 `RunResult` 都返回 `success/13`；不是只看见错误模型文本。自身补丁 015 按同一响应序列记录 `13→False`、`42→True`，首 action 为 AgentError/非 final，次 action 合法完成并返回 `42`。对方补丁 014 仍接受 `13`。优化配置正确答案控制 016/017 虽然返回正确 `42`，也仍未调用 checker；它们是**输出行为保留控制，不是校验已运行的证明**。018 恢复了 True 检查；普通解释器错误恢复控制 019–021 均保留。把观察泛化为默认解释器缺陷、所有优化模式支持承诺或无条件 upstream bug，仍不受支持。

U 的运行 022/024 将明确请求的 `sources=[reviewer]` 导出为只有 `text`，恢复来源为 `None`。相同可信本机代码实际 exit 0 并输出 `calculation 4` 与 marker；原生消息仅 `[user, executor]`，reviewer provider 从未调用，team 即因 marker 停止。自身补丁 023 导出/恢复来源限制，保留完全相同代码、exit 和输出，只在 `[user, executor, reviewer]` 后停止，消费同一固定 reviewer 响应一次。成功控制和 exit-7 控制在各变体都到 reviewer 后合法结束。**错误是已配置的来源资格在序列化中丢失，不是 marker 的文本含义或非零退出后停止。**

V 的原始运行 031/034 及对方补丁 032/035 均在第一次完成响应时已产生 user、generation event、execution event、final text 四条原生消息，却继续第二次生成/执行，最终有 7 条消息、2 次执行、4 次 provider 调用，按 `max_turns=2` 停止。自身补丁 033/036 在同一首轮代码、输出、exit 和 reflection 下，按 event-inclusive count=4 停止，只有 4 条消息、1 次执行、2 次 provider 调用。exit-0 与 exit-7 路径均如此。chat-only 控制 037–042 保留 count=2、一次执行和原始退出事实。**max-turns fallback 本身合法；缺陷是完整响应交给原生终止条件时漏掉既有事件，导致前一时点错误继续。** 固定 reflection 不是独立任务正确性检查。

## 全部运行矩阵

每一列都是独立完整源码副本，补丁未叠加。对方触发无需被某补丁修复；本表记录它实际仍在。

| 冻结输入 | original | s11 | s12 |
|---|---|---|---|
| `s11/t_literal_assignment_text` | 001: `max_steps_error/fallback`；check F；2 calls | 002: `success/fa = 42`；check T；1 calls | 003: `max_steps_error/fallback`；check F；2 calls |
| `s11/t_literal_inside_real_assignment` | 004: `max_steps_error/fallback`；check F；2 calls | 005: `success/fa`；check T；1 calls | 006: `max_steps_error/fallback`；check F；2 calls |
| `s11/c_successful_assignment_repair` | 007: `success/accepted`；check T；1 calls | 008: `success/accepted`；check T；1 calls | 009: `success/accepted`；check T；1 calls |
| `s11/c_execution_and_check_failure_recovery` | 010: `success/accepted`；check F/T；3 calls | 011: `success/accepted`；check F/T；3 calls | 012: `success/accepted`；check F/T；3 calls |
| `s12/trigger_optimized_rejection` | 013: `success/13`；check 未调用；1 calls | 014: `success/13`；check 未调用；1 calls | 015: `success/42`；check F/T；2 calls |
| `s12/control_valid_acceptance` | 016: `success/42`；check 未调用；1 calls | 017: `success/42`；check 未调用；1 calls | 018: `success/42`；check T；1 calls |
| `s12/control_failure_recovery` | 019: `success/42`；check F/T；3 calls | 020: `success/42`；check F/T；3 calls | 021: `success/42`；check F/T；3 calls |

| 冻结输入 | original | a21 | a22 |
|---|---|---|---|
| `a21/trigger_source_lost` | 022: executor 后 marker stop；exit 0；0 calls | 023: executor→reviewer 后 marker stop；exit 0；1 calls | 024: executor 后 marker stop；exit 0；0 calls |
| `a21/control_success` | 025: executor→reviewer 后 marker stop；exit 0；1 calls | 026: executor→reviewer 后 marker stop；exit 0；1 calls | 027: executor→reviewer 后 marker stop；exit 0；1 calls |
| `a21/control_execution_failure` | 028: executor→reviewer 后 marker stop；exit 7；1 calls | 029: executor→reviewer 后 marker stop；exit 7；1 calls | 030: executor→reviewer 后 marker stop；exit 7；1 calls |
| `a22/trigger_success` | 031: turns=2；7 messages；2 exec；4 calls；exit [0, 0] | 032: turns=2；7 messages；2 exec；4 calls；exit [0, 0] | 033: messages=4；4 messages；1 exec；2 calls；exit [0] |
| `a22/trigger_nonzero_exit` | 034: turns=2；7 messages；2 exec；4 calls；exit [7, 0] | 035: turns=2；7 messages；2 exec；4 calls；exit [7, 0] | 036: messages=4；4 messages；1 exec；2 calls；exit [7] |
| `a22/control_success_chat_only` | 037: messages=2；4 messages；1 exec；2 calls；exit [0] | 038: messages=2；4 messages；1 exec；2 calls；exit [0] | 039: messages=2；4 messages；1 exec；2 calls；exit [0] |
| `a22/control_nonzero_exit_chat_only` | 040: messages=2；4 messages；1 exec；2 calls；exit [7] | 041: messages=2；4 messages；1 exec；2 calls；exit [7] | 042: messages=2；4 messages；1 exec；2 calls；exit [7] |

## 身份、原生入口和脚本核对

42 份 observation 摘要均与各自 receipt/summary 一致；receipt 与 summary 的运行标识一致；记录的 source origins 和 `PYTHONPATH` 均属于对应 original 或独立 patch source。每个 launch 使用同一已封存 fixture、该案例固定参数、清洁环境和独立 work/output 位置，全部在 120 秒内返回；没有脚本耗尽、意外 provider shape、未捕获 traceback、导入/捕获/worker 异常被当作支持。框架中的预期执行错误与检查错误按控制 oracle 保留，没有因为其出现就判失败或成功。

我将四份副本的完整相关 `src` 文件树与所给原始 snapshot 比较：smolagents 每份 27 个文件，AutoGen 三个原生包每份合计 265 个文件；无新增/缺失，分别只有已声明的一个目标文件变化。把冻结 unified diff 当作文本投影核对后，目标文件字节恰为该补丁结果；未执行 patch 命令、目标 helper 或测试。由此验证了本矩阵所需的独立补丁身份，没有把根的 patch 应用成功状态直接当作内容证明。

provider 实际消耗是冻结序列的前缀。X/Y 的响应内容、调用 kwargs、native model output 与步骤代码相符；U 的 reviewer 输入确实包含相同 task 与原生 executor 输出、返回固定响应；V 的 generation/reflection 调用形状和真实生成事件/最终文本与顺序固定的四响应脚本相符。适用控制逐项核对了原生错误类型、final 标志、退出码、结果输出和停止原因。合法未消费后缀没有被误报耗尽。

**盲化摘要差异已闭合，但核验时点必须披露。** 首次身份检查发现四份盲化 `prediction.json` 的字节 SHA 与 `STARTED.json` 中原始封存 SHA 不同；四份 fixture 与四份 patch 的字节 SHA 全部一致。经根明确授权，我只读四个原始 prediction JSON，用独立静态比较核对原始字节仍等于 G2 seal，且只删除已声明顶层标签/披露字段后，所有保留字段与盲化包完全相等。实际删除字段名记录在机器文件；标签相关字段值未输出。四份原始 seal 均早于第一行为运行。**这是运行结束后对既有盲化投影的身份核验，不是执行前已有的新 seal，也没有改动预测、oracle、输入或结果。** 初始直接摘要不匹配及其解决方式保留在机器记录中，没有抹去。未读取 `GUIDANCE.md`、`diagnostic.md`、allocation 或普通/原则映射。

## 仍然不支持或未知的部分

- 行为层面未发现冻结 oracle 的矛盾或证据缺失；不把这一点升级为四项同质、无条件、普遍成立的框架漏洞。X 的严格错误 checker 判断不成立；Y 的非默认优化合同解释仍有明确范围。
- V 没有单独记录运行时 `Response.inner_messages` 或 manager 收到的 delta。该中间关系由冻结源码、仅改变两个 append 的独立补丁，以及实际原生消息/继续/停止结果共同支持，属于有证据的机制推断，不能写成存在独立 delta receipt。X 的来源记录是 package 路径与 native 类型名，而非各 class 的独立模块来源记录；源码字节和真实代码链补充了这条较窄的来源记录。
- 这些是提供的冻结 snapshot、进程记录和本机结果之间的核对，不是公开获取 commit、进程内存或零历史/训练暴露的独立远程证明。执行 fixture 的绑定依赖启动 seal、完全相同的盲化 fixture 字节和 launch 路径；未重开原诊断 prose 或指导材料。
- U 的 reviewer 与 V 的 reflection 是固定脚本，X/Y 的后续正确响应也是预先固定；不能据此证明 live model 会利用反馈、生产缺陷频率、benchmark 收益、所有分支修复完整性、补丁最小性或方法优越性。未新增样本、变体或条件。

审查者未编写四份诊断/fixture/patch，曾参与项目论文工作，并在执行前完成本轮静态资格；保留这一历史暴露。内容本身可能泄露路线，因此只声明组别标签未揭示，不声明完全盲化。本轮不作论文评分，也不要求扩实验。
