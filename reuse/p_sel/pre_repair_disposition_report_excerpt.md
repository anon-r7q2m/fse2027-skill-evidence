日期：2026-09-11。结案状态：`CLOSED_NO_QUALIFIED_P_SOURCE_REVIEW_FAILED`。

| Direct | 2 | 6/10 → 10/10 | 13/13 | FAIL | 未运行 | 否 |

Direct 在同时开启 regression/reproduction 时，如果最低失败数组的 reproduced
候选只有空归一化 key，会直接回退全池，跳过最低失败数的非空候选；较高失败数组
可能因此胜出。真实 GP 的 reproduction=false 不触发这个已确认反例，但原冻结
契约包括该预备分支，不能事后豁免。13/13 保持为有限案例通过，不改写为完整保真。
