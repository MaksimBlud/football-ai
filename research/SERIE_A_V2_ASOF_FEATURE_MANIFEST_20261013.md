# Serie A frozen V2 — as-of historical football feature adapter (13 October 2026)

**Research-only diagnostic.** This implementation does **not** refit, recalibrate, promote, or publish V2, and does not call The Odds API, another network provider, or Supabase.

## Existing code and inputs reused

- Frozen original `research/models/market_anchor_v2_serie_a_frozen_candidate.json`, including its exact 19 `ALL_FOOTBALL` feature names in frozen order.
- Existing `historical_football_signal_lab.TeamMatch` and `_snapshot` formulas. It does not invent new football features or substitute zero for missing values.
- **Already stored** Football-Data-compatible `Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR,HC,AC,HY,AY,HR,AR` historical rows. No paid provider or new source is needed.
- Previously saved quote rows with `league,event_id,home_team,away_team,commence_time_utc,snapshot_time_utc`, optionally the original decimal 1X2 quotes for subsequent preview.

## Strict data use and limits

Historical results are filtered **before 00:00 UTC on the snapshot's calendar day**. Even if the source contains results recorded later that same day, they are not read into features. Source has date-only timestamps, so exact result publication time **cannot** be verified; this is conservative but **not independently attested information-time provenance**.

The adapter checks missing or invalid original goal/corner/card stats, result/score disagreement, duplicate fixture identities, bad or inconsistent event IDs, wrong league, and quotes recorded at or after kickoff. Legitimately absent previous **venue** history becomes JSON `null`, which is the *original frozen model's* median-imputation input, never silently zero.

**IMPORTANT:** existing historical source files created/updated after the market quote do not provide historical knowledge proofs. Diagnostic output does not count as prospective cohort, remains `NO_BET` / not product-publishable, and is not a substitute for independent historical-source availability timestamps. Capture of *new* genuine quotes and an independently verifiable information-time ledger remains necessary before prospective admission. The known 30-settled-match frozen evaluation gate, model stability gate, and unchanged incumbent comparison still apply.

## Offline usage

```bash
python serie_a_v2_asof_feature_manifest.py \
  --existing-history-csv /path/to/already-saved-serie_a_historical_football_data.csv \
  --saved-quotes-json /path/to/saved-upcoming-serie_a_snapshots.json \
  --manifest-json /tmp/serie_a_v2_features_diagnostic.json \
  --audit-json /tmp/serie_a_v2_history_audit.json
```

The manifest is compatible with `serie_a_v2_frozen_shadow_preview.py --features-json ... --saved-supabase-quotes` and is **never evidence for production or frozen prospective capture**. The audit records SHA256 of supplied files, count of history rows, frozen model fingerprint and explicit ineligibility.

## Live data blockers independently checked 13 October

- Supabase Serie A odds: 605 old rows, newest 2026-09-11, no future event. 
- Existing Serie A paid workflow is **manual** by deliberate budget contract; it must remain manual until explicit fresh user authorization of a paid provider call. The separate two-hour live cycle cannot create missing odds.
- Supabase `league_finished_results` for Serie A has only 53 2026/27 results through 2026-09-20; `matches` has only EPL and cannot supply Serie A corners/cards.
- This PR cannot, and does not claim to, create live qualified V2 forecasts from absent inputs. Source freshness and independently verified feature publication times are separate blockers.

## Tests

Dedicated V2 shadow tests cover exact 19-feature order, passing the diagnostic manifest to actual SHA-pinned V2 inference, same-day/future exclusion, missing source stats, fake/mismatched quote rejection, duplication and no database/provider writes. Workflow is triggered by this adapter and its regression tests.
