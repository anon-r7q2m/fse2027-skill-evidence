# 自动发现 L1 续行：来源行为成立，目标映射未成立

2026-09-22。**14次发现请求，1/4候选冻结、0/4可进入迁移，0生成包、0新增评分或收益。**
本轮已按固定四格完整关闭，不增加原样续行；完整研究goal仍active、未完成。

| 来源 / 方法 | 请求 | 发现终态 | 独立校准 |
|---|---:|---|---|
| NexAU/AHE / Agent2Skill | 3 | OUTPUT_LIMIT | 无候选 |
| NexAU/AHE / Direct | 3 | CANDIDATE_FROZEN | BEHAVIOR_CARD_REJECTED：目标映射不可激活 |
| Refact / Agent2Skill | 4 | ABSTAINED | 未取得完整源码后放弃 |
| Refact / Direct | 4 | INVALID_PROPOSAL | 提案仅implementation区域、缺入口/调用点标注 |

唯一候选是`tool_result_observation_compaction`。独立评价者执行原始AHE
`ToolResultCompaction.compact`：2次进程尝试、1次完整成功，含4次原入口调用/4个案例，
两项来源义务O1/O2均符合实际行为。第一次进程在Pydantic导入处失败，之后用既有项目
runtime闭合依赖；未改写donor语义。该失败不算donor行为失败。

候选的冻结映射却只处理“属于包自身”的观察，而唯一声明能力是`project_observations`。
实际入口初始没有自身观察；普通求解工具观察的owner为`host`；投影只能改已有观察，
不会创建属于包的新观察。使用真实宿主类的局部见证确认host观察可投影、投影后owner
仍为host，新增observation效果则因未声明被拒。故是**候选目标映射错误**，不是宿主
普遍不能支持上下文压缩。允许其处理host观察会改变已冻结候选，本轮没有这样做。

判定已有充分证据后停止：没有执行目标正确/错误控制、隐藏案例、代码生成或真实包入口。
不能将本轮写为代码迁移失败、自动包成功、Direct优于Agent2Skill或新增benchmark收益。
前置已有L3控制的隔离及入口PASS只属于基础设施校准，不加入本轮提取成果。

全部14请求COMMIT，无新增UNKNOWN。原响应报告input283413、output14746；
其中OUTPUT_LIMIT响应报告usage0/0，原值保留，不据此声称该请求没有实际消耗，费用TBD。
发现launcher2460284于19:05:03UTC完成原wait/exit0；后续零请求收尾launcher2668086
于19:20:28UTC完成原wait/exit0，两服务0重启，四个final均null。
未用14新槽退休：**563 used＋116 retired＝cap679关闭**；benchmark仍**914/1387**。
不复用退休额度，不重发捕获响应，不改旧候选或将本轮提升为L0。

本轮的研究信息是：模型选出的真实来源机制可以隔离执行，但这一固定发现预算下的
来源到宿主映射尚未得到合格产物。下一步决策应围绕必要的可达映射反馈与无效调用，
不能靠原样追加四格、扩大评分或修补当前候选回填成功。旧四题正结果仍为L2局部结果，
十二题持平、后继四题全0以及反馈八题持平分别保留，不合并分母。

证据：[发现汇总](discovery_summary.json)、[完成汇总](completion_summary.json)、
[四格校准](generation/calibration_seal.json)、
[公开donor/映射结论](generation/public_references/nexahe_direct/calibration_outcome.json)、
[独立校准说明](../../docs/reviews/discovery_source_set_v2_outcome_20260922.md)、
[固定设计](../../experiments/discovery_source_set_v2/PLAN.md)。
