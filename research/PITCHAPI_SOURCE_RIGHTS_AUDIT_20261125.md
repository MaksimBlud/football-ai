# Original MARKET_ANCHOR_1X2_V2 — PitchAPI source-rights and field-coverage audit

**Audit date:** 2026-11-25 UTC  
**Decision:** **HOLD — free access is promising, but data rights, corners coverage and point-in-time provenance are not established.**  
**Scope:** official PitchAPI documentation and PyPI SDK metadata only. No account or API key was created; no API or odds endpoint was called; no response, match payload or dataset was downloaded; no Supabase access or protected-outcome read occurred.

## Executive finding

PitchAPI is a new no-cost candidate worth recording because its public documentation claims one free plan, 77 leagues, full history back to 2021 and no request allowance. The documentation describes match results, team statistics, yellow-card statistics, red-card events, and a read-only REST API. The Python SDK is available on PyPI.

It is **not approved for original V2 ingestion**. The reviewed documentation does not publish or link the API data terms, identify the upstream football-data provider(s), document a corners field, or expose a historical per-match first-observed/correction timestamp. The SDK's MIT licence covers only SDK code; PyPI explicitly says the API data is governed separately by PitchAPI's terms. The API documentation's `fetched_at` / `age_seconds` fields are described for the live snapshot, not as historical source-capture timestamps.

## Public evidence reviewed

- API docs and plans: https://pitchapi.dev/
- Python SDK metadata: https://pypi.org/project/pitchapi/
- API base URL shown in docs: https://api.pitchapi.dev

The documentation claims:
- one free plan, no paid tier, 77 leagues, history back to 2021, and no request allowance;
- API-key authentication;
- read-only REST endpoints for fixtures, matches, events, lineups, team/player statistics and analytics;
- UTC RFC 3339 timestamps for match date/time;
- yellow-card match statistics in the documented team-stat example;
- yellow/red-card event types in the documented event model.

These are vendor documentation claims, not independently measured coverage or an authenticated API response.

## Frozen 19-feature compatibility

The unchanged original V2 requires, among other fields, six corner-derived inputs:
- `diff_corners_for_5`
- `diff_corners_for_10`
- `diff_corners_against_5`
- `diff_corners_against_10`
- `diff_corners_for_venue5`
- `diff_corners_against_venue5`

The reviewed PitchAPI documentation does not document a corners field or corner events. It does document yellow-card statistics and red-card events, but no field-level completeness or exact definition parity for Serie A is established. Therefore the source cannot currently supply a verified, unchanged 19-feature vector.

Do not impute undocumented corners as zero, substitute another statistic, alter the feature order, or mix a different source to fill missing fields.

## Rights and provenance blockers

1. **API data terms are not located in the reviewed official pages.** PyPI states that the MIT licence applies to the SDK source only and that access to the service and returned football data is governed separately by PitchAPI terms. The reviewed PyPI project links point to the documentation and homepage, not to a terms URL.
2. **Upstream rights are unknown.** The documentation reviewed does not name the upstream match-statistics provider(s) or grant a field-level right to use the data for internal ML/model inference or retain private raw responses.
3. **No historical source-before-quote proof.** The live endpoint documents `fetched_at`, `age_seconds` and `stale` for a live snapshot. No per-match historical first-observed or correction timestamp is documented for stored match statistics. A later API response plus a local SHA would prove the bytes received, not that those exact values were available before an earlier quote.
4. **Coverage is not independently established.** The 77-league catalogue claim does not prove Serie A 2026/27 match-by-match completeness for the exact required fields or their equivalence to the frozen Football-Data training definitions.

## Requirements before reconsideration

- A published or written API data licence permitting internal model inference and private raw-response retention.
- Written identification/clearance of upstream data providers and field-level rights.
- A documented corners field and stable definitions for corners, yellow cards and red cards that match the frozen V2 feature semantics, or a demonstrated exact source-parity bridge without changing V2.
- Per-match historical source observation/correction timestamps, or a documented immutable capture mechanism that proves the source bytes were received before each quote.
- An owner-authorized, minimal, free-tier test after rights clearance, with response bytes archived privately, exact SHA-256, UTC receipt time, request ID, event identity and quote time.
- A read-only Serie A 2026/27 coverage and missingness audit before any feature calculation.

Until every requirement is independently established, keep the source at HOLD. Do not create an account, request a key, call the API, fetch odds, download data, calculate V2 features or run inference from PitchAPI.

## Frozen V2 invariants

The main candidate remains unchanged: SHA-256 `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, 19 ordered features, 20×2 weights, `active_lambda=0`, `shadow_lambda=1`, stability gate FAILED, prospective evaluation gate CLOSED. This audit does not alter model code, features, weights, thresholds, production artifacts or the 30-event gate.
