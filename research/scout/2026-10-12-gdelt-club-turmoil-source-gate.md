# SIGNAL-SCOUT — GDELT club-organizational-turmoil PIT source gate (2026-10-12)

**Status:** `IDEA / BLOCKED_BY_SOURCE_SAMPLE_AND_MARKET_BASELINE`. **No signal found. No outcome tests. No Research Brain handoff. No new Scout candidate Issue.**

## Mechanism, novelty and exclusions

Candidate family: `GDELT_CLUB_ORGANIZATIONAL_TURMOIL_1X2_V0`.

Hypothesis: verifiable, previously published off-field organizational disruption involving a club (e.g., documented player wage dispute, supporter protest or financial/governance controversy) could affect preparation, uncertainty or team performance before kickoff, potentially adding information to contemporaneous bookmaker fair 1X2 probabilities.

This is **not** the already-tested calendar, market-microstructure, SOT/process divergence, tactical-pressure, travel, manager/lineup/injury or Wikimedia *attention-volume* family. However, it has not been proved independent empirically; all personnel, transfers, injuries and manager-change terms must be excluded from the proposed mechanism. Media attention alone must not be used as a surrogate for a disruption.

## Fresh-repo duplication audit (read-only)

On 2026-10-12 read fresh default-branch `research/programs/registry.json`, `PROJECT_CONTINUITY.md`, open Issues, search for `GDELT`, `referee`, `SIGNAL-SCOUT`, and branch names. Registry: 14 programs (13 `PROGRAM_DONE`, 1 `BLOCKED`). Prior scout branches include Wikimedia attention, FPL availability, national-team workload, referee appointments, stadium elevation, air pollution, cross-tier form and bookmaker source audits. No exact GDELT club-governance family was found. This is a *provisional conceptual* distinction, not authorization to test outcomes.

Sources: [registry](https://github.com/MaksimBlud/football-ai/blob/main/research/programs/registry.json), [continuity](https://github.com/MaksimBlud/football-ai/blob/main/PROJECT_CONTINUITY.md), [Research #594](https://github.com/MaksimBlud/football-ai/issues/594).

## Official source and licensing

- [GDELT 2.0 official launch (2015-02-19)](https://blog.gdeltproject.org/gdelt-2-0-our-global-world-in-realtime/) says Event and GKG metadata are released in 15-minute batches, including themes and organizational entities.
- [Official data overview](https://gdeltproject.org/data.html) describes downloadable GKG archives and BigQuery.
- [Official terms](https://gdeltproject.org/about.html#termsofuse) explicitly allow unlimited academic/commercial/governmental use of **GDELT datasets** without fee, requiring GDELT attribution when redistributing. This does **not** grant copyright in underlying news articles; only GDELT-derived metadata would be used.
- [Official 2026-10-12 last-update manifest](https://data.gdeltproject.org/gdeltv2/lastupdate.txt) was read and lists an 11:00 UTC GKG batch (4,591,878-byte zip, MD5 `a3efe777f48acf0480e216bfb4697545`). This proves a *current listing*, **not** historical first-seen publication for a match.

## Outcome-free feasibility attempts and blocker

A fixed historical 15-minute GKG ZIP at `https://data.gdeltproject.org/gdeltv2/20261009120000.gkg.csv.zip` could not be retrieved in the present runtime (web endpoint inaccessible; container has no external DNS). A bounded official DOC API request for Arsenal football metadata in 2026-10-01–02 was likewise inaccessible. **Actual rows downloaded: 0; club-specific coverage: not measured; field-level PIT evidence: 0; historic batch publication times: not established.** Do not extrapolate GKG-wide archive size to usable football matches.

## Proposed exact, frozen-before-outcomes design (not yet authorized)

1. Predefine 5 major men's leagues, fixed seasons, canonical club entity dictionary, and an as-of decision time `T = kickoff_utc - 24h`; record source file batch timestamp and observed first-seen, with a conservative lag buffer. **Never use an article's self-reported publication date in place of the GDELT first-seen timestamp.**
2. For each club, count only unique source URLs whose first GDELT batch was verifiably available before T, and whose unambiguous club entity matches a preregistered dictionary. Require a strict club-governance-disruption category (not generic negativity, match results, injury, lineup, transfer or manager news). Define `turmoil_count_7d`, `turmoil_share_of_all_club_news_7d`, `home_minus_away_turmoil_share`, and `missing_source_flag`; **no data-driven thresholds**.
3. Outcome-free gates: archived ZIP availability and first-seen reproducibility; 2+ independent fixed seasons, five-league coverage, disambiguation false-positive audit, publish-lag distribution, proportion of matches with at least one valid item, exact bookmaker 1X2 fair-probability snapshot before T and usage-rights review. If any gate fails, stop.
4. If and only if source gates pass, Research Brain alone freezes baseline and temporal validation/OOT. Strong baseline: matched-timestamp, matched-fixture bookmaker consensus 1X2 de-vig + existing approved football controls; compare nested model via paired multiclass LogLoss and Brier, calibration, fixture-cluster bootstrap confidence intervals and league/season transport. No Scout outcome reading.
5. Negative controls: club-name collisions (Arsenal as non-club term), placebo news about unrelated clubs, articles first indexed *after* T, neutral sports coverage volume, and false associations after permuting team identities **within preregistered league/season/time blocks**.
6. SUCCESS only if independently frozen OOT improves both LogLoss and Brier over the contemporaneous market baseline with consistent signs and uncertainty gates. STOP for missing timestamps, ambiguous entities, insufficient nonzero support, rights issues, baseline absence, leakage or negative OOT.

## Decision / next step

**BLOCKED_BY_SOURCE_SAMPLE_AND_MARKET_BASELINE.** No candidate Issue or handoff. Next action only if archive access becomes possible: inspect a fixed set of 15-minute batches and field-level club-entity coverage *without opening any reserved match outcomes*. No paid API, Supabase writes, production .pkl, registry edits or other-agent prompt changes.
