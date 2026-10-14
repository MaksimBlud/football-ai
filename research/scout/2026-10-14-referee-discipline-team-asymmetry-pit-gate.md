# Signal Scout — Referee × team disciplinary asymmetry, pre-kickoff source gate

**Audit date:** 2026-10-14 UTC. **Status:** IDEA / WAITING_BY_HISTORICAL_PIT_AND_MARKET. **Outcome reads/tests:** NONE. **No candidate issue.**

## Repository and duplicate guard
Read fresh `main` `research/programs/registry.json` (14 programs: 13 PROGRAM_DONE, 1 BLOCKED), `PROJECT_CONTINUITY.md`, research-issue search and Scout branches. No referee 1X2 disciplinary-interaction research issue was found. **Critical prior work:** `REFEREE_CORNER_BIAS_DIRECTION_V1` was already tested and failed, documented in `PROJECT_CONTINUITY.md` (2026-10-04 six-family corner screen). This proposal is **not** an attempt to reopen referee-corner direction, to retune its thresholds, or to reuse its opened corner OOT. Its potential independence is a different **causal channel** (card/red-card risk in 1X2, not corner repricing) and a team–referee interaction. Full report/issue duplicate audit remains required before admission.

## Proposed hypothesis (not a discovered signal)
**REFEREE_DISCIPLINE_TEAM_ASYMMETRY_1X2_V0**. An officially appointed on-field referee's *historical* disciplinary strictness may interact with the two teams' *historical* booking propensity, changing their relative risk of playing with fewer players and thus fair 1X2 probabilities beyond bookmaker consensus. This is observational; appointments are not random, market may fully price it, and yellow cards are an imperfect proxy for red-card risk.

Exact proposed **as-of** features, all computed strictly before a predeclared decision timestamp (e.g. kickoff−24h):
1. `ref_yellows_per_match_shrunk`: referee's lagged `HY+AY` divided by number of prior officiated matches, shrunk toward league prior with fixed preregistered strength.
2. `team_yellow_rate_home_pre` and `team_yellow_rate_away_pre`: respective clubs' lagged booking rates, using only previously completed matches and a frozen lookback.
3. `strictness_x_team_asymmetry`: (referee rate − league prior) × (home rate − away rate).
4. `ref_history_count` and missingness flag, so debutants never inherit fabricated history.
5. `assigned_VAR_id` retained as **provenance/control only**, not a tuned feature until independent VAR decision-history coverage is proved.

No current-match bookings, referee post-match assignments, outcomes, future team form, market closing prices as pre-24h features, or in-play variables are allowed.

## Primary source: official dated appointment announcements
- 2026/27 Matchweek 7, **published 2026-10-12**, first kickoff **2026-10-17**: https://www.premierleague.com/en/news/4731949/match-officials-for-matchweek-7
- Independent pre-kickoff secondary corroboration dated **2026-10-12**: https://www.soccergraph.com/2026/10/premier-league-matchweek-7-referee-appointments.html
- 2025/26 Matchweek 1, published **2025-08-11**, first kickoff **2025-08-15**: https://www.premierleague.com/en/news/4373339/match-officials-for-matchweek-1-in-2025-26-premier-league-season
- 2025/26 Matchweek 7, published **2025-09-29**, first kickoff **2025-10-03**: https://www.premierleague.com/en/news/4430374/match-officials-for-matchweek-7
- **Negative control:** 2024/25 Matchweek 1 article dated **2024-08-17** despite opening fixture **2024-08-16**; the date cannot prove eligibility for every match: https://www.premierleague.com/en/news/4079193
- **Negative control:** 2024/25 Matchweek 38 article dated the match day **2025-05-25**; day-level metadata alone cannot prove kickoff−24h eligibility: https://www.premierleague.com/en/news/4311115/match-officials-for-matchweek-38

### Outcome-free pre-kickoff fixture/official manifest, MW7 2026/27
The following **10 future fixtures** and appointments are displayed by the official announcement dated Oct 12. This report's GitHub commit (if accepted before Oct 17) is an independently timestamped **prospective evidence capture**, not proof that every archived past article was immutable. No results were inspected.

| Kickoff day (local UK) | Fixture | On-field referee | VAR |
|---|---|---|---|
| Oct 17 | Everton–Chelsea | Paul Tierney | Nick Hopton |
| Oct 17 | Brentford–Liverpool | John Brooks | Darren England |
| Oct 17 | Fulham–Hull City | Chris Kavanagh | James Bell |
| Oct 17 | Manchester City–Ipswich Town | Farai Hallam | Andrew Kitchen |
| Oct 17 | Newcastle United–Aston Villa | Jarred Gillett | Stuart Attwell |
| Oct 18 | Bournemouth–Sunderland | Craig Pawson | Tony Harrington |
| Oct 18 | Brighton–Crystal Palace | Rob Jones | Paul Howard |
| Oct 18 | Leeds United–Manchester United | Darren England | Peter Bankes |
| Oct 18 | Nottingham Forest–Arsenal | Michael Oliver | Michael Salisbury |
| Oct 19 | Tottenham–Coventry City | Andy Madley | Paul Tierney |

**Sample coverage statement:** 10/10 listed fixtures in this single future round have referee and VAR names on the published page; this is **not** league-wide seasonal coverage, nor proof of each appointment's original edit timestamp. Two historical 2025/26 rounds likewise show 10 listed assignments each, but historical revision integrity and replacements are unaudited. A round can be published on/after its first kickoff (counterexamples above), and announcements can be corrected later.

## Lagged discipline source and provenance caveats
- Source field documentation `Referee`, `HY`, `AY`, `HR`, `AR`: https://github.com/natbutter/footviz/blob/master/notes.txt
- Football-Data primary portal: https://football-data.co.uk/data
- EPL field schema cross-check: https://datahub.io/football/english-premier-league
- These sources describe match statistics **after** each match; historical feature generation must use strictly older fixtures, never same-match statistics. Actual season-level completeness and referee-name identity joins were **not** measured. Rights for reuse in a public/commercial AI product require explicit verification; do not assume derivative license overrides primary source terms.
- Historical odds opening/closing are not a verified **kickoff−24h** quote snapshot. The previously audited TipsAudit source is blocked on `quote_observed_at`. No independently attested matched market baseline has been established here.

## Outcome-free feasibility plan (Research Brain must own freeze)
1. Inventory *every* EPL match in a preregistered training/validation span independently of referee availability. Find earliest published appointment and correction history; exclude/flag missing appointments, never fill using post-match referee identity. Match all official announcements to fixtures with exact kickoff and capture `source_publication_date`, `capture_timestamp`, `earliest_provable_availability`.
2. Check referee identity/name disambiguation and lagged stats coverage without opening target-match outcomes or any reserved 2026/27 result. Validate rights/terms of source.
3. Find same-fixture **time-aligned** bookmaker 1X2 snapshots at the *same frozen decision horizon*, convert to fair probabilities using a fixed preregistered de-vig rule; if absent, BLOCKED_BY_MARKET.
4. Proposed conservative source gate for Brain review (NOT FROZEN): >=90% verified appointments, >=90% lagged-feature coverage and >=90% matched timestamped 1X2 quotes over >=2 full EPL seasons, with replacement audits; otherwise STOP/BLOCKED.
5. Only after Brain preregisters cohorts and gates, compare fair-market-only vs identical market + one frozen referee×team interaction on log-loss and multiclass Brier, including calibration and fixture-cluster bootstrap. Use untouched OOT **only if Research Brain proves it is not already reserved/opened**; do not use 2026/27 reserved V2 outcomes.
6. Negative controls: shuffle referee assignments within predeclared fixture/round blocks preserving observable assignment constraints; remove interaction; compare referee-only and team-only effects; inspect selection confounding (derbies, team strength, home/away, referee appointments).
7. SUCCESS requires predeclared validation and untouched OOT improvements in **both** Brier and LogLoss with paired CI excluding zero, no material calibration harm or league/time instability. STOP if PIT, rights or market gate fails; if null or unstable, close NO_BET without new thresholds.

**Outcome-free audit verdict:** interesting independently motivated *idea* and a genuine forward-dated official 10-fixture source manifest, but **WAITING**, not DATA_FEASIBLE, ACTIVE or SIGNAL_FOUND. No candidate Issue, no registry edit, no training, no production, no paid API, no Supabase writes.
