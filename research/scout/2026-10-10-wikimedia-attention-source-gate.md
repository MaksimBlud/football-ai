# Signal Scout — Wikipedia attention shock source gate (2026-10-10 UTC)

**Verdict: IDEA / BLOCKED_BY_SOURCE. No DATA_FEASIBLE claim. No Research Brain handoff or candidate Issue. Research-only, outcome-free.**

## Fresh-main duplicate gate
Read fresh `main` `research/programs/registry.json` and `PROJECT_CONTINUITY.md` and checked open GitHub issues plus prior Scout source audits. Registry contains **14 programs: 13 PROGRAM_DONE, 1 BLOCKED** (`point_in_time_snapshot_cadence`). Relevant closed families: `team_change_faster_than_market` (manager/lineup/injury/tactical), `market_residual_process_divergence`, `kickoff_calendar_context`, `independent_information_source_disagreement`, and bookmaker price/margin families. Prior Scout reports also already cover weather, referee assignment, travel-distance duplicate, FPL availability, and halftime transition. Searches for `Wikipedia`, `attention`, `popularity` in repository issues returned no matches; search incompleteness remains possible. This is **not** a resurrection of team-form, SOT, rest, manager or price-movement features.

## One new exploratory mechanism: WIKIMEDIA_CLUB_ATTENTION_SHOCK_1X2_V1
Hypothesis (unverified): an unusual *change* in public information-seeking attention to a club may capture external news / uncertainty not fully reflected in contemporaneous market fair 1X2 probabilities. This is a public-attention channel, not an assertion that popularity, pageviews, or internet traffic directly cause wins. Confounding by recent matches, big-club size, news coverage and fixture importance is expected. No profitability claim.

**Provisional feature contract (not frozen):**
- Fixture universe: all five top leagues on a future season fixed by Research Brain *before outcomes*; no post-hoc league or club selection.
- Decision time `T = kickoff_utc - 48h`. For every fixture use only complete UTC calendar days ending at or before `T - 48h` (conservative publication lag, to be proved rather than assumed).
- Team identifier to English Wikipedia article mapping must be fixed and audited before outcomes; no hindsight joins through later renames/redirects. Any ambiguous/missing team article fails closed.
- `shock_team = log1p(mean_user_views_last_7_eligible_days) - log1p(mean_user_views_prior_28_eligible_days)`; candidate `shock_home - shock_away` plus missingness flags, using only source-observed daily counts. The 7/28-day horizons are *proposal only*; Research Brain owns preregistration.
- Negative values, missing daily values and redirect history must not be silently imputed as zero; distinguish API 404 from zero and not-yet-loaded days.

**Why mechanistically distinct:** independently measured *reader attention* rather than odds geometry, match results, strength trajectories, player availability or match time. Empirical orthogonality to market and other controls remains untested.

## Source evidence (documentation verified, NOT actual data coverage)
1. Official Wikimedia Analytics API per-article pageviews since July 2015: https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/reference/page-views.html
2. Official licensing/access policy: **CC0 1.0**, User-Agent required, rate-limits apply: https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/documentation/access-policy.html
3. Official data availability: usually within hours, **may take 24h or more**, 404 can mean zero or not loaded: https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/documentation/troubleshooting.html
4. Public hourly archive documentation: https://wikitech.wikimedia.org/wiki/Analytics/Data/Pageviews
5. Redirect caveat: https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/concepts/page-views.html
6. Data download CC0 statement: https://analytics.wikimedia.org/

**Real-response gate failed in this environment:** attempts to read official per-article API for Arsenal F.C. and Real Madrid CF for 2026-10-01…07 returned web-tool DisabledError / inaccessible; public hourly dump directory also could not be fetched. The environment's container has no external DNS. **No pageview counts, team-level coverage percentages, actual publication receipts, historical first-seen timestamps or 1X2 market baseline are proven.** No invented values. This is a source feasibility audit, not a signal finding.

## Strict outcome-free feasibility gate (must precede any candidate Issue)
1. From the official CC0 endpoint or timestamped hourly dumps, verify actual nonzero and missing/404 responses for a *predeclared*, complete five-league fixture universe and frozen team-to-article mapping. Preserve receipt UTC, source URLs, response hash and access-license version.
2. Prove source publication availability `<=T` for every used daily observation: conservative lag is a design buffer, **not proof**. If using historical daily API, verify that later backfills/edits do not change values used as-of T; if impossible, restrict to future immutable captures.
3. Quantify team/fixture join coverage, redirect/rename gaps, source missingness and date coverage **without reading match results**. Predefine acceptable coverage and missingness before querying.
4. Verify contemporaneous complete HOME/DRAW/AWAY 1X2 quotes at the *same* decision time T with first-seen/receipt provenance and usage rights; current BSD opening/current prices or TipsAudit selected-outcome quotes are not substitutes. No paid The Odds API calls.
5. Only Research Brain may freeze the training / temporal validation / untouched future OOT split and evaluator. Compare: (a) same-T de-vig fair market; (b) market + predeclared generic club popularity / recent schedule / historical strength controls; (c) market + attention shock. Primary paired multiclass **LogLoss and Brier**, time/league-cluster uncertainty, consistency across fixed leagues/time.
6. Negative controls: team-attention shocks permuted within fixed league/fixture-week/popularity strata; unrelated article pageviews; missingness-only model; a future-pageviews leakage trap that must fail. No post-hoc horizon tuning, club cherry-picking, or reuse of reserved 2026/27 outcomes.
7. **SUCCESS** only if preregistered untouched OOT shows improvement over strong controls on *both* proper scores, uncertainty intervals exclude zero in the beneficial direction and frozen consistency/negative-control gates pass. **STOP** if source rights, actual timestamp provenance, historical availability, mapping or market baseline fails, or validation/OOT gates fail.

## Measured cycle outcome
New independent mechanisms proposed: **1 (IDEA only)**. Source rights and published endpoint documented: **yes**. Actual point-in-time data and matched baseline verified: **no**. DATA_FEASIBLE: **0**. Research Brain handoffs: **0**. New Scout Issues: **0**. Signal found: **0**. No measured run-duration comparison: previous cycle start/end timestamps were not durably recorded. The Scout 24-hour throughput comparison cannot claim acceleration without actual wall-time evidence.

## Safety
No reserved future outcome reads, match-result tests, paid provider calls, Supabase writes/DDL, model .pkl/training/promotion, registry changes, changes to other agents/prompts, main writes, production deployment, or betting actions. This file is an exploratory scout-only branch report, not a new frozen program.


## Follow-up audit — 2026-10-10, 14:18 UTC cycle (outcome-free)

**Status remains BLOCKED_BY_SOURCE; not DATA_FEASIBLE.** Fresh main registry re-read: 14 programs, 13 PROGRAM_DONE and 1 BLOCKED. Open issue search showed product/development #578–#583 and Brain 24h #600; no Scout candidate Issue. No closed-family thresholds or OOT cohorts reopened.

### New directly relevant scientific evidence
Kobayashi, Gildersleve, Uno & Lambiotte (2021), *Modeling Collective Anticipation and Response on Wikipedia*, ICWSM 15(1), 315–326, DOI https://doi.org/10.1609/icwsm.v15i1.18063, explicitly models anticipatory growth **and post-event response** around football events. The abstract reports that the match's actual result influences **post-event** attention dynamics; it does **not** establish that pre-event attention predicts the result or beats bookmaker probabilities. This materially increases the need to forbid all event-day/post-match windows and to control for predictable fixture-driven traffic.

### Official measurement/provenance caveats rechecked
- https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/documentation/troubleshooting.html : loading is usually within hours but can take >=24h; a 404 is ambiguous between true zero and not-yet-loaded; zero days may be omitted from timeseries. No historical first-seen receipt is returned.
- https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/concepts/page-views.html : article redirects are **not counted as views of the destination article**. Renames/alternate spellings can create artificial shocks; a current redirect map is not an as-of historical mapping.
- https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/documentation/access-policy.html : pageview data CC0, mandatory identifiable User-Agent and rate limits.
- Attempted actual per-article API read for Arsenal F.C. August 2026 through the available web fetch: **DisabledError**; container direct HTTPS request: DNS failure. No JSON/HTTP 200 response, no verified counts, no coverage statistics and no durable T-minus receipt. These are **runtime access failures**, not evidence that the API is empty.

### Pre-registered falsification requirements for any future Brain handoff
1. Hold out entire fixture dates; exclude all article observations whose **first-seen receipt** is later than prediction T, not just dates labelled before T.
2. Use negative controls that preserve **club popularity, upcoming-fixture proximity and league-week**. Also control prior fixture results and current market fair 1X2; otherwise event anticipation is merely a schedule proxy.
3. Audit title redirects/renames as of T, 404 vs true zero, delayed loads and API revisions; no retroactive imputation.
4. Match full timestamped 1X2 fair market quotes at the same T; compare paired multiclass LogLoss and Brier vs market+popularity+fixture controls.
5. STOP before outcome testing if source response, first-seen historical provenance, club join coverage, or matched market odds remain unavailable. No Scout candidate Issue until that outcome-free feasibility gate passes.

**Cycle delta:** one newly cited peer-reviewed paper directly relevant to leakage/confounding; two verified official data semantics (404 ambiguity and redirect nonaggregation); 0 verified pageview series; 0 DATA_FEASIBLE; 0 new Scout Issues; 0 Research Brain handoffs; 0 confirmed signals. Prior run-duration telemetry remains absent, so no 24-hour speedup claim. No reserved outcome reads, paid API, Supabase write, registry edit, production/model/deployment change.
