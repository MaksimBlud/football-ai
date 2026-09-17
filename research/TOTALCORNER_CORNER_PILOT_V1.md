# TOTALCORNER_CORNER_PILOT_V1

## Purpose

Qualify TotalCorner as the historical bookmaker-corners source before any model-vs-market experiment is authorized.

This pilot is **acquisition-only**. It measures source coverage and fixture identity quality. It must not compute any model performance, betting return, edge, calibration, or outcome-prediction metric. `NO_BET` remains binding.

## Frozen scope

Leagues and TotalCorner league IDs:

- `EPL` -> `1`;
- `LA_LIGA` -> `14`;
- `SERIE_A` -> `12`.

Target season window:

- start: `2025-08-01`;
- end: `2026-06-15`;
- deterministic sample: the latest 10 eligible completed-season fixtures per league discovered through the official TotalCorner league schedule endpoint.

The pilot may use the existing Football-Data historical transport only for read-only fixture identity reconciliation.

## Token and network boundary

- TotalCorner calls are forbidden unless `TOTALCORNER_TOKEN` is explicitly present.
- Missing token must fail closed **before the first TotalCorner HTTP request**.
- Only documented official API endpoints may be called.
- No website scraping is permitted.
- Rate limit must be respected; client pacing must stay at or below 30 requests/minute.
- No paid Odds API request and no Supabase write is allowed.

## Data acquisition

For each league:

1. enumerate official `/league/schedule/{league_id}` pages until at least 10 fixtures in the frozen season window are found or the configured safety page limit is reached;
2. select the latest 10 unique fixtures deterministically by kickoff and match ID;
3. store every schedule API response used by the pilot under a raw-data directory;
4. for each selected `match_id`, request `/match/odds/{match_id}?columns=cornerList`;
5. store each raw odds response separately;
6. normalize only valid snapshots strictly before kickoff using `totalcorner_corner_history.normalize_corner_history`;
7. never substitute post-match corner totals or in-play corner state for bookmaker pre-match prices.

## Fixture identity reconciliation

Each selected TotalCorner fixture must be reconciled to the project's Football-Data 2025/26 fixture set using:

- league;
- normalized home team;
- normalized away team;
- calendar date, allowing at most +/- 1 day only to absorb profile-timezone date boundaries.

The reconciliation layer may use explicit source-name aliases (for example `AC Milan` -> `Milan`) but may not use match outcomes to choose a match.

A fixture is `identity_ok` only when exactly one Football-Data candidate matches the league/team/date contract.

## Snapshot validity

A normalized corner snapshot is valid only when:

- `corner_line` is finite;
- `over_odds > 1.0`;
- `under_odds > 1.0`;
- `observed_at < kickoff` under the TotalCorner profile timezone semantics already present in the payload;
- fixture identity is complete.

## Acceptance gate

Per league:

- exactly 10 fixtures are selected;
- at least 8/10 have at least one valid pre-match corner snapshot;
- 10/10 selected fixtures are uniquely reconciled to Football-Data identity.

Overall decision:

- `PASS_SOURCE_PILOT` only if all three leagues pass both coverage and identity gates;
- otherwise `FAIL_SOURCE_PILOT`.

No model-vs-market experiment may start from this pilot alone. If the source pilot passes, the next step is to freeze a separate historical-corners experiment contract **before** bulk acquisition or any model evaluation.

## Persistence

Pilot output must contain:

- immutable raw schedule responses;
- immutable raw odds responses per match;
- normalized pre-match corner rows;
- a coverage/identity report;
- no production artifacts.

## Safety

- research-only;
- acquisition-only;
- `NO_BET`;
- no production `.pkl` modification;
- no production promotion;
- no Supabase writes;
- no paid Odds API requests;
- no TotalCorner request without an explicit token;
- no website scraping;
- no post-pilot retuning of this acceptance gate.
