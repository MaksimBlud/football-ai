# Serie A Runbook

Normal operation is automatic after merge to `main`.

- Odds snapshots: `.github/workflows/serie-a-odds-snapshots.yml`
- Durable market/ledger cycle: `.github/workflows/serie-a-live-cycle.yml`
- Finished results + evaluation: `.github/workflows/serie-a-results.yml`
- Optional read-only inspection: `.github/workflows/serie-a-operational-smoke.yml`

Manual commands when needed:

```bash
python scheduled_serie_a_odds_snapshot.py
python serie_a_live_cycle.py
python update_serie_a_results.py --write
python evaluate_serie_a_predictions.py
```

Expected safety state:

```text
league = SERIE_A
prediction_mode = MARKET_ONLY
structural_status = CALIBRATION_REQUIRED
structural_applied = false
production model used = false
```

Do not activate Structural V2 until a separate Serie A historical/OOS calibration gate passes.
