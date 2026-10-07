# Frozen multi-market 1X2 repricing-vector protocol

Status: **PREREGISTERED / RETROSPECTIVE FALSIFICATION / OUTCOME-FREE / NO_BET**.

Question: does direct joint Bet365 STANDARD/PRE-CLOSE 1X2 + O/U 2.5 + Asian Handicap state predict the later continuous 1X2 closing repricing vector better than an otherwise identical 1X2-only baseline?

Frozen leagues: EPL, La Liga, Serie A, Bundesliga, Ligue 1.
Reference: 2019/20-2023/24; validation: 2024/25; retrospective test: 2025/26. No 2026/27 outcomes and no match outcomes are required.

Source terminology: Football-Data standard odds are not claimed to be exact timestamped opening odds. They are STANDARD/PRE-CLOSE state. Explicit Bet365 closing 1X2 fields define the later target.

Before any closing movement is computed, audit the zero-cost Football-Data/pinned-mirror source. A league is usable only when validation and test each have >=100 paired eligible fixtures and at least three reference seasons have >=100 eligible fixtures. At least four of five leagues must pass unchanged or the result is BLOCKED_BY_SOURCE_GAP.

Market transforms are frozen:
- 1X2: existing project POWER de-vig;
- O/U 2.5: proportional two-way no-vig;
- Asian Handicap: proportional two-way no-vig;
- AH line: use AHh where finite with B365AH only as the existing schema fallback. Do not subset lines after results.

Target is exactly two log-ratio coordinates:
move_home_vs_draw = log(p_close_home/p_close_draw) - log(p_state_home/p_state_draw)
move_away_vs_draw = log(p_close_away/p_close_draw) - log(p_state_away/p_state_draw).

Both models use SimpleImputer(median) -> StandardScaler -> separate Ridge(alpha=10.0) regressors for the two coordinates.
Baseline features: p_home, p_draw, p_away.
Candidate features: baseline plus p_over_2_5, ah_line, p_ah_home.
No hyperparameter, feature-subset, interaction, sign, line-scope or league search.

Temporal fitting is frozen before evaluator execution:
- validation model fit: reference seasons only;
- retrospective-test model fit: expanding history through validation, i.e. reference + 2024/25;
- baseline and candidate always use the same train/evaluation rows and the same fitting rule.

Primary paired fixture loss is mean squared error across the two target coordinates. MAE is secondary but binding in the support gate. Pearson/Spearman, coordinate sign accuracy and strongest-move-coordinate accuracy are diagnostics only.

Use a deterministic 5,000-draw league-stratified bootstrap on 2025/26 candidate-minus-baseline per-fixture squared-error loss. Negative is better.

REPRICING_STATE_SUPPORTED_FOR_PROSPECTIVE_CONFIRMATION requires all:
1. pooled 2024/25 candidate MSE < baseline MSE;
2. pooled 2024/25 candidate MAE < baseline MAE;
3. pooled 2025/26 candidate MSE < baseline MSE;
4. pooled 2025/26 candidate MAE < baseline MAE;
5. 2025/26 bootstrap 95% CI upper bound < 0;
6. 2025/26 candidate MSE delta is positive in at most one eligible league;
7. source/leakage/safety gates pass.

Historical closing targets through 2025/26 were already opened by related research, so a PASS is not untouched confirmation. It only justifies a separately frozen prospective confirmation.

Corners are not part of this child. Do not use old #385/#522/#528 corner movements to tune or rescue #573. Corner augmentation, if ever allowed, must be a separate preregistered child with point-in-time source coverage and a future target not opened when frozen.

No paid Odds API, no purchased data, no Supabase writes, no production operations, no production .pkl changes, no automatic promotion, and no post-hoc weakening of any gate.
