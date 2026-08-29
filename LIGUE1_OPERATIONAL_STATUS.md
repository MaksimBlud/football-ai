# Ligue 1 Operational Status

Status: **MARKET_ONLY operational**.

Live bootstrap on 2026-08-29 passed end-to-end with The Odds API sport key `soccer_france_ligue_one` and EU bookmaker region.

Durable bootstrap state:
- odds snapshots: 8
- generic MARKET_ONLY observations: 8
- canonical prediction ledger rows: 8
- immutable finished results: 1
- replay: inserted 0 / unchanged 8 / conflicts 0
- Structural V2 applied rows: 0

The completed result predates the first Ligue 1 prediction-ledger snapshot, so the current settled prediction count is correctly zero.

Historical source contract is Football-Data CSV `F1` for 2016/17 through 2025/26. Historical normalization/OOS Structural calibration remains a separate research phase.

Permanent UTC cadence:
- adaptive odds check: `03 */2 * * *`
- durable live cycle: `33 */2 * * *`
- finished results + evaluation: `47 */12 * * *`

Safety: production model is never loaded or modified; Structural V2 remains `CALIBRATION_REQUIRED`, alpha/threshold unset.
