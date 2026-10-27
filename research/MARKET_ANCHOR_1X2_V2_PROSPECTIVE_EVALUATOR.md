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
metadata-only completed-fixture set. The completed-fixture set must come from
a read-only query selecting only `match_date, home_team, away_team`; it must
not contain scores or results.

## Eligibility checks before the outcome gate

Every row must carry the upstream `SOURCE_ARCHIVE_AND_PARENT_RUN_VERIFIED_BEFORE_QUOTE` evidence marker and attest the exact frozen candidate SHA, original
`active_lambda=0`, research-only `shadow_residual_lambda=1`, NO_BET status,
primary league, source artifact SHA-256 and parent-run SHA, and the ordered
timestamps:

`source observation <= archive creation <= successful parent completion < quote time <= forecast capture < kickoff`.

The source observation-to-quote and quote-to-capture intervals must each be
within the preregistered 24-hour limits. The market vector must exactly match
the active lambda-zero fallback within the original 1e-12 invariant. Market,
frozen-incumbent, and lambda-one shadow vectors are all required. The helper
never loads or executes the production incumbent; it requires its already
recorded probability vector as a comparator. If that vector is unavailable,
evaluation fails closed rather than silently substituting the market.

Outcome/score fields are forbidden recursively in forecast-only payloads.
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

## Current blocker

The existing current-form forward artifact currently emits the market and
lambda-one shadow vectors, but does not include the frozen-incumbent vector in
its per-event preview. This evaluator deliberately requires that third
pre-existing vector; it does not revive or load the legacy model. Until the
incumbent vector is independently available from a valid pre-match record, the
prospective comparison cannot complete even after 30 events. No target outcome
was read or scored while implementing or testing this helper; all tests use
synthetic forecasts/outcomes only.
