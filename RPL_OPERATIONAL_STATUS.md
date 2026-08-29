# RPL Operational Status

RPL is active as a research-only `MARKET_ONLY` league.

Operational data flow:

`The Odds API (EU h2h) -> odds_snapshots -> upcoming fixtures -> market shadow -> generic observations -> prediction ledger -> The Odds API scores -> finished results -> RPL evaluation`

Safety contract:

- production model is not loaded, trained, overwritten, or promoted;
- Structural V2 remains `CALIBRATION_REQUIRED` with no alpha/threshold;
- snapshots are strictly pre-kickoff;
- durable observations and ledger rows are idempotent/immutable;
- finished results are immutable and independently persisted;
- result evaluation is read-only and uses `Europe/Moscow` fixture dates.

Schedules (UTC):

- adaptive odds snapshot check: `7 */2 * * *`;
- durable market-only live cycle: `32 */2 * * *`;
- finished-result sync/evaluation: `52 */12 * * *`.

The initial live bootstrap on 2026-08-29 created 7 RPL odds snapshots, 7 durable observations, and 7 canonical ledger predictions. Immediate replay was idempotent with zero conflicts. The finished-results bootstrap persisted the completed FC Akron Tolyatti 2-2 CSKA Moscow result; it predates the first ledger snapshot and therefore correctly produced zero settled predictions at bootstrap time.

Historical-data sourcing and Structural V2 calibration are intentionally outside the operational market-only block and remain unresolved rather than guessed.
