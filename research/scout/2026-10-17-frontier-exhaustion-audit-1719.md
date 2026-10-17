# Football AI Signal Scout — frontier exhaustion audit
Date: 2026-10-17 17:19 America/New_York
Status: WAITING_FOR_NEW_INDEPENDENT_EVIDENCE

## Decision
No new candidate meets the required standard this cycle. No `[SIGNAL-SCOUT][CANDIDATE]` Issue is created and no outcome data is read. This is not a claim that every conceivable football feature is exhausted; it means the currently visible free-source frontier has no newly identified, independent, timestamp-safe candidate with a verified fair-bookmaker baseline.

## Fresh-main audit
- Main SHA: `328bc3966c657976908acdce94809a11fdd18a24`, committed 2026-10-14T15:36:27Z.
  https://github.com/MaksimBlud/football-ai/commit/328bc3966c657976908acdce94809a11fdd18a24
- Registry blob SHA: `1ca41a63ac913efa4cda67a1af244f02d586df9c`.
  https://github.com/MaksimBlud/football-ai/blob/main/research/programs/registry.json
- PROJECT_CONTINUITY blob SHA: `5141512fdd3559d62ecdef46c70a93129b921ef5`.
  https://github.com/MaksimBlud/football-ai/blob/main/PROJECT_CONTINUITY.md
- Registry: 14 programs, 13 `PROGRAM_DONE`, one `BLOCKED` (`point_in_time_snapshot_cadence`, Issue #594).
- #594 states that there is no complete timestamp-safe fixture universe plus portable historical 1X2 snapshots with event IDs and snapshot timestamps.
  https://github.com/MaksimBlud/football-ai/issues/594
- The open candidate search returned no open `[SIGNAL-SCOUT][CANDIDATE]` Issues. Searches for Issues created 2026-10-16 through 2026-10-17 returned no new Issues in this repository.

## Relevant closed families / source-gated directions
The registry already closes cross-market lead-lag, kickoff/calendar context, corner direction, price formation, de-vig, favourite-longshot, margin structure, result-vs-process divergence, independent tactical-source disagreement, market-error correction, multi-market repricing, and goal-market validation. The continuity document also records historical closures for trajectory, rest/congestion, shot-quality, lineup capability, tactical matchup, true-xG capability, and trajectory-by-shot interactions.

Recent Scout branch names show further source-gate exploration of added-time rules, away-fan restrictions, competitive incentives, crosswind/pitch axis, GEFS forecast uncertainty, goalkeeper shot-stopping, Guardian previews, wage concentration, rail disruption, referee provenance, points deductions, shared-pitch turnaround, solar glare, suspension thresholds, pitch dimensions/surface, bench depth/five substitutions, neutral venues, transfer turnover and financial disclosures. These names are not treated as evidence of completed audits by themselves.

## Durability finding
Compared `main` with all 18 Scout branches dated 2026-10-17. Every comparison returned `identical`, with 0 ahead commits, 0 behind commits, 0 changed files. This is direct evidence that the branches are empty pointers, not durable research artifacts:
- https://github.com/MaksimBlud/football-ai/tree/scout/20261017-added-time-rule-shock-asof-identification-gate
- https://github.com/MaksimBlud/football-ai/tree/scout/20261017-gefs-ensemble-uncertainty-source-gate
- https://github.com/MaksimBlud/football-ai/tree/scout/20261017-rail-strike-stadium-access-asof-gate
- https://github.com/MaksimBlud/football-ai/tree/scout/20261017-shared-pitch-turnaround-coverage-gate-0516
- https://github.com/MaksimBlud/football-ai/tree/scout/20261017-suspension-brink-source-rights-gate-0822

The latest commit on main is still from 2026-10-14. Therefore, the source-gate conclusions in recent chat-local reports should not be described as committed project evidence unless separately linked to a durable issue/file.

## Why no new idea is admitted
A new idea must be distinct from the closed/source-gated families, supported by a free and rights-compatible source with historical pre-kickoff availability, and compared on identical fixtures against a timestamp-safe fair 1X2 baseline. The current baseline blocker #594 is still unresolved. A plausible new mechanism without that baseline cannot establish improvement beyond market; creating an issue now would merely create another blocked source-gate without an independently verified candidate.

## Next admissible trigger
Resume candidate creation only after at least one of:
1. a free, rights-compatible historical source is verified with immutable publication/first-seen timestamps and sufficient multi-season coverage for a genuinely new feature family; or
2. a complete, timestamp-safe fixture universe and matched fair 1X2 probability baseline is available for the same cutoff; or
3. the project owner grants fresh explicit authority for prospective data collection (no paid request is authorized by this report).

For any future candidate, Research Brain must freeze the feature definition, paired Brier/LogLoss comparison, temporal train/validation/untouched OOT split, negative controls and STOP/SUCCESS criteria before any reserved outcomes are read.


## One genuinely distinct research IDEA screened: pairwise lineup familiarity
**Status: IDEA → BLOCKED_BY_SOURCE. Not a candidate and not a signal.**

### Mechanism
Instead of rating the individual quality of the likely XI, estimate relational familiarity from the minutes/starts that player pairs have shared for the same club, with a separately defined prior-team familiarity component. The hypothesis is that coordinated pairs may reduce adaptation costs after a lineup change even when individual player-strength ratings are unchanged. This is conceptually different from additive lineup-strength or team-strength trajectory, but is correlated with lineup continuity; Research Brain would need to test that incremental distinction only after source gates pass.

### Scientific evidence
Pasarakonda et al., *How Team Familiarity Mitigates Negative Consequences of Team Composition Disruptions: An Analysis of Premier League Teams* (first online 2023-08-03; journal issue 2025), analyse 2,280 EPL games. They distinguish current-team from prior-team familiarity and report that familiarity modifies the effect of team-composition disruption. This supports plausibility, not a forecast edge over bookmaker fair probabilities.
- Article: https://journals.sagepub.com/doi/10.1177/10596011231193176
- DOI: https://doi.org/10.1177/10596011231193176

### Outcome-free source feasibility
The official StatsBomb Open Data repository supplies events and lineup JSON files and asks researchers to attribute StatsBomb and use its logo. README describes the data as freely available for research projects and genuine interest in football analytics; it does not provide a standard blanket commercial-use license.
- README: https://github.com/hudl/open-data
- Season/competition metadata: https://github.com/hudl/open-data/blob/master/data/competitions.json

The current metadata contains 80 competition-season rows, but not a continuous multi-season archive for the five frozen major leagues. Examples of its own `match_available` metadata:
- Bundesliga 2023/24: 2024-09-28T20:46:38Z (after the season had finished).
- Premier League 2015/16: 2025-12-17T14:38:00Z.
- Ligue 1 2022/23: 2026-04-06T18:51:07Z.
- Ligue 1 2021/22: 2026-04-25T22:22:46Z.

These release times mean the archive cannot be treated as if all same-season lineups had been publicly available before subsequent matches. A commit timestamp or season-level `match_available` value is not proof of per-match first-publication time; that would need separate immutable file-history evidence. The available coverage is also too discontinuous to support the proposed untouched multi-season OOT as specified.

### Blocking gates
1. **Timestamp gate:** no proven per-match first-seen history demonstrating lineup data was available before each prediction cutoff.
2. **Coverage gate:** the public archive has discontinuous season coverage; no complete frozen-league fixture universe has been joined outcome-free.
3. **Rights gate:** research access is clear, but rights for feature extraction in a potentially commercial Football AI product are not established.
4. **Baseline gate:** Issue #594 remains blocked; no matched full-coverage fair 1X2 baseline with exact pre-kickoff snapshot timestamps is available.
5. **Duplicate/independence gate:** relational familiarity is distinct from individual lineup strength in mechanism, but incremental independence from the closed lineup/trajectory families is unproven.

### Future preregistration contract (not run)
If the source/rights/baseline gates are later cleared, freeze: (a) weighted pairwise shared minutes in the prior 365 days, with no current-match lineup/outcome leakage; (b) prior-team familiarity kept as a separate negative/diagnostic control; (c) same-fixture fair 1X2 baseline; (d) temporal train/validation/untouched OOT split; (e) paired Brier and LogLoss; (f) negative controls using shuffled player identities and pair links, plus a simple lineup-continuity baseline. STOP if source timestamps, legal use, full fixture coverage or baseline fail, or if validation does not improve both metrics. SUCCESS only after Research Brain independently confirms improvement on untouched OOT. No outcomes were read and no evaluator was run for this IDEA.

## Operational ledger
- New candidate Issues: 0.
- Research Brain handoffs: 0.
- Outcome tests / reserved-outcome reads: 0.
- Paid Odds API calls: 0.
- Registry, Supabase, production models/deployment and other agent prompts changed: 0.
- Measured wall-clock cycle duration: not available; no claim is made that a 40-minute cycle occurred.
