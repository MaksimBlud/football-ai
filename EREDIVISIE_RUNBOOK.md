# Eredivisie runbook

Normal operation is automated by GitHub Actions.

Manual diagnostics:
- `python scheduled_eredivisie_odds_snapshot.py` — adaptive odds collection decision and snapshot when due.
- `python eredivisie_live_cycle.py` — fixtures → MARKET_ONLY shadow → durable observation → canonical ledger.
- `python update_eredivisie_results.py --write` — immutable completed-result sync.
- `python evaluate_eredivisie_predictions.py` — read-only Amsterdam-timezone evaluation.

Safety invariants: no production `.pkl` mutation or loading, no Structural V2 activation, all current predictions are pre-kickoff MARKET_ONLY, durable conflicts must remain zero, and persistence is performed from the serialized market-shadow CSV boundary.
