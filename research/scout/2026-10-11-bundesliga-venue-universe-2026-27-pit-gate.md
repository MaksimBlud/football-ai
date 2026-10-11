# Signal Scout — official Bundesliga 2026/27 venue-universe PIT audit

**Date:** 2026-10-11 UTC. **Verdict:** existing `STADIUM_ALTITUDE_ADAPTATION_1X2_V1` remains `IDEA / BLOCKED_BY_SOURCE_AND_MARKET_BASELINE`; **NOT** DATA_FEASIBLE or SIGNAL_FOUND. No new hypothesis/Issue/Brain handoff. Research-only, outcome-free.

## Fresh-main governance / duplicate gate
- Re-read GitHub `main` `research/programs/registry.json` and `PROJECT_CONTINUITY.md`, prior Scout altitude, referee/travel, weather, Wikimedia and BSD reports, and open issues.
- Registry: 14 programs, 13 `PROGRAM_DONE`, one `BLOCKED` (`point_in_time_snapshot_cadence`). Prior `V2B_TRAVEL_CITY_STAGE_B` covers geographic travel/corner repricing, not venue altitude physiology vs 1X2 fair market; do **not** reopen or retune it. No open `[SIGNAL-SCOUT][CANDIDATE]` issue.
- This note is a **source-universe audit of an existing hypothesis**, not a new independent hypothesis.

## New, directly verified, official pre-season source
- Bundesliga's 2026/27 list **published 2026-07-02**, before the season: https://www.bundesliga.com/en/bundesliga/news/stadiums-germany-2026-27-munich-dortmund-37962
- It explicitly lists all **18 club home stadiums** for 2026/27 (not a proof of every actual fixture venue):
  1. Bayern Munich — Allianz Arena
  2. Borussia Dortmund — Signal Iduna Park
  3. Bayer Leverkusen — BayArena
  4. VfB Stuttgart — MHPArena
  5. Eintracht Frankfurt — Deutsche Bank Park
  6. Hamburg — Volksparkstadion
  7. Borussia Mönchengladbach — ista-Borussia-Park
  8. Cologne — RheinEnergieStadion
  9. RB Leipzig — Red Bull Arena
  10. Werder Bremen — Weserstadion
  11. Freiburg — Europa-Park Stadion
  12. Mainz — Mewa Arena
  13. Augsburg — WWK Arena
  14. Hoffenheim — SNP Arena
  15. Union Berlin — Stadion An der Alten Försterei
  16. Schalke — Veltins-Arena
  17. Elversberg — Ursapharm-Arena an der Kaiserlinde
  18. Paderborn — Home-Deluxe-Arena
- Independent prior-season official venue list **published 2025-06-18**: https://www.bundesliga.com/en/bundesliga/news/stadiums-germany-2025-26-allianz-arena-signal-iduna-park-32656
- **Set difference of the two pre-season lists:** 2025/26-only clubs/venues: St. Pauli/Millerntor, Wolfsburg/Volkswagen, Heidenheim/Voith; 2026/27-only: Schalke/Veltins, Elversberg/Ursapharm-Arena, Paderborn/Home-Deluxe. Thus a naive *previous-season* venue roster misses **3 of 18** 2026/27 club home venues; **do not** confuse this roster audit with 18/18 match-level coverage.
- Official 2025/26 list states Heidenheim's Voith-Arena altitude **555 m**; it is absent from the official 2026/27 roster. No valid claim that 555 m is the maximum altitude of 2026/27 grounds.
- 2026/27 article documents a **stadium sponsorship rename** (Hoffenheim PreZero → SNP Arena) and planned **mid-season renovation** of Elversberg's venue. These facts must be handled as stadium-identity aliases and potential venue/geometry change flags, not as verified mid-season venue switches. Freiburg's move in 2021/22 is a historical example why modern home stadium cannot be backfilled to earlier fixtures.

## Elevation service evidence / actual response boundary
- Official free service docs: https://www.opentopodata.org/ (public instance, up to 100 locations/request, 1 request/s, 1000 requests/day); https://www.opentopodata.org/datasets/srtm/ (SRTM 30 m, latitudes -60..60); source code https://github.com/ajnisbet/opentopodata (MIT software license; verify underlying raster attribution separately).
- Tried actual OpenTopoData elevation query at **Voith-Arena** (48.668529, 10.139319) and alternatives via HTTPS from container. Requests failed at DNS resolution. The web reader also could not open actual OpenTopoData point JSON. **Measured DEM elevations = 0**, not 18; this is an access failure, not a proof that the service has no data.
- Venue coordinates for 18 grounds, point-response receipt times/hashes, per-ground altitude, full five-league spread and all match-level venue joins **remain unverified**. Official club→usual-venue mapping is only one component.

## Strict next source-only gates (no match outcomes)
1. Freeze complete five-league season/fixture universe and decision time before any outcome reads. Build an immutable per-season club→usual-venue map from dated official league/club sources; store source URLs, capture time, aliases and relocation periods.
2. Match **each fixture's actual venue** and venue change announcement as known by decision time T, with an explicit unknown/neutral/relocated state. The official 18/18 roster is not a substitute.
3. Obtain and hash real free DEM responses for **all** frozen venues (and away usual grounds), with coordinate provenance, raster/version, null handling and dataset license. Compute spread/coverage **without** choosing outcome-driven thresholds.
4. Independently prove contemporaneous, complete, permitted 1X2 HOME/DRAW/AWAY fair-price snapshots at the **same** T; registry `point_in_time_snapshot_cadence` remains blocked. No closing/opening substitution for exact T.
5. Only Research Brain may freeze train/validation/untouched-OOT and evaluate market vs market+geography/rest/absolute altitude vs +signed altitude difference. Primary paired multiclass LogLoss and Brier with clustered uncertainty, predeclared league transport and controls (height shuffle within geography, venue-alias placebo, missingness-only, post-T venue-change trap). STOP at any source gate failure, weak altitude support under a **predeclared outcome-free** rule, or negative OOT scores. SUCCESS only on both metrics against strongest baseline with favorable CIs and passing controls.

## Measured result and 24h comparison
- Official pre-season 2026/27 club-home-venue identities checked: **18/18 named**, source publication date verified. Official season-over-season roster delta: **3 in / 3 out**.
- **Not measured:** 18 DEM elevations, historical fixture-level venue coverage, exact-T 1X2 prices, any Brier/LogLoss, wall-clock durations of prior Scout cycles.
- New independent hypotheses: **0**; DATA_FEASIBLE: **0**; new Scout Issues: **0**; Research Brain handoffs: **0**; confirmed signals: **0**.
- Previous 24h Scout reports also found **0 handoffs**. No speedup can be inferred from commit counts or allowed 40-minute maximum.

## Safety
No match outcome queries/tests, no reserved OOT reads, no paid The Odds API, no Supabase writes/DDL, no production .pkl/model training/promotion/deployment, no registry edits, no other agent/prompt edits, no direct main write, no threshold mining.
