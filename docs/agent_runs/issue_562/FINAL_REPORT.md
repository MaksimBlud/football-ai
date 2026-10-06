# Research V5 final report — Issue #562

## Вывод простым языком

Детерминированное исследование **market residual process-vs-results divergence** завершено без внешней LLM/API-квоты.

Финальное решение: **NO_STABLE_MARKET_RESIDUAL_PROCESS_DIVERGENCE**.

The frozen process-vs-results representation did not pass every validation, untouched-test, uncertainty and cross-league gate; do not retune it on these outcomes.

## Technical appendix

Full reproducible result:
`research/agent_runs/issue_562/RESULT.json`.

Key registered result fields:
- `source_audit`: {"coverage": {"BUNDESLIGA:2019-2020": {"eligible_rows": 261, "raw_rows": 306}, "BUNDESLIGA:2020-2021": {"eligible_rows": 261, "raw_rows": 306}, "BUNDESLIGA:2021-2022": {"eligible_rows": 261, "raw_rows": 306}, "BUNDESLIGA:2022-2023": {"eligible_rows": 261, "raw_rows": 306}, "BUNDESLIGA:2023-2024": {"eligible_rows": 261, "raw_rows": 306}, "BUNDESLIGA:2024-2025": {"eligible_rows": 251, "raw_rows": 306}, "BUNDESLIGA:2025-2026": {"eligible_rows": 261, "raw_rows": 306}, "LIGUE_1:2019-2020": {"eligible_rows": 229, "raw_rows": 279}, "LIGUE_1:2020-2021": {"eligible_rows": 329, "raw_rows": 380}, "LIGUE_1:2021-2022": {"eligible_rows": 329, "raw_rows": 380}, "LIGUE_1:2022-2023": {"eligible_rows": 329, "raw_rows": 380}, "LIGUE_1:2023-2024": {"eligible_rows": 261, "raw_rows": 306}, "LIGUE_1:2024-2025": {"eligible_rows": 261, "raw_rows": 306}, "LIGUE_1:2025-2026": {"eligible_rows": 261, "raw_rows": 306}}, "files": {"BUNDESLIGA:2019-2020": {"market_triplet": ["B365H", "B365D", "B365A"], "missing_required_columns": []}, "BUNDESLIGA:2020-2021": {"market_triplet": ["B365H", "B365D", "B365A"], "missing_required_columns": []}, "BUNDESLIGA:2021-2022": {"market_triplet": ["B365H", "B365D", "B365A"], "missing_required_columns": []}, "BUNDESLIGA:2022-2023": {"market_triplet": ["B365H", "B365D", "B365A"], "missing_required_columns": []}, "BUNDESLIGA:2023-2024": {"market_triplet": ["B365H", "B365D", "B365A"], "missing_required_columns": []}, "BUNDESLIGA:2024-2025": {"market_triplet": ["B365H", "B365D", "B365A"], "missing_required_columns": []}, "BUNDESLIGA:2025-2026": {"market_triplet": ["B365H", "B365D", "B365A"], "missing_required_columns": []}, "LIGUE_1:2019-2020": {"market_triplet": ["B365H", "B365D", "B365A"], "missing_required_columns": []}, "LIGUE_1:2020-2021": {"market_triplet": ["B365H", "B365D", "B365A"], "missing_required_columns": []}, "LIGUE_1:2021-2022": {"market_triplet": ["B365H", "B365D", "B365A"], "missing_required_columns": []}, "LIGUE_1:2022-2023": {"market_triplet": ["B365H", "B365D", "B365A"], "missing_required_columns": []}, "LIGUE_1:2023-2024": {"market_triplet": ["B365H", "B365D", "B365A"], "missing_required_columns": []}, "LIGUE_1:2024-2025": {"market_triplet": ["B365H", "B365D", "B365A"], "missing_required_columns": []}, "LIGUE_1:2025-2026": {"market_triplet": ["B365H", "B365D", "B365A"], "missing_required_columns": []}}, "header_gate_passed": true, "leagues": ["BUNDESLIGA", "LIGUE_1"], "outcome_read_after_audit": true, "outcome_read_before_audit": false, "required_columns": ["AS", "AST", "AwayTeam", "B365A", "B365D", "B365H", "Date", "FTR", "HS", "HST", "HomeTeam"], "seasons": ["2019-2020", "2020-2021", "2021-2022", "2022-2023", "2023-2024", "2024-2025", "2025-2026"]}
- `validation.candidate_minus_market_log_loss`: -0.00042295026895394235
- `validation.candidate_minus_market_brier`: -0.00011854700093643741
- `test.candidate_minus_market_log_loss`: 0.005203696023637298
- `test.candidate_minus_market_brier`: 0.0029284511675393265
- `test.bootstrap`: {"ci95_high": 0.010103681804154538, "ci95_low": 0.0003463041449498434, "draws": 5000}
- `test.by_league`: {"BUNDESLIGA": {"candidate_minus_market_brier": -6.045048424721501e-05, "candidate_minus_market_log_loss": -0.0008175256477337083, "rows": 261}, "LIGUE_1": {"candidate_minus_market_brier": 0.005917352819325867, "candidate_minus_market_log_loss": 0.011224917695008302, "rows": 261}}
- `formal_gate`: {"gates": {"no_positive_test_league_log_loss_delta": false, "source_and_leakage_checks_pass": true, "test_brier_improves": false, "test_log_loss_ci95_upper_below_zero": false, "test_log_loss_improves": false, "validation_brier_improves": true, "validation_log_loss_improves": true}, "supported": false}
- `decision`: NO_STABLE_MARKET_RESIDUAL_PROCESS_DIVERGENCE

Safety contract: model API = false; paid Odds API = false; Supabase writes = false;
production operations = false; automatic promotion = false.
