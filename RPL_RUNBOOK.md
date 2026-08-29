# RPL Runbook

Normal operation is automatic after merge to `main`.

- Odds snapshots: `.github/workflows/rpl-odds-snapshots.yml`
- Durable market/ledger cycle: `.github/workflows/rpl-live-cycle.yml`
- Finished results + evaluation: `.github/workflows/rpl-results.yml`
- Optional read-only inspection: `.github/workflows/rpl-operational-smoke.yml`

Manual commands, when needed:

```bash
python scheduled_rpl_odds_snapshot.py
python rpl_live_cycle.py
python update_rpl_results.py --write
python evaluate_rpl_predictions.py
```

Expected safety state:

```text
league = RPL
prediction_mode = MARKET_ONLY
structural_status = CALIBRATION_REQUIRED
structural_applied = false
production model used = false
```

Do not activate Structural V2 until a separate RPL historical-data and calibration phase has passed its own out-of-sample gate.
