# Research V5 final report — Issue #510

## Вывод простым языком

Детерминированное исследование **kickoff time / weekday incremental O/U 2.5 audit** завершено без внешней LLM/API-квоты.

Финальное решение: **NO_KICKOFF_CALENDAR_OOS_SIGNAL**.



## Technical appendix

Full reproducible result:
`research/agent_runs/issue_510/RESULT.json`.

Key registered result fields:
- `reference_rows`: 5695
- `validation.calendar_minus_baseline_log_loss`: 0.0006880266691519088
- `test.calendar_minus_baseline_log_loss`: 0.001491810071060251
- `test.bootstrap.ci95_low`: -0.0014696915159004966
- `test.bootstrap.ci95_high`: 0.004388259664684446

Safety contract: model API = false; paid Odds API = false; Supabase writes = false;
production operations = false; automatic promotion = false.
