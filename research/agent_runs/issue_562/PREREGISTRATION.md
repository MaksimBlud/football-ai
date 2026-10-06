# Frozen market-residual process-vs-results divergence

Status: **PREREGISTERED / TEMPORAL OOS / CROSS-LEAGUE / RESEARCH ONLY / NO_BET**.

Formal leagues are Bundesliga and Ligue 1 from zero-cost Football-Data only. Required fields are Date, HomeTeam, AwayTeam, FTR, HS, AS, HST, AST and the exact Bet365 B365H/B365D/B365A 1X2 triplet. Audit all file headers before reading outcomes. Use no 2026/27 outcomes.

For each team use exactly its previous five same-season league matches, with no prior-season carryover and with the current fixture appended only after its features are frozen. points_rate_5 = points_won / 15. sot_share_5 = sum(SOT_for) / (sum(SOT_for) + sum(SOT_against)). process_result_divergence_5 = sot_share_5 - points_rate_5. Fixture features are home divergence, away divergence and home-minus-away divergence. Rows without five valid prior matches or a positive SOT denominator are ineligible. No window, cutoff, sign, threshold, league or feature-subset search.

Paired models use identical fixtures. MARKET_MODEL uses multiplicatively de-vigged Bet365 1X2 probabilities. MARKET_PLUS_PROCESS_DIVERGENCE uses those probabilities plus the three frozen divergence features. Both use median imputation, StandardScaler and multinomial LogisticRegression with fixed default regularization and max_iter=2000.

Development is 2019/20-2023/24, validation is 2024/25 and untouched test is 2025/26. Refit in expanding temporal order and never train on the evaluated season. Primary deltas are candidate minus baseline for multiclass Log Loss and Brier; negative is better. Support requires both deltas negative in validation and test, the league-stratified 5000-draw untouched-test Log Loss bootstrap CI wholly below zero, and no positive untouched-test Log Loss delta in either league. Accuracy is diagnostic only.

Passing returns SUPPORTED_MARKET_RESIDUAL_PROCESS_DIVERGENCE. Otherwise return NO_STABLE_MARKET_RESIDUAL_PROCESS_DIVERGENCE; source failure returns BLOCKED_BY_SOURCE_GAP. A pass is research evidence only and cannot authorize betting, production or promotion. No paid API, Supabase write, production .pkl operation, post-hoc gate change or model API.
