# Big Balls Sports Data — Free Serie A source audit for original MARKET_ANCHOR_1X2_V2

**Reviewed:** 2026-11-24 12:52 UTC  
**Provider:** [Big Balls Sports Data](https://bigballsdata.com/)  
**Decision:** **HOLD — candidate only; no account, API key, request, download, integration, feature calculation or inference.**

## Executive finding

Big Balls Sports Data is a materially stronger free-source candidate than the previously reviewed options because its official Terms of Service explicitly permit storing API responses in the user's own systems and using stored data as input to internal models, including training, evaluation and backtesting. The same terms prohibit resale or redistribution of the raw feed. The provider's public Serie A page advertises a free tier and team-level football statistics including corners and cards.

However, this is **not yet a cleared source for the original frozen V2**:

1. The provider's official documentation conflicts on the Free-plan availability of `GET /v1/matches/{id}/statistics`: the 2026-11-11 changelog says it became Free, the Serie A FAQ says the route is Free (with expected goals excluded), but the current plan matrix still labels the endpoint Edge.
2. The global pricing page says Free includes the current and most-recent season, while the Serie A page says Free covers only the current season.
3. Published Serie A team-stat coverage is 4,210 / 4,591 finished matches (91.7%) across the provider's measured archive, not a current-2026/27 per-fixture completeness result.
4. The upstream provider/field-rights chain and the meaning of per-match first-observed/correction timestamps are not independently established.
5. No authenticated Free response was examined. No account, key, API call or download was made.

The audit therefore records a **conditional candidate, not permission to integrate**.

## Provider terms and data rights

The [official Terms of Service](https://bigballsdata.com/legal/terms), effective 2026-08-10, state:

- API responses may be stored in the user's own systems and kept there.
- Stored data may be used as input to internal models, including training, evaluation and backtesting.
- Derived models, scores, predictions and aggregates may be retained/published by the user.
- Raw data may not be resold or republished as an API, file, feed, export or bulk dataset.

This is a promising written provider-level grant for **private research storage and internal model use**. It is not permission to publish the raw archive. The terms describe data as belonging to the provider or providers it licenses from, but the reviewed public terms do not identify the upstream provider or document field-level rights for each required statistic. The terms also do not separately explain raw-archive retention if an account is later closed. Those points remain for written clarification before integration.

The project must keep any future raw archive private. No GitHub artifact containing raw source bytes may be uploaded while the repository is public.

## Free-plan scope and documentation conflicts

The public global pricing page advertises:

- $0 Free tier;
- 1,000 requests/day (2,000 with a linked GitHub account);
- 100 requests/minute;
- current plus most-recent season;
- scores, standings and statistics.

The dedicated [Serie A page](https://bigballsdata.com/serie-a-api) instead says Free covers the current season. Its plan matrix currently labels advanced match statistics as Edge, while its FAQ says `/v1/matches/{id}/statistics` is Free (the `expected_goals` field is Solo+). The [2026-11-11 changelog](https://bigballsdata.com/whats-new) says this statistics endpoint was made available on Free.

These official first-party pages are inconsistent. No plan entitlement should be inferred from the most permissive statement. The exact Free-plan entitlement for the match-statistics endpoint and its season depth must be confirmed before any account or request is made.

Free odds are not available; odds require the paid Edge plan. This audit does not propose using provider odds. The original `active_lambda=0` remains the existing market anchor, and `shadow_lambda=1` remains research-only.

## Coverage and the unchanged 19-feature contract

The provider's Serie A page reports 4,210 of 4,591 finished matches with team statistics, or approximately 91.7%, across its measured archive. This is not broken down by season, fixture, or required field. The coverage page's last published refresh is 2026-11-06.

The public soccer field catalogue lists corners, yellow cards and red cards among team-level statistics. The Serie A page says match statistics are available, but it does not publish a current-season, per-field completeness matrix. Therefore no claim of exact original 19-feature parity is justified.

The unchanged original V2 feature families require:

- points and goals derived from completed match results;
- corners for and against over the original 5/10-match and venue-5 windows;
- yellow-card and red-card counts over the original 5/10-match windows.

No substitute feature, reweighting, imputer/scaler change or candidate modification is proposed. The frozen candidate remains pinned to the exact SHA below.

## Source-before-quote, raw preservation and SHA

The provider's soccer guide says freshness differs by dataset, response source/update metadata should be read when present, and completed results/player rows can be corrected after full time. The reviewed docs do not define a per-match first-observed timestamp or a per-field correction history.

If rights and Free-plan coverage are later confirmed, the only acceptable research capture would preserve, for every response:

1. exact response-body bytes;
2. canonical match ID, season, endpoint path and non-secret query parameters;
3. response headers and any provider source/update/confidence metadata;
4. local receipt timestamp in UTC;
5. SHA-256 of the exact body bytes;
6. a private immutable manifest linking the response to its receipt time.

A later quote may be considered only if the verified source archive's receipt/upload time is strictly earlier than the quote observation time, and the quote row's own persisted timestamp is before kickoff. This proves that the project possessed those exact bytes before the quote; it does **not** prove when the upstream provider first observed every field.

No API request or source capture occurred in this audit.

## Frozen candidate — unchanged

- Experiment: `MARKET_ANCHOR_1X2_V2`
- Candidate SHA-256: `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`
- Training fingerprint: `f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098`
- Training rows: 3,799
- Features: exact ordered 19
- Original weights: 20 × 2
- `active_lambda=0`
- `shadow_residual_lambda=1`
- Historical stability gate: FAILED
- Automatic promotion: false

No retraining, refit, threshold tuning, candidate change or production `.pkl` modification is authorized by this audit.

## Required clearance before reconsideration

1. Written confirmation that the Free plan selected for this account includes the Serie A match-statistics endpoint and the required season depth.
2. A provider-supplied or account-authorized sample response showing the exact fields for corners, yellow cards, red cards, final scores and canonical IDs, with no paid endpoint.
3. Current-season per-fixture and per-field completeness evidence for 2026/27.
4. Written clarification of the upstream sources/rights covering all required fields and the provider's authority to grant private retention and internal model use.
5. Explicit confirmation of raw-response retention if the account or Free plan later ends.
6. Documented source/update timestamp and correction semantics, plus a private archive design with receipt UTC and SHA-256.
7. Separate owner authorization before any account, key, API call or source capture.

## Official documents reviewed

- [Terms of Service](https://bigballsdata.com/legal/terms)
- [Global pricing](https://bigballsdata.com/)
- [Serie A API and plan matrix](https://bigballsdata.com/serie-a-api)
- [Soccer guide: freshness, corrections and timestamps](https://bigballsdata.com/docs/soccer)
- [Endpoint reference](https://bigballsdata.com/docs/endpoints)
- [Coverage](https://bigballsdata.com/coverage)
- [Changelog](https://bigballsdata.com/whats-new)

**Bottom line:** Big Balls Sports Data is a credible new Free-plan candidate because its published terms expressly allow private response storage and internal model research. It remains **HOLD_NO_INTEGRATION** until the Free-plan/statistics contradictions, current-season field coverage, upstream rights and timestamp semantics are resolved. No provider access or model operation is authorized by this audit.
