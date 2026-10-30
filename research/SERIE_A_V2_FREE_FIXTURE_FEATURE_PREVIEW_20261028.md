# Original Serie A V2 — zero-credit fixture feature-readiness probe (2026-10-28)

## Purpose

The verified Football-Data source archive currently contains completed Serie A rows only through 2026-10-25, and saved odds snapshots have no fresh future pre-kickoff rows. This separate probe tests whether the already configured The Odds API account can expose future Serie A event identities through its documented **free `/events` endpoint** without requesting odds or spending quota.

Official provider documentation says `/v4/sports/{sport}/events` returns event ID, teams, and commence time without odds and does not count against the usage quota: https://the-odds-api.com/liveapi/guides/v4/.

## Strict contract

- Manual `workflow_dispatch` only; no cron, no workflow-run trigger, no automatic provider call.
- Before the single provider request, query Supabase read-only for exactly `match_date, home_team, away_team` from the current Serie A feature-input gate; do not select scores, results, settlements, or target outcomes.
- Require the current metadata-only identity set to match the authenticated source archive's gate identities/count/SHA and require zero missing identities. Verify the successful `main` source parent, ZIP SHA-256, frozen candidate SHA, and fixed 24-hour source age before the provider request.
- The live path requires the identity/freshness verifier introduced by PR #699. If that guard or the read-only identity reader is not present on `main`, it fails closed before archive discovery/provider access.
- Make exactly one HTTPS request to `/v4/sports/soccer_italy_serie_a/events`, with redirects disabled and no retry. Do not call `/odds`, `/event odds`, `/scores`, or `/historical`.
- Require response header `x-requests-last: 0`; missing or nonzero cost fails closed. Do not print or serialize the API key or full provider URL/body.
- Accept only event identity metadata (event ID, sport key/title, home/away teams, commence time). Reject unexpected fields that could carry odds or outcomes; ignore in-play events.
- Reuse the exact original V2 feature builder pinned by Git blob SHA `401b3a0893371bfa4a488ec92a4a54af2678c8f7` and the unchanged frozen candidate `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`. Emit the 19 input features and missingness/history-age diagnostics only.
- Emit **no probability vector**, no market residual, no forecast eligibility, no Brier/LogLoss, and no target-outcome read. The preview is not an admitted prospective forecast and cannot count toward the 30-completed-forecast evaluation gate.
- Supabase access is limited to the read-only identity gate query above. No Supabase writes/DDL, no target-result columns, no production artifact/model load, no production `.pkl` mutation, no publication, no betting, and no promotion.

## Why this is separate

The fixture endpoint is a metadata source, not an odds source. Its output can help check upcoming event identity and prequote feature availability, but it cannot supply the market anchor. The metadata-only Supabase gate query is necessary because an archived gate can become stale if another primary fixture completes after source capture. The original V2 forward workflow continues to accept only saved, fresh, strictly pre-kickoff odds snapshots whose source archive and successful parent run completed earlier. No old October 13 quotes may be backfilled.

## Verification status

The unit tests use mocked provider responses and synthetic historical rows; they do not call the provider. The manual live workflow is not run from PRs. A real live artifact is required after human merge and manual dispatch before claiming fixture-source availability. If the provider reports no future events, the artifact records `NO_UPCOMING_FIXTURES`; this does not imply a model failure or permit a forecast.
