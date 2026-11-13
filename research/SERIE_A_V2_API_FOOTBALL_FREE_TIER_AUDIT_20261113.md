# API-Football free-tier audit for original MARKET_ANCHOR_1X2_V2 — 2026-11-13

## Decision

**HOLD — not approved for current-form source capture or inference.** This is a documentation-only review. No account or API key was created and no endpoint was called.

## What the official pages establish

- The official pricing page advertises the Free plan at $0 with 100 requests/day and lists fixtures, events, statistics and pre-match odds among the available API families.
- The provider's own article dated **2026-10-26** states that, in 2026, Free-plan season access is restricted to **Year-4 through Year-2**, explicitly giving **2022, 2023 and 2024** as the available years. The required current-form cohort is **2026/27**, so this free tier does not supply the needed season.
- The official terms say the data comes from partners and prohibit reselling the provider's data. They describe using the service to build apps, websites and fantasy projects, but the reviewed terms do not expressly grant internal ML training, frozen-feature inference, or private retention of raw provider responses. This is an absence of an explicit grant, not a legal conclusion that all such use is prohibited.
- The public product pages list statistics and events, but the reviewed material does not establish complete Serie A coverage for every original V2 field, especially the exact 19-feature mapping and per-field upstream observation/correction timestamps.

## Why this cannot unblock V2

The current-form contract requires lawful lagged 2026/27 statistics, a private immutable raw-source archive, a SHA-verified source artifact and parent run, and proof that source capture completed strictly before the bookmaker quote. API-Football's documented Free season window excludes 2026/27. Rights, raw-retention scope, exact Serie A field completeness and source-clock semantics are also not established.

The 100-request daily allowance does not remedy the missing season. No request-volume estimate is used to imply feasibility.

## Required evidence before reconsideration

1. Provider confirmation that the intended internal research, feature derivation and inference are allowed.
2. Explicit raw-response retention and private-archive permission, including retention after account closure.
3. An authenticated coverage response or provider-written statement confirming Serie A 2026/27 availability and all 19 frozen feature inputs.
4. A documented per-match source observation/correction clock, or a provider-approved immutable capture procedure that is sufficient for the project's source-before-quote rule.
5. A private storage destination. The public repository and public Actions artifacts are not acceptable for raw provider responses.

## Frozen V2 invariants

The original candidate remains SHA-256 `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, with 19 features, 20×2 weights, 3,799 training rows, training fingerprint `f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098`, `active_lambda=0`, and `shadow_residual_lambda=1`. The stability gate remains failed, NO_BET and automatic-promotion prohibition remain in force, and the 30-primary-completed-prospective-event target-outcome gate is unchanged.

No source/quote request, Supabase query or write, target-outcome read, feature build, live inference, training/refit, production artifact change, workflow schedule change or main update was performed.
