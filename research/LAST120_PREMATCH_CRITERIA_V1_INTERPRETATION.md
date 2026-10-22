# LAST120_PREMATCH_CRITERIA_V1 — interpretation

**Status: research-only / NO_PRODUCTION_PROMOTION.** Snapshot through 2026-10-19. GitHub Actions succeeded; the production artifact hash check passed. No Supabase writes, paid APIs or production artifact changes occurred.

## Executive finding

No reliable **pre-match** rule has been validated for selecting low-risk No Goal matches in the actual final 120 seconds. Market context contains weak signal, but it is small, differs by league, and is not robust enough to use as a hard selector.

The most plausible exploratory risk flag is a high market-implied total. It must not trigger a bet or automatically exclude a fixture.

## Data

- Target A: a verified goal event in the final 120 actual seconds before Opta's second-half end event. Criterion B (last two minutes of referee-announced added time) was not evaluated because the archive lacks a reliable per-match announced-added-time field.
- Opta universe: 7,406 Big Five fixtures from 2022/23–2026/27 through 2026-10-19; 7,398 resolved labels; 412 late-goal matches (5.57%). Eight rows failed goal-event/final-whistle reconciliation.
- Strict historical-odds join: 5,551 fixtures; 5,545 resolved target rows; 293 late goals (5.28%). Coverage is uneven. In 2025/26 the matched rows were EPL 340/380, La Liga 210/380, Bundesliga 182/306, Serie A 306/380, Ligue 1 239/305.
- RPL is not in the odds-feature model because no comparable paired historical quote table was included. Do not transfer Big Five coefficients to RPL.
- Features: de-vigged 1X2 probabilities, favorite probability/odds and favorite-vs-runner-up gap, draw probability, de-vigged O/U 2.5 probability, Poisson-implied total goals, and standard-to-explicit-closing market movement where both same-source prices exist. Standard-price columns are not assumed to be true opening prices.

## Fixed temporal model

Fixed L2 logistic regression (C=0.2). Validation: train 2022/23–2023/24, test 2024/25. OOT: train 2022/23–2024/25, test 2025/26. Baseline is training-only late-goal frequency per league.

| Split | n | Late goals | Rate | AUC | Brier model / baseline | LogLoss model / baseline |
|---|---:|---:|---:|---:|---:|---:|
| Validation 2024/25 | 1,362 | 65 | 4.77% | 0.567 | 0.045348 / 0.045468 | 0.191026 / 0.191935 |
| OOT 2025/26 | 1,276 | 66 | 5.17% | 0.545 | 0.048945 / 0.049021 | 0.202947 / 0.203329 |

OOT Brier skill is only about **0.15%** and AUC is **0.545**. Predicted-risk deciles are not monotonic: lowest decile had 8/128 late goals (6.25%) at mean predicted risk 3.25%; highest had 9/128 (7.03%) at mean predicted risk 8.17%. OOT AUC differs by league: Bundesliga 0.518, EPL 0.477, La Liga 0.633, Ligue 1 0.486, Serie A 0.433. This is not a robust universal selector.

## Overall descriptive segments, matched/resolved seasons

| Pre-match segment | Late goals / n | Rate |
|---|---:|---:|
| Poisson-implied total <2.0 | 4/64 | 6.25% |
| Total 2.0–2.29 | 21/470 | 4.47% |
| Total 2.3–2.59 | 62/1,365 | 4.54% |
| Total 2.6–2.89 | 74/1,558 | 4.75% |
| Total 2.9–3.19 | 70/1,136 | 6.16% |
| Total 3.2–3.49 | 37/556 | 6.65% |
| Total ≥3.5 | 25/396 | 6.31% |
| P(Over 2.5) <35% | 7/144 | 4.86% |
| P(Over 2.5) 35–41% | 26/611 | 4.26% |
| P(Over 2.5) 58–64% | 57/935 | 6.10% |
| P(Over 2.5) ≥65% | 46/636 | 7.23% |
| Favorite probability 42–46% | 30/768 | 3.91% |
| Favorite probability ≥70% | 45/624 | 7.21% |
| Draw probability <20% | 60/885 | 6.78% |
| Draw probability 29–32% | 37/904 | 4.09% |
| O/U probability rises 1–4pp | 87/1,381 | 6.30% |

Favorite/draw relationships are non-monotonic. Descriptive frequency alone does not prove a causal or profitable signal; many bins were inspected and small groups have wide uncertainty.

## OOT threshold diagnostics

| Condition | Validation 2024/25: condition vs others | OOT 2025/26: condition vs others | OOT OR adjusted for league | Decision |
|---|---|---|---|---|
| Implied total ≥3.2 | 14/274 (5.11%) vs 51/1,088 (4.69%) | 19/212 (8.96%) vs 47/1,064 (4.42%) | 1.83; 95% CI 0.99–3.38; p=0.053 | Watch flag only; current 2026/27 is 3/59 (5.08%) vs 8/157 (5.10%). |
| Implied total ≥2.9 | 30/543 (5.52%) vs 35/819 (4.27%) | 32/473 (6.77%) vs 34/803 (4.23%) | 1.45; CI 0.82–2.57; p=0.199 | Direction is consistent but uncertainty is large. |
| P(Over 2.5) ≥65% | 11/185 (5.95%) vs 54/1,177 (4.59%) | 13/136 (9.56%) vs 53/1,140 (4.65%) | 1.80; CI 0.89–3.61; p=0.099 | Not reproduced in current 2026/27: 2/39 vs 9/177, both about 5.1%. |
| P(draw) <20% | 12/232 (5.17%) vs 53/1,130 (4.69%) | 16/179 (8.94%) vs 50/1,097 (4.56%) | 1.94; CI 1.08–3.46; p=0.026 | Nominal OOT association, but exploratory multiple-testing FDR q≈0.142; current sample 0/39 vs 11/177. |
| Favorite probability ≥70% | 10/171 (5.85%) vs 55/1,191 (4.62%) | 10/123 (8.13%) vs 56/1,153 (4.86%) | 1.65; CI 0.82–3.31; p=0.159 | Not robust; only 0/26 current matches have a late goal, too few to conclude. |
| Favorite-vs-second gap ≥40pp | 17/325 (5.23%) vs 48/1,037 (4.63%) | 21/273 (7.69%) vs 45/1,003 (4.49%) | 1.77; CI 1.03–3.04; p=0.037 | Exploratory FDR q≈0.142; current sample reverses direction (1/51 vs 10/165). |
| P(Over 2.5) rises ≥1pp | 28/438 (6.39%) vs 37/924 (4.00%) | 24/435 (5.52%) vs 42/841 (4.99%) | 1.10; CI 0.65–1.86; p=0.725 | No independent OOT movement signal. |

These thresholds were not preregistered as one isolated primary hypothesis. FDR values are diagnostic. For total ≥3.2 in OOT, rates were 7/40 (17.5%) in La Liga, 6/49 (12.2%) in Ligue 1, 3/70 (4.3%) in Bundesliga, 3/50 (6.0%) in EPL and 0/3 in Serie A. This indicates league heterogeneity; the league-adjusted interval still includes no effect.

## Strategy decision

1. **No hard pre-match selection rule is validated** for No Goal in the actual final 120 seconds.
2. Implied total ≥3.2 or P(Over 2.5) ≥65% may be used only as a provisional higher-risk watch flag, not as a bet/no-bet rule.
3. Low expected total is not a validated safe zone: total <2.6 had 16/477 (3.35%) in validation but 23/489 (4.70%) in OOT versus 53/952 (5.57%) among the remainder; OOT difference is not decisive.
4. Favorite/underdog and equal-team labels alone are not useful enough: relationships are non-monotonic and do not transport reliably.
5. The earlier level-score-at-85:00 finding is a live-state signal, not a pre-match criterion.
6. Criterion B remains untested; do not substitute actual final-match length for referee-announced added time.

## Reproducibility

- Branch: research/last120-prematch-criteria-20261021
- Final GitHub Actions run: https://github.com/MaksimBlud/football-ai/actions/runs/39791798472
- Raw output bundle includes match-level CSV, bin rates, season/league stability, coverage, model metrics, summary JSON and initial report.
- No paid API, no Supabase writes, no production artifact changes, no production promotion.
