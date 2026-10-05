# Frozen cross-book price-formation transport

Status: **PREREGISTERED / CROSS-BOOK + CROSS-LEAGUE FALSIFICATION / RESEARCH ONLY / NO_BET**.

Issue #532's negative result remains binding. Use only Bundesliga and Ligue 1 zero-cost Football-Data files. Reference is 2019/20-2023/24, validation is 2024/25 and untouched OOT is 2025/26. Bet365 and Pinnacle are anchors. Predeclared third books are BW, IW, WH and VC; include every third book with finite positive opening+closing 1X2 coverage >=90% in both OOS seasons and both leagues. If none qualifies, return BLOCKED_BY_SOURCE_GAP before reading outcomes. No proxy, interpolation or performance-based bookmaker selection.

Multiplicatively de-vig each bookmaker and the Football-Data Avg opening/closing 1X2 vectors. The external Avg representation is the frozen consensus. COMMON_MOVE is closing minus opening consensus. Each bookmaker residual is fair bookmaker probability minus consensus; BOOK_SPECIFIC_MOVE is closing residual minus opening residual; OVERROUND_MOVE is closing minus opening raw implied sum.

Support requires OOT COMMON_MOVE Log Loss improvement with a fixture-cluster bootstrap CI wholly below zero; negative OOT deltas in both leagues; every qualifying third book specific-movement share >=5%; at least 25% of each third book's component variance remaining after the frozen linear margin projection; and non-contradictory validation/OOT mean specific-move vectors (dot product >=0). Brier, residual persistence/mean-reversion and margin interaction are diagnostics only.

Passing returns SUPPORTED_CROSS_BOOK_PRICE_COMPONENT_TRANSPORT. Failing returns NO_CROSS_BOOK_PRICE_COMPONENT_CONFIRMATION. A pass does not identify bettor flow, liabilities, intent or an economic edge. No paid API, Supabase, production .pkl change, production promotion or automatic betting action.
