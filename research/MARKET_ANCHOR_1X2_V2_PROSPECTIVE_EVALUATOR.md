# Original MARKET_ANCHOR_1X2_V2: guarded prospective evaluator

## Scope

This is a pure, research-only scoring helper for the already-preregistered
`MARKET_ANCHOR_1X2_V2_CURRENT_FORM_FORWARD_ONLY` cohort. It does not change
the frozen candidate, its 19 features, weights, imputer/scaler, lambda contract,
parent protocol, production artifacts, or any workflow schedule.

The helper has no Supabase, network, filesystem, or model-loading code. It
accepts normalized forecast-only rows, a set of completed fixture identities,
and a lazy outcome-loader callback. The callback is never invoked until at
least 30 **unique eligible completed Serie A prospective forecasts** match the
metadata-only completed-fixture set. The completed-fixture set must be accompanied by an explicit digest-bound attestation for the frozen identity-only query contract: source table `public.league_finished_results`, exact columns `match_date, home_team, away_team`, Serie A 2026/27 date bounds, a fixed query-contract SHA-256, the UTC capture/cutoff date, unique identity count and identity-set SHA-256. The evaluator rejects unknown attestation fields, any score/result-column claim, digest/count mismatches, and fixture identities on or after the date-only cutoff. This is a structural caller contract, not a claim that the pure helper cryptographically proves which upstream SQL actually ran; the capture caller must build the attestation directly from the metadata-only response.

## Eligibility checks before the outcome gate

Every row must carry the upstream `SOURCE_ARCHIVE_AND_PARENT_RUN_VERIFIED_BEFORE_QUOTE` evidence marker and attest the exact frozen candidate SHA, original
`active_lambda=0`, research-only `shadow_residual_lambda=1`, NO_BET status,
primary league, source artifact SHA-256 and parent-run SHA, and the ordered
timestamps:

`source observation <= archive creation <= successful parent completion < quote time <= forecast capture < kickoff`.

The separate cohort is pinned to main commit `9df6f63db10e0128aff89c38fb8c6d88703ef8b8`, frozen at
`2026-10-18T08:15:32Z`. Every accepted quote must be strictly later than that
commit time; pre-contract quotes (including the saved October 13 observations)
are ineligible even if their timestamps otherwise look valid. The fixture date
must also fall inside the frozen 2026/27 season (`2026-07-01` through
`2027-06-30`). These are fixed contract boundaries, not tuned thresholds.

The source observation-to-quote and quote-to-capture intervals must each be
within the preregistered 24-hour limits. The market vector must exactly match
the active lambda-zero fallback within the original 1e-12 invariant. Market,
frozen-incumbent, and lambda-one shadow vectors are all required. The helper
never loads or executes the production incumbent; it requires its already
recorded probability vector as a comparator. Incumbent evidence must also
attest the same league, canonical match date/home/away identity, and exact UTC
kickoff as the V2 forecast; missing or mismatched identity fails before the
lazy outcome callback. If the incumbent vector is unavailable, evaluation
fails closed rather than silently substituting the market.

Outcome/score fields are forbidden recursively in forecast-only payloads. The evaluator also enforces an exact allowlist for normalized top-level forecast fields and nested incumbent evidence; unknown fields fail closed even when their spelling is not in the current outcome-alias denylist. Regression tests prove unknown fields are rejected before the lazy outcome callback can run.

Duplicate provider event IDs and duplicate canonical fixture identities are
rejected.

## Gate and scoring

Below 30 matched completed forecast identities, the helper returns
`OUTCOME_READ_GATE_CLOSED`, no metrics, and `target_outcomes_read=false`;
the outcome callback is not called.

Only after the gate opens is the callback invoked once for exactly the matched
fixture identity set. It must return exactly one H/D/A label per requested
identity and no extras. Metrics follow the original V2 research scoring
convention in `market_anchor_1x2_v1.score_probabilities`:
- multiclass Brier = mean over events of the sum of three squared one-hot errors;
- LogLoss = mean negative natural log of the probability assigned to the
  observed class.

The review signal is true only if lambda-one shadow Brier **and** LogLoss are
each lower than both the de-vigged market and the frozen production incumbent.
It is diagnostic only. There is no fitting, selection, threshold tuning,
promotion, product publication, or betting.

## Current blockers

There are two independent blockers; neither may be bypassed by substituting a
market vector or loading the legacy production model.

1. The current-form forward artifact does not yet emit a frozen-incumbent
   vector in its per-event preview. The evaluator requires that comparator as a
   separate, pre-existing vector.
2. The frozen policy names `FROZEN_PRODUCTION_INCUMBENT` but does not pin its
   exact model version and artifact SHA-256. Accordingly,
   `FROZEN_INCUMBENT_REFERENCE` remains unset and the evaluator returns
   `EVALUATION_BLOCKED_UNPINNED_INCUMBENT` without invoking the outcome
   callback, even if 30 eligible completed forecasts and a vector are supplied.
   Each row must also provide incumbent provenance (model version, artifact
   SHA-256, unique source-record ID, generation time, and history cutoff). The
   incumbent history cutoff must be no later than the authenticated V2 source
   observation, so the comparator cannot use historical information that was not
   available to the V2 source archive; it must also be no later than incumbent
   generation, and generation must be no later than the market quote. Legacy
   XGBoost incumbent evidence is rejected.

This is an additional fail-closed guard, not a change to the frozen model or
current cohort policy. Reopening the outcome gate requires a separately
approved prospective protocol amendment that pins a permitted, non-legacy
incumbent identity; do not silently edit the existing frozen policy in place.

No target outcome was read or scored while implementing or testing this
helper; all tests use synthetic forecasts/outcomes only.
