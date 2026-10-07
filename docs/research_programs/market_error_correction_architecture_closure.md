# Market-error correction architecture — terminal duplicate and eligibility audit

Status: **PROGRAM_DONE / RESEARCH ONLY / NO_BET**.

## Roadmap question

Direction 4 asked for a model that predicts a correction to bookmaker 1X2
probabilities instead of forecasting 1X2 from scratch, using only feature
families that had already earned independent support. Zero correction had to be
the exact fallback and evaluation required a separate untouched OOS gate.

## Architecture duplicate audit

The repository already contains that architecture:

- `MARKET_ANCHOR_1X2_V1` defines
  `p = softmax(log(m) + lambda * r(x))`, where `m` is the de-vigged market
  distribution, `r(x)` is a football-only residual, and `lambda=0` is exact
  market identity.
- V1 selected only on 2024/25 and evaluated once on untouched 2025/26. Its
  pooled deltas were slightly favorable (Brier `-0.000338`, LogLoss
  `-0.000386`), but the corrected robustness intervals crossed zero
  (Brier `[-0.005165,+0.003237]`; LogLoss
  `[-0.008069,+0.006039]`) and the fixed configuration won both metrics in
  only `2/6` earlier seasons.
- `MARKET_ANCHOR_1X2_V2` consequently freezes `ACTIVE_LAMBDA=0.0`; the
  non-zero residual remains shadow-only.
- La Liga POWER Anchor V3 tested the same football residual over a stronger
  fixed market prior and did not establish a production-worthy incremental
  win. Conditional Residual V4's validation-only improvement reversed on the
  untouched test. Multi-Market V5 changed the information set rather than
  proving a football residual, and Incremental Robustness V9 attributed the
  durable signal to market-state geometry rather than new football information.

A fresh correction-model child would therefore repeat a materially equivalent
architecture on already-opened feature families.

## Supported-feature eligibility audit

The roadmap permits only football feature families that independently earned
stable information beyond the market:

- Direction 1, Issue #562: process-vs-results divergence harmed untouched-test
  probability quality; test LogLoss delta `+0.005204`, with 95% CI
  `[+0.000346,+0.010104]`.
- Direction 2: manager, lineup, availability and tactical changes lack a
  timestamp-safe zero-cost historical source; generic process proxies are
  already tested and are not valid substitutes.
- Direction 3, Issue #568: the independent Understat tactical-pressure estimate
  passed source/support gates but was worse than market on validation and
  untouched test. Test LogLoss delta was `+0.090703`, Brier delta
  `+0.064621`, bootstrap 95% CI `[+0.052615,+0.130185]`, and all five
  leagues were worse.
- Earlier football-only form, goals, corners, shot and trajectory families did
  not establish stable market-incremental support. Football-only predictive
  quality is not enough to satisfy this prerequisite.

No admissible non-zero correction input remains.

## Terminal decision

Do not create a duplicate Issue or rerun the market-anchor family. The binding
answer is exact zero correction: use the market distribution unless a genuinely
new timestamp-safe football family first earns stable independent support on a
separate untouched OOS gate.

Reopening requires one of:

1. a new zero-cost point-in-time football source with a mechanistically distinct
   feature family and independent untouched-OOS support beyond market; or
2. fresh explicit user approval for otherwise unavailable data.

This decision does not authorize betting, production promotion, Supabase writes,
paid data, or production `.pkl` changes.
