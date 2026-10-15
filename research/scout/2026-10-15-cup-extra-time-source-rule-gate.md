# Signal Scout — 2026-10-15 — Cup extra-time carryover: source and rule gate

**Status:** IDEA / WAITING_BY_VERIFIED_120_MIN_COVERAGE_AND_PIT_MARKET  
**Decision:** Do not create a [SIGNAL-SCOUT][CANDIDATE] Issue; do not transfer to Research Brain until outcome-free data feasibility passes. No outcome tests or 2026/27 outcome reads.

## Repository check first
- Fresh main: `328bc3966c657976908acdce94809a11fdd18a24` (GitHub compare main...main).
- Read `research/programs/registry.json` (14 programs: 13 PROGRAM_DONE, 1 BLOCKED), `PROJECT_CONTINUITY.md`, open issues and Scout issue search.
- GitHub issue searches for "extra time", "penalty shootout", "fatigue" returned no matching issues. This **does not** prove absence from all older research reports. Related existing rest/travel/calendar families must be audited before any candidate.
- Never reopen PROGRAM_DONE or retune its thresholds/OOT.

## One mechanistically distinct preliminary idea
**`PREVIOUS_CUP_EXTRA_TIME_LOAD_1X2_V0`**: extra 30 minutes played in the *last completed knockout cup fixture* may change team-level fatigue/rotation at the next league fixture, over and above identical elapsed recovery hours and market fair probabilities. This is a potential incremental **minutes-load shock**, not another weekday/rest-gap transform.

Research motivation: Mohr et al. (2023), *Extended Match Time Exacerbates Fatigue and Impacts Physiological Responses in Male Soccer Players*, DOI https://doi.org/10.1249/MSS.0000000000003021. The experiment documented worse metabolic/physical fatigue after 120 versus 90 minutes. This is physiological evidence, **not evidence of 1X2 predictive edge**.

Preliminary exact feature contract (NOT frozen): for each team before fixture kickoff, identify last *completed* cup fixture; record cup kickoff and completion timestamp, competition and stage, **verified actual 120-minute participation** (0/1), hours elapsed until next league fixture and opponent differential. If cup completion/publication cannot be verified earlier than prediction as-of, mark missing, never infer from score/penalties. A player-minutes extension is forbidden without independently lawful PIT lineup/minute source.

## New decisive source finding — false-positive control
The free public-domain OpenFootball Europe archive contains French Coupe de France 2024/25 cup fixtures, dates, scores and `score.p` (penalty shootout) field:
https://openfootball.github.io/europe/france_2024-25_frcup.json
For example, 2024-11-15 Paris FC vs US Quevilly-Rouen shows `score.ft=[1,1]` and `score.p=[2,4]`; this **does not establish extra time**.

Crucial primary-source rule: FFF 2024/25 Coupe de France regulation, Article 7.4, page 10 of PDF (PDF page index 9): rounds 1 through semi-finals go **directly to penalties** if tied after 90 minutes; **only the final** allows 30 extra minutes when level.
https://lfpl.fff.fr/wp-content/uploads/sites/20/2024/07/REGLEMENT-DE-LA-COUPE-DE-FRANCE-2024-2025.pdf

Therefore `penalties == true => 120 minutes` is demonstrably INVALID for this source/competition. Blindly using OpenFootball `score.p` as extra-time fatigue creates fabricated exposures. A source with explicit 90/120 duration and competition-specific rules is required. No outcome tests were run.

Alternative 2024/25 FA Cup fixture listing includes descriptive AET labels (example):
https://fbref.com/en/comps/514/2024-2025/schedule/2024-2025-FA-Cup-Scores-and-Fixtures
But publication provenance, permission for automated research and stable cross-season extraction are **not verified**. Official FA result pages also show AET/AET+P but historic coverage and timestamping remain unproven.

## Strict outcome-free feasibility plan
1. **Frozen scope before outcomes**: all five major leagues; fixed historic seasons selected *before* any performance read; next domestic league fixture after prior cup appearance. No selecting best league, cup stage or fatigue window after outcome inspection.
2. Audit complete cup fixture universes per season/league; join stable team IDs; collect verified 90/120 and actual cup completion times, stage/rules, publication timestamps. Compute coverage by league-season and missingness without viewing league results or bookmaker outcome performance.
3. Require all predictor information `published_at <= asof` and `cup_end <= asof` for as-of chosen **T-24h** before league kickoff. Never use subsequent disciplinary, lineup, cup corrections or match outcomes.
4. Find legal free historical **1X2 quote_observed_at** for the *same T-24h* and fixed de-vig convention. Opening/closing odds with no observation timestamp are not valid substitutes.
5. If source gate passes, Research Brain alone freezes features, temporal train/validation/untouched OOT, baseline fair market vs market+extra-time vs market+rest-hours, league-stratified paired Brier/LogLoss and fixture-cluster CI.
6. Negative controls: direct-to-penalties French Cup as **90-minute** matches; prior cup fixture of unrelated club; future cup exposures (must be impossible under as-of); equal rest-hours 90-minute controls; league/season coverage drift.
7. **STOP** if verified 120-minute histories or quote-observed-at matching are insufficient, or if independent validation/OOT does not show robust improvement. **SUCCESS** only if independently frozen paired OOT improves BOTH Brier and LogLoss with appropriate uncertainty and league stability; no claim of profit or automatic promotion.

## Current gate
- Scientific mechanism: plausible, preliminary IDEA only.
- A free cup schedule source: YES, concrete 2024/25 example.
- Verified historical 120-minute exposure coverage: **NO**; one source would misclassify penalties.
- Verified T-24h bookmaker market snapshot: **NO**.
- Historical 5-league coverage: **NO**.
- New Scout Issues: 0. Research Brain handoffs: 0. Production/Supabase/paid API operations: 0.
- **WAITING_BY_SOURCE**. No candidate Issue justified.

## Sources
- Mohr et al. 2023 https://doi.org/10.1249/MSS.0000000000003021
- OpenFootball France Cup 2024/25 https://openfootball.github.io/europe/france_2024-25_frcup.json
- FFF 2024/25 official rules Article 7.4 https://lfpl.fff.fr/wp-content/uploads/sites/20/2024/07/REGLEMENT-DE-LA-COUPE-DE-FRANCE-2024-2025.pdf
- FA Cup historical fixtures https://fbref.com/en/comps/514/2024-2025/schedule/2024-2025-FA-Cup-Scores-and-Fixtures
- Research registry https://github.com/MaksimBlud/football-ai/blob/main/research/programs/registry.json
