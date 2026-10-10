# Signal Scout — pre-kickoff weather forecast revision source gate (2026-10-10)

**Verdict: IDEA / BLOCKED_BY_SOURCE_AND_MARKET_BASELINE.** Research-only; outcome-free. No [SIGNAL-SCOUT][CANDIDATE] Issue, no Research Brain handoff.

## Fresh-main and duplicate audit

- Read fresh `main` commit `96d9a4f8be6cd6fd9f7412603c0695ad48bcf7bb`, `research/programs/registry.json`, and `PROJECT_CONTINUITY.md`. Registry: 14 programs, 13 `PROGRAM_DONE`, 1 `BLOCKED` (point-in-time snapshot cadence, #594).
- Read existing Scout source reports in the BSD, referee/travel, Wikimedia and DataHub branches; checked current open GitHub issues via REST (including #609) and issue search. No open `[SIGNAL-SCOUT][CANDIDATE]` Issue was found.
- Prior BSD Scout report already discusses **48-hour weather forecast level** and the missing exact-T bookmaker consensus; do **not** call ordinary weather levels a new family. This note considers a *different input*: **revision of the forecast for the same kickoff hour between two previously issued model runs**, conditional on the latest forecast level. This is not a tweak to a closed price/odds statistic and does not reopen any `PROGRAM_DONE` outcome sample. Distinctness remains a proposed mechanism, not an empirical result.

## One candidate mechanism: WEATHER_FORECAST_REVISION_1X2_V1 (provisional IDEA only)

An abrupt change in **predicted weather at the same future stadium kickoff** may convey externally generated, time-stamped new information that is not equivalent to historical team form, Elo, rest, referee, market lead/lag, or the *absolute level* of predicted weather. Whether the bookmaker already prices it is unknown; no signal or profit is claimed.

Provisional feature definition (Research Brain alone may freeze):
- Fixed decision time `T = kickoff_utc - 36h`.
- For the stadium grid point, choose the most recent NOAA GFS cycle with **verified source publication/first-seen <= T** and a second cycle **exactly 24h older**, with both runs forecasting the same UTC kickoff hour. Do not substitute pseudo-analysis or later reanalysis. Require exact forecast initialization, valid time, run ID, and original first-seen timestamps. Do not assume model initialization = data publication.
- `revision_wind10m = predicted_wind_speed_at_kickoff(new_run) - predicted_wind_speed_at_kickoff(old_run)` (m/s).
- `revision_precip6h = predicted_6h_accumulated_precip_ending_at_kickoff(new_run) - corresponding_old_run` (mm), only if both source files explicitly support matching 6h accumulation semantics. No interpolation or silently switching 3h/6h definitions.
- Always control for *new-run absolute wind and precipitation levels* to test whether revisions add information rather than rediscover weather; stadium, season, fixed league and fixture-date effects are training-only controls.
- Primary intended target 1X2 multiclass probability; O/U 2.5 only a separately preregistered secondary target with its own same-T baseline. **No outcome data examined.**

## Newly verified source evidence — critical correction

1. Official NOAA ARL archive description: https://www.ready.noaa.gov/archives.php — GFS quarter-degree archive from 2019, public cloud and web download, MD5 manifest and NOAA packed format. NOAA archive includes basic wind, temperature, humidity fields.
2. Official NOAA ARL GFS0p25 README: https://www.ready.noaa.gov/data/archives/gfs0p25/readme_gfs0p25_info.txt — **decisive**: daily `YYYYMMDD_gfs0p25` files concatenate the **+0h and +3h** forecasts from successive six-hourly runs into a *pseudo-analysis*. The source also explicitly says files are **overwritten with more current forecasts as they become available**; occasional anomalous +24h to +45h files are documented. Therefore these large daily archives **are not the historical 36–72h point-in-time forecasts needed for forecast revision**. Do not treat their daily timestamps as proof of 48h weather forecast availability.
3. Official NOAA ARL web directory (metadata only, no binary download): https://www.ready.noaa.gov/data/archives/gfs0p25/2025/10/ lists 31 dated daily files (October 2025), with last-modified timestamps usually on the corresponding day. https://www.ready.noaa.gov/data/archives/gfs0p25/2026/09/ lists 30 daily files (September 2026). These counts establish **archive-object listing coverage only**, not eligible forecast-run coverage or first-seen times. Files are ~2.7–3.1 GB each. No 2026/27 football outcomes inspected.
4. Official NOAA NCEI GFS page https://www.ncei.noaa.gov/products/weather-climate-models/global-forecast notes a **trailing 30-day window** for NOAA AWS public GFS forecasts, though other historical access methods exist. Direct attempts to retrieve 2025/2026 48h GFS `.idx` objects from AWS failed in this environment; no object existence, 2025/26 full-horizon coverage, or publish time was proven.
5. Official Open-Meteo historical forecast docs https://open-meteo.com/en/docs/historical-forecast-api distinguish *stitched short-term runs* from individual Single Runs and Previous Runs. Historical Forecast API is **not** proof of exact 36h/72h issuance; Single Runs are the appropriate semantic class, but available time ranges vary by model.
6. Official Open-Meteo terms https://open-meteo.com/en/terms and pricing https://open-meteo.com/en/pricing: **free API only for non-commercial use**; commercial historical APIs require a paid plan. Do not assume the free endpoint grants eventual product use, and do not purchase/subscribe. No API calls were made.

## Outcome-free source gate before any Scout candidate Issue

1. Identify a **free and legally usable** source of full, original GFS (or equivalent) model-run forecasts for a *predeclared* complete league/season fixture universe; validate with actual small forecast-index responses and exact initialization/valid/publication times. Distinguish analysis (+0/+3) from actual 36–72h predictions.
2. Obtain fixed venue coordinates with as-of provenance; verify both forecast runs and identical weather variable accumulation semantics, and publication <=T for each fixture. Audit missingness by league/season/round **without reading target outcomes**.
3. Establish a complete same-T HOME/DRAW/AWAY fair-probability baseline (all three prices, timestamped receipt, bookmaker/source rights, kickoff and event identity); no retroactive use of `opening_at` as a 36h quote and no paid The Odds API calls.
4. Only after the two source gates pass, Research Brain may preregister training, temporal validation and untouched OOT, including the already reserved 2026/27 outcome firewall. Baselines: contemporaneous de-vig 1X2; market + forecast **level**; market + level + **revision**. Primary paired multiclass LogLoss and Brier with date/league-cluster uncertainty; no posthoc weather threshold/league/sample selection.
5. Negative controls: permute revisions within predeclared stadium/season/calendar strata while preserving absolute forecast level; compare revision-only against level-only; a future-run leakage trap must fail; report missingness-only model.
6. **SUCCESS** only if both proper scores improve on untouched OOT versus strongest market+level control, paired uncertainty excludes zero in favorable direction, consistency and negative controls pass. **STOP** on missing full-run source, legal-rights failure, timestamp coverage gap, missing same-T market, or negative validation/OOT. Scout must not perform outcome testing.

## Decision and measured productivity

- One **conceptual** nonduplicate candidate considered: forecast *revision*, not weather *level*. No independence proof or matched source evidence, so status **IDEA / BLOCKED_BY_SOURCE_AND_MARKET_BASELINE**, **not DATA_FEASIBLE**.
- New source finding: NOAA ARL daily files are pseudo-analysis, **not** retrospective 36–72h forecasts; 61 daily object names inspected across two complete months, 0 eligible full-horizon run pairs verified.
- `DATA_FEASIBLE = 0`, `SIGNAL_FOUND = 0`, new Scout candidate Issues `=0`, Research Brain handoffs `=0`.
- Prior Scout reports likewise show zero admitted handoffs. The GitHub Research Brain 24h tracker #600 closed with zero admitted candidates. Actual per-run wall-clock duration remains unlogged, so no acceleration is claimed.

## Safety

No reserved outcomes, football result tests, paid API calls, Supabase writes/DDL, production .pkl/model training/promotion, registry edits, other-agent prompt edits, direct main write, production deployment, or fabricated economic claims. This document is a Scout branch source-gate report only.


## Additional source-provenance gate — 2026-10-10, NOAA/NCAR historical-vs-operational distinction

**Decision remains `IDEA / BLOCKED_BY_SOURCE_AND_MARKET_BASELINE`; no new candidate and no Research Brain handoff.** This is a continuation of the existing weather-revision hypothesis, not an additional hypothesis.

### Verified official source metadata (outcome-free)

- NSF NCAR GDEX historical full-run dataset `d084001`: https://gdex.k8s.ucar.edu/datasets/d084001/ (DOI `10.5065/D65D8PWK`). Its published documentation explicitly says it **will stop updating in early 2026** in favor of a continuously updated AWS copy. Do not assume the archived historical collection is guaranteed to cover 2026/27 simply because a metadata landing page displays an extended date range. GDEX advertises GFS cycles 00/06/12/18 UTC and 3-hourly forecast steps, which are the correct forecast-run class; forecast initialization is **not** proof of time of availability.
- Current NOAA NODD GFS public AWS listing: https://registry.opendata.aws/noaa-gfs-bdp-pds/ . Its documentation confirms four daily 6-hourly runs, public no-account S3 listing, and open use with attribution/no-endorsement requirements. This confirms a *potential prospective collection source*, not archived 2025/26 object completeness or immutable first-seen timestamps.
- **Do not confuse** the older Unidata `noaa-gfs-pds` bucket with the NOAA NODD bucket. https://registry.opendata.aws/noaa-gfs-pds/ explicitly marks the old source **deprecated** and describes a **rolling four-week archive**; this is not proof of historical 2025/26 full-run availability.
- GDEX and AWS pages do not provide an auditable first-seen receipt log for the precise `f036/f048` objects used at a fixed `T = kickoff - 36h`. An attempted read of a specific public 2025-09-20 NOAA NODD `.idx` object did not succeed in the current environment; no existence or historical availability claim is made on that basis.
- Previously inspected GDEX historical catalogs for 2025-09-20, 2025-10-04, and 2025-10-05 show named full forecast horizons; their current last-modified dates are not original first-seen evidence. The 2026-09 catalog could not be independently fetched during this audit. No GRIB or football outcomes were downloaded.

### Remaining deterministic feasibility gate

Before a candidate Issue, require (1) real historical full-run forecast index responses for a *predeclared* fixture universe; (2) source first-seen or independently established publication schedule with a conservative lag, proving both runs available by T; (3) original fixed stadium coordinates, matching valid-time and accumulation semantics; (4) all three legally usable contemporaneous 1X2 market prices with observed receipt <= T. Existing main's `point_in_time_snapshot_cadence` remains `BLOCKED_BY_TIMESTAMP_COVERAGE`; do not substitute late/opening/closing quotes for same-T snapshots.

If these gates ever pass, **Research Brain alone** freezes temporal validation/OOT, paired multiclass LogLoss/Brier against fair market + absolute weather-level baseline, negative controls (time-shift, permutation, missingness-only), uncertainty and STOP/SUCCESS. Scout performs no outcome test and does not read reserved 2026/27 outcomes.

### Productivity and safety

Fresh-main audit: 14 programs, 13 `PROGRAM_DONE`, one `BLOCKED`; no open `[SIGNAL-SCOUT][CANDIDATE]` Issue. This audit: 0 new candidates, 0 `DATA_FEASIBLE`, 0 new Scout Issues, 0 Research Brain handoffs. The existing 24-hour Research Brain tracker #600 also records zero admitted candidates, but no reliable per-cycle elapsed times are available for an acceleration claim. No paid odds requests, Supabase write/DDL, production model changes, deployment, registry changes, frozen-gate weakening, or result reads.
