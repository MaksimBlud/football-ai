# Signal Scout — THERMAL_ACCLIMATIZATION_GAP_FORECAST_1X2_V0 (2026-10-12)

**Verdict: IDEA / BLOCKED_BY_RAW_FORECAST_SAMPLE_AND_SAME_T_MARKET.** Research-only, outcome-free. **No [SIGNAL-SCOUT][CANDIDATE] Issue, no Research Brain handoff, no signal claim.**

## 1. Governance / duplicate check

- Fresh GitHub main inspected: `c18f0df0b4a579282f366fda8ae1d3b2a9015d03` (latest commit found); read `research/programs/registry.json` and `PROJECT_CONTINUITY.md`. Registry: 14 programs, 13 `PROGRAM_DONE`, 1 `BLOCKED`.
- Queried Scout GitHub branches and Scout/CANDIDATE issues. Found existing weather family branch `scout/20261010-weather-forecast-revision-source-gate` and read its report. That work explicitly covers forecast **levels** and **run-to-run revisions**, and documents NOAA ARL pseudo-analysis and market as-of blockers. This report **does not** rename those signals or reopen any `PROGRAM_DONE` research. Found no Scout candidate Issue by title.
- Other prior Scout families include referee/travel, stadium elevation, air pollution/CAMS, squad availability, league stakes, cross-tier promoted clubs, fixture revision, and crowd policy. Do not substitute those as novel.
- **Distinct proposed mechanism, not yet independently established:** the *relative thermal adaptation of two teams to forecast match conditions*, not absolute stadium weather and not weather forecast revision. Its novelty is an interaction between pre-match weather and pre-match team-specific climate history. It may ultimately be rejected as redundant with the prior weather/travel families.

## 2. Independent scientific lead (not evidence of an edge)

Ru Li, Xiang Li, Chen Zhang (first published 2026-08-05), *Climate Justice in Sports: Quantifying the Thermally-Induced Competitive Inequality*, Journal of Sports Economics, DOI 10.1177/15270025261474144:
https://journals.sagepub.com/doi/abs/10.1177/15270025261474144

The abstract reports an observational study of >39,000 top-five-league matches (1996–2019) and a possible climate **adaptation gap** in home advantage. **This is not a demonstrated improvement over timestamp-matched bookmaker fair 1X2 probabilities.** Do not use its historical match outcomes as an untouched Football AI OOT.

## 3. Proposed preregisterable mechanism / features (no outcomes inspected)

Unit: each fixture in a **predeclared** complete EPL/La Liga/Serie A/Bundesliga/Ligue 1 season universe, not selected after viewing outcomes.

- Fixed decision cutoff proposal: `T = kickoff_utc - 12 hours`. Historical forecast at the stadium must be from a **genuine previously issued run** with archived first-seen/publication `<= T`; a model's nominal init time is insufficient. Proposed forecast valid time is the kickoff UTC hour.
- `H`: forecast apparent temperature (or a preregistered heat-stress proxy from forecast temperature and relative humidity) for the venue at kickoff; **one formula only**, frozen before outcome access. Do not reconstruct from observed match-time/reanalysis weather.
- `C_home`, `C_away`: each club's trailing 30 calendar-day **pre-match** average heat proxy at its documented home training-city/stadium coordinate. Every historical input must have valid time and publication before the match cutoff; do not compute normals from later data.
- `adaptation_gap = abs(H - C_away) - abs(H - C_home)`. Positive values mean the away team's recent home climate is farther from the forecast match climate. No posthoc thresholds, team/league subsets, or sign reversal.
- Main question: does this interaction improve 1X2 probability scoring beyond **(i)** contemporaneous bookmaker fair 1X2, **(ii)** bookmaker + absolute forecast heat level, **(iii)** bookmaker + level + separate home/away climate levels? Include training-only team/venue fixed effects and calendar controls if feasible.
- A 30-day history is a **proposal**, not an approved frozen choice; Research Brain alone may freeze/modify before accessing outcomes. Potential confounders: players may train away from nominal club city, travel acclimatization varies, stadium roofs/solar exposure, forecast grid resolution, game postponements.

## 4. Free source evidence and strict limitations

1. Official NOAA NODD GFS: https://registry.opendata.aws/noaa-gfs-bdp-pds/ . Open use with attribution/no implied endorsement; four model cycles per day, global atmospheric variables. Source documentation confirms **model class and license**, not fixture-specific 2024/25–2025/26 historical object completeness, original publication times, or readable GRIB samples.
2. NSF NCAR GDEX historical full-run archive `d084001`: https://gdex.ucar.edu/datasets/d084001/ (DOI 10.5065/D65D8PWK). Catalog claims 2015+ historical runs, 00/06/12/18 cycles, surface temperature/wind/humidity. Archive metadata alone does not prove a particular fixture's forecast was public before T; site notes archive transition in early 2026. Do not trust metadata dates after the current audit date as availability proof.
3. Open-Meteo Previous Runs API docs: https://open-meteo.com/en/docs/previous-runs-api . `_previous_day1` refers to prediction at a fixed 24-hour lead; most models archived from Jan 2024, variable coverage differs. It is **not** itself a verified exact published model-run receipt; a 12h cutoff leaves margin for issuance latency only after a real as-of audit.
4. Open-Meteo terms: https://open-meteo.com/en/terms ; pricing https://open-meteo.com/en/pricing . Hosted free API **non-commercial only**; data CC BY 4.0 is not blanket permission for commercial hosted API access. No purchases. Commercial product path, if ever needed, would require a separately approved legally usable NOAA self-managed pipeline or proper license.
5. Peer-reviewed caution: https://www.mdpi.com/2076-3417/10/19/6750 studies weather and soccer results but not this preregistered bookmaker-incremental gate. https://doi.org/10.1371/journal.pone.0247771 reports limited meaningful effects of light rain in Bundesliga player performance, reinforcing risk of a null result.

**Actual outcome-free sample proof this cycle:** 0 archived GRIB/forecast rows; 0 fixture-to-forecast matches; 0 verified stadium coordinates; 0 same-T full H/D/A bookmaker triplets. The environment's container cannot resolve external weather-data hosts; the web retrieval could read source documentation but not the requested historical raw GFS `.idx` object. Thus **not DATA_FEASIBLE**.

## 5. Mandatory source gate BEFORE a candidate Issue

1. Predeclare fixture universe, years, leagues, stadium-coordinate source, kickoff timestamp source and legal rights. Produce fixture count by league/season without reading outcomes.
2. Obtain a **real** archived forecast object or response for a predeclared date, log raw URI/checksum/run init/valid hour/variable units and evidence of first-seen/publication <= T. Check >=90% complete predeclared coverage (illustrative gate only; Research Brain must approve before outcomes) for both venue and two team climate histories. No imputation or future reanalysis.
3. Obtain same-T bookmaker H/D/A prices with event identity, exact timestamp receipt <= T, overround and rights; compare only on paired fixtures. Historical opening/closing odds without exact T cannot be silently relabeled as a T quote.
4. Only after outcome-free source pass, Research Brain owns frozen model/evaluator and independent train/validation/OOT split. Primary paired multiclass **LogLoss and Brier**, fixture/date-cluster bootstrap CIs, cross-league consistency, source missingness audit. 2026/27 reserved outcome firewall remains closed.
5. Negative controls: (a) within-calendar-month permutation of away-city climate among predeclared away teams; (b) placebo same venue climate for both teams, forcing adaptation gap to zero; (c) weather-level-only model; (d) future-run leakage test that must fail as-of gate; (e) missingness-only predictor.
6. **SUCCESS** only if the full stronger market+weather-level+climate-level control is beaten on untouched OOT on both proper scores with paired uncertainty and cross-league robustness. **STOP** on rights/coverage/as-of/market failure, leakage, negative validation or OOT. Scout performs **no outcome tests**.

## 6. Cycle and 24h productivity

- Conceptual mechanism considered: **1**; empirically admissible new independent candidate: **0**.
- `DATA_FEASIBLE=0`; `Research Brain handoffs=0`; `new candidate Issues=0`; `paid The Odds API calls=0`; `outcome reads=0`.
- Compared with accessible 2026-10-10 through 2026-10-12 Scout reports: multiple distinct source-gate investigations, **no confirmed admitted Research Brain handoffs**. Source/license and historical same-T market gaps remain binding. Exact per-cycle wall-clock runtime is not instrumented; cannot claim the 40-minute experiment accelerated discovery. Do not count branch count as scientific output.
- No new candidate Issue because the key raw data and same-T bookmaker feasibility are unproven.

## 7. Safety

No paid The Odds API/cron, no Supabase writes/DDL, no production model .pkl/training/promotion, no deployment, no edits to other agents/prompts, no registry changes, no reserved outcomes, no threshold/league/sample mining, no main write/force-push, no profit claims.
