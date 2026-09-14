# POINT_IN_TIME_CROSS_LEAGUE_REPLAY_V1

Status: **AI PROBABILITY VECTORS FROZEN BEFORE OUTCOME READ**.

Research-only retrospective point-in-time replay. Existing MARKET_ONLY rows remain unchanged and are not relabeled as prospective AI evidence.

Frozen cohort: BUNDESLIGA 9, EREDIVISIE 9, LA_LIGA 10, LIGUE_1 9, SERIE_A 10; total 47 events. EPL is excluded and remains governed by EPL_AI_MARKET_PAIR_V1.

Frozen production artifact SHA-256: `1e516fe91420fdc2d6479e9fb92b005c4a0c75c7f0f217493dd6b27fd64d99a5`. Frozen model Git blob: `f8d9b2cd92ff5e8e550bb8c0de358f1d795d3327`. Frozen feature-formula blob: `3068d08c1e28523ca71f3218e8db3a1fef4b0c05`. Pre-capture source commit: `3ecb981080f724ec6f10c0c762f75bd535307ed3`.

History is rebuilt from the same Football-Data CSV family already used by repository research: D1, N1, SP1, F1 and I1, seasons 2016-2017 through 2026-2027. Current-season rows dated 2026-09-11 or later are rejected before result/stat values are converted into model history. Per-event history is filtered to the saved market snapshot with the existing conservative four-hour result-availability buffer. Later rows are never admitted to the feature state.

The replay is explicitly `RETROSPECTIVE_POINT_IN_TIME_REPLAY`, never prospective. No training, fitting, calibration, threshold search or league-specific retuning is allowed. The completed replay confirmed that all 47 home and away teams had historical state; neutral cold-start defaults were not used by any rescued event.

## Frozen evidence

The first successful outcome-blind reconstruction was GitHub Actions run `34856998454`, artifact id `10353432512`. At that point no outcome/settlement join had been performed.

- exact cohort inventory SHA-256: `1580ec1d361f97fd08040d0ebdfb78e922a9100180fe587f91b124e265f0d808`
- canonical 47 AI probability vectors SHA-256: `4a28ac7d728d6b9c394af7ec1c1b96d3fc41bae1f17e18c14d7be09594209d94`
- complete replay CSV SHA-256: `9c19001961b997d9b653d30f5cb660efbc7aeeecfe4069f9ef1de5aa522aef1e`
- replay manifest SHA-256: `3c878d70904c9811da69581d1caadf359405c28bf66dad6ecc30227dbc06defb`
- GitHub Actions artifact digest: `sha256:9fb205e602b87c3adffd799de8d7b0ba99a0e9eddd568c8f3cd9fb476db03faa`

The 47 exact H/D/A model probability vectors plus per-event feature hashes are committed at `experiments/point_in_time_cross_league_replay_v1_predictions.json`. `point_in_time_cross_league_replay_v1_freeze_guard.py` fails closed if the cohort, model, probability vectors, feature hashes, complete replay CSV or manifest drift from this freeze.

Historical state used by the replay ended no later than: Bundesliga 2026-09-06, Eredivisie 2026-09-09, La Liga 2026-09-07, Ligue 1 2026-09-06, Serie A 2026-09-07. There were zero duplicate event identities and zero cold-start teams in the final 47-event reconstruction.

## Evaluation rule — frozen before outcomes

Only after this freeze may a separate evaluator join outcomes for these 47 non-EPL replay events. The evaluator must not alter the replay probabilities or feature construction.

Primary pooled descriptive metrics are fixed to multiclass Brier, multiclass LogLoss and top-1 accuracy for AI and Market. Both delta Brier < 0 and delta LogLoss < 0 => EARLY_SIGNAL; both > 0 => WARNING; otherwise INCONCLUSIVE. No subgroup search, threshold tuning, optional stopping or betting decision is permitted.

The replay collector reads only prediction-ledger and odds-snapshot fields from Supabase. Finished-result and settlement tables are outside this collector. Production `.pkl` files are not modified.
