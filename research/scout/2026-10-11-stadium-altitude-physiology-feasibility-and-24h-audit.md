# Football AI Signal Scout — stadium altitude feasibility + 24h throughput audit (2026-10-11)

**Decision:** `IDEA / BLOCKED_BY_SOURCE_AND_MARKET_BASELINE`; not `DATA_FEASIBLE`, not a signal. This is a continuation of the previously identified `STADIUM_ALTITUDE_ADAPTATION_1X2_V1`, **not** a second hypothesis.

## Fresh-main and duplicate controls

- Read GitHub `main` at `f24a71a22f314b2f10fd423fd255a57096ef7b6e`, `research/programs/registry.json` and `PROJECT_CONTINUITY.md`.
- Registry: **14 programs: 13 `PROGRAM_DONE`, one `BLOCKED`**. Existing travel-city Stage B concerns corner-market direction, not physiological altitude effects on 1X2; no reopened closed program or reused OOT.
- Read existing weather Scout source report, previous local altitude source gate, and open issues via GitHub REST. No open `[SIGNAL-SCOUT][CANDIDATE]` issue found. This report creates no issue.

## Additional official-source / literature audit (outcome-free)

1. **Physical mechanism is plausible but scale-dependent.** Gatorade Sports Science Institute, "Impact Of Altitude And Heat On Football Performance", describes **0–500m** as near sea level and **>500–2,000m** as low altitude with *minor* aerobic impairment, noting substantial individual variation and limited direct team-sport evidence: https://www.gssiweb.org/en/sports-science-exchange/article/sse-131-impact-of-altitude-and-heat-on-football-performance . Thus it is invalid to assume the large high-altitude South America effect applies unchanged to ~500–700m European venues.
2. Independent team-sport review describes directly observed reductions in match running distance at **1,200–1,753m**, not at every European stadium elevation: https://doi.org/10.1136/bjsports-2013-092834 . The European association study on 2,012 UEFA matches is observational, not a bookmaker-fair-probability incremental test: https://www.iza.org/publications/dp/12143 .
3. **Free elevation dataset and precise request contract verified from documentation, not from a live stadium response.** Open Topo Data official API supports WGS84 `locations=latitude,longitude` and multi-point batching: https://www.opentopodata.org/api/ ; its public `srtm30m` uses SRTM v3 with ~30m resolution, coverage 60°S–60°N: https://www.opentopodata.org/datasets/srtm/ . Public limits: 100 locations/request, 1 request/second, 1,000/day: https://www.opentopodata.org/ .
4. **Real stadium query remains unverified:** direct `api.opentopodata.org/v1/srtm30m?locations=40.4531,-3.6883` returned inaccessible through web and DNS failure from the container. Do not turn example documentation JSON or third-party estimated heights into measured fixture coverage.
5. **As-of nuance:** terrain elevation itself is effectively time-invariant for the study period, so it is not necessary to pretend that a modern SRTM lookup was published before each match. The **historical identity of the actual match venue and visiting club's usual stadium** must, however, be provable at the frozen prediction time. A club-city altitude is not a substitute for stadium altitude. Stadium relocations/neutral sites are leakage hazards.
6. **Critical separate market gate remains blocked:** `point_in_time_snapshot_cadence` in registry is `BLOCKED_BY_TIMESTAMP_COVERAGE`; no complete free lawful matched HOME/DRAW/AWAY 1X2 price receipts at fixed `T = kickoff - 24h` are proven. No use of later/opening/closing odds as exact-T surrogate.

## Preregisterable follow-up only after source gates

- **Source-only, no outcomes:** predeclare complete five-league season/fixture universe and venues, venue identity at T, minimum venue/odds coverage and minimum altitude spread *before seeing any target results*. Query real elevation API or self-host legally reusable DEM; pin raster version, coordinates, source response hash, missingness and actual height distribution. No threshold chosen after performance results.
- Research Brain alone may freeze expanding-season training / validation / untouched OOT. Compare (A) contemporaneous fair 1X2 market, (B) market + home advantage + distance + rest + absolute altitude, (C) B + predeclared home-venue vs away-usual-venue altitude difference. Primary paired multiclass LogLoss and Brier, clustered confidence intervals, league transport; negative controls: venue-height permutation in frozen geographic strata, missingness-only, irrelevant venue placebo, post-T venue change trap.
- **STOP** if stadium or market PIT evidence fails, altitude variation is insufficient under a predeclared source-only rule, or validation/OOT fails. **SUCCESS** requires improvement in both scores against strongest baseline on untouched OOT with favorable uncertainty and controls. No profitability claim.

## 24-hour actual persisted Scout work

At this checkpoint, GitHub compare `main...scout/*` enumerated **12 Scout branches**, **5 with branch-only commits**, **7 with zero branch-only commits**. The five committed branches contain **7 research/scout commits** (verified by GitHub REST `commits?sha=<branch>&path=research/scout`) dated between **2026-10-10 09:17:31Z** and **2026-10-10 21:14:52Z**; all fall in the last 24h of this checkpoint. Evidence commits:
- BSD `5bec15e28099bafa6438f8ba7b61ec83ab54bdca`
- Referee `0fa02d24158ae252fa5f8906621cfdc861ebea8d`
- Wikimedia `daf84d99d3577b92ec10e08db1592cff8ddc371c`, `9c902bf430ff263478a2636e8a6b63d6a3e1aa52`
- DataHub `eed4692cc2f17812fdcdccde5180de143711ea3a`
- Weather `5e8811e080ede2d321e9cd7707d229c01520ed5b`, `3cd6462ab98772167f61a814d5c7541b929f9029`

This count is **persisted commits, not seven admitted hypotheses**; 0 new `DATA_FEASIBLE`, 0 Research Brain handoffs, 0 confirmed signals. Per-run wall-clock duration and 40-minute utilization are not reliably recorded; no acceleration is claimed. The present report commit, if successful, is **not** included in the historical seven-commit baseline.

## Safety

No target outcomes or reserved prospective OOT read, no paid The Odds API call, no Supabase writes/DDL, no production model training/promotion/.pkl changes, no registry changes, no edits to other agents, no direct main write, no deployment, no posthoc threshold tuning, no Scout candidate issue.
