# Football AI Signal Scout — cross-tier upstream-vs-JSON source gate

**UTC date:** 2026-10-11. **Status:** `IDEA / BLOCKED_BY_SOURCE_COMPLETENESS_AND_MARKET_BASELINE`. Existing hypothesis `PROMOTED_CROSS_TIER_PRESEASON_STRENGTH_1X2_V1`; **no new independent hypothesis**, **no Scout candidate Issue**, **no Research Brain handoff**.

## First: fresh-main governance and duplicate check

Read current GitHub `main` `research/programs/registry.json`, `PROJECT_CONTINUITY.md`, relevant research issues, and searched `[SIGNAL-SCOUT]` issues. Registry has **14 programs**: **13 `PROGRAM_DONE`**, **1 `BLOCKED`** (`point_in_time_snapshot_cadence`, Issue [#594](https://github.com/MaksimBlud/football-ai/issues/594)). No open Scout candidate was returned. Do not reopen finished market/form/team-change programs or reinterpret their OOT.

## Reproducible no-target-outcomes source audit

**New source checked:** upstream public-domain [openfootball/deutschland](https://github.com/openfootball/deutschland), specifically [2025-26/2-bundesliga2.txt](https://github.com/openfootball/deutschland/blob/master/2025-26/2-bundesliga2.txt), blob SHA `b639906648d3ce58de914c0824602b96301bda52`; [CC0 license](https://github.com/openfootball/deutschland/blob/master/LICENSE.md).

Compared to downstream [openfootball/football.json 2025-26/de.2.json](https://github.com/openfootball/football.json/blob/master/2025-26/de.2.json), blob SHA `d7a5d081ac99327f6d3afd52d0f4e90125de5a17`. The upstream project documents that JSON is generated from Football.TXT sources; these are **not independent providers**.

Method (metadata/completeness only): count upstream lines containing fixture separator ` v `; among these count those with a terminal full-time `digit-digit` score. Parse downstream `matches` and count `score.ft` arrays of exactly two integers. **No top-flight target outcomes, OOT, model fitting, Brier/LogLoss or profit computations.**

| German second tier 2025/26 | Fixtures | FT available | FT absent | Coverage |
|---|---:|---:|---:|---:|
| Football.TXT upstream | 306 | **112** | **194** | **36.60%** |
| football.json downstream | 306 | **94** | **212** | **30.72%** |

Upstream has **18 more score-bearing rows** than JSON in the observed current blobs, but still lacks **194/306** results. This proves that switching from downstream JSON to this upstream TXT **does not resolve** the source-completeness blocker. The two repositories must not be presented as independent cross-checks; downstream synchronization can lag upstream. The upstream blob is a current read; this cycle **did not establish its historical first-seen commit before 2026/27 kickoff**. Consequently **not `DATA_FEASIBLE`**.

## Independent alternative and rights gate

[OpenLigaDB](https://www.openligadb.de/) advertises free historical match API, but this cycle could not verify its 2025/26 full-season fixture/score coverage, historical publication/last-update timestamps, or permitted downstream use. Remains **WAITING_BY_SOURCE**; do not infer coverage.

**Do not switch to football-data.co.uk** for Football AI model training: its [official contact page](https://football-data.co.uk/contact.php) explicitly restricts data to private individuals and excludes commercial and AI/data-training products. Free download is not usage permission.

## Scientific pre-registration boundary (for Research Brain only, if sources pass)

Feature: `zscore((GF-GA)/played)` over the **fully completed regular second-tier season**, computed within the relevant division/season, with a deterministic club promotion mapping and cutoff **before first higher-tier kickoff**. It is a different information origin from five-match top-tier SOT/form residuals, but its incremental utility is **unproven** and the promoted-team concept is not novel in literature. Never select only complete leagues or retune a threshold after outcome exposure.

Before admission require: (1) complete rights-safe as-of source across preregistered league/season scope, (2) deterministic club IDs, (3) exact as-of fair 1X2 bookmaker baseline with matched pre-kickoff timestamp, (4) train/validation/untouched-OOT splits frozen by Research Brain, (5) paired multiclass Brier and LogLoss vs strong market+Elo+promoted baseline, club-season clustered uncertainty, (6) negative controls: promoted-only, within-league permutation, missingness-only and swapped club IDs. **SUCCESS** only if both losses improve on independent untouched OOT with uncertainty and cross-league stability; otherwise **STOP / NO_SIGNAL**.

## Result and safety

New independent hypotheses **0**; source alternatives directly checked **1**; decisive negative source-completeness gate **1**; `DATA_FEASIBLE` **0**; Research Brain handoffs **0**; new Scout Issues **0**; target outcome tests **0**. Previous available Scout reports over ~24h also show **0 Research Brain handoffs**; cycle-duration logs are insufficient to claim faster throughput. A source blocker is a useful falsification, not a discovered predictive signal.

Research-only branch. No registry edits, other-agent prompts, Supabase writes, production models/training/deployment, paid The Odds API calls, reserved 2026/27 outcomes, or direct main writes.
