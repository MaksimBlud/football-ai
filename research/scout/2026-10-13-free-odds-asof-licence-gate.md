# Football AI Signal Scout — outcome-free source gate, 2026-10-13 UTC

**Status: SOURCE_LEAD / WAITING_BY_HISTORICAL_COVERAGE_AND_INDEPENDENT_PROVENANCE. Not a signal. Not a candidate Issue.**

## Fresh project anti-duplicate gate
Read GitHub `main` `research/programs/registry.json` (14 programs: 13 PROGRAM_DONE, 1 BLOCKED), `PROJECT_CONTINUITY.md` and `research/EPL_MARKET_FLOOR_V1_20261012.md`. Searched existing open/closed research/scout Issues. No open `[SIGNAL-SCOUT][CANDIDATE]` issue identified. Closed market-microstructure, de-vig, lead-lag, calendar and process programs remain closed. This audit tests only **new source feasibility**, not a new market calibration strategy and not any already-opened OOT outcome.

## Positive free source lead: TipsAudit public API
- Live endpoint: https://tipsaudit.com/api/v1/predictions
- API terms: https://tipsaudit.com/api (free including commercial use **with visible attribution**, 60 requests/minute, ~5-minute update interval).
- Dataset description: https://tipsaudit.com/data (claimed 5,202 predictions, 2026-06 through 2026-10, CC-BY-4.0; source notes that Pinnacle odds can be filled after the logging time but before kickoff, sometimes entered retrospectively; do **not** assume every CSV row has a trustworthy as-of time).
- Official independent fixture reference: https://www.uefa.com/uefachampionsleague/news/02a8-2174c9e9019d-f909a77bd77a-1000--2026-27-champions-league-all-the-league-phase-fixtures/ (UEFA published 2026-10-07).

### Outcome-free sample of publicly returned 1X2 fair-probability vectors
Observed API `generated_at=2026-10-13T02:21:15+00:00`, `methodology_version=2.0`, `count=399` (count covers multiple leagues and statuses, **not** verified 1X2 sample coverage). Both fixtures were independently matched against UEFA's 2026-10-13 schedule **before kickoff**. All fields below are taken from the same API response and deliberately exclude results, predictions, betting signals, closing odds, and any later event information.

| API id | Fixture | Kickoff UTC | fair_read_at UTC | p(H) | p(D) | p(A) | sum |
|---|---|---|---|---:|---:|---:|---:|
| 5595 | Arsenal — Lille | 2026-10-13 19:00 | 2026-10-13 01:34:46 | 0.8148 | 0.1242 | 0.0610 | 1.0000 |
| 5606 | Atlético Madrid — Manchester United | 2026-10-13 19:00 | 2026-10-13 01:34:46 | 0.5094 | 0.2378 | 0.2528 | 1.0000 |

The provider labels both `fair_source=live`, with `benchmark_read_at=2026-10-13T01:34:46+00:00`. This commit is a durable **external-observation timestamp** if the GitHub commit timestamp is before kickoff, but it does **not** independently validate the provider's internal `fair_read_at`, raw bookmaker prices, or the claimed archival 5,202-row coverage. Source supplies already-devigged fair estimates, not complete same-book raw 1X2 quotes; this is **not yet** a verified bookmaker baseline of the same quality as raw matched Pinnacle prices. No OOT results were read.

**Feasibility achieved only for 2 contemporaneously observed pre-kickoff vectors**; not DATA_FEASIBLE for a historical/longitudinal study, no sample-size claim, no incremental predictive value claim.

### Mandatory next source gates (outcome-free)
1. Inspect a *permitted* historical raw CSV / dated public git snapshots, excluding any `result`, `prediction_won`, `pin_close_*`, CLV or future-outcome columns. Check 1X2 completeness, source/book identity, actual quote timestamps, kickoff matching, and coverage per league/season.
2. Verify whether archived snapshots were independently committed **before each fixture** and whether `record_hash` genuinely covered the price vector at the intended prediction horizon. Exclude all post-logged or retrospectively filled prices from same-time baselines.
3. Check original quote vs devig method. Prefer raw same-book H/D/A prices with an auditable publication time and a frozen no-vig transform. Do not treat an external provider's calibrated probabilities as unmodified market odds.
4. Freeze a future collection timestamp and compare independently with UEFA/league schedules and an alternative raw-quote source; document missingness before evaluating any outcomes.
5. Only if independently timestamp-safe historical coverage and source rights pass, Research Brain may preregister a **separate** independent football-mechanism test against matched fair 1X2; Scout must not do outcome tests.

### Access blocker
The source CSV link is publicly advertised but the browser returned an unsupported `text/csv` response and direct container HTTP retrieval failed DNS; **no historical CSV rows were read**. Its claimed full-history coverage and daily Git/OpenTimestamps verification therefore remain unverified. No API keys or paid calls were used.

## Independent official free historical source with a hard rights gate: Betfair BASIC
- Official pricing / terms: https://historicdata.betfair.com/ (Soccer BASIC **free**, one-minute **last-traded** price, no volume; history since ~2015, requires registered Betfair.com account; data available only after settlement).
- Official field/frequency guide: https://betfair-datascientists.github.io/data/usingHistoricDataSite/
- Official account/jurisdiction access rules: https://support.developer.betfair.com/hc/en-us/articles/360008664937-Which-jurisdictions-is-Betfair-Exchange-Historical-Data-available-to

**Crucial limitation:** Betfair's official historical portal expressly restricts historical data to **personal/internal use** and requires a separate **commercial licence** for business use; onward distribution is prohibited. Its free BASIC price data are *exchange last-traded prices*, not a matched bookmaker 1X2 closing quote. It is **NOT an authorized commercial Football AI training/product source**, and no account login/download was attempted.

## Decision / governance
- No independent football mechanism met all admission gates in this cycle; no `[SIGNAL-SCOUT][CANDIDATE]` Issue.
- New source leads: 2; verified pre-kickoff public API vectors: 2; verified historical full coverage: 0; Research Brain handoffs: 0; OOT/outcome tests: 0; paid Odds API calls: 0.
- **WAITING_BY_HISTORICAL_COVERAGE_AND_INDEPENDENT_PROVENANCE**. Neither the Betfair BASIC personal-only source nor the unverified retrospective TipsAudit CSV can be used to declare DATA_FEASIBLE.
- No writes to `main`, `registry.json`, Supabase, production .pkl, agent prompts, or deployments; this branch note is research-only.
