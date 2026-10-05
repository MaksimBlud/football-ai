# Research V5 final report — Issue #428

## Вывод простым языком

Исследование времени начала и дня недели завершено deterministic Python без внешней
LLM/API-квоты. Решение: **NO_KICKOFF_CALENDAR_OOS_SIGNAL**.

Validation calendar-minus-baseline log loss:
**0.0006880266691519088**.

OOT calendar-minus-baseline log loss:
**0.001491810071060251**,
paired-bootstrap 95% CI:
**[-0.0014696915159004966, 0.004388259664684446]**.

## Technical appendix

Temporal split: <=2023/24 / 2024/25 / 2025/26.
Market baseline: devigged Bet365 O/U 2.5 + league.
Extension: weekday + kickoff cyclic features + frozen slot.
No paid API, Supabase, production model operation or promotion.
Full result: `research/agent_runs/issue_428/RESULT.json`.
