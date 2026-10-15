# Football AI — actual final 120 seconds, five leagues, 2026/27
**Status:** DONE (research-only, no production changes)  
**Coverage:** Completed games dated 2026-08-01 through 2026-10-14 inclusive, EPL / La Liga / Bundesliga / Serie A / Ligue 1.  
**Authoritative reproduction:** [GitHub Actions run 38764264517](https://github.com/MaksimBlud/football-ai/actions/runs/38764264517), head `6ac48c503471b49afb57da039bd975f80097867b` (source collectors); `full_opta_audit.py` executed at that ref.  
**Source data:** public FotMob list/score and Opta season fixtures / per-league full event history from pannadata `opta-latest` GitHub releases. All pulls read-only; no paid Odds API.

## Frozen definition

For each completed match take the exact second-half-ending timestamp *inside Opta*: latest valid event of type `30` and `period_id=2`. For each regulation goal take the Opta type `16` timestamp. Both are measured in elapsed match seconds as `minute*60+second`.

A match is positive if `final_end_seconds - 120 <= goal_seconds <= final_end_seconds` for one or more goals. Distinct matches, not goals, form the denominator. No conversion of 90+4/90+5 to final 120s. Exclude unavailable/unverifiable cases rather than inferring no goal.

Strict matching used competition + local calendar date + home/away final score + both team identities, allowing explicitly normalized Auxerre / Rennes official names. All 297 matches joined one-to-one, 0 duplicates in the final keyed sample, all goals reconciled against final results, and period-end records present.

## Final results

| League | Matches verified | Goal in last 120s | No goal | Goal frequency |
|---|---:|---:|---:|---:|
| Premier League | 60 | 5 | 55 | 8.33% |
| La Liga | 78 | 1 | 77 | 1.28% |
| Bundesliga | 45 | 4 | 41 | 8.89% |
| Serie A | 60 | 4 | 56 | 6.67% |
| Ligue 1 | 54 | 6 | 48 | 11.11% |
| **TOTAL** | **297** | **20** | **277** | **6.73%** |

20 goal-bearing games; 20 qualifying goals. 0 remaining UNKNOWN classifications. Empirical no-goal rate is 277/297 = 93.266%; a goal happens in roughly 1 of 14.85 games.

### All qualifying matches (goal interval before final whistle)

| League | Date | Home — Away | FT score | Goal occurred before end |
|---|---|---|---|---:|
| EPL | 2026-08-23 | Newcastle — Liverpool | 2–2 | 67s |
| EPL | 2026-08-30 | Chelsea — Brighton | 4–3 | 43s |
| EPL | 2026-09-06 | Everton — Manchester United | 2–2 | 96s |
| EPL | 2026-09-12 | Sunderland — Arsenal | 0–2 | 74s |
| EPL | 2026-09-19 | Tottenham — Aston Villa | 2–3 | 37s |
| La Liga | 2026-09-13 | Real Sociedad — Atlético Madrid | 0–3 | 81s |
| Bundesliga | 2026-08-30 | Augsburg — Schalke 04 | 3–0 | 95s |
| Bundesliga | 2026-09-05 | Werder Bremen — RB Leipzig | 3–1 | 88s |
| Bundesliga | 2026-09-06 | Hamburg — Mainz 05 | 0–5 | 120s |
| Bundesliga | 2026-09-11 | Union Berlin — Schalke 04 | 1–3 | 55s |
| Serie A | 2026-08-23 | Torino — Milan | 1–2 | 91s |
| Serie A | 2026-08-31 | Atalanta — Bologna | 1–0 | 113s |
| Serie A | 2026-09-13 | Sassuolo — Juventus | 3–2 | 71s |
| Serie A | 2026-10-10 | Napoli — Frosinone | 3–0 | 77s |
| Ligue 1 | 2026-08-21 | Marseille — Strasbourg | 4–0 | 107s |
| Ligue 1 | 2026-08-28 | Lille — Paris Saint-Germain | 2–2 | 93s |
| Ligue 1 | 2026-08-29 | Brest — Toulouse | 2–2 | 58s |
| Ligue 1 | 2026-09-06 | Troyes — Strasbourg | 2–6 | 82s |
| Ligue 1 | 2026-10-11 | Rennes — Auxerre | 4–1 | 76s |
| Ligue 1 | 2026-10-11 | Troyes — Marseille | 0–2 | 26s |

## Goals recorded after the 90th minute (separate, fixed-minute descriptive measure)

| Minute | Goals |
|---|---:|
| 90+1 | 16 |
| 90+2 | 13 |
| 90+3 | 8 |
| 90+4 | 7 |
| 90+5 | 8 |
| 90+6 | 7 |
| 90+7 | 2 |
| 90+8 | 3 |
| 90+9 | 1 |
| 90+10 | 1 |
| 90+13 | 1 |
| **Total after 90:00** | **67** |

These counts refer to Opta match-clock buckets, not to the final-120s interval. Exactly 20 of these events were in final-120s. The number of goals may exceed the number of goal-bearing matches, but here each of the 20 goal-bearing matches had one qualifying goal.

## Score gap at the instant the final 120s started

| Score difference | Games with goal | Without goal | Eligible games | Goal rate |
|---|---:|---:|---:|---:|
| Draw | 2 | 71 | 73 | 2.74% |
| One-goal lead | 7 | 112 | 119 | 5.88% |
| Two-goal lead | 6 | 44 | 50 | 12.00% |
| Three or more | 4 | 50 | 54 | 7.41% |

All 277 no-goal games can use their final score as their prewindow score. Prewindow score is recoverable for 19 of 20 goal-bearing games from Opta scoring-team fields; one positive was excluded **only from this score-stratified analysis** because its prewindow home/away split could not be independently reconciled. Therefore stratified N=296 (not 297). Four-cell Pearson chi-square exploratory test gives χ²≈4.38, df=3, p≈0.223: **not statistically significant**. The apparent high rate when leading by two is not proof of a causal or predictive effect.

## Fair price and limits

- Empirical P(no goal in final 120 seconds) = 277/297 = **93.266%**.
- No-margin empirical break-even decimal odds: 297/277 = **1.0722**.
- Illustrative realized-sample profit/loss assuming a fixed bet each match: odds 1.05 → −2.07% per unit staked; 1.06 → −1.14%; 1.07 → −0.21%; 1.08 → +0.73%; 1.10 → +2.59%. These **are not** a validated forward bet strategy.
- Approximate Wilson 95% interval for P(goal): **4.40% to 10.17%**, wide because N=297 and positives=20.
- Betting-market quoted prices, commission, suspended markets, settlement rules, and OOS validation **have not** been checked. Do not claim a profitable strategy or tune new thresholds post hoc.
- Earlier seasons' 94–95-minute figures (e.g. 2024/25, 2025/26) are **different indicators** and are not directly comparable to actual final-120s probabilities.

## Audit trail

Workflow: `.github/workflows/research-last120-whistle.yml`  
Collectors: `research/last120_20261015/audit.py`, `opta_probe.py`, `whistle_probe.py`, `full_opta_audit.py`  
GitHub Actions artifact: `last120-202627-evidence`, containing raw/merged/fully independently audited JSON outputs including `all_opta_matches.json` and `all_opta_summary.json` (artifact retention 7 days; this report remains in git).

No write to Supabase, no change to production artifacts/models, no paid The Odds API, no automatic promotion or merge. Main branch remains unchanged. This is a research-only candidate for future prospective out-of-sample validation.
