# Capacity-aware harness comparison: sixteen fixed tasks

The primary panel is repeat1 on sixteen tasks. All remaining runs are a separately fixed four-task variability panel.

| Arm | Solved / observed | Missing | Fixed primary tasks |
| --- | ---: | ---: | ---: |
| N | 5/16 | 0 | 16 |
| L | 5/16 | 0 | 16 |
| P | 8/16 | 0 | 16 |
| LP | 13/16 | 0 | 16 |
| Ln | 7/16 | 0 | 16 |
| Pn | 10/16 | 0 | 16 |
| LnPn | 4/16 | 0 | 16 |
| Hmini | 5/16 | 0 | 16 |

| LP versus | Complete pairs | Added | Lost | Observed net | Fixed-panel net bounds |
| --- | ---: | ---: | ---: | ---: | --- |
| Hmini | 16 | 8 | 0 | 8 | [8, 8] |
| L | 16 | 8 | 0 | 8 | [8, 8] |
| Ln | 16 | 7 | 1 | 6 | [6, 6] |
| LnPn | 16 | 10 | 1 | 9 | [9, 9] |
| N | 16 | 9 | 1 | 8 | [8, 8] |
| P | 16 | 5 | 0 | 5 | [5, 5] |
| Pn | 16 | 5 | 2 | 3 | [3, 3] |

Prespecified resource decision: **PASS_DESCRIPTIVE**. This descriptive decision does not by itself establish stable or statistically confirmed gains.

Full row matrix, exact tests where eligible, task bootstrap and separate repeat diagnostics: [analysis](analysis.json) and [complete outcome matrix](outcomes.csv). Missing values remain missing, no old arm or score is reused, and this version closes without result-directed extension.

Original L/P are L2 given-target migrations. This compares whole installed policies; it does not isolate source necessity, capacity-gate causality or pure synergy. Equal ceilings do not imply equal actual costs.

Actual requests: 1449; newly unknown usage requests: 0. Benchmark starts: **1214/1387**. All original dispositions and parents have closed. Usage and activation: [execution aggregates](execution_by_policy.json).

The full automatic-discovery-to-stable-composition research goal remains incomplete.
