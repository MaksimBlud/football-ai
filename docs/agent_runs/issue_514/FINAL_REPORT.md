# Research V5 final report — Issue #514

## Вывод простым языком

Детерминированное исследование **kickoff/calendar preregistered league heterogeneity** завершено без внешней LLM/API-квоты.

Финальное решение: **NO_STABLE_KICKOFF_CALENDAR_LEAGUE_HETEROGENEITY**.

League heterogeneity is diagnostic only and cannot rescue the already rejected pooled kickoff/calendar OOS hypothesis.

## Technical appendix

Full reproducible result:
`research/agent_runs/issue_514/RESULT.json`.

Key registered result fields:
- `validation.pooled_calendar_minus_baseline_log_loss`: 0.000688026669152182
- `test.pooled_calendar_minus_baseline_log_loss`: 0.0014918100710607984
- `stable_heterogeneity_pairs`: []
- `pairwise_bonferroni_ci_level`: 0.9833333333333333
- `pooled_null_rescued`: False

Safety contract: model API = false; paid Odds API = false; Supabase writes = false;
production operations = false; automatic promotion = false.
