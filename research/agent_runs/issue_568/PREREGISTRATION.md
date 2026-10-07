# Frozen independent tactical-pressure disagreement

Status: **PREREGISTERED / INDEPENDENT FOOTBALL SOURCE / TEMPORAL OOS / CROSS-LEAGUE / RESEARCH ONLY / NO_BET**.

The football-only estimate uses zero-cost prior-match Understat deep, deep_allowed, PPDA and PPDA_allowed and never consumes odds. Football-Data AvgH/AvgD/AvgA are used only as the multiplicatively de-vigged average-bookmaker 1X2 control. Formal leagues are EPL, La Liga, Serie A, Bundesliga and Ligue 1. Audit every source/schema and deterministic identity mapping before reading reserved outcomes. Do not use 2026/27 outcomes.

For each fixture and team, use exactly the previous five same-season completed Understat matches, excluding all matches on the target calendar day. Frozen features are home and away last-five means for all four fields plus four signed home-minus-away contrasts. No window, field, side, sign, league or threshold selection. Fit one StandardScaler plus multinomial LogisticRegression football-only model on 2019/20-2023/24 outcomes. Do not refit on validation. Validation is 2024/25 and untouched test is 2025/26.

The disagreement class is symmetric and fixed: football-only argmax differs from market-control argmax. There is no magnitude threshold or chosen outcome side. Before reading validation/test outcomes, both splits must have at least 50 disagreement fixtures pooled and at least 8 in every league; otherwise return BLOCKED_LOW_DISAGREEMENT_SAMPLE.

Primary deltas are football-only minus raw market control for multiclass Log Loss and Brier on disagreement fixtures; negative is better. Support requires both deltas negative in validation and test, the league-stratified 5000-draw test Log Loss bootstrap CI wholly below zero, negative test Log Loss delta in at least four of five leagues, and no league delta above +0.01. Full-sample metrics are diagnostic only and cannot rescue failure.

Passing returns SUPPORTED_INDEPENDENT_TACTICAL_DISAGREEMENT_EDGE. Otherwise return NO_STABLE_INDEPENDENT_TACTICAL_DISAGREEMENT_EDGE; source failure returns BLOCKED_BY_SOURCE_GAP. Do not blend estimates or learn a market correction here; that belongs only to roadmap Direction 4. No paid API, Supabase write, production .pkl operation, model API, promotion, betting authorization or post-hoc gate change.
