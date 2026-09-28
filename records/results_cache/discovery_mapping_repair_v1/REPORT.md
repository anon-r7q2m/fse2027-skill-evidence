# 单个模型自选目标的映射续行：未进入代码迁移

2026-09-22。**1次映射请求、0次代码生成、0个包、0新增评分或收益。**
模型修正了旧卡的观察归属限制，但没有说明保留参数如何进入目标运行。
独立校准判为 `BEHAVIOR_CARD_REJECTED`；原流程已零请求关闭，最终处置为
`NOT_ELIGIBLE_NO_PACKAGE`。这是映射规格缺口，不是已生成代码的迁移失败。

## 本轮实际得到什么

沿原 Direct 自选 `tool_result_observation_compaction` 继续，保留来源、入口、
O1/O2和排除项；模型只收到公开失败、来源证据及真实宿主实现。
本轮标签为 L1 开发续行，不能称新来源自动发现或 Agent2Skill 优于 Direct。

新卡改为选择 eligible host observations，按 `origin_query` 分组、保留最近若干组，
并声明避免重复投影的状态。这修正了旧卡只处理 package-owned observations 的不可达映射。
但它仍承诺可配置的 `keep_iterations >= 1`，却没有定义配置交付或初始化，
`required_domain=[]`，实际会话初始状态为 `{}`。内部字段名可留给实现选择；配置值的
来源则决定可检验行为。固定 donor factory 显式传入 `config.keep_iterations`，
构造器默认3不能唯一决定该调用路径。评价者不能新增配置键或只测试3而缩窄原义务。

按[冻结计划](../../experiments/discovery_mapping_repair_v1/PLAN.md)中明确的配置要求拒绝，
没有人工补卡、修改候选代码或新增判定规则。没有将抽象的65条观察边界认定为宿主缺陷。
[独立说明](../../docs/reviews/discovery_mapping_repair_v1_outcome_20260922.md)记录判定依据。

新卡身份为 `e0c1d872a86075502ffdc264617973ad844b505fd83504026d9772018b1a67c0`；
原卡 `d6b973571e9d7b2871ec0b6dccbd39d443f6819ce79224c9ee1852cf3c3ea40a` 及失败结果不改。
历史4个 donor 案例按原字节复用，不计新增来源执行。新增 donor、正确/错误控制、
hidden 案例、生成包真实入口、benchmark求解与评分均为0。

## 执行与关闭

唯一请求COMMIT，input41827/output3773，无新增UNKNOWN或未知usage，费用TBD。
发现原launcher3085234于20:17:59UTC wait/exit0；零请求关闭launcher3230982于
20:36:54UTC wait/exit0，两服务0重启。最终包为null，独立最终处置函数确认无包可验收。

3个未用迁移槽已退休：**564 used＋119 retired＝cap683 CLOSED**，0在途。
benchmark累计仍为**914/1387**。本版不重开、不换目标、不追加同样请求。

本轮没有新增益，也没有证明宿主无法实现压缩或模型无法写出实现。它显示当前协议下
模型没有在冻结前补齐可执行映射。下一方法决策需解释为什么继续在代码前的规格环节
投入能降低研究不确定性；不能原样重复四格或把流程关闭算作研究成功。
历史L2四题局部正差保留，十二题持平、后继四题全零和反馈持平同样保留；完整goal未完成。

证据：[完成汇总](completion_summary.json)、[校准seal](generation/calibration_seal.json)、
[最终seal](generation/all_final_seal.json)、[额度关闭](generation/allocation_close.json)、
[最终无包处置](acceptance/nexahe_direct/result.json)。
