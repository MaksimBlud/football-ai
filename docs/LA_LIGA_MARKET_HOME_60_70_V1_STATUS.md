# LA_LIGA_MARKET_HOME_60_70_V1 — Status

Status: **ACTIVE PROSPECTIVE / RESEARCH ONLY / OUTCOME-FREE ACCUMULATION**

The historical strategy lab froze this La Liga market-only candidate before prospective implementation. Its rule remains HOME market pick with margin-free HOME probability `>= 0.60` and `< 0.70`.

The operational prospective boundary is `2026-09-04T17:00:00Z`. Only immutable `MARKET_ONLY` ledger rows observed at or after that timestamp are eligible. The canonical decision is the latest durably recorded pre-kickoff ledger row for the provider event, joined to the exact raw odds snapshot at the same `event_id + snapshot_time_utc` to preserve the offered HOME odds.

The candidate requires no new Supabase table. Existing append-only `league_prediction_ledger` rows are the durable pre-kickoff tag source; existing `odds_snapshots` rows are the exact-price authority. Ambiguous provider revisions are excluded fail-closed.

Scheduled monitoring is outcome-free and read-only. It may report canonical decisions, provisional/final tags, settlement identity coverage, and accumulation state, but it does not query result values. Production `.pkl` artifacts are hash-guarded.

Outcome evaluation can run only through an explicit manual workflow dispatch and is blocked before `2027-06-01T00:00:00Z`. The post-gate report is descriptive only and cannot trigger production promotion.

Historical observations are never pooled into the prospective score. Threshold retuning, contextual exclusions, bookmaker reselection, or model-family changes based on prospective outcomes are prohibited.
