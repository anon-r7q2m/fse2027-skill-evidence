# smolagents 静态资格审查

日期：2026-09-29。审查对象仅为盲化的 `case_x`、`case_y` 三文件包、冻结的 smolagents 原始源码及相关公开文档/测试，以及 `PROTOCOL.md`。本审查没有导入或执行目标、fixture、测试、补丁、模型或容器，没有访问网络，也没有改写预测。下文的行为均为源码推断，不是运行发现。

审查者未构造这两份预测；未读取 `allocation.json`、原 diagnostics、另一组材料或论文。此前参与过项目论文及证据工作，不能声称对项目整体毫无接触；本轮没有使用那些材料判断诊断。组别标签隐藏，但预测内容、源码选择和写法可能泄露分析路线，因此只是标签盲化，不声称完全盲化。

路径约定：`X/`、`Y/` 分别表示 `/STUDY_ROOT/qualification/case_x/`、`case_y/`；`S/` 表示 `/STUDY_ROOT/sources/smolagents/`；`P` 表示本目录的 `PROTOCOL.md`。行号均对应本次冻结文件。

| 包 | 静态资格 | 可以检验的命题 | 不可升级为 |
|---|---|---|---|
| `case_x` | **QUALIFIED_WITH_SCOPE** | 原生代码修复器误改字符串常量，导致正确源级答案在真实工作流中丢失；保留预先声明的两个触发和两个控制 | 校验器对其实际收到的损坏值作出了错误拒绝；fallback 是错误成功；一般 Python 重命名正确性 |
| `case_y` | **QUALIFIED_WITH_SCOPE** | `PYTHONOPTIMIZE=1` 时，公开注册的布尔校验被框架的 `assert` 一并省略，随后产生原生成功接受；补丁恢复调用和重试 | 默认解释器也有此行为；优化运行的广泛支持承诺；任意错误答案都证明框架缺陷 |

两项资格都不代表已确认发现或允许忽略下面的启动条件。`case_y` 存在真实 dotenv 导入入口；根随后提供了公共执行器的环境约束，并明确授权只读核对其环境构造和已安装 dotenv 的对应实现。该入口在指定执行器与依赖组合下已静态排除，未修改冻结 fixture，未执行行为。

## case_x

**公开义务足以支持限定的表示完整性命题。** `S/README.md:205–232` 将动作定义为 Python 代码和 Python 函数调用；`S/src/smolagents/local_python_executor.py:332–336` 明确说明修复对象是变量赋值并保留 `final_answer()` 调用；同文件 `1461–1463` 对 `ast.Constant` 返回原始值。这不承诺接受任意错误模型代码，但第一个触发的唯一赋值目标是 `answer`，常量 `"final_answer = 42"` 无需变量修复（`X/prediction.json:111–156`）。第二个触发及成功控制保留确有必要的名字修复（`158–239`）。上游已有名字修复测试明确期待赋值和引用被改名，同时保留函数调用（`S/tests/test_local_python_executor.py:2139–2168`），所以不能把删除修复器当作充分干预。

**源码预测链连贯。** 原函数以原始文本搜索赋值并执行两次正则替换，没有区分 `Name` 和字符串常量（`S/src/smolagents/local_python_executor.py:338–356`）。第一触发预言的常量变成 `final_answer_variable = 42`，第二触发的常量变成 `final_answer_variable`，均直接由冻结代码和上述替换规则推出。`CodeAgent._step_stream` 先解析并调用该修复器，再把同一 `code_action` 交给原生 executor（`S/src/smolagents/agents.py:1702–1726`）；executor 返回真实输出和 final 标志（`local_python_executor.py:1630–1654,1747–1758`）。主循环只有校验成功后才置 `returned_final_answer` 和 `ActionStep.is_final_answer`（`agents.py:582–603`）。fixture 记录了实际代码、执行观察/状态、校验参数与返回布尔、原生 action 标志和 `RunResult`（`X/fixture.py:106–181`），没有重写 executor 或 acceptance loop。

**必须固定决策层次。** `X/prediction.json:91–108` 已承认校验器正确拒绝损坏值、预算耗尽合法，且不指控 fallback 假成功。这一限定成立：`agents.py:625–637` 显式记录 `AgentMaxStepsError`，`523–526` 返回 `max_steps_error`；上游测试也明确允许失败校验后最终提供 fallback（`S/tests/test_agents.py:717–735`）。因此，本案只能记为“框架前处理改变了代码的数据，造成原生工作流丢失正确源级答案”。若 G4 汇总专门计数“校验器对实际收到的对象作出的错误接受/拒绝”，本案不满足该更窄计数口径，必须单列，不能用控制流走到 `False` 或出现 fallback 文本来补足。其 source-preservation 义务已经写入冻结预测，并非本审查新加义务。

**补丁足以作为该有限命题的预先干预。** `X/intervention.patch:13–59` 改为解析 AST，只替换存在真实 `Name(Store)` 且有直接 `final_answer` 调用时的非调用目标名字；原文件已导入 `ast`（`local_python_executor.py:17`）。对冻结的简单赋值输入，UTF-8 字节偏移逆序替换保留字符串常量并保留必要名字修复；它没有降低校验标准、增加预算或改变返回状态。静态未发现 hunk 对不上冻结原文、缺少导入或这些输入所需的语法/API 障碍。但这不是全语法、作用域、变量碰撞或通用 alpha-renaming 的证明，预测 `315–317,351–356` 的有限范围应保留。

**脚本和控制合格。** `X/fixture.py:70–102` 只按响应序号选择内容，实际消息只被记录；匹配原生 `ChatMessage` 列表和固定 kwargs。正常动作调用与 `agents.py:1651–1681` 一致，fallback 的无额外 kwargs 调用与 `810–848` 一致。合法提前停止允许留下脚本后缀；unexpected call/exhaustion 强制 `INCONCLUSIVE`（fixture `174–179`）。两个触发各至多 2 个响应、1 步；控制分别为成功名字修复和“执行失败→校验失败→成功”的 3 步恢复（prediction `203–309`），未超过 P:61–80 的限额。它测量固定下一响应能否被原生路径消费，不证明真实模型会根据错误反馈恢复。

## case_y

**校验义务明确，配置范围必须显式保留。** `S/src/smolagents/agents.py:287–290` 规定在接受答案前运行注册函数；`S/docs/source/en/guided_tour.md:394–398` 规定返回 `False` 后继续运行。实际调用接受三个参数，fixture 的 `accept_42(final_answer, memory, agent)` 与源码一致（`Y/fixture.py:98–106`、`agents.py:616`），没有照抄文档示例中较窄的签名。对已注册普通布尔函数，框架在 `assert check_function(...)` 内完成调用；Python 的优化语义会省略整个断言表达式，而非只省略失败异常。这支持冻结的条件机制预测。已读的相关公开文档没有给出优化模式排除条款，但“没有找到排除条款”也不是全面支持认证。

准确分类为 **非默认运行配置触发的公开校验合同缺口**。它可以支持受条件限制的接口违反/实现风险；不得报告为普通配置缺陷率，亦不能仅凭应用选择 `-O` 就宣布一个无条件 upstream bug。预测本身明确承认这一边界（`Y/prediction.json:66–70,226–233`）。如裁定方不认可优化模式属于此公开接口的支持范围，framework-defect 分类必须保留争议或降为 application-configuration hazard，不能在看到结果后悄悄扩大合同。

**存在真正的原生成功消费者。** `Y/fixture.py:51–60,111–135` 导入整套原生 agent/executor，注册真实 checker，通过 `CodeAgent.run(..., return_full_result=True)` 取 `RunResult`；`108–109,122` 还注册原生 `FinalAnswerStep` 回调。回调 API 与 `agents.py:416–434`、`memory.py:289–316` 相符。主循环的 `agents.py:589–592` 在 `_validate_final_answer` 返回后置 final 标志，`523–526` 计算 success，`609–611` 发出真实 `FinalAnswerStep`。本案要求同时看到 checker 未运行、候选值 `13`、第一 action 被接受及原生 success，已排除“错误模型文本本身就是框架缺陷”（prediction `80–101`）。原生 `ChatMessage.token_usage` 可为 `None`（`models.py:124–129`），监控与完整结果都允许它（`monitoring.py:110–117`、`agents.py:509–521`），故未提供 token usage 不是静态 API 阻断。

**脚本和局部补丁一致。** `Y/fixture.py:71–96` 按固定序号返回响应，检查 kwargs，不按历史/补丁标签分支。native 默认代码标签就是 `<code>`/`</code>`（`agents.py:1556–1564`），实际生成调用与冻结调用形状一致。子解释器只按冻结输入设定 `PYTHONOPTIMIZE`，同一案例的原始/补丁运行没有不同脚本（fixture `194–210`）。触发至多 2 响应/2 步；控制分别是优化模式正确答案和普通模式下执行失败、拒绝、再成功的 3 响应/3 步（prediction `104–210`）。优化成功控制原始运行预计没有 checker 调用，不能据此说校验合同保持正确；它只是保留合法正确输出的控制。拒绝/恢复控制在 `optimize=0`，不能外推为所有优化错误路径覆盖。

`Y/intervention.patch:3–11` 用普通条件及 `ValueError` 代替断言，保留既有 `AgentError` 转换、重试和接受逻辑。补丁没有改变 `accept_42`、答案任务或步数限制；对这些输入足以测试“断言抹除调用”机制。异常消息改变不影响冻结的异常类型 oracle。没有静态语法或引用缺失问题被发现；未实际应用补丁或执行确认。任何意外 fallback 不在脚本许可中，fixture 必须保留 `unexpected_calls` 并标为 `INCONCLUSIVE`，即便上游 `provide_final_answer` 捕获生成异常后返回了文本。

## 执行前需排除的具体问题

1. **dotenv 入口已由指定执行器静态排除，须保持该条件。** `S/src/smolagents/agents.py:80` 无条件导入 remote executor 模块，该模块 `45–48` 在可导入依赖时调用 `load_dotenv()`，且 `pyproject.toml:21` 列有 `python-dotenv`。`Y/fixture.py:197–210` 复制父环境，导入前没有自身的禁用/阻断代码；仅 `chdir` 和清空环境并不足够。但只读核对 `/RESEARCH_ROOT/analysis/prospective_decision_v1.py:59–73,167,182–185` 后，确认所给执行器构造环境白名单，设置 `PYTHON_DOTENV_DISABLED=1` 并明确传给每个 fixture。指定 venv 的 `lib/python3.12/site-packages/dotenv/main.py:22–29,418–425` 在调用 `find_dotenv()` 之前识别该值并返回 `False`。Y 子进程继承此约束，故无需修改冻结 fixture。这是环境构造和依赖源码的静态验证，不是实际运行证明，亦未读取任何 `.env`。X 的 `fixture.py:33–51` 另有 audit hook。若换执行器/依赖、丢失该变量或直接从交互 shell 启动，必须重新排除此具体入口；不能把由此造成的失败当作发现。
2. **解释器和源身份必须由执行器落实。** X 要求 `sys.flags.optimize==0`；Y 通过子进程设置并核对 `0/1`（`Y/fixture.py:48–49,198–205`）。不得用会忽略 `PYTHONPATH`/优化环境的启动选项而把错误导入判成预测反例。两包依赖根持有的 source pin，未自行声称 git commit（`X/prediction.json:47–51`；`Y/prediction.json:17`）；本审查未越界读取 pin 元数据。执行记录需确认加载的是所选独立 source copy，Python 至少 3.10（`S/pyproject.toml:13`），依赖包含实际无条件导入的 `yaml`（`agents.py:33`）。导入失败只属于可行性问题。不要用已安装的另一版本或截取 helper 代替。
3. **输出路径和过程边界由外层保证。** 两 fixture 都接受任意 `--workdir`/`--output`，本身不验证二者落在 owned tree 内（`X/fixture.py:185–211`；`Y/fixture.py:174–191`）。执行器必须只传 owned 输出位置，保持任务代码、输出及临时文件远离个人文件。X 原生单动作 10 秒，外层 alarm 110 秒；Y 原生单动作 2 秒、子进程 10 秒（`X/fixture.py:125,213–229`；`Y/fixture.py:118,208–210`）。仍需 P:96 的外层进程上限。Y 的短启动期限可能只测到冷导入超时，必须记录为 `INCONCLUSIVE`，不能追加响应、放宽预测或当作机制反例。
4. **两套 fixture 均是证据收集器，不是断言器。** `OBSERVED` 和进程退出状态不等于命题成立。必须逐项比较冻结 oracle，保留 unexpected call、script exhaustion、capture/import/run exception、实际 action/error/checker 记录及原生结果。Y 即使返回进程码 0，也可能在 JSON 中为 `INCONCLUSIVE`（fixture `137–169,220–230`）。X 的 fallback 与 Y 的错误接受不能混记。
5. **联合矩阵保持同一输入同一脚本。** P:92–94 要求两包输入分别在 original、X-only patch、Y-only patch 上运行，不叠加补丁；应保留各自原 fixture 和相邻 prediction，不能把脚本改成“适配当前补丁”。静态看 X 补丁不需要改变 Y 的脚本，Y 补丁不需要改变 X 的脚本；这是结构相容性判断，不是交叉运行结果。任何 wiring 修复只能按 P:100–106 记录为有限 import/API/harness 修复；不得改承诺、响应、优化级别、控制、预期决策或补丁语义以得到确认。

本次未发现需要在执行前更改预测或冻结输入的 API 阻断；指定执行器的 dotenv 条件已静态核对，实际源身份、完整运行及其余执行约束仍须由运行证据落实。静态资格、运行可行性、原始缺陷出现、干预成功、控制保持和最终 G4 计数应分别记录。本报告不作论文评分，也不把两个触发输入当作两项独立发现。
