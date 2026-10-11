# Signal Scout — no-key terrain-tile source gate and offline decoder proof

**Date:** 2026-10-11 UTC. **Family:** existing `STADIUM_ALTITUDE_ADAPTATION_1X2_V1`. **Status:** `IDEA / BLOCKED_BY_SOURCE_AND_MARKET_BASELINE`; not DATA_FEASIBLE, not SIGNAL_FOUND. Research-only, outcome-free.

## Governance and novelty
Read fresh GitHub main `research/programs/registry.json` (14 programs: 13 PROGRAM_DONE, one BLOCKED), `PROJECT_CONTINUITY.md`, existing altitude Scout reports and open issues. No open `[SIGNAL-SCOUT][CANDIDATE]` issue found. Existing travel/rest and tactical families are closed. This is **a new acquisition/verification method for the existing altitude hypothesis**, not a newly independent hypothesis, and does not reopen a PROGRAM_DONE family.

## New source path (direct original-provider documentation)
- AWS Registry of Open Data: https://registry.opendata.aws/terrain-tiles/ — Mapzen/Tilezen Terrain Tiles; anonymous S3 read documented with `--no-sign-request`, source-dependent attribution.
- Direct static Terrarium PNG format: `https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png`; described by https://geodataviewer.com/datasets/dem/aws-elevation-tiles/ and https://github.com/tilezen/joerd/blob/master/docs .
- Required provider attribution: https://github.com/tilezen/joerd/blob/master/docs/attribution.md ; underlying source list: https://github.com/tilezen/joerd/blob/master/docs/data-sources.md . **Do not conflate MIT-licensed code with terrain-data licenses.**
- Open stadium coordinates candidate: https://drawonamap.com/datasets/european-football-stadiums/ (4,564 point records from 2026-09-14 OSM snapshot; ODbL; no claim of historical fixture-level venue coverage).

Unlike the OpenTopoData public API, this route needs no API account/key and uses static AWS tiles. It still requires live tile retrieval and correct source attribution before claiming actual elevations.

## Reproducible outcome-free local probe
Implemented an offline-capable, Python-stdlib-only dry-run tile locator and PNG/Terrarium decoder, plus six deterministic unit tests (all **6/6 PASS** locally). No football outcomes or paid endpoints were accessed.

For illustrative coordinates **(48.2188, 11.6247)**, zoom 12 dry-run returned XYZ `12/2180/1420`, pixel `(67,25)`, and expected S3 URL `https://s3.amazonaws.com/elevation-tiles-prod/terrarium/12/2180/1420.png`. These coordinates are **illustrative, not a verified venue coordinate receipt**. `height_m=null` by design until an actual tile is downloaded and decoded. Terrarium decoding: `height_m = R*256 + G + B/256 - 32768`. The probe defaults to NO network and requires an explicit `--fetch` for a read-only S3 request.

A direct real HTTPS GET to S3 from this runtime failed at DNS resolution (NameResolutionError). **Actual retrieved tiles: 0; independently measured venue heights: 0.** Offline tests validate only code logic, not provider reachability, coverage, historical venue correctness, or height accuracy.

## Exact source-only gate before Research Brain
1. Pin OSM data snapshot/license and complete season-specific official club/home-ground mapping, including actual match venue at predeclared prediction T; handle renames, neutral venues, relocations and unknowns.
2. Fetch and hash actual terrain tiles, capture UTC retrieval time, fixed zoom/raster version, coordinate provenance and source attribution. Cross-check sampled heights with an independent DEM; record all failures. No height or venue coverage figures until actual reads succeed.
3. Predeclare minimum coverage and minimum height spread **outcome-free**, before any match-result reads; do not cherry-pick leagues, clubs, or stadiums after inspection.
4. Independently establish legally usable complete 1X2 HOME/DRAW/AWAY market prices at **the same fixed pre-kickoff T**. Registry `point_in_time_snapshot_cadence` is BLOCKED_BY_TIMESTAMP_COVERAGE. Opening/closing odds must not masquerade as exact-T prices.
5. Only Research Brain can preregister train/validation/untouched-OOT, compare market fair 1X2 vs strongest geography/rest/absolute-altitude baseline vs + signed venue-altitude difference, and evaluate paired multiclass Brier and LogLoss with clustered CIs and league transport. Negative controls: height permutation within geographic strata, venue-alias placebo, missingness-only and post-T venue change. STOP on any source/coverage gate failure or failed OOT; SUCCESS only on frozen OOT superiority in both scores with supportive uncertainty and controls.

## Measured Scout productivity
This cycle: 1 new **source access path**, 0 new independent hypotheses, 0 DATA_FEASIBLE, 0 Research Brain handoffs, 0 new Scout Issues, 0 measured DEM elevations. Prior available 24h reports also record 0 Brain handoffs. Six local decoder tests passed; these are not signal evidence. No reliable per-cycle elapsed-runtime measurements: cannot claim improvement from the 40-minute experiment.

## Safety
No paid The Odds API requests, no Supabase writes/DDL, no outcomes/reserved OOT reads, no model .pkl training/promotion, no production deployment, no registry changes, no agent/prompt edits, no main write, no fabricated market probabilities or profit.
