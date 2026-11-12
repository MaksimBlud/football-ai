# Original MARKET_ANCHOR_1X2_V2 runtime audit — 2026-11-12 15:53 UTC

Repository: `MaksimBlud/football-ai`  
Main SHA: `40887ebb215730190d7a6c7a1693373ec4afcdfc`  
Frozen candidate SHA-256: `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`

## Actual main-branch runtime

### Current-form source capture

[GitHub Actions run 43232728352](https://github.com/MaksimBlud/football-ai/actions/runs/43232728352) completed successfully on main.

- 19 source-capture tests passed.
- Feature-input metadata gate: 110 completed primary fixture identities.
- 10 frozen historical CSVs plus one gated current-season CSV: 11 source files.
- 3,910 historical match rows.
- Candidate SHA matched the frozen V2 candidate.
- 0 paid provider calls; 0 Supabase writes; target outcomes not scored.
- Public artifact ID: `13951945358`, 439,426 bytes.
- GitHub artifact ZIP SHA-256: `e7bb6e90466c278882225766424b17c229cab46da35dd80a4418e627c8ccb1e8`.

### Current-form forward preview

[GitHub Actions run 43232894044](https://github.com/MaksimBlud/football-ai/actions/runs/43232894044) completed successfully.

- 53 tests passed.
- Exact source artifact and successful parent run were verified.
- Source artifact ID `13951945358`, SHA-256 above.
- Parent source run ID `43232728352`, head SHA main `40887ebb215730190d7a6c7a1693373ec4afcdfc`.
- Source age at verification: 48 seconds.
- 0 saved quotes, 0 current-form shadow forecasts.
- 0 target outcomes read/scored; 0 paid calls; 0 production/Supabase writes.
- Public forward artifact ID: `13951795906`, ZIP SHA-256 `5b522ac1c95cee939f2120f584c131c8a51ae3cfd7b6ead882ec09e534037d65`.

This is a real source-archive and parent-provenance runtime proof, **not a prospective forecast** and not model-quality evidence. Because the repository is public, these artifacts are public. Provider AI-use/retention rights and private storage remain unresolved.

### Free historical V2 diagnostic

[GitHub Actions run 43243852372](https://github.com/MaksimBlud/football-ai/actions/runs/43243852372) completed successfully on main at 15:04 UTC.

- 53 offline/source diagnostic tests passed.
- Historical source: Football-Data CSV, 3,800 rows.
- 0 quoted fixtures; 0 feature rows; 0 V2 previews.
- `eligible_for_frozen_prospective_cohort=false`; `no_bet=true`.
- 0 paid provider requests; 0 Supabase writes.
- Mode: `RESEARCH_ONLY_UNVERIFIED_PROVENANCE_NO_BET`.
- Public diagnostic artifact ID: `13954739310`, 425,066 bytes.
- ZIP SHA-256: `b81100b497ce689aa339da25853999c2ffe306eb7fc3541fc0fb22f2c4ccbb95`.

The diagnostic still publishes a public artifact on main; the default-deny workflow hold has not yet been integrated into main.

## Fresh Supabase read-only, pre-match-only counts

Project: `besxwboamipygwvrsblz`.

Strict odds condition: `snapshot_time_utc < commence_time_utc AND snapshot_time_utc <= now()`.

- 3,915 pre-match snapshot rows across 327 events.
- First snapshot: 2026-08-15 12:23:35 UTC.
- Latest snapshot: 2026-10-13 14:48:53 UTC.
- New rows in the last seven days: 0.
- Exact frozen candidate SHA in `product_prediction_snapshots`, with `generated_at_utc < commence_time_utc`: 0 rows / 0 events.

For the separate feature-input gate, only `match_date, home_team, away_team` identity metadata was counted from `league_finished_results` for `SERIE_A / 2026-2027`: 113 rows / 113 unique fixture identities, 2026-08-22 through 2026-11-08. No score, result, or settlement columns were selected. This metadata/input gate does not open the prospective outcome-evaluation gate.

## Live-access hold and CI

[PR #781](https://github.com/MaksimBlud/football-ai/pull/781) remains OPEN, non-draft, mergeable, and HUMAN-MERGE only.

- Exact head: `27da7c204d402b76f1f0a52fc1a3bef845fcc5d2`.
- Base main: `40887ebb215730190d7a6c7a1693373ec4afcdfc`.
- 43 commits ahead / 0 behind.
- 8/8 exact-head workflows SUCCESS.
- Frozen V2 tests: 103 PASS.
- Recovery offline tests PASS; candidate rebuild, proof, and archive upload SKIPPED under default deny; production pickle hashes unchanged.

The PR gates all five original/current-form source/quote/recovery workflows, their live credential bindings, and every artifact upload. The same current-form and diagnostic workflows still ran on main before the hold is manually merged. No merge or main write was performed.

## Scientific status

- Original candidate, 19-feature contract, weights, scaler, imputer and training fingerprint unchanged.
- `active_lambda=0` remains the market baseline; `shadow_lambda=1` remains research-only.
- Prospective V2 forecasts: 0.
- Protected outcome gate: CLOSED (0/30 eligible completed primary forecasts).
- Brier / LogLoss comparison: not available.
- No claim of V2 superiority or production readiness.

No paid API calls, Supabase writes/DDL, production `.pkl` changes, model refits, promotions, bets, or protected target-outcome reads were performed.
