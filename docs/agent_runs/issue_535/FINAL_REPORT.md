# Research V5 final report — Issue #535

## Вывод простым языком

Детерминированное исследование **bookmaker-specific 1X2 margin allocation on matched fixtures** завершено без внешней LLM/API-квоты.

Финальное решение: **SUPPORTED_BOOKMAKER_MARGIN_HETEROGENEITY**.

Bet365 and Pinnacle show a stable same-fixture difference in how 1X2 margin is allocated between longshots and favourites after each bookmaker's total overround is removed. The pattern transfers from validation to untouched OOT, survives an alternate consensus, and is not merely a total-margin difference. This is observational market-structure evidence only, not a causal claim or betting edge.

## Technical appendix

Full reproducible result:
`research/agent_runs/issue_535/RESULT.json`.

Key registered result fields:
- `source_audit`: {"external_consensus": "Football-Data Avg 1X2 columns", "frozen_bookmakers": ["BET365", "PINNACLE"], "intraday_snapshot_gaps": {"1h": "No exact timestamped 1h snapshot in frozen source.", "24h": "No exact timestamped 24h snapshot in frozen source.", "6h": "No exact timestamped 6h snapshot in frozen source."}, "outcome_read_after_audit": true, "outcome_read_before_audit": false, "source_files": {"EPL:2019-2020": {"has_outcome_column": true, "missing_required_price_columns": []}, "EPL:2020-2021": {"has_outcome_column": true, "missing_required_price_columns": []}, "EPL:2021-2022": {"has_outcome_column": true, "missing_required_price_columns": []}, "EPL:2022-2023": {"has_outcome_column": true, "missing_required_price_columns": []}, "EPL:2023-2024": {"has_outcome_column": true, "missing_required_price_columns": []}, "EPL:2024-2025": {"has_outcome_column": true, "missing_required_price_columns": []}, "EPL:2025-2026": {"has_outcome_column": true, "missing_required_price_columns": []}, "LA_LIGA:2019-2020": {"has_outcome_column": true, "missing_required_price_columns": []}, "LA_LIGA:2020-2021": {"has_outcome_column": true, "missing_required_price_columns": []}, "LA_LIGA:2021-2022": {"has_outcome_column": true, "missing_required_price_columns": []}, "LA_LIGA:2022-2023": {"has_outcome_column": true, "missing_required_price_columns": []}, "LA_LIGA:2023-2024": {"has_outcome_column": true, "missing_required_price_columns": []}, "LA_LIGA:2024-2025": {"has_outcome_column": true, "missing_required_price_columns": []}, "LA_LIGA:2025-2026": {"has_outcome_column": true, "missing_required_price_columns": []}, "SERIE_A:2019-2020": {"has_outcome_column": true, "missing_required_price_columns": []}, "SERIE_A:2020-2021": {"has_outcome_column": true, "missing_required_price_columns": []}, "SERIE_A:2021-2022": {"has_outcome_column": true, "missing_required_price_columns": []}, "SERIE_A:2022-2023": {"has_outcome_column": true, "missing_required_price_columns": []}, "SERIE_A:2023-2024": {"has_outcome_column": true, "missing_required_price_columns": []}, "SERIE_A:2024-2025": {"has_outcome_column": true, "missing_required_price_columns": []}, "SERIE_A:2025-2026": {"has_outcome_column": true, "missing_required_price_columns": []}}, "validation_test_column_gate_passed": true}
- `validation.closing.paired.overround`: {"ci95_high": 0.026512006731799768, "ci95_low": 0.025711962111018716, "draws": 5000, "mean_delta_bet365_minus_pinnacle": 0.026111868614350203, "rows": 1140}
- `validation.closing.paired.fl_allocation_contrast`: {"ci95_high": 0.03750795764818959, "ci95_low": 0.02903500729008222, "draws": 5000, "mean_delta_bet365_minus_pinnacle": 0.03316818890921773, "rows": 1140}
- `test.closing.paired.overround`: {"ci95_high": 0.026473634293964057, "ci95_low": 0.02530634439148414, "draws": 5000, "mean_delta_bet365_minus_pinnacle": 0.025901783406217977, "rows": 596}
- `test.closing.paired.fl_allocation_contrast`: {"ci95_high": 0.027325389839300388, "ci95_low": 0.01323450245722342, "draws": 5000, "mean_delta_bet365_minus_pinnacle": 0.020353050830885445, "rows": 596}
- `test.closing.paired.draw_allocation_tilt`: {"ci95_high": -0.0032178653418021338, "ci95_low": -0.008544453330497132, "draws": 5000, "mean_delta_bet365_minus_pinnacle": -0.005856651150441787, "rows": 596}
- `test.closing.draw_specific`: {"BET365": {"flat_stake_return": -0.012281879194630864, "mean_allocation_tilt": -0.004805253452979671, "rows": 596}, "PINNACLE": {"flat_stake_return": 0.005704697986577194, "mean_allocation_tilt": 0.0010513976974621153, "rows": 596}}
- `formal_gate`: {"gates": {"alternate_consensus_oot_ci_excludes_zero": true, "alternate_consensus_same_sign": true, "at_least_two_leagues_same_oot_sign": true, "oot_allocation_ci_excludes_zero": true, "opening_and_closing_oot_same_sign": true, "validation_allocation_ci_excludes_zero": true, "validation_and_oot_same_sign": true}, "matching_oot_leagues": 3, "supported": true}
- `decision`: SUPPORTED_BOOKMAKER_MARGIN_HETEROGENEITY

Safety contract: model API = false; paid Odds API = false; Supabase writes = false;
production operations = false; automatic promotion = false.
