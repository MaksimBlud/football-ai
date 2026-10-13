# Signal Scout — referee assignment/source-rights/prior-family gate
Date: 2026-10-13 UTC
Status: **BLOCKED_BY_SOURCE_RIGHTS_AND_ASOF / RELATED_PRIOR_FAMILY** (not DATA_FEASIBLE; not SIGNAL_FOUND)
Scope: read-only, outcome-free source audit; no production/registry/other-agent modifications.

## Fresh source of truth
- GitHub main at audit: `cd307c951623aa24da5649fe376b4c6bfa1b4a9e`.
- Read `research/programs/registry.json` (13 `PROGRAM_DONE`, one `BLOCKED`) and `PROJECT_CONTINUITY.md` from that main, plus search of repository Issues for Scout/referee research.
- Continuity records **REFEREE_CORNER_BIAS_DIRECTION_V1 -> NO_PORTABLE_REFEREE_CORNER_SIGNAL** in `CORNER_SIX_SIGNAL_SCREEN_V1` (run 37179398571). Historical referee model failed even in EPL; referee fields were absent for La Liga/Serie A in that source. This is a **related referee-family negative**, not a proof that the distinct referee-card-to-1X2 mechanism has already been tested. Avoid relabeling a derivative of the old signal as independent without a new source and preregistered mechanism.
- Other related completed families include `kickoff_calendar_context`, `team_change_faster_than_market`, `market_residual_process_divergence`, `multi_market_repricing_state`; do not reopen them or their OOT.

## Newly verified primary-source restrictions
1. Football-Data explicitly states its freely downloadable data are **for private individuals, NOT commercial or data-training products using automated bots/scrapers/AI**: https://football-data.co.uk/data . The contact page reinforces that permission requests for AI/model training and commercialisation are not granted: https://football-data.co.uk/contact.php . **No automated dataset acquisition or AI training from this site in this cycle.** Historical `Referee`, cards and odds columns cannot be assumed usable for a Football AI research-to-product pipeline merely because the CSV is freely downloadable.
2. The official Premier League published match-official assignments for Matchweek 31 on **2025-04-05**, before the matchweek: https://www.premierleague.com/en/news/4271849 . This demonstrates that some referee appointments are public pre-kickoff. It does **not** establish historical full-season coverage, revisions, or archived individual appointment timestamps.
3. El Colegiado claims 9,880 La Liga matches 2000/01–2025/26 and explicit match/referee/cards/odds fields: https://elcolegiado.com/developers/ . But its own licence table lists CC BY-NC 4.0 for some data, notes Football-Data provenance, and says `ai-train=no`. Thus **not an unrestricted commercial training substitute**; do not bypass upstream restrictions via a derivative mirror.
4. Pappalardo et al. 2019 Wyscout open event data are CC BY 4.0 and cover the **2017/18 season only** across the big five leagues (1,826 league matches: 380+380+380+306+380): https://www.nature.com/articles/s41597-019-0247-7 ; referee metadata: https://figshare.com/articles/dataset/Referees/8082665 . Useful as a historical *schema feasibility* example, **insufficient alone for independent multi-season temporal validation/OOT**; do not read any reserved 2026/27 outcomes.
5. Cornerflick advertises CC BY 4.0 season/match exports with referee, lineup and statistics: https://cornerflick.com/data . **Caveats:** the stated licence applies to its compilation; underlying provider terms are separate; the described `last_updated_at` is a refresh time, not necessarily first-publication as-of; raw season CSV/JSON endpoints were not accessible in this environment, so coverage, timestamps and field consistency are unverified. Do not count as DATA_FEASIBLE.

## Decision for prior idea REFEREE_APPOINTMENT_HOME_CARD_ASYMMETRY_1X2_V0
- Mechanism remains hypothetical: prior referee-specific propensity for asymmetric home-vs-away disciplinary decisions could affect expected match result after accounting for team strength. Distinct target from old corner direction, but overlapping referee-family risk requires explicit independence proof.
- **BLOCKED_BY_SOURCE_RIGHTS_AND_ASOF**: no verified usable multi-season, commercially compatible, time-safe (appointment pre-kickoff + past match cards) source matched to a lawful contemporaneous 1X2 fair-market baseline.
- No outcome analysis, post-hoc selection, OOT inspection, new candidate Issue, registry write, or claim of edge.
- New independent hypothesis admitted this cycle: **0**. DATA_FEASIBLE: **0**. Research Brain handoffs: **0**. New Scout Issues: **0**. Paid provider calls: **0**.
- Historical cycle durations not independently measured; do not infer speedup from report timestamps.

## Exact future source-only gate (not authorization to run evaluator)
A future *new independent* candidate would first require:
- dated, verifiable pre-kickoff official appointments, including changes and cancellations;
- licensed past-match referee, card, foul and penalty events with per-match kickoff, fixture IDs and dates of initial publication;
- source-rights audit permitting the intended AI research/product use;
- outcome-free join coverage and missingness by fixed league/season; only past completed matches with a conservative publication lag enter rolling referee features;
- a **separate**, licensed, fixture-matched fair 1X2 market baseline with verified pre-kickoff as-of;
- explicit non-duplication against closed referee-corner family.
If and only if these gates pass, Research Brain owns freezing: fixed features, training/validation/untouched OOT, market-anchored baseline, paired Brier/LogLoss + clustered uncertainty, placebo shuffled-referee/assignment-time controls, STOP on non-improvement or missing provenance. Scout must not read OOT outcomes.

Evidence is primary-source links above plus repository main continuity. No source restriction was bypassed.
