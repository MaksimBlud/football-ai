# Frozen favourite-longshot bias protocol

Status: **PREREGISTERED / TEMPORAL OOS / RESEARCH ONLY / NO_BET**.

Primary market: 1X2. Frozen leagues: EPL, La Liga, Serie A. Frozen bookmakers: Bet365 and Pinnacle. Primary no-vig representation: multiplicative/proportional normalization.

Outcome-free header/source audit must complete before reading FTR. Both bookmakers must have exact opening and closing 1X2 columns for all validation/test league-seasons. Missing coverage fails closed; no proxy bookmaker and no paid source.

Temporal design:
- reference/descriptive: 2019/20-2023/24;
- validation: 2024/25;
- untouched OOT: 2025/26.

Primary horizons: opening and closing. Exact 24h/6h/1h snapshots are evaluated only if an honest timestamped source exists. The current frozen Football-Data source does not provide those exact snapshots, so they must be reported as SOURCE_GAP and never interpolated.

Frozen probability bins, left-inclusive/right-exclusive:
0-20%, 20-30%, 30-40%, 40-50%, 50-60%, 60-70%, 70-80%, 80%+.

For every bin report N, mean fair probability, realized frequency, 95% frequency interval, calibration gap, average raw odds and historical flat-stake return. Historical return is diagnostic only and cannot authorize betting.

Primary structural statistic: slope of calibration residual (y - p) on fair probability p, with deterministic league-stratified fixture-cluster bootstrap. Positive slope is the classic favourite-longshot direction: low-p outcomes are overestimated while high-p outcomes are underestimated.

Frozen aggregate regions:
- longshot: p < 0.30;
- favourite: p >= 0.60.

STABLE_FAVOURITE_LONGSHOT_BIAS requires all:
1. validation closing residual-slope 95% CI lower bound > 0;
2. untouched OOT closing residual-slope 95% CI lower bound > 0;
3. validation longshot gap < 0 and favourite gap > 0;
4. OOT longshot gap < 0 and favourite gap > 0;
5. positive OOT slope for both frozen bookmakers;
6. positive OOT slope in at least two of three frozen leagues.

Otherwise return NO_STABLE_FAVOURITE_LONGSHOT_BIAS. Source failure returns BLOCKED_BY_SOURCE_GAP.

Opening versus closing is reported as a frozen time-path diagnostic and cannot rescue a failed primary gate. League/bookmaker/outcome-type/season breakdowns are diagnostics only. No post-hoc bin changes, no probability correction fitted on this OOT sample, no production promotion.
