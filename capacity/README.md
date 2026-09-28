# Released sixteen-task capacity comparison

This directory contains the complete released outcome matrix for
`raw_repo_capacity_comparison_v1`, not a new run. All original solver and
scorer dispositions closed and both original parents exited normally before
uniform release on 2026-09-28. The version is closed.

- `DESIGN.md`: unchanged frozen design from before issue access. Its final
  statement that results are TBD is historical; released outcomes are below.
- `outcomes.csv`: all 192 logical outcomes, projected from the original
  reconciliation. Task ID, policy, repeat, reward and exact-identity sharing
  are retained. No task annotations, model trajectories or grader logs are
  included. Reward 1 means solved and 0 means not solved; there are no missing
  outcomes in this version.
- `analysis.json`: original released analysis, including primary counts,
  paired contrasts, exact tests, Holm correction, task bootstrap and repeats.
- `execution_by_policy.json`: original aggregate execution counts, usage and
  route choices across all 24 task-repeat paths per policy.
- `primary_participation_cost.json`: descriptive aggregation restricted to the
  sixteen repeat-1 paths per policy, as reported in the manuscript's usage
  table. It retains all stopped paths and reports native pool entry as N/A.
  Input includes cached tokens; reported output and reasoning fields are not
  added. The aggregate is an export from the released execution records,
  not a new run, a monetary-cost estimate, or a full execution-record bundle.
- `REPORT.md`: original report with only local links adapted to this bundle.

N is the ordinary host; L/P are the source-based localization/editor
installations; LP is their composition; Ln/Pn/LnPn are the corresponding
source-blind controls; Hmini is complete mini-SWE-agent 2.4.6 under the common
nine-request ceiling. Common ceilings do not imply equal actual costs.

Repeat 1 contains the primary 16 tasks, with all eight arms. Four tasks fixed
by the design also receive repeats 2 and 3. Their R1 values are already in the
primary matrix. The 24 task-repeat blocks are not 24 independent tasks.
The 192 logical rows use 108 distinct score cells under the frozen identity
sharing rule; repeated score-cell IDs do not mean additional grading runs.

LP solves 13/16 versus 4--10/16 for the seven controls. Prespecified one-sided
exact McNemar tests with Holm correction pass .05 against N, L, LnPn and
Hmini, but not P, Ln or Pn. The paired bootstrap intervals are not simultaneous.
`fixed_panel_net_bounds` describe observed fixed-panel net differences with
missingness accounted for; with no missingness they collapse to the exact
observed difference and are not confidence intervals.

LP's same-four-task repeat totals are 3/4, 3/4 and 1/4. All 24 LP paths use
the original pool route. Nine primary tasks are from Django. The result
supports a local whole-policy benefit without establishing stable superiority,
source necessity, pure mechanism synergy, a fallback benefit or general
benchmark performance. It does not authorize sample expansion.

The matrix supports inspection and arithmetic recomputation. This bundle does
not execute the original agents or reproduce official grading. The separate
20-condition principles replays did not generate these benchmark results.
