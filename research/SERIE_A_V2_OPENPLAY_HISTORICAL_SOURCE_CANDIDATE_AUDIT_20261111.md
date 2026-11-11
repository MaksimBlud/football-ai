# Original MARKET_ANCHOR_1X2_V2 — openplay historical-source candidate audit

**Audit date:** 2026-11-11  
**Scope:** source metadata and schema only; no dataset download, no inference, no feature calculation, no target-outcome access.

## Decision

`openplay` is a **candidate for a separately authorized historical cross-source concordance study only**. It is not approved here as a replacement for the original V2 training/source data, current-form source, or quote source.

Do not connect it to the frozen feature builder or use it to produce prospective V2 forecasts until both (1) upstream data rights are clarified in writing and (2) a frozen feature-by-feature source-parity protocol is approved. The original candidate and its training fingerprint remain untouched.

## Pinned public metadata inspected

Repository: https://github.com/nlbair/openplay

- Default-branch commit: `1681bc4076a290c6a020394ac24792d5141aeeb4` (2026-11-03 17:55:44 UTC).
- README blob: `af0bc2777c4482ce5e9fb6b2773a44b394bbb3cc`.
- LICENSE blob: `142fa4ff0698664de7f81c37d8587f7e34d5f8a5`.
- DATA_DICTIONARY blob: `67aad458fefc7a2d33bcb190ce382131a2216716`.

The repository reports Serie A coverage from 2014/15 through 2025/26: 4,561 matches played, 4,549 with event data (99.74%). That implies 12 Serie A matches without event coverage; the release also documents known gaps and data issues. Coverage is not complete.

## Relevance to the frozen 19-feature contract

The documented `matches` data contains match date, home/away teams, and final scores. The `team_match_stats` data has one row per team per match and documents:

- `date`, `team_id`, `opponent_id`, `side` (home/away);
- `goals_for`, `goals_against`;
- `corners_taken`;
- `yellow_cards`, `second_yellows`, `red_cards`.

In principle, points can be derived from goals for/against, and the date/side fields permit rolling and venue-specific grouping. This means the dataset appears to contain ingredients related to the original V2 features:

- points differential over 5/10 and venue-5;
- goals-for/goals-against differentials over 5/10 and venue-5;
- corners-for/corners-against differentials over 5/10 and venue-5;
- yellow/red-card differentials over 5/10.

This is **schema-level potential only**. No feature values were computed or compared.

### Non-equivalence risks

1. The repository says its statistics are counted from event data and may differ from figures published elsewhere. The frozen V2 training fingerprint was created from a different historical source contract. Numerically similar column names do not prove feature parity.
2. `second_yellows` and straight `red_cards` are separate fields. Do not assume how they map to the original source's red-card count; that mapping needs an explicit source-definition check.
3. The dataset lists 12 Serie A matches without event coverage. Missing rows can alter rolling 5/10 and venue-5 windows for later fixtures; no silent fill or median substitution is permitted as a source-parity workaround.
4. The latest documented season is 2025/26. It contains no 2026/27 current-form archive and no bookmaker 1X2 quote observations.
5. It cannot establish source-before-quote for past observations. Any future use would require pinning a fixed release/commit, archiving exact bytes and SHA-256, and completing the archive before the relevant future quote observation.

## License and upstream-rights gate

The repository's LICENSE declares the data release under **CC-BY 4.0**, says it may be shared/adapted for any purpose including commercial use with attribution to “openplay (Noah Bair)”, and identifies the underlying event data as collected from public WhoScored pages showing an Opta feed (Stats Perform). It also states that the repository is not affiliated with or endorsed by those upstream parties and that rights holders may request removal.

Therefore the repository-level CC-BY declaration is promising but is not treated by this audit as sufficient confirmation of upstream database/feed rights for this project. Obtain written clarification from the dataset maintainer and, where required, the relevant rights holder before any download, storage, training, or inference. Do not infer permission from public accessibility.

## Binding V2 invariants

- Original candidate SHA-256 remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.
- Original 19-feature order, weights, scaler, imputer, training fingerprint and 20x2 matrix remain unchanged.
- `active_lambda=0`; `shadow_lambda=1` remains research-only.
- Stability gate remains failed; NO_BET and automatic-promotion prohibition remain.
- No use of the legacy XGBoost production model.
- No paid odds calls, no Supabase writes/DDL, no production `.pkl` changes, and no target-outcome reads.

## Actions taken

- Read only public GitHub README, LICENSE and DATA_DICTIONARY metadata at the pinned refs above.
- Did not download or materialize any dataset/release archive.
- Did not call an API, access Supabase, read any match result rows, calculate features, run inference, or create forecasts.
- Did not change the original candidate, source manifest, schedules, or other agents.

## Next admissible step

Only after written upstream-rights clarification: define a frozen, source-only comparison protocol for the ten original V2 training seasons, pin the exact openplay release, and measure missing-match/field-definition differences without refitting, selecting features, changing weights, or opening the protected prospective target-outcome cohort. Treat any differences as a source-compatibility result, not a reason to retune V2.
