# RPL Automation

All cron expressions are UTC.

- `07 */2 * * *`: adaptive RPL odds snapshot check.
- `32 */2 * * *`: durable MARKET_ONLY live cycle.
- `52 */12 * * *`: finished-result synchronization and read-only evaluation.

The snapshot scheduler only calls The Odds API when the adaptive freshness gate says a new snapshot is due. The results endpoint is intentionally limited to twice daily because it has a higher request cost.
