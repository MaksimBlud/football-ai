# Frozen kickoff/calendar O/U 2.5 protocol

Status: **PREREGISTERED / TEMPORAL OOS / RESEARCH ONLY**.

Leagues: EPL, La Liga, Serie A. No 2026/27.
Reference/train: through 2023/24; validation: 2024/25; untouched test: 2025/26.
Target: FTHG + FTAG > 2.5.
Baseline: league + devigged Bet365 O/U 2.5 probability.
Calendar extension: weekday, kickoff-hour sin/cos and frozen time-slot buckets.
Estimator: fixed regularized logistic regression.
Primary metric: log loss; Brier/AUC diagnostics.
Support requires lower calendar-model log loss in validation and OOT plus OOT paired bootstrap 95% CI for calendar-minus-baseline delta entirely below zero.
No production model, paid API, Supabase or automatic promotion.
