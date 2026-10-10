# Signal Scout — referee assignment source gate and travel duplicate audit
Date (UTC): 2026-10-10. Status: **BLOCKED_BY_SOURCE** for REFEREE_HOME_ADVANTAGE_1X2_V1; **REJECTED_DUPLICATE_FEATURE_FAMILY** for previously suggested GEO_AWAY_TRAVEL_DISTANCE_1X2_V1.
Research-only; no outcomes, no paid APIs, no registry edits, no production operations.

## Fresh-main / duplicate gate
Read fresh main `research/programs/registry.json` and `PROJECT_CONTINUITY.md`: 14 programs, 13 PROGRAM_DONE and 1 BLOCKED (`point_in_time_snapshot_cadence`). Read open issues: product/development issues #578–#583 and Brain 24-hour experiment #600; no open `[SIGNAL-SCOUT][CANDIDATE]` issue located. Prior Scout source audit:
https://github.com/MaksimBlud/football-ai/blob/scout/20261010-bsd-free-consensus-source-gate/research/scout/2026-10-10-bsd-consensus-pit-audit.md

**Important correction to earlier Scout GEO travel idea**: fresh main already has `V2B_TRAVEL_VENUE_FEASIBILITY_V1`, `V2B_TRAVEL_CITY_STAGE_B_FREEZE_V1`, and `V2B_TRAVEL_CITY_STAGE_B_EVALUATOR_V1`:
- https://github.com/MaksimBlud/football-ai/blob/main/research/V2B_TRAVEL_VENUE_FEASIBILITY_V1_RESULTS.md
- https://github.com/MaksimBlud/football-ai/blob/main/research/V2B_TRAVEL_CITY_STAGE_B_EVALUATOR_V1_RESULTS.md
Existing travel-city source reconstructed 43/43 locked fixtures and 86/86 team-sides. Frozen travel-based direction on **corners market movement** scored 4/13 = 30.77% on nonzero comparable movements, vs constant-UP 9/13 = 69.23%; hypothesis closed. This **does not evaluate travel vs 1X2 outcomes**, but the geographic travel feature family is not new. It cannot be presented as a *principally new* Scout discovery, and retuning opened V2B travel thresholds, signs, away-only variants or league subsets is forbidden. No travel issue opened.

## Independent mechanism under source audit: REFEREE_HOME_ADVANTAGE_1X2_V1
Mechanism: heterogeneity in referee-specific asymmetric yellow/red-card or penalty decisions may moderate the home advantage, potentially conditional on crowd influence. Unlike rest, travel, team strength, shot process, kickoff timing, or odds geometry, this is an identifiable **official-assignment / decision-propensity** input. This is a hypothesis about incremental 1X2 calibration, **not** an allegation of referee misconduct and **not** an established edge.

Scientific context:
- https://www.tandfonline.com/doi/abs/10.1080/02640410601038576 — English EPL study found heterogeneous refereeing home-bias measures, but match-goal result sensitive to one outlier.
- https://ideas.repec.org/a/eee/ecolet/v197y2020ics0165176520303815.html — ghost-match evidence of crowd effects on relative fouls/cards.
- https://www.premierleague.com/en/news/4516739/match-officials-for-matchweek-20 — dated 2026-01-01, published before its weekend fixtures, names match referee and VAR; one verified **example**, not a coverage proof.
- https://www.premierleague.com/en/news/4615111/match-officials-for-matchweek-32-in-2025-26-premier-league-season — dated 2026-04-06, ahead of 2026-04-10 to 13 fixtures; a second example, not a complete immutable archive.
- https://cornerflick.com/data — publishes match referee, timeline, match-level stats under stated CC BY 4.0 compilation license, **but underlying provider rights and historical season/referee coverage are unverified**.
- https://football-data.co.uk/data and https://football-data.co.uk/contact.php — football-data historical referee/cards/odds fields exist, **but official terms explicitly restrict AI-training/commercial product usage**. Do not assume public availability grants Football AI production rights.
- https://elcolegiado.com/developers/ — 9,880 La Liga matches with referee/cards/odds, but CC BY-NC and upstream Football-Data restrictions; `ai-train=no`. Not a clean commercial source.

### Exact candidate feature (provisional, **not frozen**)
At decision time `T = kickoff_utc - 24h`, require a verifiably already-published match-referee assignment. For referee `r`, use **only past matches whose original observation was available by T** to calculate a predeclared shrinkage-smoothed home/away yellow-card asymmetry `(away_yellows-home_yellows)/(away_yellows+home_yellows+1)`, with referee match count, and a parallel past red-card asymmetry; compute a league-season prior and shrink to it using a fixed training-only prior weight. No match-level feature may include any statistic or match result from the target match. Need predeclared handling for VAR and replacements. This is not a new 1X2 outcome test.

### Outstanding outcome-free feasibility gates
1. Predeclare fixture universe (all EPL matches for a *future* full season, not a convenient league subset), horizon T and missingness policy; check archived official appointment publication/first-seen time for **every** target fixture. A present-day article with an old displayed date does not prove that its *current text* was unchanged at T; seek contemporaneous immutable capture or trusted version history.
2. Prove licensed historical referee-level decision fields, match identifiers, original observation availability timestamps and reliable referee identity join, without relying on restricted commercial/AI-use data.
3. Verify at T both appointment and historical referee stats were accessible; quantify exact match coverage and referee-identity failure by round, with zero outcomes read.
4. Verify contemporaneous complete 1X2 fair-probability market baseline at T (all HOME/DRAW/AWAY), with provider receipt and price timestamps, and permitted rights; **closing odds are not a 24h substitute**. Avoid reopening the blocked BSD/TipsAudit source assumptions.
5. Only then ask Research Brain to preregister expanding-season train, temporally held-out validation, and an untouched future OOT cohort; no 2026/27 reserved outcome reads. Baselines: same-time de-vig market, market + league home advantage, and market + generic card rate. Primary: multiclass LogLoss and Brier, paired deltas with league/time-stratified uncertainty. Negative controls: referee IDs permuted *within predeclared league/season/assignment strata*, feature lag perturbation, appointment-missingness-only, and a deliberate future-leakage trap that must fail.
6. SUCCESS only if the predeclared independent OOT confidence interval favors the candidate on **both** proper scoring metrics, and predeclared league/time consistency gates pass. STOP if provenance/rights/coverage fail, either metric is harmed, confidence intervals cross zero, or negative controls match candidate. No threshold, referee, league, or sample cherry-picking; no production change.

### Feasibility verdict
- Mechanism/source pointers: **IDEA**.
- Published pre-match referee assignments: **two examples confirmed**, no season-wide immutable point-in-time coverage.
- Licensed historical referee-decision history with proven as-of timestamps: **NOT VERIFIED**.
- Complete same-T market baseline and independent untouched future cohort: **NOT VERIFIED**.
- **Overall BLOCKED_BY_SOURCE**. No candidate Issue; no Research Brain handoff; no claim of signal.

## Productivity evidence
This run: 0 new data-feasible nonduplicate hypotheses handed to Brain; 0 Scout Issues; 1 earlier Scout novelty claim corrected with exact main evidence; 1 distinct referee source feasibility audit. The previous visible Scout audit also had 0 handoffs and 0 Issues. Actual per-cycle elapsed wall times are not durably logged, so a 24h throughput/speed comparison is **not measurable** and no acceleration claim is justified.

## Safety
No results/outcome tests, no reserved cohort reads, no paid Odds API, no Supabase write, no .pkl/training/promotion, no registry change, no agent/prompt edits, no deployment, no main write.
