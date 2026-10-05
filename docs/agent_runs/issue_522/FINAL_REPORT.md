# Research V5 final report — Issue #522

## Вывод простым языком

Детерминированное исследование **corner cross-market match-shape falsification** завершено без внешней LLM/API-квоты.

Финальное решение: **SUPPORTED_FOR_FUTURE_CONFIRMATION**.

The same already-opened sample was used for falsification, not independent confirmation. Binary direction remains weaker than always-UP and DOWN has only 11 rows. A positive result supports only a future untouched confirmation; it is not a betting edge and NO_BET remains binding.

## Technical appendix

Full reproducible result:
`research/agent_runs/issue_522/RESULT.json`.

Key registered result fields:
- `rows`: 117
- `nonzero_movement_rows`: 56
- `binary_direction_status`: WEAK_BELOW_ALWAYS_UP_WITH_DOWN_SCARCITY
- `continuous_ranking_status`: ROBUST_WITHIN_OPENED_SAMPLE_REQUIRES_UNTOUCHED_CONFIRMATION
- `falsification.residual_spearman_nonzero`: 0.5596035543403964
- `falsification.residual_spearman_all_rows`: 0.43105269863412893
- `falsification.permutation_p`: 0.00019998000199980003
- `leave_one_cohort_out`: {"REP50": 0.5091159549469249, "V1_46": 0.6296896523782514, "V1_55": 0.47799227799227806, "V2B_43": 0.5367998263135041}
- `leave_one_league_out`: {"EPL": 0.4818011257035648, "LA_LIGA": 0.4569900687547746, "SERIE_A": 0.6400043768464821}

Safety contract: model API = false; paid Odds API = false; Supabase writes = false;
production operations = false; automatic promotion = false.
