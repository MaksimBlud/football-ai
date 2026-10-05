# Research V5 final report — Issue #540

## Вывод простым языком

Детерминированное исследование **Power de-vig Bundesliga/Ligue 1 frozen transport** завершено без внешней LLM/API-квоты.

Финальное решение: **POWER_CROSS_LEAGUE_TRANSPORT_NOT_SUPPORTED**.

The frozen Power transform did not pass every independent Bundesliga/Ligue 1 transport gate. The negative parent #533 decision remains binding.

## Technical appendix

Full reproducible result:
`research/agent_runs/issue_540/RESULT.json`.

Key registered result fields:
- `source_audit`: {"candidate_bookmakers": ["BET365", "PINNACLE"], "excluded_bookmakers": [], "included_bookmakers": ["BET365", "PINNACLE"], "outcome_read_after_audit": true, "outcome_read_before_audit": false, "source_files": {"BUNDESLIGA:2019-2020": {"bookmakers": {"BET365": {"missing_required_columns": []}, "PINNACLE": {"missing_required_columns": []}}, "has_outcome_column": true}, "BUNDESLIGA:2020-2021": {"bookmakers": {"BET365": {"missing_required_columns": []}, "PINNACLE": {"missing_required_columns": []}}, "has_outcome_column": true}, "BUNDESLIGA:2021-2022": {"bookmakers": {"BET365": {"missing_required_columns": []}, "PINNACLE": {"missing_required_columns": []}}, "has_outcome_column": true}, "BUNDESLIGA:2022-2023": {"bookmakers": {"BET365": {"missing_required_columns": []}, "PINNACLE": {"missing_required_columns": []}}, "has_outcome_column": true}, "BUNDESLIGA:2023-2024": {"bookmakers": {"BET365": {"missing_required_columns": []}, "PINNACLE": {"missing_required_columns": []}}, "has_outcome_column": true}, "BUNDESLIGA:2024-2025": {"bookmakers": {"BET365": {"missing_required_columns": []}, "PINNACLE": {"missing_required_columns": []}}, "has_outcome_column": true}, "BUNDESLIGA:2025-2026": {"bookmakers": {"BET365": {"missing_required_columns": []}, "PINNACLE": {"missing_required_columns": []}}, "has_outcome_column": true}, "LIGUE_1:2019-2020": {"bookmakers": {"BET365": {"missing_required_columns": []}, "PINNACLE": {"missing_required_columns": []}}, "has_outcome_column": true}, "LIGUE_1:2020-2021": {"bookmakers": {"BET365": {"missing_required_columns": []}, "PINNACLE": {"missing_required_columns": []}}, "has_outcome_column": true}, "LIGUE_1:2021-2022": {"bookmakers": {"BET365": {"missing_required_columns": []}, "PINNACLE": {"missing_required_columns": []}}, "has_outcome_column": true}, "LIGUE_1:2022-2023": {"bookmakers": {"BET365": {"missing_required_columns": []}, "PINNACLE": {"missing_required_columns": []}}, "has_outcome_column": true}, "LIGUE_1:2023-2024": {"bookmakers": {"BET365": {"missing_required_columns": []}, "PINNACLE": {"missing_required_columns": []}}, "has_outcome_column": true}, "LIGUE_1:2024-2025": {"bookmakers": {"BET365": {"missing_required_columns": []}, "PINNACLE": {"missing_required_columns": []}}, "has_outcome_column": true}, "LIGUE_1:2025-2026": {"bookmakers": {"BET365": {"missing_required_columns": []}, "PINNACLE": {"missing_required_columns": []}}, "has_outcome_column": true}}, "transport_leagues": ["BUNDESLIGA", "LIGUE_1"], "validation_test_column_gate_passed": true}
- `validation_closing_log_loss_delta_vs_multiplicative`: 7.520388294879332e-06
- `confirmation`: {"candidate": "power", "closing_deltas_vs_multiplicative": {"brier": -0.000951065229209576, "log_loss": -0.0015337774468296113, "rps": -0.00044905015367866397}, "confirmed": false, "gate": {"at_least_two_bookmakers": true, "at_least_two_leagues_improve": true, "bootstrap_ci95_upper_below_zero": false, "both_bookmakers_improve": true, "brier_not_worse": true, "closing_log_loss_improves": true, "coverage_ge_0_99": true, "opening_sensitivity_not_worse": true, "rps_not_worse": true}, "method_valid_coverage": 1.0, "opening_log_loss_delta_vs_multiplicative": -0.0015124736936806646, "paired_fixture_cluster_bootstrap": {"ci95_high": 0.0013369042423982895, "ci95_low": -0.0033460959215361563, "draws": 5000, "mean_delta": -0.0010942788683774014}, "stability": {"by_bookmaker": {"BET365": -0.0015163117512329608, "PINNACLE": -0.0015691715054559363}, "by_league": {"BUNDESLIGA": -0.0021004081912361335, "LIGUE_1": -0.0009720846609800086}}}
- `transfer_gate`: {"gates": {"all_included_bookmakers_improve": true, "both_leagues_improve": true, "opening_not_worse": true, "test_bootstrap_ci95_upper_below_zero": false, "test_brier_not_worse": true, "test_closing_log_loss_improves": true, "test_rps_not_worse": true, "validation_closing_log_loss_improves": false}, "supported": false}
- `decision`: POWER_CROSS_LEAGUE_TRANSPORT_NOT_SUPPORTED

Safety contract: model API = false; paid Odds API = false; Supabase writes = false;
production operations = false; automatic promotion = false.
