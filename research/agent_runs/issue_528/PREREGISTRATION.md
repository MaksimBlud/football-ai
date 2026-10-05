# Frozen Bundesliga/Ligue 1 corner match-shape transport

Status: **PREREGISTERED / CROSS-LEAGUE FALSIFICATION / OPENED FOR OTHER HYPOTHESES / NO_BET**.

Use only Bundesliga and Ligue 1 rows from authoritative artifact 11294063833 (SHA-256 92b958e6f5f8c911236f5e6451ed2f974d4e02af727637644dc2ad037cd78aa0): exactly 35 Bundesliga and 39 Ligue 1 fixtures across all four frozen cohorts. Before reading closing corner state or centre_delta, require an exact same-fixture join for all 74 rows to free Football-Data 2026/27 opening 1X2/O-U2.5/AH inputs; otherwise fail closed without a proxy.

For each league, use the exact #522 pipeline: SimpleImputer(median), StandardScaler and Ridge(alpha=1.0); train 2019/20-2024/25 on actual total corners, validate without tuning on 2025/26, then refit through 2025/26. Frozen score: expected total corners minus opening corner FAIR_CENTRE. No feature, alpha, sign, threshold, cohort, league or row selection.

Primary set is every non-zero movement row. Support requires positive Spearman separately in Bundesliga and Ligue 1 and pooled; positive pooled residual Spearman controlling for opening FAIR_CENTRE and league; a one-sided 10,000-draw within-league permutation p <= 0.05; and both leave-one-league-out signs positive. Binary UP/DOWN metrics versus always-UP are secondary only.

These league rows were excluded from #522 but their movements were opened for other hypotheses, so a pass supports only future untouched confirmation. No paid API, Supabase, production operation, betting claim or promotion.
