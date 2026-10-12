# SIGNAL-SCOUT — BeatTheBookie exporter PIT and selection-bias static audit (2026-10-12)

**Verdict: BLOCKED_BY_RAW_SOURCE_PROVENANCE_AND_OUTCOME_CONDITIONED_EXPORT.** This is a source-quality finding, **not** a new signal, not DATA_FEASIBLE, and not a reason to reopen a PROGRAM_DONE family. No new candidate Issue / Research Brain handoff / match outcome test.

## Repository context and duplicate check
Read fresh `main` `research/programs/registry.json`, `PROJECT_CONTINUITY.md`, Scout branches and GitHub Issues. The registry contains 14 programs (13 PROGRAM_DONE, 1 BLOCKED, #594); prior BeatTheBookie source audit exists in `scout/20261012-beatthebookie-historical-1x2-source-gate`. This note **only adds a previously unrecorded exporter integrity gate**, not a new signal family.

## Direct primary evidence
- Original author's [README and data description](https://github.com/Lisandro79/BeatTheBookie/blob/master/README.md) describes `matches`, `odds_history`, `odds_history_series` and `odds_datetime`; raw SQL is not embedded in GitHub.
- [First series exporter](https://github.com/Lisandro79/BeatTheBookie/blob/master/src/generate_odds_series_csv.php) blob SHA `8c7feb8386723ddeaa407fe6cc6f3c025144b14a`.
- [Second series exporter](https://github.com/Lisandro79/BeatTheBookie/blob/master/src/generate_odds_series_b_csv.php) blob SHA `28e562670c527feb23d62973b06ae801aa685bd4`.
- [Kaggle dataset card](https://www.kaggle.com/datasets/austro/beat-the-bookie-worldwide-football-dataset) lists five compressed files and a stated CC BY-SA 4.0 license; **not** independent evidence of upstream bookmaker permissions or quote collection timestamps.

## Confirmed code-level issues (no football outcomes read)
1. **Outcome-conditioned fixture universe.** Both exporters select `matches` using `result not like ...`, `result <> ''`, and extra-time/penalty filters. This selects matches based on post-match completion/status, and therefore **cannot establish the pre-kickoff fixture denominator** or prospective coverage without a separate point-in-time fixture source. The audit inspects SQL source text only, not any match results.
2. **Hourly CSV strips original quote timestamps.** The exporters read `ohs.odds_datetime` but write only 32 rows x (72 hourly bins x 3 outcomes) per match. Bins are reconstructed relative to `strtotime($row->date)`; exact per-quote timestamps, ingestion timestamps and raw offer identity are not exported. A bin label is **not** a source first-seen receipt timestamp. Final stored kickoff may also differ from the earlier scheduled kickoff, requiring independent fixture-revision checks.
3. **Conditional disabled/reactivation defect.** Each exporter adds disabled bookmaker indices to `$already_disabled` and never removes them; on *every subsequent sampling marker* it forces that bookmaker to `nan`. If a later valid offer exists for the same bookmaker/outcome after a disable marker, the next sampled value is still `nan` even though `$current_array` was updated. Toy no-outcome trace: quote at T-60h, disable at T-50h, new quote at T-30h, sample T-24h -> exporter `nan`, whereas an active new quote would imply its price. **This is a conditional code-path finding; actual frequency cannot be measured without raw rows.** `$disabled_dates` also overwrites per-bookmaker entries without an explicit ordering in the SQL query, so it may not capture multiple distinct offer disable times.
4. **Final scores embedded in filenames.** Both exporters construct filenames ending `_$score1_$score2.txt`; a feature pipeline must never derive match identity from score-bearing filenames or accidentally expose these values to feature engineering. This was noted in the previous audit and remains a hard exclusion.

## Outcome-free source access attempt
- Public Kaggle data card confirms compressed filenames, but direct Kaggle API view/download URLs were inaccessible to the web tool; container network DNS for Kaggle failed. Original author Dropbox links returned an error in the web reader and the Google Drive folder redirected to sign-in. **Raw records fetched: 0. Complete pre-match same-book 1/X/2 triples: unmeasured.** No historical first-seen metadata proved.
- This is not proof that files are universally unavailable; it is a runtime access limitation.

## STOP / exact future gate
**STOP:** Do not use exported hourly matrices as certified PIT fair 1X2 baseline, do not count exporter-selected completed matches as all fixtures, and do not compute any signal performance on this archive yet.

Reopen source feasibility only if lawfully accessible **raw** SQL/CSV (not outcome-bearing filename features) can be hashed and read with `match_id, original scheduled kickoff, bookmaker, 1/X/2, odds_datetime, odds, offer disabled_date, independent observed_at/first_seen`, plus pre-kickoff fixture-universe history and source-rights verification. Freeze T = kickoff - 24h before examining outcomes; require same-book three-way triples, no quote after T, actual historical publication provenance, coverage by fixed five leagues and seasons, and an independent first-seen proof. If any required provenance is absent, retain BLOCKED.

If a genuinely new football mechanism later passes this gate, **Research Brain only** preregisters matched-timestamp fair 1X2 market control, temporal validation / untouched OOT, paired Brier/LogLoss with uncertainty, negative controls, and STOP/SUCCESS. No historical outcome tests in Scout.

## Run accounting
- New independent hypotheses: 0; DATA_FEASIBLE: 0; Research Brain handoffs: 0; new Scout Issues: 0.
- One new verifiable static source integrity finding: **outcome-conditioned fixture universe** plus the conditional reactivation defect and timestamp-loss detail.
- No paid The Odds API calls, no Supabase writes, no production model/registry/deploy changes, no 2026/27 reserved outcomes.
- Prior visible reports show zero confirmed handoffs. No reliable per-run wall-clock logs to compare 40-minute cycle duration over 24h.
