# GP v1：一次有界的候选选择诊断

日期：2026-09-12。独立诊断：`/root/gp_public_domain_review`。

**本版本结案，未达到组合开发信号。主要可行动限制是：单轨迹候选池太小，且现有 G 回执只能区分声明的既有行为是否保持，不能保证候选包含修复，也可能看不到被投影掉的候选差异。** 本轮唯一的 GP 多候选选择，实际在两个仅修改测试文件的候选间平票，回选了带语法错误的较早版本。

这说明一种真实的候选准入与排名局限；不证明该回选导致了整个 GP 臂的分数下降，也不证明改选 final current 就会成功。

## 范围与已发布结果

读取范围为已揭分的 [reconciliation.json](reconciliation.json)、冻结 [protocol.json](../../../experiments/gp_generated_effect_v1/protocol.json)、该文件列出的 `trial_path/agent/trajectory.json` 中公开生成代码、动作和机制事件，以及 `analysis/candidate_selection_v1/{host,broker,session}.py` 与冻结 P 原包的 `mechanism.py`。没有读取 verifier/grader/hidden/evaluator_only 正文、旧 P 独立隐藏案例或凭据；没有调用模型、启动 benchmark/Docker、重测候选、修改 frozen 代码或旧产物。

计分和资源闭合采用已审查的 reconciliation，未另行运行评分器或 Docker 检查：16/16 格有效，0 个无效，`EXACT_OWN_RESOURCES_ABSENT`，共 277 次模型请求；`development_signal=false`。四题均为已暴露开发任务，`R=1`，不构成确认或因果效应估计。

| 任务 | N | G | P | GP |
|---|---:|---:|---:|---:|
| `matplotlib__matplotlib-14623` | 1 | 1 | 1 | 0 |
| `django__django-13925` | 0 | 1 | 1 | 0 |
| `matplotlib__matplotlib-24177` | 0 | 0 | 0 | 0 |
| `django__django-11292` | 1 | 1 | 1 | 1 |
| 总计 | 2/4 | 3/4 | 3/4 | 1/4 |
| 模型请求 | 58 | 66 | 66 | 87 |

冻结要求是 GP 在完整 roster 上严格超过 N、G 和 P，本轮不满足。不能将三组独立轨迹的总分差直接解释为 P 或 G 的因果损害；不追加同题样本、换题补格或复用有利臂。

## P 实际拿到了什么

下表的“非空”是当前契约中的非空 patch/key，不等于有效修复。`comparable` 指 G 回归证据符合冻结比较条件；P-only 关闭回归，因此其 comparable 为 0 是设计结果，不是未知回执或执行故障。

| 任务/臂 | 入池非空候选 | G 可比候选 | key 与排名信息 | 所选与 final current |
|---|---:|---:|---|---|
| 14623/P | 2 | 0，回归关闭 | 两个不同 PY key，各 1 票；按首出现次序破平 | 不同，选第 1 个 |
| 14623/GP | 1 | 1 | PY；0 个 preservation failures；1 票 | 相同 |
| 13925/P | 1 | 0，回归关闭 | PY；1 票 | 相同 |
| 13925/GP | 2 | 2 | 第 1 个 RAW（`NORMALIZATION_EXCEPTION`），第 2 个 PY；两者 0 failures，各 1 票 | 不同，选第 1 个 |
| 24177/P | 1 | 0，回归关闭 | RAW（`TEXT_SIZE_LIMIT`）；1 票 | 相同 |
| 24177/GP | 1 | 1 | RAW（`TEXT_SIZE_LIMIT`）；0 failures；1 票 | 相同 |
| 11292/P | 1 | 0，回归关闭 | PY；1 票 | 相同 |
| 11292/GP | 1 | 1 | PY；0 failures；1 票 | 相同 |

八个 P-bearing 单元均完成真实包调用，总计 38 次隔离回调；没有 P package failure 或 P deadline interruption。所有最终选择理由都为 `MAJORITY_VOTE`，但该名字不能被解释成多候选形成了多数共识：六格只有一个候选，另两格是不同 key 各一票后按首出现次序破平。没有超过一票的胜者，没有复现信号（本协议关闭 reproduction）。所有 pool 都远低于 32 上限，无 overflow；增加候选槽上限不能解释或解决本轮稀疏性。

候选来自同一次 solver 运行的不同完整树，重复树不重复计票。这样的 checkpoint 不是独立生成样本，不能直接赋予独立投票的统计解释。

## G 回执完整，但没有形成排序差异

G/GP 共执行 18 次 G 检查：8 次 base、10 次 post-change，10 条反馈已记录送达。检查均 completed、return code 0，无 timeout、cancelled 或截断。五个 GP 候选均有本次运行中匹配其 snapshot 的 G 回执及 P bridge：共 5 条，全部 available/comparable、failure count 0。

这五次 post-change 决策的 `native_complete` 与 `execution_complete` 均为 true，`unresolved=[]`、`execution_issues=[]`，状态 `BASE_PASSES_PRESERVED`；观察分别是 14623 的 4 个 PASSED、13925 两次各 4 个、24177 的 5 个和 11292 的 6 个。没有混合 unknown 导致剔除或把 unknown 算成 zero failures 的现象。

与此同时，五个决策的 `issue_fixed` 全为 null。四个冻结 G domain 都只有 `PRESERVE` 义务，并事前明确现有 guard 不直接断言对应 issue 已修复。因此“G 检查完整”和“G 能在候选中识别正确修复”是两件事；本轮只有前者成立。

## 唯一 GP 多候选路径：13925

公开轨迹入口：

`live/02_GP/jobs/a2s-gp-effect-v1-2-gp/django__django-13925__hry4f6f/agent/trajectory.json`

1. query 13 首次修改 `tests/check_framework/test_model_checks.py`，增加一个 abstract-base 显式主键继承测试，但 replacement 中保留了字面量行首 `+`。形成候选 `508c251e5b694a2d7328145f19dd44f31ab16857`，patch 1,074 bytes；没有生产文件修改。
2. P 记录 `NORMALIZATION_EXCEPTION`，按已声明适配保留 RAW key。query 14 的实际公开测试执行报告该文件第 418 行 `SyntaxError: invalid syntax`。该错误不是本诊断新运行的结果。
3. query 16 删除这些字面量 `+`，得到候选/current `befc36e3265f789e28c1168e8ee6468c42631bb2`，patch 1,057 bytes，PY key。query 17 的新测试和 query 18 的五个公开测试均通过。该版本仍只增加测试，没有修改生产代码。
4. 两个 G 执行的冻结投影都把 `tests/check_framework/test_model_checks.py` 等四个测试文件恢复为 base。两次 `preserved_candidate_entries={}`，`projected_tree` 均等于 base `6403efc1a2b35c548b174165fd14e16c9d99396c`。因此语法错误版与修正版对这个 G domain 没有可观察差异，都获得完整 4/4 PASS。
5. P 收到两个 comparable、zero-failure、nonempty key 候选；RAW 与 PY 各一票，原包 `_majority_vote` 以首次出现次序破平，回选第一个。最终发布的是该候选的原始完整补丁，未被 host 重写；它与 final current 不同，公开已发布 reward 为 0。

这里的直接结论是：恢复测试的 G 投影让两个候选无法被这个回归域区分；RAW fallback 让一个已出现 normalization error 的 Python 候选仍进入一般排名；first-index tie-break 确实回选了较早语法错误版。该路径符合冻结版本的实现，不是事后宣布这次运行 invalid 的依据。

不能声称“正确 current 被 P 换成错误 patch”。current 没有独立评分，且它也只有测试变更。新测试在生产代码未变时就通过，说明该具体自写案例没有展示 bug 的 fail-to-pass 修复；这不是 donor 或完整 issue 已验证的证明。最终 reward 0 不能归因于语法错误，因为底层评分执行细节不在此次诊断读取范围内，且缺乏同轨迹 current 的测量。

## 另外三个 GP 单元的责任边界

- **14623：** 只有一个候选，query 21 修改 `lib/matplotlib/scale.py` 的 `limit_range_for_scale`；G 4/4 保持，P 选=current，reward 0。本轨迹没有 P 回退的机会。不能把独立 N/G/P 的成功当成这个 current 本来能成功的证据，也不能把“有 G PASS”当作倒置 log limit 已修复。
- **24177：** query 29 才形成唯一候选，在 `hist` 末尾加 `relim()` 与 `_request_autoscale_view()`；G 的五个 guards 全部通过。query 32 的公开检查仍打印 `scale 1.2: tops.max≈0.33476, ylim upper≈0.27918` 和 `scale 2.0: tops.max≈0.20320, ylim upper≈0.12808`，即公开目标症状仍有可见证据。随后达到 32 次调用上限，P 只能选择同一个 current。该失败是已计分的请求耗尽，不是 G timeout；无第二候选可以回退。有限预算何时应转向修复是后续设计问题，不能据此推断更多调用必然解题。
- **11292：** 唯一候选，G 6/6 保持，P 选=current，reward 1。证明这条组合路径能完成正确提交，不证明 P 选择带来增益，因为没有另一可选候选且四个臂都成功。

P-only 的 14623 提供另一个有实际回选的例子：第一个候选只改 `LogLocator.nonsingular`，final current 又扩大到 `LogitLocator.nonsingular`。两者 PY key 不同，各一票，P 回选第一版并得分 1。这只证明所选版本成功；current 未独立评分，因此不能说 P 避免了退化或新增了成功。

24177 的 P 和 GP 都因完整 Python 文件超过 262,144-byte 文本上限而用 RAW key，虽然实际 patch 分别仅 2,017 和 1,048 bytes。这是归一化覆盖的真实限制，不是本轮 ranking loss 的证据：两格都只有一个候选，没有归一化投票可比较。

## 下一方向：补候选可用性与区分信息，保留本轮结案

**建议优先修订下一版本的候选准入与证据范围表达，然后再决定是否投入下一轮选择效果实验。** 这是针对上述单个失败模式的最小动作，不是给当前四题补样或追正。

1. 区分“完整 patch 非空”“投影后保留了生产变化”“未投影候选可解析/可执行”“目标症状获得 fail-to-pass 证据”。G 的 preservation PASS 只承担第一类既有行为义务，不能隐含后三项。不要取消 G 恢复测试的保护来让这两个候选变得不同；应单独表达候选在该 domain 中是否有保留变化，以及实际未投影语法证据。
2. `NORMALIZATION_EXCEPTION` 与 `TEXT_SIZE_LIMIT` 不应被当成相同的正确性信息。原包的 RAW fallback 仍可保留为当前来源忠实行为；若后续改为排除已确定语法错误或测试-only 候选，须作为新的显式适配/策略版本，不能手改原包或回写旧验收。先用公开合成的“语法错误测试-only / 修正测试-only / 真实生产变更”控制件验证可观察区分，不使用本轮分数选择规则。
3. 若继续研究选择收益，应先确认来源机制能提供真正的候选差异或目标相关的可执行修复判据，再在新的预声明任务块评测。当前只收集单轨迹 checkpoints，在六个 P-bearing 单元中没有两个候选；全部 GP preservation failure count 为零。未测 issue-correctness 下，增加同类回归次数或 candidate cap 不会自动产生选择依据。复现类信号或明确的候选生成机制可以作为后续来源方向，但它们的收益仍待测，不能把模型自写且 base 已通过的案例当作有效复现。

本轮足以关闭“原样 G+P 选择能带来真实增益”的该版本开发尝试；无需继续读取隐藏评分细节或反复审计同一轨迹。自主发现 epoch 是独立证据链，可按其已冻结协议继续；本诊断不修改它的材料或规则。完整聚合、跨模型、完整 harness 优势与来源价值仍未确认。
