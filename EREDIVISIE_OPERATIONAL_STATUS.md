# Eredivisie operational status

Status: **LIVE MARKET_ONLY research loop**.

- League: `EREDIVISIE`
- Timezone: `Europe/Amsterdam`
- Odds source: The Odds API `soccer_netherlands_eredivisie`, EU region
- Historical contract: Football-Data CSV `N1`, 2016/17 through 2026/27
- Structural V2: `CALIBRATION_REQUIRED`; alpha/threshold unset
- Production model: never used

Live bootstrap on 2026-08-29 persisted 8 odds snapshots, 8 durable observations, 8 canonical ledger predictions, and 1 completed result. Immediate replay was idempotent: 0 inserted / 8 unchanged / 0 conflicts for observations and ledger. The completed Groningen 2-3 Fortuna Sittard fixture predates the first ledger snapshot, so settled prediction count correctly remained 0.

Scheduled UTC cadence:
- adaptive odds check: `33 */2 * * *`
- durable live cycle: `58 */2 * * *`
- finished results + evaluation: `23 */12 * * *`
