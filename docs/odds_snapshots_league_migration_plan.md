# League-aware `odds_snapshots` migration plan

This change does **not** execute SQL or alter Supabase.

A later, separately reviewed migration should add:

`league TEXT NOT NULL`

Existing rows must first be explicitly backfilled as `EPL`; no generic
league-less ingestion should infer a league.

Recommended canonical fixture identity/index:

`(league, home_team, away_team, commence_time_utc)`

Recommended snapshot uniqueness/index should also include league, for example:

`(league, snapshot_time_utc, event_id)`

Collection remains independently gated by `collection_enabled`.
Possessing a valid Odds API sport key is not sufficient to enable collection.
