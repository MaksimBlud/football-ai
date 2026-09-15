# H2H_BOOKMAKER_V1

Status: **RESEARCH-ONLY / FORWARD COLLECTION**

## Purpose

Preserve bookmaker-level 1X2 (H2H) quotes that are already present in the same
The Odds API response used by existing league collectors. This closes the live
data gap exposed by the historical bookmaker-reconstruction block: historical
`AVG` market evidence cannot be transferred honestly to live data if individual
bookmaker quotes are discarded after ingestion.

## Cost and provider contract

- No additional The Odds API request is allowed for this capture.
- The collector must receive already-fetched H2H `events` from the existing
  league snapshot path.
- A research persistence failure must not make an otherwise successful paid H2H
  snapshot fail or trigger a retry solely for this optional sink.
- Persistence is idempotent on deterministic `snapshot_key`.

## Temporal and data contract

Each durable row is strictly pre-kickoff:

`league + event_id + snapshot_time_utc + H2H_BOOKMAKER_V1`

The row stores:

- league and provider event identity;
- home/away teams;
- kickoff and snapshot timestamps;
- raw provider bookmaker count;
- accepted complete-H2H bookmaker count;
- complete bookmaker H/D/A decimal quotes with bookmaker key/title and market
  `last_update`;
- the pre-existing aggregate H/D/A odds/probabilities reproduced from the same
  response;
- deterministic payload SHA-256.

Outcome, score, completion and settlement fields are forbidden from the payload.
Rows at or after kickoff fail closed.

## Storage

Table: `public.league_h2h_bookmaker_snapshots`

- append-like point-in-time history with deterministic upsert identity;
- RLS enabled;
- `anon` and `authenticated` receive no access;
- service role has only `SELECT` and `INSERT` grants for this table;
- no update/delete product path is introduced.

This table is intentionally separate from `league_multi_market_snapshots`.
Reusing that table would couple H2H writes to the existing multi-market freshness
gate and could suppress spreads/totals collection.

## League integration

Capture is wired into existing H2H collection paths for:

- EPL;
- Serie A;
- Bundesliga;
- Eredivisie;
- Ligue 1;
- La Liga (manual-only collector remains manual-only);
- RPL (manual-only collector remains manual-only);
- Turkey Super Lig;
- Primeira Liga.

No league becomes scheduled or paid-enabled merely because this sink exists.
The existing collector's own gate remains authoritative for whether a provider
request occurs.

## Research boundary

`H2H_BOOKMAKER_V1` does **not** authorize any of the following:

- replacing the active proportional market baseline;
- activating POWER, SHIN, consensus, dispersion, line movement or another new
  probability method;
- changing `MARKET_ANCHOR_1X2_V2` or its exact-market fallback;
- reading prospective outcomes earlier than an independently allowed gate;
- betting, staking or model promotion;
- changing production `.pkl` artifacts.

The stored quotes may later support a separately preregistered transferability
experiment comparing live bookmaker consensus/de-vig methods on genuinely
point-in-time data. Selection/evaluation rules for that experiment must be
frozen before outcomes are used.
