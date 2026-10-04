# PROJECT_CONTINUITY ADDENDUM — 2026-10-04 — Cross-market lead-lag independent replication

## Experiment

`CROSS_MARKET_LEAD_LAG_INDEPENDENT_REPLICATION_V1`

Branch:

`research/market-lead-lag-v1-20261004`

PR:

`#466`

Parent experiment:

`CROSS_MARKET_LEAD_LAG_V1`

## Frozen independent scope

Leagues not used by the parent experiment:

- Bundesliga;
- Ligue 1.

The protocol was committed before opening target-bearing closing prices:

`67f8cfae2364bb44444502ae3cc9d9c7e3cba1b7`.

The exact parent statistic was transferred unchanged:

`alignment_dot = dot(p_score_open - p_1x2_open, p_1x2_close - p_1x2_open)`.

Same-bookmaker Bet365, half-goal AH only, 10k within-league permutation,
10k stratified bootstrap, seed 20261004.

Temporal contract:

- reference: 2019/20–2023/24;
- validation: 2024/25;
- untouched OOT: 2025/26;
- no 2026/27 data.

## First frozen run

Workflow:

`37178894589`

Artifact:

`11294905716`

Digest:

`sha256:d37588ac0fdcdaa9cf319c63859eda2e3703a338650ac1a0e86c38a236c31f4c`

Generating head:

`e74d13d3139d59e64e6a6eb9948337a1e6573cbb`

## Result

Sample gate passed.

Validation 2024/25:

- pooled rows: 137;
- Bundesliga: 64;
- Ligue 1: 73;
- mean alignment: +0.00001213;
- positive leagues: 1/2;
- permutation p = 0.1933;
- bootstrap 95% CI = [-0.00008197, +0.00009962];
- `validation_admissible = false`.

Untouched OOT 2025/26:

- pooled rows: 168;
- Bundesliga: 76;
- Ligue 1: 92;
- mean alignment: +0.00010681;
- positive leagues: 2/2;
- permutation p = 0.00760;
- bootstrap 95% CI = [+0.00003668, +0.00018327];
- `test_gate = true`.

The strong OOT season cannot rescue failed validation.

Formal decision:

`INDEPENDENT_LEAGUE_REPLICATION_NOT_SUPPORTED`

`NO_BET`

Binding interpretation:

`SEASON_DEPENDENT_ALIGNMENT_WITHOUT_STABLE_REPLICATION`

## Research boundary

Close this specific historical open→close cross-market lead-lag proxy under the
preregistered rules.

Do not:

- relax the validation gate;
- select only 2025/26;
- drop an unfavorable league;
- optimize thresholds on opened data;
- claim a tradable signal;
- spend paid Odds API credits on an intraday collector for this hypothesis;
- promote anything to production.

A revisit requires genuinely new information, preferably a prospectively collected
timestamped multi-market path under a new preregistered hypothesis.

## Safety proof

- match outcomes used: false;
- opened 2026/27 data used: false;
- paid Odds API calls: 0;
- Supabase writes: 0;
- production model hash verification: passed;
- production promotion: false.
