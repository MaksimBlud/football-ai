# Turkey / Portugal Structural V2 Calibration V1 — Status

Status: **HISTORICAL OOS EVALUATED / RESEARCH-ONLY / NO RUNTIME ACTIVATION**

The frozen protocol is `research/turkey_portugal_structural_v2_calibration_v1.json`. The durable result record is `research/turkey_portugal_structural_v2_calibration_v1_result.json`.

The research was run independently for `TURKEY_SUPER_LIG` and `PRIMEIRA_LIGA`. No final parameters from EPL or any other league were copied and no cross-league pooling was used.

Historical source readiness used completed seasons 2016/17 through 2025/26. The frozen 1X2 market source for both leagues was BET365 (`B365H/B365D/B365A`) converted to no-vig probabilities. Current season 2026/27 remained excluded.

The permitted post-preregistration evaluation completed successfully in GitHub Actions run `33965220775` on main commit `385331fcb1799749fd053e9dc67393c9a35db9e4`. The result artifact was `turkey-portugal-structural-v2-evaluation`, artifact id `9969216176`, digest `sha256:2fc4f5f5dd4f8d95466cfafb4b37b5f6e5c1ce89276abff756f9ced3ce2b29b5`.

## Turkey Super Lig

The frozen nested season walk-forward produced `HISTORICAL_OOS_SIGNAL_OBSERVED` over 1,716 outer-test rows.

- weighted logloss delta vs market: `-0.0010542716010495574`
- weighted Brier delta vs market: `-0.0004530200963225977`
- weighted accuracy delta: `0.0`
- market argmax changes: `0`
- structural candidate selected in all 5 outer folds
- both logloss and Brier improved in 4 of 5 outer seasons; 2025/26 was slightly worse on both metrics

This is evidence of a small historical OOS probability-quality signal, not an activation decision. The selected candidate varied across outer folds, so there is no single production parameter pair established by this result.

## Primeira Liga

The frozen nested season walk-forward produced `CALIBRATION_NOT_SUPPORTED_OR_INCONSISTENT` over 1,528 outer-test rows.

- weighted logloss delta vs market: `-0.0005029266108470644`
- weighted Brier delta vs market: `+0.0001820944975439356`
- weighted accuracy delta: `0.0`
- market argmax changes: `0`
- structural candidate selected in all 5 outer folds, but aggregate Brier worsened and season-level direction was inconsistent

The preregistered calibration criterion is therefore not satisfied for Portugal. V1 must not be converted into runtime parameters from this result.

## Governance outcome

Both league runtime configurations remain `CALIBRATION_REQUIRED`. The evaluation made zero The Odds API requests, performed zero Supabase operations, did not mutate runtime configuration, did not perform automatic promotion, and verified production model artifacts unchanged.

The Turkey result remains historical research evidence only. Portugal remains a negative/inconsistent result for this V1 calibration hypothesis. Any future runtime change requires a separate explicit review and PR and must not reinterpret this result after the fact.

Current-season cross-source identity/prospective evidence remains independently gated by the availability of canonical current `odds_snapshots`; historical calibration results do not bypass that gate.
