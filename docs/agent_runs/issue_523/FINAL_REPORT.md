# Research V5 final report — Issue #523

## Вывод простым языком

Детерминированное исследование **kickoff/calendar opening-to-closing O/U 2.5 movement** завершено без внешней LLM/API-квоты.

Финальное решение: **NO_STABLE_KICKOFF_CALENDAR_OU25_REPRICING**.

This outcome-free test concerns opening-to-closing market repricing only; it cannot rescue the rejected goal-outcome hypothesis or authorize betting.

## Technical appendix

Full reproducible result:
`research/agent_runs/issue_523/RESULT.json`.

Key registered result fields:
- `reference_rows`: 5695
- `validation.calendar_minus_baseline_mse`: -6.856730675336157e-07
- `test.calendar_minus_baseline_mse`: -2.117198799672056e-06
- `test.bootstrap.ci95_low`: -8.102040370619977e-06
- `test.bootstrap.ci95_high`: 3.6296139408614745e-06
- `source_gaps`: []
- `match_outcomes_used`: False

Safety contract: model API = false; paid Odds API = false; Supabase writes = false;
production operations = false; automatic promotion = false.
