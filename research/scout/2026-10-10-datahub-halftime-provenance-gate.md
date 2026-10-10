# Football AI Signal Scout — DataHub halftime-history source audit
Date: 2026-10-10 UTC. Verdict: **BLOCKED_BY_SOURCE_RIGHTS_AND_FRESHNESS**.
Research-only, outcome-free. **No candidate Issue and no Research Brain handoff.**

## Scope and fresh-main duplicate gate
Re-read `main:research/programs/registry.json` and `main:PROJECT_CONTINUITY.md` through the connected GitHub repository; checked open issues and earlier Scout reports. Registry: **14 programs: 13 PROGRAM_DONE, 1 BLOCKED** (`point_in_time_snapshot_cadence`). No open `[SIGNAL-SCOUT][CANDIDATE]` issue found. Existing research includes kickoff/calendar, team-strength trajectory, shots, tactical pressure, travel and referee-corner work. No frozen `PROGRAM_DONE` feature is retuned, no outcomes are opened, and no new hypothesis is claimed in this cycle.

This is **source-feasibility follow-up** to previously proposed `OPENFOOTBALL_HALFTIME_TRANSITION_1X2_V1` (second-half goal-difference tendency based on *prior* matches only). The previous OpenFootball snapshot audit found stale upstream historical revisions; the question here is whether an alternative purportedly daily archived provider can repair point-in-time provenance without new paid data.

## New evidence: a promising-looking derivative source fails two gates

**Candidate archive:** https://github.com/datasets/football-datasets

1. The project's current `README.md` explicitly advertises daily GitHub Actions updates for the five major European leagues, declares the league datasets to be PDDL 1.0, and identifies **football-data.co.uk as its underlying source**: https://github.com/datasets/football-datasets/blob/main/README.md
2. Its Bundesliga dataset documentation confirms the existence of halftime fields `HTHG`, `HTAG`, `HTR` and caveats on early seasons: https://github.com/datasets/football-datasets/blob/main/datasets/bundesliga/README.md . This establishes **schema support**, not timely first-seen availability.
3. GitHub connected-repository latest-commit search (read on 2026-10-10) returned `436a51f15258e7d0c6042c231227202b70a5a0ae` as the newest visible commit. GitHub's commit metadata gives **2026-06-23T04:55:43Z**, i.e. more than 100 days before this audit: https://github.com/datasets/football-datasets/commit/436a51f15258e7d0c6042c231227202b70a5a0ae . Its changed-file metadata identifies a single `datasets/ligue-1/season-2526.csv` update. **No versioned post-June 2026 change was established**. This does not prove that the scheduled workflow has not run; it does mean the asserted *daily fresh historical snapshot stream* cannot be assumed from the README. We deliberately did **not** inspect 2026/27 match rows.
4. The **original data provider** explicitly says that its free files are intended for private individuals, **not commercial or AI/model-training products using automated bots/scrapers/AI**: https://football-data.co.uk/data.php and https://football-data.co.uk/contact.php (checked 2026-10-10). A downstream repository's PDDL claim is **not sufficient proof** that it can sublicense or clear the underlying data for Football AI's eventual public/commercial application. This is a **rights-provenance conflict**, not a definitive legal finding.
5. Therefore this archive cannot currently be used as a clean, timestamp-safe, commercially permitted basis for the proposed halftime 1X2 signal. Even if historical file commits can be replayed, original-source rights remain unresolved; conversely, rights clearance would not by itself prove first-seen coverage.

## Exact point-in-time feasibility contract (no outcome tests)
- Candidate mechanism, **unchanged**: past-match second-half goal-difference trend could capture substitutions, fatigue and tactical adaptation distinct from Elo and opening bookmaker 1X2. This is only a proposed mechanism, not a proven independent effect.
- Proposed feature inputs: for each club's **last 10 eligible prior fixtures** (exact window subject to Brain freeze), calculate `second_half_gd = (FT_for-HT_for) - (FT_against-HT_against)`; home-minus-away rolling mean, prior-match count and missingness indicator. For every contributing fixture require `past_kickoff < target_prediction_T` **and original-source first-seen <= T**. Current fixture halftime/FT fields forbidden.
- Fix `T = target kickoff - 48h` before collection. Validate historical snapshot receipts/commit timestamps, field completeness, fixture identities and updates as-of T on a **predeclared complete league-season universe**, with no outcomes for the target fixtures opened. Exclude any previous match whose published FT/HT was not demonstrably available by T. Never fill historical gaps from today's backfilled files.
- Independently establish source-origin usage rights (not merely downstream PDDL), and the complete contemporaneous 1X2 home/draw/away fair-probability baseline at T with quote receipts and legal use. No paid Odds API call.
- Only Research Brain may freeze train/validation/untouched OOT splits and evaluate paired multiclass LogLoss and Brier against same-T fair market, market+strength/form controls, and market+halftime tendency. Negative controls: permute past-second-half feature within predeclared league/round/strength strata; compare against full-time-only prior-goal trend; explicit future-field leakage trap must fail. Require predeclared uncertainty/consistency gates; STOP on source-rights/provenance/coverage failure or unsupported OOT, never choose windows/leagues after observing outcomes.

## Verdict and measurable throughput
- New genuinely independent hypothesis this cycle: **0** (existing exploratory halftime family, source audit only).
- New source checked: **1**. Source license/rights provenance: **blocked**. Recent point-in-time Git archive freshness: **not demonstrated**.
- DATA_FEASIBLE: **0**; candidate Scout Issues: **0**; Research Brain handoffs: **0**; confirmed signals: **0**.
- Prior visible Scout cycles also report **0 handoffs**. No durable start/end telemetry exists for the prior runs, so no wall-time speedup can be calculated or claimed. The 24-hour window from the 2026-10-09 experiment had not yet elapsed at this cycle's start.
- No reserved 2026/27 outcome reads, outcome-based tests, paid The Odds API calls, Supabase writes/DDL, model training/promotion, production .pkl or deployment changes, registry writes, other-agent prompt changes, or direct main writes.

**Next admissible action:** search for an independently licensed, truly as-of timestamped source; do not open a candidate Issue for this derivative archive without resolving both gates.
