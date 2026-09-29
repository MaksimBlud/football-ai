# MARKET_DEVIG_BOOKMAKER_TIMING_V1

Status: **research-only preregistered historical source/timing experiment**.

## Motivation

`MARKET_DEVIG_METHODS_V1` found no reason to replace proportional/multiplicative
margin removal on Football AI's stored Football-Data average 1X2 prices.

That result does not answer a narrower literature-motivated question: the quality of
probability forecasts can differ by bookmaker/source, and a favorite-longshot-aware
de-vig transform may work for one source even when it does not work on a market average.

This experiment tests that hypothesis without changing the already-closed average-odds
V1 decision.

## Historical source

Zero-cost Football-Data EPL CSV files are downloaded directly for:

- 2019/2020
- 2020/2021
- 2021/2022
- 2022/2023
- 2023/2024
- 2024/2025
- 2025/2026

No Odds API credits are used.

Candidate 1X2 price sources/timings:

- `AVG_STANDARD`: `AvgH / AvgD / AvgA`
- `BET365_STANDARD`: `B365H / B365D / B365A`
- `PINNACLE_STANDARD`: `PSH / PSD / PSA`
- `AVG_CLOSING`: `AvgCH / AvgCD / AvgCA`
- `BET365_CLOSING`: `B365CH / B365CD / B365CA`
- `PINNACLE_CLOSING`: `PSCH / PSCD / PSCA`

The labels are source-column labels only. Closing prices are a benchmark for historical
information efficiency; they are not authorized as pre-close production features.

## Availability gate

A source/timing is evaluable only when:

1. all three required columns exist;
2. decimal odds are finite and > 1;
3. each of the seven seasons has at least 90% valid fixture coverage.

Coverage is checked without using match outcomes.

Sources failing this gate are reported as unavailable and cannot generate a positive
research conclusion.

## De-vig methods

For every evaluable source, compare the exact deterministic methods already frozen in
`MARKET_DEVIG_METHODS_V1`:

- MULTIPLICATIVE — baseline;
- ADDITIVE;
- POWER;
- SHIN.

The implementation is imported from `market_devig_methods_v1.py`; formulas are not
redefined in this experiment.

## Temporal protocol per source

Each evaluable source is treated as its own preregistered family.

### Discovery

2019/20–2023/24.

An alternative method is discovery-eligible only if, against MULTIPLICATIVE on the exact
same valid rows for that source:

1. pooled LogLoss is lower;
2. pooled multiclass Brier is lower;
3. both metrics improve in at least 3 of the 5 discovery seasons.

The eligible alternative with the lowest pooled LogLoss wins; Brier is tie-breaker.
If none qualifies, that source selects MULTIPLICATIVE.

### Validation

2024/25.

A selected alternative must improve both LogLoss and Brier against MULTIPLICATIVE.

### Final temporal test

2025/26.

The frozen selected alternative is evaluated once and must again improve both metrics.

### Paired bootstrap

For a non-baseline selected method, use all seven valid seasons for that source and compute
10,000 paired bootstrap samples of candidate-minus-baseline per-match loss.

A source has `ROBUST_SOURCE_DEVIG_SUPPORT` only when:

- discovery selected a non-baseline method;
- validation improves both metrics;
- final test improves both metrics;
- 95% bootstrap CI is entirely below zero for both LogLoss and Brier.

Otherwise that source remains MULTIPLICATIVE.

Global interpretation is `SOURCE_SPECIFIC_DEVIG_SUPPORT` if at least one evaluable
source passes the full gate. Otherwise it is `NO_SOURCE_SPECIFIC_DEVIG_SUPPORT`.

## Cross-source diagnostic

On the intersection of fixtures where all evaluable sources have valid prices, the
experiment reports MULTIPLICATIVE LogLoss/Brier by source.

This diagnostic does **not** choose a production source. In particular, closing prices are
not treated as if they were available earlier than their real market timing.

## Safety

- research only;
- zero paid Odds API requests;
- no Supabase reads or writes are required;
- no model training;
- no model artifact creation;
- no production promotion;
- no production `.pkl` modification;
- output is a JSON research report only.

## First frozen execution

First complete run:

- workflow run: `36513803897`
- head: `0df53e6c710dc931c6a3ef56326d93600637ba16`
- artifact: `11009517965`
- artifact digest: `sha256:417440fc7776dd02cef619e51a1e831052b9ef9d64d08a0527eb079d440e1aac`

Environment:

- pandas `3.0.6`
- numpy `2.5.3`
- requests `2.32.5`

### Availability

Four sources passed the frozen 90% per-season coverage gate with 100% coverage across
all seven seasons:

- AVG_STANDARD
- BET365_STANDARD
- AVG_CLOSING
- BET365_CLOSING

Pinnacle standard and closing each had only 210/380 valid rows in 2025/26
(`55.26%`), so both failed closed and were excluded from source-specific conclusions.

### Source-specific de-vig result

- AVG_STANDARD selected MULTIPLICATIVE.
- BET365_STANDARD selected MULTIPLICATIVE.
- BET365_CLOSING selected MULTIPLICATIVE.
- AVG_CLOSING was the only source where an alternative survived discovery:
  POWER improved discovery LogLoss by `-0.00004075` and Brier by
  `-0.00018527`, with 3/5 joint season wins.

However the AVG_CLOSING POWER candidate failed both temporal holdouts:

2024/25:

- MULTIPLICATIVE: LogLoss `0.9667334`, Brier `0.5751878`
- POWER: LogLoss `0.9670590`, Brier `0.5756091`

2025/26:

- MULTIPLICATIVE: LogLoss `1.0117669`, Brier `0.6077370`
- POWER: LogLoss `1.0127802`, Brier `0.6088196`

Its all-season paired bootstrap also did not support the alternative:

- LogLoss 95% CI: `[-0.0008755, +0.0012287]`
- Brier 95% CI: `[-0.0005089, +0.0006727]`

Frozen global interpretation:

`NO_SOURCE_SPECIFIC_DEVIG_SUPPORT`

Therefore no tested bookmaker/timing source justifies replacing multiplicative margin
removal with Additive, Power, or Shin.

## Separate timing diagnostic

The common-fixture comparison contains all 2,660 matches for the four eligible sources.
Using MULTIPLICATIVE throughout:

| Source | LogLoss | Brier | Accuracy | Mean overround |
| --- | ---: | ---: | ---: | ---: |
| AVG_STANDARD | 0.9676615 | 0.5744651 | 54.47% | 4.456% |
| BET365_STANDARD | 0.9688773 | 0.5748651 | 54.47% | 5.426% |
| AVG_CLOSING | **0.9638785** | 0.5716831 | **54.96%** | 4.271% |
| BET365_CLOSING | 0.9640491 | **0.5716797** | **54.96%** | 5.478% |

This is **not** evidence that closing prices may be used earlier than close. It is evidence
that the closing market is a stronger historical benchmark than the corresponding standard
prices in this sample.

That makes closing-line information useful as a benchmark/CLV target for future Football AI
research, while the production de-vig decision remains unchanged.
