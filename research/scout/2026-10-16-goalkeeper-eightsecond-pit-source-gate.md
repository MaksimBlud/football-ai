# Signal Scout — goalkeeper 8-second rule / distribution-pressure interaction — source gate (2026-10-16)

**Status: IDEA / BLOCKED_BY_SOURCE. NOT DATA_FEASIBLE, NOT SIGNAL_FOUND.** Research-only. No outcome reads, no candidate issue, no changes to registry or production.

## Provenance / independent mechanism

Official IFAB announcement, published **2025-03-01**: https://www.theifab.com/news/the-ifab-tackles-goalkeeper-time-wasting/

Law for 2025/26 (effective 2025-07-01, with competition-specific transitional provisions): a goalkeeper holding the ball with hands/arms longer than **8 seconds** concedes a corner, with a visual final-five-second referee countdown. This is a *rule-regime × goalkeeper release-behaviour × opponent pressing* mechanism, not a threshold variant of completed kickoff/calendar, market-microstructure, SOT-vs-results or team-change programs. It is not evidence of predictive advantage; the rule is public and can already be priced by bookmakers.

**Frozen conceptual question, NOT tested:** does historical goalkeeper release-speed under hand control interact with opposition restart pressure under the new rule to improve 1X2 probability forecasts over same-timestamp de-vigged bookmaker fair probabilities?

## Source feasibility: verified hard gaps

- Official law date and contents: https://www.theifab.com/news/the-ifab-tackles-goalkeeper-time-wasting/
- StatsBomb public catalogue: https://github.com/hudl/open-data/blob/master/README.md and https://github.com/hudl/open-data/blob/master/data/competitions.json
- GitHub source inspection on 2026-10-16: StatsBomb open-data `competitions.json` has **80 competition-season entries**; the top-five men’s league entries found in the catalogue were La Liga (historical seasons), Ligue 1 (historical), EPL (2003/04, 2015/16), Serie A (1986/87, 2015/16), and **no Bundesliga**. No top-five 2025/26 or 2026/27 league-season entry was present.
- Exact sample: `data/matches/11/90.json` for La Liga 2020/21 contained **35 listed matches**, not a complete 380-match season; first record `match_id=3773386`, played **2020-10-31**, `last_updated=2023-07-25T03:54:59.280826`. The post-match update field is NOT proof of a pre-kickoff raw video or possession record. See https://github.com/hudl/open-data/blob/master/data/matches/11/90.json
- The repository documents **event and lineup JSON**, not an independently verified start/end timestamp for *continuous goalkeeper hand/arm control*, which is the precise IFAB legal variable. Attempts to parse a full event file through the GitHub connector returned truncated JSON; therefore **do not claim** event-schema proof of absence. Historical per-control holding seconds, post-rule opponent pressure, and publication timestamps are **unverified**.
- StatsBomb's README frames public data for research and requires attribution; **commercial/product reuse rights not confirmed**. No source scraping or paid data accessed.
- No verified rights-cleared 1X2 market fair-probability snapshots at a fixed T−24h aligned to the proposed feature timestamps were obtained.

## Conditional preregistration sketch — only if source becomes verifiable

1. Fixed prediction timestamp **kickoff−24h**; each feature requires raw source publication/archival time <= this timestamp. Source snapshot immutable by content hash. Never infer as-of from today's mutable aggregate or the match date.
2. Goalkeeper feature: median hand-control-to-release seconds from the **previous 10 goalkeeper appearances**, and share of those hand-control sequences exceeding 8s; preserve missingness when fewer sequences exist (no retrospectively selected minimum). Team-opponent interaction: opposing team's prior-10-match high-pressure recovery rate *only if event definitions and timestamps can be independently validated*. Never use match-worn starting keeper known only after T−24h.
3. Before touching outcomes, Research Brain alone must freeze keeper selection (e.g., most recent pre-T−24h starter), source mapping, missingness, leagues, fixed training/validation/untouched OOT seasons, model family, probability normalisation, sample size, and all criteria.
4. Primary comparator: matched **same-T−24h** 1X2 bookmaker de-vigged fair probabilities, plus a market-anchored calibrator controlling strength, home, and rest. Evaluate paired match-level multiclass **LogLoss** and **Brier**; require both validation and untouched OOT improvement, uncertainty intervals excluding zero in beneficial direction and league stability. No economic claims from point estimates.
5. Negative controls: within-season keeper identity permutation preserving club/market strata, pre-2025 placebo rule interaction, shuffled pressure labels; no leakage from the next fixture, post-match events, 2026/27 reserved results, or market closing odds into T−24h features.
6. **STOP** before outcome testing if no timestamped keeper hand-control release records, insufficient whole-league coverage, no rights-cleared matched T−24h bookmaker snapshots, or no independent untouched OOT. Do not loosen gates or move to a different league after observing outcomes.

## Dedupe and governance

Read fresh `main` registry and `PROJECT_CONTINUITY.md` on 2026-10-16. Registry: **13 PROGRAM_DONE, 1 BLOCKED**. Searched Scout branch names for keeper/time-wasting and GitHub Issues for goalkeeper/eight second: no direct matches returned. This is **not** a proof against all unseen historical branches or textual reports. It is conceptually distinct from the existing goalkeeper-absence/team-change family because it targets a rule-triggered *within-possession duration* mechanism rather than roster availability.

No candidate Issue created: source gate failed. Research Brain is the only evaluator/freeze owner. No protected outcomes, paid Odds API, Supabase writes, training, model changes, promotion, deployment, or agent prompt changes.

## Cycle outcome / durability

One mechanism checked; 0 DATA_FEASIBLE; 0 transmitted to Research Brain; 0 candidate Issues; 0 outcome tests; 0 paid API calls. This report is an **evidence note**, not a discovered signal. Compare actual cycle duration only from verifiable start/end records; previous summaries lack comparable timings. Previously reported transmissions were 0; cannot establish productivity improvement from branch count alone.
