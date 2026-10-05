# Frozen kickoff/calendar market-movement protocol

Status: **PREREGISTERED / OUTCOME-FREE / TEMPORAL OOS / RESEARCH ONLY**.

Fixed leagues: EPL, La Liga, Serie A.
Source: the same pinned/public Football-Data transport used by Issues #428 and #514.
Required fields: Date, Time, Bet365 opening O/U 2.5 odds and Bet365 closing O/U 2.5 odds. Fail closed without substitution if the exact source contract is unavailable.
Reference/train: 2019/20–2023/24; validation: 2024/25; untouched OOT test: 2025/26.
Target: closing minus opening no-vig Bet365 Over-2.5 probability.
Baseline: league plus opening no-vig Over-2.5 probability.
Calendar extension: frozen weekday indicators, kickoff-hour sin/cos and the same four slots as #428.
Estimator: StandardScaler plus Ridge(alpha=1.0), fixed for baseline and extension.
Primary metric: per-match squared-error loss. Support requires lower MSE in validation and OOT plus an OOT league-stratified paired-bootstrap 95% CI for calendar-minus-baseline squared-error loss entirely below zero.
MAE and non-zero-movement sign accuracy are secondary diagnostics only.
Match outcomes must not be loaded or used. No arbitrary cutoff/league/threshold selection, paid data, Supabase, production operation, betting claim or promotion.
