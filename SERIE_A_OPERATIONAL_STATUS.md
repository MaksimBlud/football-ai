# Serie A Operational Status

Serie A is active as a research-only `MARKET_ONLY` league.

Operational flow:

`The Odds API (EU h2h) -> odds_snapshots -> upcoming fixtures -> market shadow -> generic observations -> prediction ledger -> The Odds API scores -> finished results -> Serie A evaluation`

Safety contract:

- production model is not loaded, trained, overwritten, or promoted;
- Structural V2 remains `CALIBRATION_REQUIRED` with no alpha/threshold;
- snapshots and ledger predictions are strictly pre-kickoff;
- durable observations/results are immutable and replay-safe;
- result evaluation is read-only and uses `Europe/Rome` fixture dates;
- historical source contract is Football-Data CSV `I1`, seasons 2016-17 through 2025-26, but Structural calibration remains a separate research gate.

Schedules (UTC):

- adaptive odds snapshot check: `12 */2 * * *`;
- durable MARKET_ONLY live cycle: `42 */2 * * *`;
- finished-result sync/evaluation: `2 */12 * * *`.
