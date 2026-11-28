# Original MARKET_ANCHOR_1X2_V2 — PitchAPI source-rights and field-coverage audit

**Original review:** 2026-11-25 UTC  
**Superseding official-plan recheck:** 2026-11-28 20:05 UTC  
**Decision:** **HOLD — free research access is advertised, but data rights, corners coverage and point-in-time provenance are not established.**  
**Scope:** official PitchAPI pages and PyPI SDK metadata only. No account or API key was created; no API or odds endpoint was called; no response, match payload or dataset was downloaded; no Supabase access or protected-outcome read occurred.

## Executive finding

PitchAPI is a technically interesting candidate: its current public pages advertise 77 leagues, 25 endpoints, history from 2021, and a Free plan with a 15,000-request daily allowance. The current pricing page distinguishes plan positioning:

- Free is described for **side projects, research and evaluation**.
- Pro is **€4.99/month** and is positioned for **products and daily pipelines**.
- The pricing page does **not** explicitly define commercial-use rights or grant a data licence. Do not treat plan positioning as a legal grant.

The candidate remains **not approved for original V2 ingestion**. The official pages do not surface a service-data licence or terms URL; the PyPI page says its MIT licence applies only to SDK source and that returned football data is governed separately by PitchAPI terms. The public docs do not document a match-level corners field, do not identify upstream data providers, and do not provide historical match-stat first-observed or correction timestamps. Serie A 2026/27 per-fixture completeness and exact frozen 19-feature parity remain unverified.

## Superseding official pricing and documentation review — 2026-11-28

Official pages reviewed:

- Home: https://pitchapi.dev/
- Pricing: https://pitchapi.dev/pricing
- API reference: https://pitchapi.dev/docs
- Python SDK metadata: https://pypi.org/project/pitchapi/

The current pricing page advertises:

- Free: €0; 15,000 requests/day; 600 requests/minute sustained; live snapshot 60 requests/minute.
- Free includes all 77 leagues, all 25 endpoints and full history back to 2021.
- The Free plan is positioned for side projects, research and evaluation.
- Pro: €4.99/month, unlimited requests, positioned for products and daily pipelines.
- The pricing page does not explicitly define commercial-use rights or state that the Pro tier grants a particular right to train or run internal models.
- No credit card is required for Free.

This supersedes the earlier description of PitchAPI as having no paid tier or unlimited free requests. The current Free allowance is finite, and a separate Pro tier exists.

The API reference describes a read-only REST API, match summaries, upcoming fixtures, match statistics, events, lineups, player/team data and advanced analytics. It documents RFC 3339 UTC timestamps for API date/time values. The live-match endpoint has `fetched_at`, `age_seconds` and `stale`; those fields are documented for the live snapshot and are not a historical source-observation/correction record for stored match statistics.

The docs describe team statistics per half and for the full match, but the reviewed public reference does not expose a stable, explicit match-statistics corner-count key. The event model documents yellow-card and red-card events, but that does not supply the six frozen corner-form features. No field-level Serie A 2026/27 completeness matrix was found.

## Rights and provenance blockers

1. **Service-data terms are not located.** The official PyPI page says the MIT licence covers the SDK source only; access to the service and returned football data is governed separately by PitchAPI terms. The reviewed official navigation/pages do not expose a terms URL or data licence.
2. **Plan positioning is not a data licence.** Free is positioned for research/evaluation and Pro for products/daily pipelines, but the pricing page does not expressly define commercial-use rights, internal model training/inference rights or private raw-response retention.
3. **Upstream rights are unknown.** The docs describe data as coming from a raw event feed but do not identify upstream football-data providers or grant field-level rights for internal ML/model inference and private raw-response retention.
4. **Corners are undocumented.** The frozen V2 requires six corner-derived features. No documented match-level corner-count field or corner event type was found in the reviewed PitchAPI reference. Do not infer corners from another metric.
5. **No historical source-before-quote proof.** The live endpoint documents `fetched_at`, `age_seconds` and `stale`; no per-match historical first-observed or per-field correction timestamp is documented for stored match statistics. A future local receipt UTC + SHA-256 archive could prove possession before a later quote, but it has not been authorized or created.
6. **Coverage is unverified.** The 77-league claim does not prove Serie A 2026/27 match-by-match completeness for every required feature or equivalence to the frozen Football-Data training definitions.

## Frozen 19-feature compatibility

The unchanged original V2 requires, among other fields, six corner-derived inputs:

- `diff_corners_for_5`
- `diff_corners_for_10`
- `diff_corners_against_5`
- `diff_corners_against_10`
- `diff_corners_for_venue5`
- `diff_corners_against_venue5`

The reviewed PitchAPI documentation does not document a corners field or corner events. It documents yellow-card and red-card event types and a team-statistics endpoint, but exact field-level completeness and semantic parity for Serie A are not established. Therefore PitchAPI cannot currently supply a verified, unchanged 19-feature vector.

Do not impute undocumented corners as zero, substitute another statistic, alter feature order, or mix a different source to fill missing fields.

## Requirements before reconsideration

- A published or written API data licence permitting the intended internal model use and private raw-response retention.
- Written identification/clearance of upstream data providers and field-level rights.
- Written clarification of whether either plan permits internal ML/model inference and whether Free can be used for the intended non-commercial research.
- A documented corners field and stable definitions for corners, yellow cards and red cards matching the frozen V2 feature semantics.
- Per-match historical source observation/correction timestamps, or an owner-approved immutable capture design that records exact response bytes, local receipt UTC and SHA-256 strictly before each later quote.
- Read-only evidence of Serie A 2026/27 per-fixture/per-field coverage and missingness before feature calculation.
- Separate owner authorization before account creation, key issuance, API request, download, feature calculation or inference.

Until every requirement is independently established, keep PitchAPI at HOLD. Do not create an account, request a key, call the API, fetch odds, download data, calculate V2 features or run inference from PitchAPI.

## Frozen V2 invariants

The original candidate remains unchanged: SHA-256 `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, 19 ordered features, 20×2 weights, `active_lambda=0`, `shadow_lambda=1`, historical stability gate FAILED, prospective evaluation gate CLOSED. This audit does not alter model code, features, weights, thresholds, production artifacts or the 30-event gate.

## Actions not performed

- No PitchAPI account or API key.
- No PitchAPI API request, odds request, source response or data download.
- No Supabase access, writes or DDL for this source audit.
- No protected 2026/27 outcome reads.
- No feature calculation, inference, refit or model evaluation.
- No production `.pkl` changes, merge, main update, promotion, schedule change or other-agent setting change.
