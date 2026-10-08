# Research V5 final report — Issue #594

## Вывод простым языком

Детерминированное исследование **point-in-time league-wide 1X2 snapshot cadence audit** завершено без внешней LLM/API-квоты.

Финальное решение: **BLOCKED_BY_TIMESTAMP_COVERAGE**.

The quota arithmetic is reproducible, but fresh main does not contain timestamp-safe snapshot metadata for at least two frozen leagues. P1 costs 300 credits per 30 days (12-hour sweeps); P2 costs the full 400-credit spendable budget (9-hour sweeps). No empirical coverage winner can be claimed.

## Technical appendix

Full reproducible result:
`research/agent_runs/issue_594/RESULT.json`.

Key registered result fields:
- `source_gate.available_leagues`: []
- `source_gate.available_league_count`: 0
- `source_gate.complete_fixture_universe_available`: False
- `policy_arithmetic.P1_fixed_12h`: {"credits": 300, "full_sweeps": 60, "spacing_hours": 12, "unused_spendable_credits": 100}
- `policy_arithmetic.P2_fixed_9h`: {"credits": 400, "full_sweeps": 80, "spacing_hours": 9, "unused_spendable_credits": 0}
- `workflow_audit`: {"BUNDESLIGA": {"activation": "MANUAL_WORKFLOW", "collector_exists": true, "collector_path": "save_bundesliga_odds_snapshot.py", "workflow_exists": true, "workflow_path": ".github/workflows/bundesliga-odds-snapshots.yml"}, "EPL": {"activation": "MANUAL_WORKFLOW", "collector_exists": true, "collector_path": "save_epl_odds_snapshot_with_bookmakers.py", "workflow_exists": true, "workflow_path": ".github/workflows/odds-snapshots.yml"}, "LA_LIGA": {"activation": "MANUAL_COLLECTOR_ONLY", "collector_exists": true, "collector_path": "save_la_liga_odds_snapshot.py", "workflow_exists": false, "workflow_path": null}, "LIGUE_1": {"activation": "MANUAL_WORKFLOW", "collector_exists": true, "collector_path": "save_ligue1_odds_snapshot.py", "workflow_exists": true, "workflow_path": ".github/workflows/ligue1-odds-snapshots.yml"}, "SERIE_A": {"activation": "MANUAL_WORKFLOW", "collector_exists": true, "collector_path": "save_serie_a_odds_snapshot.py", "workflow_exists": true, "workflow_path": ".github/workflows/serie-a-odds-snapshots.yml"}}
- `safety`: {"automatic_promotion": false, "match_outcomes_used": false, "paid_odds_api_calls": 0, "production_model_operations": 0, "production_schedule_changes": 0, "reserved_2026_27_outcomes_used": false, "supabase_reads": 0, "supabase_writes": 0}

Safety contract: model API = false; paid Odds API = false; Supabase writes = false;
production operations = false; automatic promotion = false.
