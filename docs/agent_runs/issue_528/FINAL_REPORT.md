# Research V5 final report — Issue #528

## Вывод простым языком

Детерминированное исследование **corner match-shape Bundesliga/Ligue 1 transport** завершено без внешней LLM/API-квоты.

Финальное решение: **WEAK_OR_INCONSISTENT_CROSS_MARKET_CORNER_DIRECTION_HYPOTHESIS**.

Bundesliga/Ligue 1 are independent of #522, but their movements were opened previously for other hypotheses. This is cross-league falsification, not untouched confirmation or a betting edge; NO_BET remains binding.

## Technical appendix

Full reproducible result:
`research/agent_runs/issue_528/RESULT.json`.

Key registered result fields:
- `coverage_audit`: {"exact_same_fixture_join_required": true, "expected_rows_by_league": {"BUNDESLIGA": 35, "LIGUE_1": 39}, "historical_validation": {"BUNDESLIGA": {"mae_league_mean_baseline": 2.838636889814963, "mae_match_shape_model": 2.8304835373168147, "train_rows": 1835, "validation_rows": 306}, "LIGUE_1": {"mae_league_mean_baseline": 2.8167611895037714, "mae_match_shape_model": 2.8043836576524797, "train_rows": 2026, "validation_rows": 306}}, "joined_rows_by_league": {"BUNDESLIGA": 35, "LIGUE_1": 39}, "movement_target_loaded": true, "passed": true}
- `rows`: 74
- `nonzero_movement_rows`: 22
- `binary_direction_status`: WEAK_BELOW_ALWAYS_UP_WITH_DOWN_SCARCITY
- `continuous_ranking_status`: CROSS_LEAGUE_TRANSFER_NOT_SUPPORTED
- `raw_continuous.by_league`: {"BUNDESLIGA": {"pearson": 0.7083086553582941, "rows": 11, "spearman": 0.790909090909091}, "LIGUE_1": {"pearson": 0.7287986049028593, "rows": 11, "spearman": 0.6818181818181819}}
- `raw_continuous.pooled_spearman`: 0.733691076983739
- `falsification.mechanical_opening_component_pearson_nonzero`: 0.7690433971270064
- `falsification.residual_pearson_nonzero`: 0.15196834217929853
- `falsification.residual_spearman_nonzero`: 0.050254093732354614
- `falsification.permutation_p`: 0.41245875412458755
- `leave_one_league_out`: {"BUNDESLIGA": -0.19090909090909092, "LIGUE_1": 0.19090909090909092}

Safety contract: model API = false; paid Odds API = false; Supabase writes = false;
production operations = false; automatic promotion = false.
