# POINT_IN_TIME_CROSS_LEAGUE_REPLAY_V1

Research-only retrospective point-in-time replay. Existing MARKET_ONLY rows remain unchanged and are not relabeled as prospective AI evidence.

Frozen cohort before outcome evaluation: BUNDESLIGA 9, EREDIVISIE 9, LA_LIGA 10, LIGUE_1 9, SERIE_A 10; total 47 events. EPL is excluded and remains governed by EPL_AI_MARKET_PAIR_V1.

Frozen production artifact SHA-256: `1e516fe91420fdc2d6479e9fb92b005c4a0c75c7f0f217493dd6b27fd64d99a5`. Frozen model Git blob: `f8d9b2cd92ff5e8e550bb8c0de358f1d795d3327`. Frozen feature-formula blob: `3068d08c1e28523ca71f3218e8db3a1fef4b0c05`. Pre-capture source commit: `3ecb981080f724ec6f10c0c762f75bd535307ed3`.

History is rebuilt from the same Football-Data CSV family already used by repository research: D1, N1, SP1, F1 and I1, seasons 2016-2017 through 2026-2027. Current-season rows dated 2026-09-11 or later are rejected before result/stat values are converted into model history. Per-event history is filtered to the saved market snapshot with the existing conservative four-hour result-availability buffer. Later rows are never admitted to the feature state.

The replay is explicitly `RETROSPECTIVE_POINT_IN_TIME_REPLAY`, never prospective. No training, fitting, calibration, threshold search or league-specific retuning is allowed. Neutral cold-start behavior follows production for teams without prior top-flight history in the reconstructed horizon.

Before any outcome join, the replay freezes exact AI H/D/A probabilities, exact market probabilities, all model feature values, history SHA-256, feature SHA-256, model SHA-256 and cohort inventory SHA-256.

Later evaluation is fixed to pooled multiclass Brier, LogLoss and top-1 accuracy for AI and Market. Both delta Brier < 0 and delta LogLoss < 0 => EARLY_SIGNAL; both > 0 => WARNING; otherwise INCONCLUSIVE. No subgroup search, threshold tuning or optional stopping.

The replay collector reads only prediction-ledger and odds-snapshot fields from Supabase. Finished-result and settlement tables are outside this collector. Production `.pkl` files are not modified.
