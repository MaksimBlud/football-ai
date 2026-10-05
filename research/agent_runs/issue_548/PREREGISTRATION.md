# Frozen bookmaker margin market-type transport

Status: **PREREGISTERED / OUTCOME-FREE / MATCHED FIXTURES / RESEARCH ONLY / NO_BET**.

Transport Issue #535 from 1X2 to the exact same fixtures' opening Asian Handicap market. Frozen books are Bet365 (B365AHH/B365AHA) and Pinnacle (PAHH/PAHA). Use AHh, with B365AH only as the documented schema fallback. Only exact half-goal lines are eligible; no push lines, bookmaker substitution or synthetic closing snapshot.

Leagues are EPL, La Liga and Serie A. Reference is 2019/20-2023/24, validation is 2024/25 and untouched temporal test is 2025/26. The source gate audits both books, the shared line and the opening 1X2 fields before any derived price effect. Match outcomes are not read.

For each book compute two-way AH overround, multiplicative fair probabilities and allocation tilt relative to the mean two-book fair consensus. Favourite/underdog is determined from the frozen AH-line sign. Primary AH statistic is underdog tilt minus favourite tilt; paired effect is Bet365 minus Pinnacle. Reproduce the frozen #535 opening 1X2 effect on the identical subset and report AH minus 1X2 with a bootstrap CI.

Support requires the AH effect to have the same non-zero sign in validation and test, the test CI to exclude zero, and at least two of three leagues to share the pooled test sign. Total overround and AH-minus-1X2 must be reported separately. Otherwise return NO_STABLE_CROSS_MARKET_MARGIN_STRUCTURE; source failure returns BLOCKED_BY_SOURCE_GAP. A failure does not negate #535. No causal intent, betting edge, production weighting, paid API, Supabase or promotion.
