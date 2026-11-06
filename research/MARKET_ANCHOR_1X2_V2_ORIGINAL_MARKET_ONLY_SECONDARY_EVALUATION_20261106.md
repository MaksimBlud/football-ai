# Original MARKET_ANCHOR_1X2_V2 — secondary market-only evaluation

## Why this is separate

The original old-season-only forward workflow currently emits diagnostic rows with
eligible_for_frozen_prospective_cohort=false. The original contract also records
that no independent incumbent as-of prediction was captured. PR #701 is not a
substitute: its evaluator declares
MARKET_ANCHOR_1X2_V2_CURRENT_FORM_FORWARD_ONLY, a separate current-form cohort.

This proposal therefore adds a separate secondary analysis only. It does not
change the original V2 candidate, its 19 features, frozen weights, imputer,
scaler, active/shadow lambda semantics, stability gate, or original cohort
eligibility. It does not make any old row eligible under the original contract.

## Frozen comparison

- Candidate: a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6.
- Exactly the original 19-feature, 20x2 frozen candidate.
- active_lambda=0: active output remains the exact de-vigged market.
- shadow_residual_lambda=1: research-only residual comparison.
- Comparator: de-vigged 1X2 market only. No incumbent model or legacy XGBoost inference.
- Primary cohort: Serie A 2026/27 only.
- One forecast per canonical fixture: earliest source-verified pre-kickoff capture.
- No selection by outcome, market price, or observed performance.

## Two independent gates

Before target outcomes can be requested, both conditions must hold:

1. At least 30 completed primary Serie A fixture identities, attested using only
   match_date, home_team, away_team from public.league_finished_results.
2. At least 30 unique source-verified original-V2 secondary forecasts whose
   fixtures are in that completed identity set.

The first gate is the original 30-completed-primary-event protection. The second
is a stricter minimum sample-size guard for this separate market-only analysis.
If either gate is closed, the evaluator returns without invoking the lazy
outcome loader.

## Source-before-quote chain

The pure evaluator accepts only caller-authenticated GitHub artifact metadata:
- exact original forward artifact name and workflow path;
- exact successful main forward parent run;
- exact free source artifact name and source workflow path;
- exact successful main source parent run;
- independently verified ZIP SHA-256 values;
- source artifact creation and source workflow completion strictly before the
  saved market quote;
- source loader, source-rights helper, and rights-manifest blob SHA pins;
- exact candidate SHA, quote time, feature-history cutoff, and kickoff.

The module itself is pure and has no GitHub, Supabase, filesystem, or network
client. A future read-only runner must authenticate the GitHub metadata and ZIP
bytes before calling it, and must call the source-rights guard before any
external reads.

## Metrics and limits

After both gates, the lazy outcome loader may return only the exact selected
fixture identities. The evaluator reports market and shadow multiclass Brier
and LogLoss, paired 10,000-resample bootstrap intervals, and the probability
that the shadow loss is lower for each metric. It never emits individual
outcomes, bets, product predictions, or a promotion decision.

This is explicitly not the original frozen prospective cohort and cannot
satisfy or replace the original protocol. No claim of superiority is permitted
from this secondary analysis. The original model contract remains unchanged.
