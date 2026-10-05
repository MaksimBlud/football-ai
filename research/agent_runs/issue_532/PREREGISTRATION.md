# Frozen bookmaker price-formation decomposition

Status: **PREREGISTERED / TEMPORAL OOS / MATCHED FIXTURES / RESEARCH ONLY / NO_BET**.

Use only same-fixture Bet365 and Pinnacle opening and closing 1X2 odds from the zero-cost Football-Data transport for EPL, La Liga and Serie A. Source/header coverage is audited before FTR is read. Reference is 2019/20-2023/24, validation is 2024/25 and untouched test is 2025/26.

Multiplicatively de-vig each book. Consensus is the simple mean of the two books present at each horizon. COMMON_MOVE is closing minus opening consensus. Each book's residual is book fair probability minus consensus; BOOK_SPECIFIC_MOVE is closing residual minus opening residual. OVERROUND_MOVE is closing minus opening raw implied sum. No result enters those features.

Primary common-information test is fixture-level closing-consensus minus opening-consensus Log Loss on untouched 2025/26 with a deterministic league-stratified 5000-draw bootstrap. Support requires negative mean and CI upper bound below zero, with negative league means in at least two of three leagues.

Book-specific movement is non-trivial only when its pooled and each-book squared-movement share is at least 5% of total book movement. To prevent pure margin movement being mislabeled, at least 25% of bookmaker-specific component variance must remain after linear projection on OVERROUND_MOVE. These thresholds are frozen before execution. Book-close versus close-consensus Log Loss/Brier, residual persistence and margin association are reported as diagnostics and cannot rescue a failed common-information gate.

Passing returns SUPPORTED_PRICE_COMPONENT_DECOMPOSITION; otherwise NO_STABLE_BOOKMAKER_SPECIFIC_PRICE_COMPONENT. Missing paired source coverage returns BLOCKED_BY_SOURCE_GAP. The result is observational and cannot identify bettor flow, liabilities or bookmaker intent. No production feature, paid API, Supabase write or automatic promotion.
