# Research V5 final report — Issue #482

## Вывод простым языком

Независимая репликация на Bundesliga и Ligue 1 уже выполнена canonical zero-cost кодом.
По заранее замороженному правилу она **не подтвердила** lead-lag: validation 2024/25
не прошёл gate. Положительный OOT 2025/26 не может задним числом спасти validation.

Финальное решение: **CLOSE_DIRECTION**. Не запускать платный intraday collector, не
использовать сигнал в betting/production и не ослаблять frozen gates.

## Technical appendix

Canonical source: `experiments/cross_market_lead_lag_replication_v2_report.json`.

Validation 2024/25: rows=137, mean=1.2128151012796614e-05,
positive leagues=1/2,
permutation p=0.1932806719328067,
bootstrap 95% CI=[-8.196999466573126e-05, 9.961887301429277e-05],
admissible=False.

OOT 2025/26: rows=168, mean=0.00010680996910608444,
positive leagues=2/2,
permutation p=0.007599240075992401,
bootstrap 95% CI=[3.6680819337470654e-05, 0.00018326946356555203],
gate=True.

Frozen decision: **LEAD_LAG_REPLICATION_NOT_SUPPORTED**. Result: **NO_BET**.
No outcomes, no 2026/27 outcomes, no paid API, no Supabase writes, no production operation
or promotion.
