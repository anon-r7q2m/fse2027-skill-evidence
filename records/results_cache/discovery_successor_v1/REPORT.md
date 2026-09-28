# 新来源发现与迁移：实现和公开校准进度

更新：2026-09-11 04:02 UTC。状态：`CLOSED_NO_ELIGIBLE_MIGRATION_TARGET`。

**14次真实发现请求完成，3个候选、1格弃权；独立校准后0个合格迁移目标。**
具体启动审查PASS、原始账本恢复PASS。原migration正常执行一次，新增请求0，
四格终态及额度已结案。没有新代码包、隐藏验收、新包入口或benchmark成绩。

| 来源/方法 | 请求 | 最终状态 | 输入/输出tokens | 投递源码页/正文bytes |
| --- | ---: | --- | ---: | ---: |
| Moatless/A2S | 2 | NOT_ELIGIBLE_NO_CANDIDATE | 24271/1063 | 1/6253 |
| Moatless/Direct | 4 | REFERENCE_CALIBRATION_FAILED | 65534/3701 | 4/24481 |
| Trae/A2S | 4 | BEHAVIOR_CARD_REJECTED | 76197/3504 | 6/35379 |
| Trae/Direct | 4 | BEHAVIOR_CARD_REJECTED | 57749/4029 | 4/23068 |

Trae两候选均为LakeView摘要机制；固定donor在无有效tag时立即抛IndexError，
与原O3重试义务矛盾。Moatless实际三方法链已隔离执行，普通清理正常；重复请求
会覆盖首次成功记账，但此例不单独否定原卡。决定性问题是原卡允许状态内记账、
可选输出，effects-only验收无法区分正确与错误内部账目。没有偷偷强化原卡。
完整校准责任层分别见各public_references报告；这是model-mediated评价。

14/14均completed COMMIT，合计input223751/output12297；cache84352、reasoning5721
为各自子集，served model为gpt-5.4-2026-03-05/medium，费用TBD。页数不是机制数量。
Moatless/A2S第2次误以为已到只能提交阶段并提前弃权，仍按原始主动停止记录。

最终提取账**222 used +33 retired +1 unallocated =256**，0在途；14个本轮未用
额度已退休，不能挪作修复。历史1笔unknown usage保留。benchmark仍252/512，新增0。
[发现封存](generation/all_discovery_seal.json)、[发现时对账](generation/discovery_reconciliation.json)、
[校准封存](generation/calibration_seal.json)、[最终封存](generation/all_final_seal.json)、
[额度结案](generation/allocation_close.json)。发现时对账的PENDING为历史快照，不改写。

下一步是独立新epoch的[L2给定目标迁移](../../experiments/moatless_cleanup_transfer_v1/PLAN.md)，
先零生成校准，再各方法最多3请求；当前尚未新分配或调用。原自主发现结果不回写。

## 先前准备记录（下文状态均为历史）

03:28 UTC：用户回复“没写过，现在什么情况了”，明确两源没有专用规则、适配器
或模板开发历史；一般阅读保持UNKNOWN。两源资格、28请求配置及方法/元数据已
冻结，manifest `475af530f33c9c10f43e6536d8886eeb87e668f77de9dff3832f85d9d1ac00c5`。
实际账208已用、19退休、28新分配、1未分配，0在途；无调用runner预检通过。
具体启动审查进行中，尚未发送新请求；下方未获声明/未分配描述为9月10日历史。

具体审查发现首次freeze遗漏三项直接协议依赖，未发送请求即修正。原manifest及
原public_host保留在`experiments/discovery_successor_v1/prelaunch/attempt_01/`；
只补源码读取、schema与native-call三项绑定。create-only的public_host曾阻止首次
重建，归档原文件后同内容重建成功。当前manifest为
`8c8d4fe33073cf5a3ac0cac152215b07b2045866da41f1fd0d2397e5c306a72f`，
runner预检再次通过，额度、来源与方法条件不变，新增模型请求仍0。

**有界发现/迁移流程已实现并完成限定审查，真实新来源评价尚未启动。**
当前0个新来源候选、0个新来源生成包、0个新计分结果；没有新分配或消耗提取额度。
既有G/R八臂负结果保持独立，不因本轮基础设施通过而改变。

## 已完成

四格按固定顺序交错运行：Moatless/A2S、Moatless/Direct、Trae/A2S、Trae/Direct。
每格4次自主发现、至多3次迁移/公开修复；计划、工具请求和修复都计入该格。
目标由方法自己选择并在首次提交时封存。全部发现终结后才创建候选专属donor
参考件，全部最终包封存后才允许隐藏结果揭示。

新流程复用原始响应先落盘及实际账本封装，区分COMMIT、已知不完整与UNKNOWN。
源码引用须来自成功完成请求中实际携带的完整物理行；搜索片段只授导航。
每格累计正文返回上限64 KiB，跨发现/迁移并计重复读取。批量工具内的操作相互
独立，路径权限由当前请求已有目录证据决定。

恢复只在全部发现封存处进行。它核对实际BEGIN/REQUESTED/raw/VALIDATED/COMMIT
和账本，重建路径权限、源码交付及每轮会话。最终候选必须等于捕获的模型提交；
最后模型输出不能被改写，也不能在末尾追加未捕获内容。UNKNOWN与已有请求不重发。

公开验收使用真实隔离Program回放事件/effects，区别候选失败与评价故障。
参考接口追到固定donor的执行收据、观察值和每项义务，要求正确L3控制通过及至少
三种错误控制失败。接口检查本身不认证实际donor语义；候选专属执行记录尚未产生。
生成端只收到公开packet，不收到L3实现、隐藏期望或评价执行索引。

首次PUBLIC_PASS立即选定；否则保留普通停止前最后一个完整、语法和manifest有效
的包，并单列停止原因。无完整提交为NO_CANDIDATE。源码完整性和评价故障停止整组，
不能改成免费修复反馈或把故障当作候选语义失败。

## 校准和验证证据

| 证据 | 实际结果 | 可支持范围 |
| --- | --- | --- |
| 中性检查宿主真实入口 | L3包4个脚本请求、9事件、1次真实源码读取、2次隔离执行、2次实际反馈；N与共同上限路径另有终态；24worker/5自有project已清理 | 通用检查/反馈入口与回放可用 |
| 观察压缩宿主真实入口 | L3包4请求、9事件、1投影、1实际派生投递；10,524字符观察变为245字符；N3请求，cap路径2请求且投影未发送；30worker/3自有project已清理 | 包内策略能修改实际下一输入；不代表来源机制或真实成本节省 |
| 新流程最终本地检查 | **14 passed in 4.24s**；Ruff check与format均通过 | 合成源码/响应/收据下的实现检查；不估计发现成功率 |
| 独立实现审查 | **GO，限实现和冻结准备**；末尾会话恢复缺口已修复并复核 | 源码投递、账本、恢复与runner准入；不代替具体启动审查 |
| 独立参考接口审查 | **PASS，限接口和链接** | 候选/评价身份、失效分类和执行证据链接；不等于donor语义验收 |

上述真实入口均使用脚本化模型响应和公开L3控制，live模型与benchmark启动为0。
观察宿主的后续三项异常路径修复另通过16项本地检查，原入口证据未重写。
新流程各次9/12/14项检查逐步重叠，不能累加为独立试验。
四格合成端到端案例共20个脚本请求；实际native客户端/继承账本恢复测试与其
分别记录。它们均没有调用真实provider或实际提取账本的写入方法。

## 当前唯一外部事实缺口

`sources.json`已固定两个repository、commit和tree，但以下团队历史未获声明：
`prior_author_read`、`source_specific_method_development`、`dedicated_binding_or_template`。
当前两源均`PENDING`，后两项均`UNKNOWN`。既往一般阅读可以单列；只有专用开发
与模板历史满足本轮资格，才能进入“未作来源专用开发”的发现评价。

该问题已向用户提出，尚未收到事实答复。不存在本地搜索命中不足就自动改NO的规则。
资格处理依据[设计第1节](../../docs/reviews/discovery_successor_design_2026-09-10.md)：
固定两源，不按结果换第三源；一源合格只跑其两格，零源合格零请求结束。

资格到达后，在既有连续执行授权内准备实际账本配置、冻结方法与元数据、完成
具体启动检查和审查，然后执行发现。候选专属donor执行/参考封存、迁移、隐藏
验收、同原包真实入口和新的效果实验仍是后续实际工作，不能提前写成完成。
当前没有正式`generation`、`policy.json`、`authority.json`或`launch_manifest.json`。

## 额度与现有研究结论

本次只读实际提取账确认：**208 used + 19 retired + 29 unallocated = 256**，
0在途。计划28请求尚未分配，第29次继续未分配。benchmark仍为252/512、余260。
本轮实现与最终检查新增live模型、benchmark、Docker启动均0；上表真实宿主校准
是此前已有的公开执行记录。

八臂`gr_strategy_effect_v2`已经结案：F/F_naive各0/2，其余六臂各1/2。正组合
收益、来源价值、完整harness优势、新来源自主发现及跨模型/profile仍待实测。
论文已纳入该负结果和旧v1中断前缀，限定事实对齐审查PASS。17:22 UTC方法补全：
RQ2恢复自主发现问题，提取小节写明当前实现的等预算发现/迁移、donor执行校准、
参考件和最终包封存及原包真实入口；两源仍PENDING，真实发现仍未执行。
G/R来源目标与人工公共义务已分开，方法限定审查PASS。最新版latexmk退出0，
19总页，Conclusion/Data Availability在第18页，最终log无overfull或undefined。
本次论文修改没有新增live请求、额度分配或benchmark。完整研究目标保持进行中。

## 入口

- [计划](../../experiments/discovery_successor_v1/PLAN.md)、[来源元数据与资格](../../experiments/discovery_successor_v1/sources.json)、[参考与执行协议](../../experiments/discovery_successor_v1/REFERENCE_PROTOCOL.md)。
- [流程实现](../../analysis/discovery_successor_v1/workflow.py)、[恢复](../../analysis/discovery_successor_v1/recovery.py)、[runner](../../analysis/discovery_successor_v1/runner.py)。
- [最终14项检查](local_validation/workflow_final.xml)、[中性真实入口终态](public_entry/attempt_01/terminal.json)、[资源清理](public_entry/attempt_01/resource_absence.json)。
- [观察压缩校准](../observation_context_v1/REPORT.md)、[实现审查](../../docs/reviews/discovery_successor_v1_implementation_review.md)、[参考接口审查](../../docs/reviews/discovery_successor_v1_reference_interface_review.md)。
- [八臂实际结果](../gr_strategy_effect_v2/REPORT.md)、[论文事实对齐审查](../../docs/reviews/gr_strategy_v2_manuscript_alignment_review.md)。
- [论文发现方法限定审查](../../docs/reviews/discovery_successor_manuscript_method_review.md)。
