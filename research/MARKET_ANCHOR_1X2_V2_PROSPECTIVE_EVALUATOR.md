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
metadata-only completed-fixture set. The completed-fixture set must be accompanied by an explicit digest-bound attestation for the frozen identity-only query contract: source table `public.league_finished_results`, exact columns `match_date, home_team, away_team`, Serie A 2026/27 date bounds, a fixed query-contract SHA-256, the UTC capture/cutoff date, unique identity count and identity-set SHA-256. The evaluator rejects unknown attestation fields, any score/result-column claim, digest/count mismatches, and fixture identities on or after the date-only cutoff. This is a structural caller contract, not a claim that the pure helper cryptographically proves which upstream SQL actually ran; the capture caller must build the attestation directly from the metadata-only response. The production-facing `read_completed_fixture_gate(client)` samples the current UTC clock internally; callers cannot inject a backdated or future cutoff. Its private timestamp-controlled helper exists only for deterministic offline tests.

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
the active lambda-zero fallback within the original 1e-12 invariant. For the
full three-way path, market, frozen-incumbent, and lambda-one shadow vectors are
all required. The full path never loads or executes the production incumbent;
it requires its already recorded probability vector as a comparator. The
separate market-only diagnostic deliberately accepts no incumbent vector or
evidence and compares only the de-vigged market against the original V2 shadow.
Incumbent evidence for the full path must also attest the same league, canonical
match date/home/away identity, and exact UTC kickoff as the V2 forecast; missing
or mismatched identity fails before the lazy outcome callback. If the incumbent
vector is unavailable, the full three-way path fails closed rather than
silently substituting the market; callers must explicitly choose the separately
named market-only diagnostic when no incumbent is pinned.

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

After the outcome gate opens, the evaluator also reports supplementary paired
fixture-level nonparametric bootstrap summaries for the shadow-minus-market
and shadow-minus-incumbent loss differences, separately for Brier and LogLoss.
Each of the four summaries uses 10,000 resamples with replacement from the
paired per-fixture loss differences, percentile 95% intervals, and fixed
integer seeds recorded in the output. The reported fraction of bootstrap means
below zero is only a descriptive resample frequency; it is not a p-value or
posterior probability. These intervals are supplementary only: they do not
change the 30-event gate, the frozen point-mean review signal, any model
parameter, or any promotion decision. This method was added before any
prospective target outcomes were read.

The review signal is true only if lambda-one shadow Brier **and** LogLoss are
each lower than both the de-vigged market and the frozen production incumbent.
It is diagnostic only. There is no fitting, selection, threshold tuning,
promotion, product publication, or betting.

## Supplementary market-only diagnostic

The full `evaluate_after_gate()` path remains unchanged: it requires a separately
pinned non-legacy incumbent and will not invoke the outcome callback without
that comparator. The frozen review signal still requires lambda-one shadow
Brier **and** LogLoss to beat both the de-vigged market and that incumbent.

A separate `evaluate_market_only_after_gate()` diagnostic is added for the
specific market-comparison question while no admissible incumbent is pinned.
It uses the **same** 30-unique-eligible-completed-prospective-forecast gate,
the same identity-only Supabase attestation, the same source/quote/kickoff
eligibility checks, and the same H/D/A scoring convention. It compares only
the exact de-vigged market vector (`active_lambda=0`) with the frozen
lambda-one V2 research shadow. It accepts no unpinned incumbent vector or
evidence and never substitutes another model.

After the 30-event gate opens, this supplementary path reports market and
shadow Brier/LogLoss plus paired fixture-level bootstrap summaries. It always
returns `review_signal=false`, marks the full three-way comparison unavailable,
and cannot promote, publish, bet, alter weights, or change the original V2
contract. Below 30 eligible completed forecasts it returns no metrics and does
not invoke the lazy outcome callback. This diagnostic is supplementary; it
does not amend the frozen policy's three-way review requirement.

The method and its tests are committed before any prospective target outcomes
are read. Synthetic tests are not live performance evidence.

## Exact lazy Supabase outcome reader

For the supplementary market-only path, live callers may use
`evaluate_live_market_only_from_supabase(client, forecast_rows)`. It obtains
the same current UTC identity-only gate first, then passes a closure to the
pure evaluator. Below 30 eligible completed prospective forecasts, the closure
is never called and no result column is selected.

Only after the gate opens does the closure query the exact requested fixture
identities one at a time, selecting exactly
`match_date,home_team,away_team,result,persisted_at_utc` from the Serie A
2026/27 table. For each row, `persisted_at_utc` must be a valid ISO-8601
timestamp with an explicit UTC offset and must be strictly later than that
forecast's frozen `kickoff_utc`; a timestamp at or before kickoff, or one
without an explicit offset, fails closed. The persistence timestamp is used
only as post-kickoff outcome provenance, not as a model feature or selection
input. The reader does not select goal totals, scores, or unrelated fixtures.
It canonicalizes the existing Serie A aliases (including Atalanta BC), accepts
duplicate raw aliases only when their H/D/A labels agree, and rejects missing,
conflicting, malformed, or identity-mismatched rows. It is read-only and
returns exactly the identity-to-H/D/A mapping expected by the evaluator.

Synthetic integration tests prove that 29 eligible completed forecasts cause
zero result queries, while 30 cause exact identity+result-only queries and
never a score/goals selection. These tests are not live outcome evidence.

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


## Safe live orchestration entry point

The live market-only workflow calls
`evaluate_live_market_only_from_supabase(client, source_candidates, token=...)`
from `market_anchor_1x2_v2_prospective_runner.py`. It does not accept a
caller-supplied preflight callback, source-SHA map, completed-fixture set,
gate attestation, or result reader. The runner checks provider inference rights
and private artifact storage before inspecting candidate input.

The runner obtains the production identity-only completed-fixture gate,
validates its digest-bound attestation, and internally re-verifies every
captured source candidate against GitHub artifact metadata, embedded source ZIP
bytes, parent workflow/run SHA, source manifest, feature-gate attestation and
source-before-quote ordering. Only after all candidates pass does it apply the
frozen earliest-eligible-per-fixture selection policy. The separate
`evaluate_live_prospective_cohort()` full three-way path uses the same
runner-owned source verifier and remains blocked while the non-legacy incumbent
reference is unpinned.

The market-only Supabase result reader is a nested closure, not an importable
module-level helper. It is invoked only by the pure evaluator after the
preregistered completed-primary metadata gate and the separate 30-eligible-
completed-forecast gate pass. It queries only the exact selected fixture
identities and the allowlisted result/persistence columns. A future observation
clock, missing source proof, mismatched SHA, unresolved rights, public artifact
repository or fewer than 30 eligible completed forecasts fails closed before
the first target-result query. All tests use synthetic data; no live result is
read during validation.


## Real forward-artifact bridge and live market-only evaluation

The current-form forward workflow writes a GitHub Actions artifact named
`serie-a-v2-current-form-forward-preview`. The prospective evaluator has a
separate read-only bridge for that exact artifact schema.

- It accepts only a completed, successful main run of the exact
  `.github/workflows/serie-a-v2-current-form-forward-preview.yml` workflow.
- It verifies the forward ZIP against the GitHub artifact SHA-256 and validates
  the run ID, head SHA, workflow path, branch, event and artifact time.
- It maps nested `v2_preview` and `source_artifacts_used` fields to the strict
  normalized schema, including source parent run ID, SHA and completion time.
- The `odds_snapshots` source has `commence_time_utc` but no `match_date`.
  The adapter derives the date-only fixture identity from the UTC kickoff date.
  If this identity does not match the metadata-only completed-fixture gate,
  the event does not count; there is no team/date guessing fallback.
- Before frozen selection, the runner rechecks every candidate's source artifact
  metadata, embedded source ZIP SHA-256, successful source parent run, source
  manifest and current-form gate freshness relative to each quote time. The
  current Supabase gate query remains identity-only: `match_date, home_team,
  away_team`.
- No caller-supplied preflight callback or self-reported SHA map is accepted.
  Source verification is runner-owned and covers all captured candidates
  before the frozen earliest-eligible selection policy is applied. Invalid or
  conflicting source references fail the entire evaluation before any target
  result query.
- Repeated forward artifacts can contain multiple quotes for one fixture. The
  separate frozen selection policy in
  `experiments/market_anchor_1x2_v2_prospective_selection_policy.json` selects
  the earliest eligible forecast capture per canonical fixture. Equal capture
  timestamps fail closed; one provider event ID mapping to two fixture
  identities also fails closed. This rule is outcome-independent and
  performance-independent and does not change the 30-event gate.
- The live workflow runs only after a successful main current-form forward run
  or an explicit manual dispatch on main. It has no schedule, makes no odds
  provider calls, writes nothing to Supabase and archives only metrics and
  provenance summaries, never raw outcomes.

The market-only path uses two distinct frozen gates. First, the runner reads
only completed-fixture identities (date and team names) and validates the
preregistered 30-primary-completed-event metadata gate; no score or result
column is selected. It then verifies source archives and applies the frozen
selection policy. Second, the pure evaluator requires 30 unique eligible
completed prospective forecasts intersecting that identity set. Only then can
the nested reader select exact H/D/A outcomes and their persistence timestamps.
Below either gate, the target-result reader is never invoked. The output is a
market-versus-original-V2-shadow Brier and LogLoss diagnostic; it cannot emit a
promotion decision.

The separate three-way review path remains blocked while no approved,
non-legacy frozen incumbent reference is pinned. This does not block the
market-only comparison requested for the original V2; the market-only path
does not fabricate an incumbent and does not revive the former XGBoost model.

No live outcomes were read during implementation. This is code/test readiness
only; actual market evaluation still requires eligible main-branch forward
artifacts with verified source archives and 30 completed primary forecast
events.


## Current source-rights and private-storage blockers — 2026-11-12

The evaluator is stacked on the integrated source-rights/privacy pipeline. These
permissions are intentionally separate:

- The current Football-Data manifest is pinned to the official data page updated 2026-11-10 and records `research_source_capture_permitted=false`, `research_inference_permitted=false`, `provider_issued_ai_inference_license=false`, and the scopes `NONE_PENDING_PROVIDER_CLARIFICATION` / `NONE_PENDING_SCOPE_CLARIFICATION`.
- The previous 2026-11-07 source-only archival allowance was withdrawn internally after the updated policy wording. The two-session rolling-seven-day limit is a ceiling, not authorization.
- Therefore automated Football-Data source capture and frozen-model inference remain fail-closed pending explicit provider clarification or an applicable written licence. This is the project's conservative rights classification, not a legal conclusion about every form of manual personal research.
- Private GitHub Actions storage is a separate requirement. The privacy helper
  rejects a public repository before source/forward artifact discovery or
  download; SHA-256 integrity does not provide confidentiality.

The CLI checks the inference-rights manifest before constructing a Supabase
client. The live bridge repeats the inference-rights check inside
`run_live_evaluation()` as defense in depth, then checks private storage before
listing forward artifacts. The market-only evaluator remains lazy: it first
reads only the frozen completed-fixture identity metadata, verifies the
source-before-quote evidence, and does not invoke the H/D/A outcome callback
until both the preregistered 30-primary-completed-event gate and the
30-eligible-completed-forecast gate pass.

The old evaluator branch's conditional-inference test is intentionally
replaced with a fail-closed assertion against the current integrated manifest.
No protected 2026/27 outcomes were read in this integration; all evaluator
and runner tests use synthetic data.


## Market-only evaluation and current rights-stack rebase — 2026-11-12

The separately named `evaluate_market_only_after_gate()` path is the appropriate preregistered comparison when no frozen incumbent artifact identity has been approved. It accepts only the de-vigged market vector and original V2 lambda-one shadow vector, rejects incumbent evidence, and preserves the same 30-unique-eligible-completed-primary-forecast gate. Below 30, the lazy H/D/A loader is not called. At or above 30, it reports multiclass Brier and LogLoss plus paired fixture-level 10,000-resample percentile summaries. The bootstrap fraction is descriptive, not a p-value; the market-only path always keeps `review_signal=false`, NO_BET, and no promotion.

The full three-way market/incumbent/shadow review remains blocked until a separately approved non-legacy incumbent version and artifact SHA are pinned. No XGBoost model is restored or substituted.

This evaluator port is based on the exact direct-access rights stack from PR #787 at `272a0dc2d6a97fedc7964e8cc2614ba670220fae`, rather than the stale #727-only branch. The current source-rights manifest remains deny-by-default, the repository remains public, and PR #781 still holds live source/quote workflows. This rebase adds no source permission and does not enable live inference. Validation is offline/synthetic only; no Supabase, source archive, quote, or target outcome is read by CI.
