# Research V5 final report — Issue #542

## Вывод простым языком

Детерминированное исследование **favourite-longshot Bundesliga/Ligue 1 frozen transport** завершено без внешней LLM/API-квоты.

Финальное решение: **NO_CROSS_LEAGUE_FAVOURITE_LONGSHOT_CONFIRMATION**.

The frozen favourite-longshot pattern did not clear every Bundesliga/Ligue 1 transport gate. The negative parent #534 decision remains binding.

## Technical appendix

Full reproducible result:
`research/agent_runs/issue_542/RESULT.json`.

Key registered result fields:
- `source_audit`: {"candidate_bookmakers": ["BET365", "PINNACLE"], "excluded_bookmakers": [], "included_bookmakers": ["BET365", "PINNACLE"], "intraday_snapshot_gaps": {"1h": "No exact timestamped 1h snapshot in frozen Football-Data source.", "24h": "No exact timestamped 24h snapshot in frozen Football-Data source.", "6h": "No exact timestamped 6h snapshot in frozen Football-Data source."}, "outcome_read_after_audit": true, "outcome_read_before_audit": false, "source_files": {"BUNDESLIGA:2019-2020": {"bookmakers": {"BET365": {"missing_required_columns": []}, "PINNACLE": {"missing_required_columns": []}}, "has_outcome_column": true}, "BUNDESLIGA:2020-2021": {"bookmakers": {"BET365": {"missing_required_columns": []}, "PINNACLE": {"missing_required_columns": []}}, "has_outcome_column": true}, "BUNDESLIGA:2021-2022": {"bookmakers": {"BET365": {"missing_required_columns": []}, "PINNACLE": {"missing_required_columns": []}}, "has_outcome_column": true}, "BUNDESLIGA:2022-2023": {"bookmakers": {"BET365": {"missing_required_columns": []}, "PINNACLE": {"missing_required_columns": []}}, "has_outcome_column": true}, "BUNDESLIGA:2023-2024": {"bookmakers": {"BET365": {"missing_required_columns": []}, "PINNACLE": {"missing_required_columns": []}}, "has_outcome_column": true}, "BUNDESLIGA:2024-2025": {"bookmakers": {"BET365": {"missing_required_columns": []}, "PINNACLE": {"missing_required_columns": []}}, "has_outcome_column": true}, "BUNDESLIGA:2025-2026": {"bookmakers": {"BET365": {"missing_required_columns": []}, "PINNACLE": {"missing_required_columns": []}}, "has_outcome_column": true}, "LIGUE_1:2019-2020": {"bookmakers": {"BET365": {"missing_required_columns": []}, "PINNACLE": {"missing_required_columns": []}}, "has_outcome_column": true}, "LIGUE_1:2020-2021": {"bookmakers": {"BET365": {"missing_required_columns": []}, "PINNACLE": {"missing_required_columns": []}}, "has_outcome_column": true}, "LIGUE_1:2021-2022": {"bookmakers": {"BET365": {"missing_required_columns": []}, "PINNACLE": {"missing_required_columns": []}}, "has_outcome_column": true}, "LIGUE_1:2022-2023": {"bookmakers": {"BET365": {"missing_required_columns": []}, "PINNACLE": {"missing_required_columns": []}}, "has_outcome_column": true}, "LIGUE_1:2023-2024": {"bookmakers": {"BET365": {"missing_required_columns": []}, "PINNACLE": {"missing_required_columns": []}}, "has_outcome_column": true}, "LIGUE_1:2024-2025": {"bookmakers": {"BET365": {"missing_required_columns": []}, "PINNACLE": {"missing_required_columns": []}}, "has_outcome_column": true}, "LIGUE_1:2025-2026": {"bookmakers": {"BET365": {"missing_required_columns": []}, "PINNACLE": {"missing_required_columns": []}}, "has_outcome_column": true}}, "transport_leagues": ["BUNDESLIGA", "LIGUE_1"], "validation_test_column_gate_passed": true}
- `validation.closing.residual_slope`: {"ci95_high": 0.1482317087262252, "ci95_low": -0.1366754057019276, "draws": 5000, "slope": 0.01014570375562904, "valid_draws": 5000}
- `validation.closing.regions`: {"favourite_p_ge_0_60": {"flat_stake_return": -0.0621584699453552, "gap": -0.00963230648133473, "mean_p": 0.7008891370824276, "rows": 366, "win_rate": 0.6912568306010929}, "longshot_p_lt_0_30": {"flat_stake_return": -0.05110380460310006, "gap": -0.00036257238548384474, "mean_p": 0.21783556440051438, "rows": 2129, "win_rate": 0.21747299201503054}}
- `test.closing.residual_slope`: {"ci95_high": 0.3010285070600532, "ci95_low": -0.006598519101078773, "draws": 5000, "slope": 0.1504696076565474, "valid_draws": 5000}
- `test.closing.regions`: {"favourite_p_ge_0_60": {"flat_stake_return": 0.08448598130841123, "gap": 0.09080940743105004, "mean_p": 0.7035831159334359, "rows": 214, "win_rate": 0.794392523364486}, "longshot_p_lt_0_30": {"flat_stake_return": -0.13951581665590704, "gap": -0.016154692113267255, "mean_p": 0.2233851633850555, "rows": 1549, "win_rate": 0.20723047127178826}}
- `transfer_gate`: {"gates": {"bookmaker_signs_not_contradictory": true, "both_leagues_positive_test_slope": true, "both_leagues_positive_validation_slope": false, "test_pooled_ci_above_zero": false, "test_region_direction": true, "validation_pooled_ci_above_zero": false, "validation_region_direction": false}, "supported": false}
- `decision`: NO_CROSS_LEAGUE_FAVOURITE_LONGSHOT_CONFIRMATION

Safety contract: model API = false; paid Odds API = false; Supabase writes = false;
production operations = false; automatic promotion = false.
