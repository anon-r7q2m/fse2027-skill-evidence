# 六 Benchmark 结果导向审计交付

状态：`WORKING_TRIAGE_COMPLETE_SIX_ATTENTION_QUEUES_DISPOSITION_COMPLETE_FINAL_DISPOSITION_PENDING`

这份主表回答“有多少题暂未发现实质问题、有多少题需要重点改进，以及正式有效/可修/排除结论还缺什么”。协议、哈希和执行过程仅作为附件。

## 当前结果

| Benchmark | 审计单元 | 已审证据中存在实质疑点 | 已审证据中暂未发现实质疑点 | 第三阶段复核 | 正式有效 / 可修 / 排除 | 最终未决 |
|---|---:|---:|---:|---:|---|---:|
| Terminal-Bench 2.0 | 89 | 85–89 | 0–4 | 69 | TBD / TBD / TBD | 89 |
| SWE-bench Pro | 731 | 59 | 672 | 65 | TBD / TBD / TBD | 731 |
| SWE-bench Multimodal | 517 | 257 | 260 | 517 | TBD / TBD / TBD | 517 |
| FeatureBench | 252 | 192 | 60 | 216 | TBD / TBD / TBD | 252 |
| Multi-SWE-bench | 2,937 | 124 | 2,813 | 137 | TBD / TBD / TBD | 2,937 |
| SWE-Lancer | 463 | 363 | 100 | 445 | TBD / TBD / TBD | 463 |
| 合计 | 4,989 | 1,080–1,084 | 3,905–3,909 | 1,449 | TBD / TBD / TBD | 4,989 |

注意：前两列是工作队列，不是有效性结论。‘暂未发现实质疑点’不能直接写成有效，‘存在实质疑点’也不能直接写成可修复或无效。

## 已完成的逐题处置：关注队列静态证据层

下表汇总的是关注候选在限定静态证据范围内的处置，不是整个 benchmark 的最终有效性统计。

| Benchmark | 关注候选 | 原样保留 | 保留但注明限制 | 同构念可修复 | 应排除 | 继续未解决 |
|---|---:|---:|---:|---:|---:|---:|
| Terminal-Bench 2.0 | 85–89 | 0–89 | 0–89 | 0–89 | 0–89 | 0–89 |
| SWE-bench Pro | 59 | 0–10 | 9 | 40 | 0–10 | 0–10 |
| SWE-bench Multimodal | 257 | 0–257 | 0–257 | 0–257 | 0–257 | 0–257 |
| FeatureBench | 192 | 0–15 | 0–15 | 177 | 0–15 | 0–15 |
| Multi-SWE-bench | 124 | 0–21 | 0–21 | 103 | 0–21 | 0–21 |
| SWE-Lancer | 363 | 0–129 | 42 | 192 | 0–129 | 0–129 |

### 分榜证据边界

### Terminal-Bench 2.0

已完成 85–89 条关注候选的 `STATIC_INSTRUCTION_ORACLE_VERIFIER_AND_RUNTIME_ONLY` 处置；这只是该证据范围内的局部结论，未覆盖相应运行时与评分证据，因此整体最终有效性仍全部为 `UNRESOLVED_TBD`。

| 处置 | 数量 |
|---|---:|
| 原样保留 | 0–89 |
| 保留但注明限制 | 0–89 |
| 同构念可修复 | 0–89 |
| 应排除 | 0–89 |
| 继续未解决 | 0–89 |
| 合计 | 85–89 |

### SWE-bench Pro

已完成 59 条关注候选的 `STATIC_CONTENT_ALIGNMENT_ONLY` 处置；这只是该证据范围内的局部结论，未覆盖相应运行时与评分证据，因此整体最终有效性仍全部为 `UNRESOLVED_TBD`。

| 处置 | 数量 |
|---|---:|
| 原样保留 | 0–10 |
| 保留但注明限制 | 9 |
| 同构念可修复 | 40 |
| 应排除 | 0–10 |
| 继续未解决 | 0–10 |
| 合计 | 59 |

### SWE-bench Multimodal

已完成 257 条关注候选的 `STATIC_TEXT_VISUAL_ASSET_AND_RELEASE_ONLY` 处置；这只是该证据范围内的局部结论，未覆盖相应运行时与评分证据，因此整体最终有效性仍全部为 `UNRESOLVED_TBD`。

| 处置 | 数量 |
|---|---:|
| 原样保留 | 0–257 |
| 保留但注明限制 | 0–257 |
| 同构念可修复 | 0–257 |
| 应排除 | 0–257 |
| 继续未解决 | 0–257 |
| 合计 | 257 |

### FeatureBench

已完成 192 条关注候选的 `STATIC_FEATURE_GOLD_TEST_AND_METRIC_ONLY` 处置；这只是该证据范围内的局部结论，未覆盖相应运行时与评分证据，因此整体最终有效性仍全部为 `UNRESOLVED_TBD`。

| 处置 | 数量 |
|---|---:|
| 原样保留 | 0–15 |
| 保留但注明限制 | 0–15 |
| 同构念可修复 | 177 |
| 应排除 | 0–15 |
| 继续未解决 | 0–15 |
| 合计 | 192 |

### Multi-SWE-bench

已完成 124 条关注候选的 `STATIC_CONTENT_AND_VARIANT_IDENTITY_ONLY` 处置；这只是该证据范围内的局部结论，未覆盖相应运行时与评分证据，因此整体最终有效性仍全部为 `UNRESOLVED_TBD`。

| 处置 | 数量 |
|---|---:|
| 原样保留 | 0–21 |
| 保留但注明限制 | 0–21 |
| 同构念可修复 | 103 |
| 应排除 | 0–21 |
| 继续未解决 | 0–21 |
| 合计 | 124 |

### SWE-Lancer

已完成 363 条关注候选的 `STATIC_PROPOSAL_ORACLE_TEST_AND_AGREEMENT_ONLY` 处置；这只是该证据范围内的局部结论，未覆盖相应运行时与评分证据，因此整体最终有效性仍全部为 `UNRESOLVED_TBD`。

| 处置 | 数量 |
|---|---:|
| 原样保留 | 0–129 |
| 保留但注明限制 | 42 |
| 同构念可修复 | 192 |
| 应排除 | 0–129 |
| 继续未解决 | 0–129 |
| 合计 | 363 |

固定保护类别与全部小于 5 的单元采用联合隐藏；逐题 ID、理由和动作仅保存在私有台账。

## 每个 Benchmark 目前发现了什么

### Terminal-Bench 2.0

- 口径：89 frozen public tasks。
- 关注信号：`exposure_and_contamination` 49；`interactivity_and_randomness` 24；`release_supersession` 17；`resource_budget` 11；`runtime_fetch_and_network` 80。
- 下一步：关注队列静态内容处置已完成；补齐共享运行时与评分证据后，才可形成整体最终有效性。

### SWE-bench Pro

- 口径：731 frozen public tasks。
- 关注信号：`issue_pr_alignment` 59。
- 下一步：关注队列静态内容处置已完成；补齐共享运行时与评分证据后，才可形成整体最终有效性。

### SWE-bench Multimodal

- 口径：517 audited atoms; current public test snapshot has 510 rows。
- 关注信号：`issue_asset_alignment` <5（已隐藏）；`release_supersession` 6；`visual_necessity` 254。
- 下一步：关注队列静态内容处置已完成；补齐共享运行时与评分证据后，才可形成整体最终有效性。

### FeatureBench

- 口径：252 audit atoms over a 200-task source with variant/level projections。
- 关注信号：`feature_request_gold_alignment` 169；`level_and_metric_alignment` 29；`test_adequacy` 181。
- 下一步：关注队列静态内容处置已完成；补齐共享运行时与评分证据后，才可形成整体最终有效性。

### Multi-SWE-bench

- 口径：2,937 audit atoms across named variants; no single combined score denominator。
- 关注信号：`issue_patch_alignment` 113；`variant_and_revision_identity` 12。
- 下一步：关注队列静态内容处置已完成；补齐共享运行时与评分证据后，才可形成整体最终有效性。

### SWE-Lancer

- 口径：463 audit atoms: 198 IC and 265 manager; no combined score denominator。
- 关注信号：`ambiguity_and_agreement` 196；`candidate_set_completeness` 69；`first_decision_oracle` 50；`issue_test_gold_alignment` 88；`proposal_exposure` 189；`pytest_any_success_semantics` 83。
- 下一步：关注队列静态内容处置已完成；补齐共享运行时与评分证据后，才可形成整体最终有效性。

## 完成标准

最终交付必须对每个 benchmark 给出五档互斥统计：有效原样保留、有效但有限制、同构念可修复、应排除、未解决。当前六个 benchmark 的关注候选均已完成静态证据处置；所有 benchmark 的整体最终有效性仍未闭合，不能把局部处置数直接写进正式有效/排除总数。

## 下一步最短路径

1. 不重复审阅未变化的题目证据，只处理实质疑点关注队列。
2. 按 benchmark 一次性补共享缺失证据；只重开受新证据影响的维度。
3. 生成最终五档数量、修复类型汇总，以及修复或排除后的评分敏感性。

## 权威边界

`formal_authority=false`，`BVC=TBD`，`strict_blacklist_rate=null`，`blacklist_published=false`。未发布题目 ID、题目原文、逐题理由、reviewer 信息或小于 5 的可反推单元格。
