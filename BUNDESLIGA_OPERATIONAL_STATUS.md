# Bundesliga Operational Status

Status: **MARKET_ONLY operational**.

Live bootstrap on 2026-08-29 passed end-to-end with the verified The Odds API sport key `soccer_germany_bundesliga` and EU bookmaker region.

Durable state after two successful live bootstrap passes:
- odds snapshots: 34
- generic MARKET_ONLY observations: 34
- canonical prediction ledger rows: 34
- immutable finished results: 1
- replay conflicts: 0
- Structural V2 applied rows: 0

Each bootstrap pass saw 17 current fixtures. The immediate replay of each durable cycle was idempotent (`inserted=0`, `unchanged=17`, `conflicts=0`).

The completed result predates the first Bundesliga prediction-ledger snapshot, so current settled prediction count is correctly zero.

Historical source contract is Football-Data CSV `D1` for 2016/17 through 2025/26. Historical normalization/OOS Structural calibration is a separate research phase and is not required for the MARKET_ONLY operational loop.

Permanent UTC cadence:
- adaptive odds check: `22 */2 * * *`
- durable live cycle: `52 */2 * * *`
- finished results + evaluation: `17 */12 * * *`

Safety: production model is never loaded or modified; Structural V2 remains `CALIBRATION_REQUIRED`, alpha/threshold unset.
