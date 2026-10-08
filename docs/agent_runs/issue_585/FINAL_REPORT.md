# Research V5 final report — Issue #585

## Вывод простым языком

Детерминированное исследование **website BTTS untouched-evidence source readiness** завершено без внешней LLM/API-квоты.

Финальное решение: **BLOCKED_BY_UNTOUCHED_DATA_OR_PROVENANCE**.

Source readiness only. Existing calibrator-selection rows are opened and cannot confirm the refit calibrator. Do not inspect reserved 2026/27 outcomes, reconstruct forecasts with post-result features, deploy, or recommend a bet.

## Technical appendix

Full reproducible result:
`research/agent_runs/issue_585/RESULT.json`.

Key registered result fields:
- `market`: BTTS
- `evidence_ready`: False
- `source_audit`: {"artifact_presence_checked_without_loading": {"away_goals_model_no_odds.pkl": false, "btts_calibrator.pkl": false, "home_goals_model_no_odds.pkl": false, "over_2_5_calibrator.pkl": false}, "contract_files": {"bootstrap_product_predictions_from_pair_ledger.py": true, "calibrate_goal_markets.py": true, "docs/total-goals-readiness-audit.md": true, "evaluate_goal_markets_thresholds.py": true, "save_odds_snapshot.py": true, "total_goals_inference_contract.py": true}, "current_odds_contract_is_h2h_only": true, "exact_paired_market_prices_present": false, "four_artifact_bundle_complete": false, "immutable_prematch_forecasts_present": false, "lineage_documented": true, "point_in_time_inference_contract_present": true, "previous_method_selection_scope": ["2023/2024", "2024/2025", "2025/2026"], "previous_scope_is_untouched_post_refit_evidence": false, "required_market_price_fields": ["btts_yes_odds", "btts_no_odds"]}
- `missing_prerequisites`: [{"code": "PORTABLE_FOUR_ARTIFACT_BUNDLE_UNAVAILABLE", "detail": "Missing runtime artifacts: home_goals_model_no_odds.pkl, away_goals_model_no_odds.pkl, over_2_5_calibrator.pkl, btts_calibrator.pkl"}, {"code": "IMMUTABLE_PREMATCH_GOAL_FORECASTS_UNAVAILABLE", "detail": "Current durable bootstrap writes null goal probabilities; no independent pre-match forecast cohort is tracked."}, {"code": "EXACT_PAIRED_MARKET_PRICES_UNAVAILABLE", "detail": "Required timestamped price fields are absent: btts_yes_odds, btts_no_odds"}, {"code": "UNTOUCHED_POST_REFIT_TARGET_COHORT_UNAVAILABLE", "detail": "2023/24-2025/26 selected/refit the calibrator; reserved 2026/27 outcomes were not inspected."}]
- `safety`: {"automatic_deployment": false, "match_outcomes_read": false, "model_pickle_files_loaded": false, "model_training_or_promotion": false, "paid_api_calls": 0, "production_operations": 0, "reserved_2026_27_outcomes_read": false, "supabase_reads": 0, "supabase_writes": 0}
- `no_bet`: True

Safety contract: model API = false; paid Odds API = false; Supabase writes = false;
production operations = false; automatic promotion = false.
