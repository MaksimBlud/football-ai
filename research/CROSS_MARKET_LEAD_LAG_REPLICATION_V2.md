# CROSS_MARKET_LEAD_LAG_REPLICATION_V2

Status: **PREREGISTERED INDEPENDENT-LEAGUE REPLICATION / OUTCOME-FREE / NO_BET**.

## Purpose

CROSS_MARKET_LEAD_LAG_V1 on EPL / La Liga / Serie A produced a borderline result:

- validation passed the frozen permutation gate;
- OOT had positive mean alignment in 3/3 leagues;
- OOT within-league permutation p = 0.00020;
- but the frozen OOT stratified bootstrap 95% CI for absolute mean alignment crossed zero:
  `[-0.00001073, +0.00010252]`.

The formal V1 decision therefore remained:

`NO_OPEN_TO_CLOSE_CROSS_MARKET_LEAD_SIGNAL`.

V2 does **not** retune V1.

It asks whether the exact same match-specific opening→closing alignment appears in two
independent leagues available from zero-cost Football-Data history:

- Bundesliga;
- Ligue 1.

No paid intraday collection is permitted from V1 evidence alone.

## Immutable inherited hypothesis

Same bookmaker:

**Bet365**

Opening inputs:

- 1X2: `B365H / B365D / B365A`;
- O/U 2.5: `B365>2.5 / B365<2.5`;
- AH: line from `AHh` then `B365AH`, prices `B365AHH / B365AHA`.

Closing target:

- 1X2: `B365CH / B365CD / B365CA`.

Primary AH rows:

- exact half-goal handicap only.

Structural reconstruction:

- identical Poisson/Skellam opening O/U+AH inversion from V1.

Primary per-match statistic:

`alignment_dot = dot(p_score_open - p_1x2_open, p_1x2_close - p_1x2_open)`.

No alternative statistic may replace it.

Primary null:

- within-league permutation of opening lead vectors;
- 10,000 draws;
- seed `20261004`.

Bootstrap:

- stratified by league;
- 10,000 draws;
- seed `20261004`.

## Temporal scope

Reference diagnostic:

- 2019/20–2023/24.

Validation:

- 2024/25.

Untouched OOT:

- 2025/26.

No 2026/27 data.

No match outcome is used anywhere.

## Pinned source provenance

Official Football-Data transport may fail inside GitHub Actions. V2 therefore uses pinned
raw mirrors with Git blob verification.

### Old source mirror

Repository:

`Emire221/kahin`

Pinned commit:

`97c22f31564baafbd18ef818bb2df9fcb49319bc`

Used for:

- 2019/20;
- 2020/21.

Pinned blobs:

Bundesliga:

- D1 2019/20: `a07e4ab36464bd1c4b62c2e98e4559aff4fdb4ef`;
- D1 2020/21: `0d3370c801e43c5dcb9012e405678dc5179b325d`.

Ligue 1:

- F1 2019/20: `4e2cd6384a05d10cd9ad1a4c1b4d087d60fddd45`;
- F1 2020/21: `0227119200af3698163fb0265d0910e377bcf335`.

### New source mirror

Repository:

`yusufislamoruk/football-prediction-bot`

Pinned commit:

`47ca08e08f46d16a8f6a0494777b1e16ae5562b3`

Used for 2021/22–2025/26.

Bundesliga blobs:

- 2021/22: `5796451d8caa093b8176f6eecf82051a239604f6`;
- 2022/23: `406b28aee2ccd37177eec474447f4a3325247db4`;
- 2023/24: `54efdb13aa7b537a80aca0a2378942d373594c06`;
- 2024/25: `5ab934bebe32bfd689d97eb8303795dac4e8c407`;
- 2025/26: `361e63baa038b50f549f2bc75b0c03a655d15673`.

Ligue 1 blobs:

- 2021/22: `b98b8533c186704863ef63f25f65be770a4289d6`;
- 2022/23: `f6cbe993e0a6be9322026acaed8015cb5e5ee14b`;
- 2023/24: `3836a0b1a91ca4e9f97a61bbe3717b5fddd1a131`;
- 2024/25: `fe5478bb28dd899b9646207ffc8e01bbb2dfc5ff`;
- 2025/26: `3979f0a22d5a60d3d331a31785f3c963da794e45`.

For overlapping 2021/22–2024/25 seasons, the old and new repositories have identical Git
blob SHAs for both D1 and F1. This is source-provenance evidence only and was checked before
any V2 market calculation.

The older mirror's 2025/26 files are smaller/incomplete and are explicitly not used.

## Outcome-free contract

Football-Data distributes results and odds in the same CSV.

V2 must drop historical outcome/stat columns immediately after loading and before any
feature/target calculation.

It must not read, branch on, score, join or report:

- FTR;
- FTHG / FTAG;
- HTHG / HTAG / HTR;
- match-stat outcome columns.

The target is **future bookmaker movement**, not football result.

## Replication gates

The V1 metric/sign/null are transferred unchanged.

### Validation 2024/25

Replication is validation-admissible only if all are true:

1. pooled mean `alignment_dot > 0`;
2. **both 2/2 leagues** have positive mean alignment;
3. each league has at least 40 eligible rows;
4. within-league permutation one-sided p < 0.05.

### OOT 2025/26

`INDEPENDENT_LEAGUE_LEAD_LAG_REPLICATION_SUPPORTED` only if validation passes and all
OOT conditions also hold:

1. pooled mean `alignment_dot > 0`;
2. **both 2/2 leagues** have positive mean alignment;
3. each league has at least 40 eligible rows;
4. within-league permutation one-sided p < 0.05;
5. stratified bootstrap 95% CI of absolute mean alignment is entirely above zero.

Otherwise:

`LEAD_LAG_REPLICATION_NOT_SUPPORTED`.

V2 cannot rescue itself by:

- changing sign;
- selecting one of the two leagues;
- changing the half-goal restriction;
- switching to HOME-only / AWAY-only;
- using gap reduction instead of alignment dot;
- changing permutation or bootstrap sidedness.

## Diagnostics

Report unchanged V1 diagnostics:

- mean/median alignment dot;
- positive-alignment rate;
- opening synthetic gap TV;
- gap reduction TV;
- opening→closing movement TV;
- HOME/DRAW/AWAY component correlations;
- AH reconstruction residual;
- coverage by league/season.

## Interpretation

If V2 passes, then five leagues collectively support a small but reproducible opening
cross-market -> closing 1X2 relationship. Only then would it be reasonable to consider a
future **timestamped** prospective collector.

If V2 fails, close this lead-lag family for now and do not spend paid provider credits to
measure finer timing.

Even if supported, V2 remains:

- historical;
- open→close rather than true intraday;
- non-betting;
- non-production.

## Safety

- research-only;
- NO_BET;
- no outcomes;
- no 2026/27 data;
- zero paid Odds API calls;
- no Supabase writes;
- no production model operations;
- no production `.pkl` changes;
- no automatic promotion.
