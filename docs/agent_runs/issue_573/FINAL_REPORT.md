# Research V5 final report — Issue #573

## Вывод простым языком

Детерминированное исследование **multi-market state to future 1X2 repricing vector** завершено без внешней LLM/API-квоты.

Финальное решение: **NO_STABLE_MULTI_MARKET_REPRICING_SIGNAL**.

The frozen direct multi-market representation failed at least one validation, retrospective-test, uncertainty or cross-league gate. Do not rescue it by changing features, Ridge alpha, AH scope, target coordinates, league subset, sign rules or by adding corners to the same opened history.

## Technical appendix

Full reproducible result:
`research/agent_runs/issue_573/RESULT.json`.

Key registered result fields:
- `source_audit.eligible_leagues`: ["EPL", "LA_LIGA", "SERIE_A", "BUNDESLIGA", "LIGUE_1"]
- `validation.candidate_minus_baseline_mse`: -5.3556086855197575e-05
- `validation.candidate_minus_baseline_mae`: 0.0001612956862735878
- `test.candidate_minus_baseline_mse`: -7.956285650255627e-05
- `test.candidate_minus_baseline_mae`: -0.00011262169413421543
- `test.bootstrap.ci95_low`: -0.0001562419179007653
- `test.bootstrap.ci95_high`: -3.946866651291164e-06
- `formal_gate.supported`: False

Safety contract: model API = false; paid Odds API = false; Supabase writes = false;
production operations = false; automatic promotion = false.
