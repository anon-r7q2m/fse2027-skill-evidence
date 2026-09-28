# SWE-agent Chooser：原包通过行为验收，暂无效果分数

2026-09-20。**新原包公开12/12通过；权限恢复后的重复独立回归20/20例、78/78步
通过。** 原始0/20记录为包导入前评价器权限错误、行为未测，原样保留。
本组件迁移阶段取得L2开发机制资格，模型请求以外没有benchmark／评分启动。
后继固定单题池现已完成，四候选官方均1、两选择策略分差0，仍无新增增益证据。
本轮唯一生成请求已关闭，不追加第三次模板修复，不修改原比较器或候选代码。

原包为
`0272999914d1f4203224ae94b1f6b263a387a3f82031d771203e6a10bec568e9`。
它由固定 donor 源码、原公开合同、原失败包与公开模板差异生成；没有使用独立
案例、隐藏答案或官方任务分数。人工候选代码修补为0。首次失败包及两请求的
原验收保留在 `results_cache/sweagent_chooser_transfer_v1/`，不重标、不重跑。

| 实际执行 | 结果 |
|---|---|
| 新生成请求 | 1次，completed／COMMIT，原包封存，原进程退出0 |
| 原公开套件 | 12/12通过，33workers全部清理 |
| 独立旧套件首次重复回归 | 原始FAIL、0/20例、0/78步；包导入前权限错误，20workers全部清理 |
| 权限恢复公开加载校准 | 人工EMPTY控制1/1通过，真实UID65534，1worker清理 |
| 权限恢复后同包重复回归 | 20/20例、78/78步通过，78workers全部清理 |
| 新隐藏案例 | 0；本轮不能算新的留出评价 |
| 同包真实入口 | scripted实际入口PASS，5scripted COMMIT、3环境／7workers清理 |
| 本组件分配benchmark／官方评分 | 均0；后继独立分配结果见下 |

评价维护者一次只读已有日志后定位：独立runner的`umask(0o077)`让通用stager
的`mkdir(mode=0o755)`实际成为0700，隔离UID65534无法读取`/package/package.json`。
20例都在导入候选模块之前发生同一PermissionError。因此这是评价基础设施错误，
原始FAIL保留，不能据此计为20次候选行为失败。未读取或回传隐藏输入／期望答案。
最小权限恢复另立runner和输出，仅显式将临时包目录设为0755；私有父目录／日志
保持0700／0600。公开加载校准1/1通过后，同一原包一次重复回归20/20通过。
原套件、比较器、worker和包均保持不变，未追加生成请求，fresh hidden仍0。

独立源码复核为`PASS_STATIC_SOURCE_REVIEW_ONLY`、无阻断项；其结论仅支持静态
来源对应。结合两项行为验收已生成资格记录。同包scripted实际入口一次PASS：
5个scripted COMMIT，投票选sample1、Chooser选sample4，两个原完整补丁发布，
3环境／7workers清理。模型与评分均0，这个控制不提供解题增益。

本轮实际用量：50,904 input、11,264 output tokens，费用TBD；未发生新UNKNOWN。
提取／诊断账本累计299 used＋71 retired＝cap370，0在途、0可用；
历史UNKNOWN保留。benchmark仍370/512，剩142。

预定单题 `django__django-14752` 的公开材料、两镜像与四个评分配置已准备；
后继live政策／authority和launch manifest另行固定，5新请求上限、cap375，
4份完整P2请求预检通过、1worker清理。后继实际5请求全部COMMIT，四原候选均完成
官方评分且reward均1；投票选1、Chooser选2，得分差0。两原父进程均退出0，
全部资源清理，后继已关闭不加K／换题。见[后继实测报告](../sweagent_chooser_pool_v1/REPORT.md)。
准备工作不构成效果证据，不因本次失败更换任务或追加采样。

证据：

- [原包与生成终态](generation/direct/final.json)
- [请求分配关闭](generation/allocation_close.json)
- [公开验收](public_summary.json)
- [独立重复回归](independent_summary.json)
- [回归范围声明](regression_attestation.json)
- [旧失败责任定位](evaluation_responsibility.json)
- [权限恢复后回归](permission_recovery/independent_summary.json)
- [原包资格](qualification.json)

行为合格机制增加为8类／5 donor，此Chooser同包实际入口已通过。
没有稳定收益、组合超过最佳单机制、naive或完整
harness优势的新证据；完整研究goal保持active、未完成。
