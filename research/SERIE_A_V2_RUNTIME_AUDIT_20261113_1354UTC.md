# Original MARKET_ANCHOR_1X2_V2 — live runtime checkpoint, 2026-11-13 13:54 UTC

This is a read-only audit of the original frozen V2 path. It records the newest actual main-branch source/forward Actions pair and the matching pre-kickoff database state. It is not a model-quality evaluation.

## Immutable model contract

- Main SHA: `40887ebb215730190d7a6c7a1693373ec4afcdfc` (latest main commit remains 2026-10-18).
- Candidate SHA-256: `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.
- Original feature builder Git blob: `401b3a0893371bfa4a488ec92a4a54af2678c8f7`.
- Frozen contract remains 19 features, original 20x2 weights, 3,799 training rows, fingerprint `f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098`.
- `active_lambda=0`; `shadow_lambda=1` research-only; stability gate FAILED; automatic promotion false.
- No model artifact, weight, scaler, imputer, feature order, production `.pkl`, or Supabase schema/data was changed.

## Actual main-branch source/forward run pair

The first 100 repository Actions runs contain two new matching V2 runs on 2026-11-13, both on the unchanged main SHA above:

1. Current-Form Source Capture — [run 43433793441](https://github.com/MaksimBlud/football-ai/actions/runs/43433793441), created 13:27:26 UTC, completed 13:28:24 UTC.
2. Current-Form Forward-Only Preview — [run 43433932979](https://github.com/MaksimBlud/football-ai/actions/runs/43433932979), created 13:28:26 UTC, completed 13:29:13 UTC.

The source run log reports:
- feature-input metadata gate: 110 completed primary-event identities (minimum 30);
- 110 prior-day 2026/27 current-season rows;
- 10 frozen historical CSV files, 3,910 historical match rows, 11 source files total;
- candidate SHA exactly matches the frozen candidate;
- paid provider calls = 0; Supabase writes = 0; target outcomes scored = false.

Source archive:
- artifact ID: `14041720658`;
- ZIP SHA-256: `fd0f01fde281e37711a748aed01fe630c760d9d2879e06470893955e8e5e2932`;
- archive created 13:28:21 UTC;
- latest source observation 13:28:20.165321 UTC.

The forward run independently reported `latest_source_archive_verification.status=VERIFIED`, matched artifact ID/SHA and the successful parent run ID `43433793441`, whose completion time was 13:28:24 UTC. It verified the archive at 13:29:06 UTC, with source age 46 seconds. It then reported:
- `quotes_seen=0`;
- `v2_current_form_shadow_captured=0`;
- `target_outcomes_read=false`;
- `target_outcomes_scored=false`;
- paid provider calls = 0; production/Supabase writes = 0.

The forward report artifact is ID `14042126424`, ZIP SHA-256 `ab1088dde3689c486a372225114fffcba6cd0ea716beb0b60e56db3205adee41`.

**Interpretation:** this is a real source-archive and parent-run SHA/provenance verification, but it is NOT a source-before-quote matched event: there were no quotes, no candidate forecasts, and no per-event source/quote pair. The feature-input gate (110 identities) only permits lagged current-season feature-source preparation. The separate target-outcome evaluation gate remains **0/30 eligible prospective forecasts** and CLOSED. No protected target outcomes were read.

## Source-rights / public-artifact blocker

The main source workflow still ran because the direct-main hold PR below is not merged. The separate source-policy review in [PR #780](https://github.com/MaksimBlud/football-ai/pull/780) records the official Football-Data page update (2026-11-10) and conservatively sets source capture permission to false / `NONE_PENDING_PROVIDER_CLARIFICATION`. This is an internal fail-closed policy decision, not a legal conclusion about every form of manual research.

Both new Actions artifacts were uploaded by workflows in this public repository. The raw source artifact is therefore publicly exposed; the forward artifact is also public. The hold PR gates future live source/quote steps and uploads but does not retroactively remove existing artifacts. This audit did not download, copy, delete, or republish either artifact. Do not use these artifacts for further ingestion/inference until rights and private retention are resolved.

## Read-only Supabase pre-match inventory

Queries selected only `odds_snapshots` and strict pre-kickoff rows in `product_prediction_snapshots`; no score, result, settlement, or target-outcome columns were selected.

- `odds_snapshots`: 3,915 strict pre-match rows across 327 events and 9 leagues.
- Strict pre-match rows in the last 7 days: 0.
- Upcoming events with a saved strict pre-match quote: 0.
- Latest Serie A strict quote: 2026-10-13 14:48:53.042620 UTC (620 rows / 63 events).
- `product_prediction_snapshots`: 40 strict pre-match EPL rows, all `EPL_AI_MARKET_PAIR_V1` with SHA `1e516fe91420fdc2d6479e9fb92b005c4a0c75c7f0f217493dd6b27fd64d99a5`; zero rows for the original V2 candidate SHA.

Therefore no current saved quote can produce a new original-V2 prospective observation. No result table was queried.

## Current PR / CI state

- [PR #781](https://github.com/MaksimBlud/football-ai/pull/781): OPEN, Ready for review, mergeable; exact HEAD `27da7c204d402b76f1f0a52fc1a3bef845fcc5d2`, base main `40887ebb215730190d7a6c7a1693373ec4afcdfc`; 8/8 exact-head Actions SUCCESS. It holds live source/quote and recovery-candidate steps plus all related artifact uploads, while preserving existing triggers/schedules. It is not active on main until HUMAN-MERGE.
- [PR #796](https://github.com/MaksimBlud/football-ai/pull/796): OPEN; exact HEAD `e69ad9c2700b999ef186e4771a2fe06fd010155d`; 7/7 exact-head Actions SUCCESS; atomic source-archive publication. Keep after #781 and revalidate on fresh main.
- [PR #793](https://github.com/MaksimBlud/football-ai/pull/793): Draft, stacked on #787; exact HEAD `a7eeb519d967a05bc528c878b0a8fc458cfbe016`; evaluator 196 tests and Frozen V2 440 tests on Python 3.11 plus 440 on Python 3.12. Offline/synthetic only.
- [PR #800](https://github.com/MaksimBlud/football-ai/pull/800): Draft, 7/7 exact-head CI; offline 5Dollar adapter only. Rights manifest remains HOLD; no API call or real source archive.
- Source audits #794 (Big Balls), #803 (SportAPI), #804 (Live Football API), #790 (open-matchday), #792 (5Dollar), #798 (Stats API), and #802 (Footballdata.io) are documentation/offline checks only. None is approved for capture/inference; each has an explicit rights, field-coverage, timestamp, or private-retention blocker.

## Next safe step

1. Owner manually integrates #781; do not auto-merge.
2. Re-read fresh main and prove every live source/quote and upload step is skipped.
3. Resolve a provider's written model-use/upstream/private-retention scope and private raw-archive destination before any new source request.
4. Only after a genuinely new strict pre-kickoff quote exists may the original frozen 19-feature shadow be captured; preserve source-run completion, raw-page SHA, archive SHA, quote timestamp and kickoff in the same immutable evidence chain.
5. Keep target-outcome reads closed until 30 eligible prospective primary forecasts have completed. Then compare market vs original V2 shadow using the frozen Brier/LogLoss protocol.

No PR was merged, main or schedules were changed, no paid API was called, no Supabase write/DDL was executed, no target outcomes were read, and no production artifact or model contract was modified.
