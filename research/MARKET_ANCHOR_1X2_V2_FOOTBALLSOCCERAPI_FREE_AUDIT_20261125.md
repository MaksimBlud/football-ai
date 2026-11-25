# MARKET_ANCHOR_1X2_V2 — Football Soccer API free-tier audit

**Decision: `HOLD_FREE_TIER_NO_HISTORICAL_STATISTICS_AND_ENDPOINT_CONFLICT`.**

Reviewed 2026-11-25 from the provider's public documentation only. This is an offline rights/coverage audit for the original frozen Serie A `MARKET_ANCHOR_1X2_V2`. No account or key was created; no API request, source download, Supabase access, feature build, inference, or protected-outcome read occurred.

## What the current Free plan actually says

The current pricing and account/free-key pages describe a $0 plan with no card, 50 calls/day and 60/minute. It reads **yesterday only, as one complete UTC day**. The free-key page explicitly holds back everything before yesterday, statistics, events, tables, form, head-to-head, odds and fixtures ahead. The $49/month Archive plan adds ten seasons of history, statistics and exchange prices. That paid plan is excluded by the project constraints.

Sources:
- [Pricing](https://footballsoccerapi.com/pricing)
- [Current free-key scope](https://footballsoccerapi.com/account)

## Official documentation conflict

The [Match detail](https://footballsoccerapi.com/documentation/match) page labels `GET /v1/matches/{id}` as Free and says its `team_figures` can contain xG, shots, shots on target, corners, fouls, yellow/red cards and possession.

However:
- the current [pricing page](https://footballsoccerapi.com/pricing) says Free has no statistics;
- the current [free-key page](https://footballsoccerapi.com/account) says statistics are held back;
- the dedicated [Match statistics](https://footballsoccerapi.com/documentation/match-statistics) endpoint explicitly requires Archive.

This is a material entitlement conflict. No assumption is made that the match-detail response exposes statistics to a Free key. No live request was made to resolve it.

## Rights are comparatively clear

The [Acceptable Use Policy](https://footballsoccerapi.com/acceptable-use), last updated 2026-09-05, expressly allows building applications, dashboards, models, research and content; storing what is needed in one's own systems; and retaining it after cancellation. The [Terms of Service](https://footballsoccerapi.com/terms), last updated 2026-10-27, also allow use in one's own work/apps/sites, including commercial use, while prohibiting bulk resale, redistribution, republishing, or downloading the archive to rebuild a competing database.

Those terms make the provider more promising for private research than several previously reviewed providers: private raw response retention and retention after cancellation are explicitly permitted by the acceptable-use policy. They do **not** solve the Free-tier data-availability problem.

## Why the Free plan cannot feed the frozen 19-feature candidate

The candidate needs rolling 5-match and 10-match team history, including points, goals for/against, corners for/against, yellow/red cards, and venue-specific goal/corner history. A Free feed restricted to yesterday cannot supply the prior 5/10 matches for both teams. The dedicated statistics endpoint is Archive-only, while the one-match endpoint's statistics entitlement conflicts with the current pricing/free-key pages.

The provider's public docs also do not establish a per-match first-observed timestamp or per-field correction history. A future private capture could prove when this project possessed exact response bytes (local UTC receipt time + SHA-256) and that the archive preceded a later quote; it would not prove the provider's upstream first-observation time.

## Binding decision

- **HOLD**: no account/key creation, API call, capture, source integration, feature build, or inference.
- Do not buy Archive or Live.
- Do not treat the Match detail page's `team_figures` wording as Free entitlement while it conflicts with the pricing/free-key pages.
- Reconsider only if the provider confirms in writing that the Free plan exposes complete Serie A match statistics and sufficient historical depth for the frozen rolling 5/10 features, and documents the actual endpoint/field coverage.
- If later authorized, capture exact raw response bytes privately, record offset-aware UTC receipt time and SHA-256, bind source match/team identity, and require the source archive to precede the later target quote. Missing fields remain missing; no zero-fill or imputation is introduced here.
- Keep the original candidate SHA, 19-feature order, weights, scaler/imputer, training fingerprint, `active_lambda=0`, `shadow_lambda=1`, failed historical stability gate and closed 30-primary-completed-event outcome gate unchanged.

## Frozen candidate

- Experiment: `MARKET_ANCHOR_1X2_V2`
- Candidate SHA-256: `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`
- Features: 19; weight matrix: 20×2
- `active_lambda=0` (market); `shadow_lambda=1` (research only)
- Historical stability: FAILED; prospective outcome gate: CLOSED (0/30)

No model-quality conclusion follows from this provider audit.

## Non-actions

No account/key, provider request, source download, Supabase read/write/DDL, raw-response capture, protected 2026/27 outcome read, feature calculation, inference, refit, threshold tuning, production `.pkl` change, model-contract change, paid call, schedule change, main update, merge, promotion or bet occurred.
