# OpenHands S：一个生成包通过独立验收，尚无计分增益

2026-09-11。五次真实生成请求全部 completed/COMMIT，双方最终包已先于隐藏
结果封存，无人工候选代码修补。A2S 原包已通过独立隐藏、来源/适配及同包实际入口，
按预声明优先规则选为 S；标签仍是 L2 给定目标同源开发。尚无 S 或 GS 计分结果。

| 方法 | 实际生成请求 | 公开测试轨迹 | 最终选择 | 独立隐藏/来源/真实入口 |
| --- | ---: | --- | --- | --- |
| A2S | 2 | 3/5 → 5/5 | 第2次，首次公开通过 | 隐藏5/5；来源/适配PASS；实际入口22/22＋9/9 |
| Direct | 3 | 3/5 → 3/5 → 3/5 | 第3次，额度内最后完整包 | 隐藏3/5，接口失败；未进入实际入口 |

公开失败均集中于首次摘要与旧摘要/长文本两个案例的第1步 `INVALID_EFFECT`。
阈值、受保护选择和剩余一次调用案例均通过。失败没有被改标为评价器无效，也
未追加相同版本请求。A2S最终包为 `710899ac…a9955`，Direct为
`1d6f57f0…71d21`；完整身份在双方封存记录中。

Direct 将 `model_request.instructions` 设为 `None`，运行器要求字符串。
冻结 `HOST_PROFILE` 只列字段而未显式写出该类型，公开反馈也仅给 `INVALID_EFFECT`。
这是必须披露的接口说明缺口；此轮不能证明 A2S 的摘要语义或方法一般性优于 Direct。
冻结说明、失败包和次数保持原样，没有用隐藏结果追加修复。

两方法输入相同的固定OpenHands源码、接口和公开案例，使用 gpt-5.4、medium，
各最多三次请求，只有方法说明不同。所有分析、生成和公开修复均计费。
机制目标、16/1/10000配置、原始summary prompt及complete-group映射在请求前
固定，仍是 **L2给定目标同源开发迁移**，不是自主发现或未见来源评价。

新增input **161,390**、output **31,275** tokens；cached input **88,320**和
reasoning **13,894**分别是上述总量子集，费用 **TBD**。56个公开评价worker
全部清理。六槽分配用了五槽，余一槽退休；提取累计 **229 used＋38 retired＝267**，
零在途、零未分配。更早的一笔未知用量继续保留。

本epoch新增benchmark启动 **0**；累计仍 **261/512**、余 **251**。
生成前独立L3控制校准另有公开5/5、隐藏5/5、4种错误实现检出、真实入口22/22＋9/9，
136个worker与45次脚本native请求；这些数量与本次真实生成分开记录。

独立验收另有118个worker（隐藏26、实际入口92），全部清理；45次脚本native请求
中2次为摘要，真实provider和benchmark均0。合并本次生成公开评价共174个worker；
前置L3控制的136个worker单列。实际入口证明同包摘要能按原文进入下一次solver请求，
没有证明真实摘要质量、token节省或解题收益。

下一步按已审查的 [N/G/S/GS计划](../../experiments/gs_generated_effect_v1/PLAN.md)
准备四题、最多16个新计分启动。公共任务域、实际adapter与历史资格检查仍需闭合，
本报告不表示已启动。正组合收益、source-blind优势、完整harness优势与跨条件
profile仍为 **TBD**。

证据：[最终对账](reconciliation.json)、[独立验收](generated_evaluation/REPORT.md)、
[生成阶段原始对账](generation_reconciliation.json)、
[双方最终封存](generation/all_final_seal.json)、
[额度结案](generation/allocation_close.json)、
[独立控制校准](host_calibration/REPORT.md)、
[冻结计划](../../experiments/openhands_summary_transfer_v1/PLAN.md)。
