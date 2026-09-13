# Football AI — Project Continuity

Этот файл — каноническая память проекта между чатами. Source of truth: **fresh GitHub `main` + live Supabase**. Git history хранит исторический detail; здесь фиксируются только binding rules, текущие contracts/gates, доказанные live facts и следующий execution pointer.

## Правила работы

- Repo: `MaksimBlud/football-ai`, default branch `main`.
- Существенный change: fresh main -> branch -> tests -> PR -> полный CI -> fresh-main compare -> exact-head merge -> post-merge/live proof -> continuity-only update.
- Production `.pkl` нельзя менять как побочный эффект research/training. Training/research != promotion. Automatic model promotion запрещён.
- Не делать mass-clean/reset/mass-format и не перетирать параллельные изменения.
- Frozen/preregistered research contracts нельзя ослаблять задним числом; prospective outcomes нельзя читать до разрешённого gate.
- Paid provider calls остаются manual-only и требуют explicit permission; сначала использовать zero-cost/read-only proof.
- Реальные дефекты закрывать regression-тестами. Fail-closed red нельзя искусственно превращать в green.
- Forecast, value, bet decision и portfolio exposure — разные сущности и не подменяют друг друга.
- Unsupported markets/results нельзя синтезировать ради полноты UI.

---

# Research state

## `ALL_LEAGUES_MARKET_ONLY_V1_1` — FROZEN / SAMPLE_CLOSED / COLLECT, DON'T PEEK

- Freeze: `2026-09-12T02:04:34Z`; first seed kickoff: `2026-09-12T12:00:00Z`.
- Frozen seed: exact `127` immutable keys across 8 leagues.
- Gate: минимум `100` eligible events **в каждой** лиге + минимум `4` UTC kickoff months **в каждой** лиге; все 8 проходят одновременно.
- Primary sample = deterministic kickoff/event/key prefix; outcomes закрыты минимум до 24h после latest primary-prefix kickoff.
- Interim outcome peeking, threshold search, subgroup selection и performance-based optional stopping запрещены.
- Primary metrics после открытия gate: multiclass log loss + multiclass Brier; secondary: argmax accuracy; report per league + pooled micro + unweighted league macro.
- До gate разрешены только outcome-blind health/identity/completeness checks и frozen future-only capture.

## `EPL_AI_MARKET_PAIR_V1` — separate frozen EPL experiment

- Не смешивать с eight-league MARKET_ONLY cohort и не backfill его product rows как research evidence.
- Production EPL model нельзя переносить на другие лиги ради ускорения sample.
- Product bootstrap использовал durable paired-AI outputs, но это не меняет frozen research membership/gates.
- Frozen model artifact SHA used by the product bridge: `1e516fe91420fdc2d6479e9fb92b005c4a0c75c7f0f217493dd6b27fd64d99a5`.

## Historical corners — CLOSED / STOP RULE

CORNERS10 остаётся полезным football-only signal для 1X2, но не доказательством качества corner-total prediction. Historical corner-total V1–V4 не переоткрывать на тех же данных без independent evidence.

## Signal Discovery 2026-09-13 — BLOCKS 1–7 COMPLETE / RESEARCH-ONLY

User explicitly authorized a bounded historical Signal Discovery pass. The initial three candidate-signal tests were followed by explicit source-capability closure for lineup/tactical/true-xG ideas and one bounded interaction test. This work is an explicit research diversion and **does not replace the accepted P0–P4 anti-jump strategy, alter frozen cohorts, open prospective outcomes or authorize Candidate V2/production changes**.

Common methodology:
- existing Historical Football Signal Lab reused instead of creating a second incompatible research framework;
- Football-Data seasons `2016-2017` through `2025-2026`, EPL + La Liga + Serie A, `11,400` historical fixtures total;
- expanding-season walk-forward: first 3 seasons train, next season test, then expand; 7 evaluated seasons per league;
- fixed feature contracts were coded before reading the new ablation results; no window/threshold search after results;
- each performance candidate compared both with football-only `CORNERS10` and/or an explicit main-effect baseline and with `MARKET_MODEL` where applicable, so football signal quality is separated from incremental value beyond market;
- all features are point-in-time and current-match values/results cannot affect current-match features by regression contract;
- capability gates deliberately fail closed rather than synthesizing unsupported lineup/tactical/xG data;
- no frozen prospective target/outcome tables were read; no Supabase writes; no paid-provider calls; no training/promotion; production `.pkl` hashes were checked before/after every full historical run and remained unchanged.

### Block 1 — `TEAM_STRENGTH_TRAJECTORY_V1` — FOOTBALL-ONLY STRONG / MARKET-INCREMENTAL NOT PROVEN

Fixed signals:
- pre-match Elo level difference;
- five-prior-match Elo trajectory difference;
- five-prior-match performance-vs-Elo-expectation residual difference.

Historical paired result vs `CORNERS10`:
- EPL: accuracy `+0.003759`, Brier `-0.010168`, log loss `-0.012839`; Brier wins `7/7`, log-loss wins `6/7`;
- La Liga: accuracy `+0.018421`, Brier `-0.012917`, log loss `-0.016970`; Brier/log-loss wins `7/7`;
- Serie A: accuracy `+0.007895`, Brier `-0.009481`, log loss `-0.013597`; Brier/log-loss wins `7/7`.

Historical paired result vs `MARKET_MODEL`:
- EPL: Brier `+0.000235`, log loss `+0.000741`;
- La Liga: Brier `+0.000092`, log loss `+0.000356`;
- Serie A: Brier `-0.000435`, log loss `-0.000412`.

Decision: trajectory is a **promising portable football-only candidate signal**, but it has no robust historical incremental edge beyond market and is not promoted or inserted into frozen prospective cohorts. Any future use must go through a separately justified Candidate/prospective contract after higher-priority evidence gates permit it.

PR #291:
- head `0c0332555bcf30af931ad3083ff8ce75e80d254d`;
- all Product/Research/Serie A/Bundesliga/Ligue 1/Eredivisie + Historical Signal Lab validations green;
- historical run `34747661915`, job `103698449664`; regression suite `13 passed`;
- artifact `10315155019`, digest `sha256:0bbe33c5a7fb456860cb421a6ef75f7456fe1d2d32612e724573e51bd77386a3`;
- exact-head merge `174775e5f80710aac36aa492b065ab6b1bc25ceb`.

### Block 2 — `REST_CONGESTION_V1` — NEGATIVE / CLOSED

Source limitation was declared before results: Football-Data league history does not provide full cup/European/travel calendar, therefore these are explicitly **league-schedule proxies**, not full physical congestion.

Fixed signals:
- relative rest days since prior league match;
- relative league matches in prior 7 days;
- relative league matches in prior 14 days.

Historical paired result vs `CORNERS10`:
- EPL: Brier `+0.002043`, log loss `+0.005107`;
- La Liga: Brier `+0.000933`, log loss `+0.001509`;
- Serie A: Brier `+0.002033`, log loss `+0.013757`.

Historical paired result vs `MARKET_MODEL`:
- EPL: Brier `+0.002429`, log loss `+0.007620`;
- La Liga: Brier `+0.001607`, log loss `+0.002576`;
- Serie A: Brier `+0.002104`, log loss `+0.015254`.

Decision: exact `REST_CONGESTION_V1` is **historically negative and CLOSED**. Do not tune alternative windows/thresholds on the same sample. Reopen only with independent richer schedule evidence/source that includes cup/Europe/travel or another genuinely new hypothesis.

PR #292:
- head `a5467159b7baae1872277180e2677b5a54c61c44`;
- all seven validation contours green; historical regression suite `16 passed`;
- historical run `34747790372`, job `103698795459`;
- artifact `10314692143`, digest `sha256:852025fcc582561efcc195f2bc4cb2d65124a78e3fb75dcd668b6294006741ed`;
- exact-head merge `0eda74a2bc9dd5a0bbd8246add263b26ca79edd2`.

### Block 3 — `SHOT_QUALITY_PROXY_V1` — FOOTBALL-ONLY PROMISING / MARKET-INCREMENTAL NEGATIVE; TRUE xG DATA-SOURCE GATE

The free historical source exposes shots/shots-on-target but the actual 30 downloaded season files exposed **no detected true-xG column pair**. The implementation therefore deliberately uses only a `SHOT_QUALITY_PROXY` and never calls it xG.

Fixed rolling-10 point-in-time profile:
- shots for/against;
- shots on target for/against;
- aggregate SOT/shots attacking and conceding rates;
- home-away differences for the six fields above.

Evidence tiers were frozen before results:
- EPL + La Liga = `PRIMARY`;
- Serie A = `SOURCE_CAVEAT_SENSITIVITY` because the source documents a historical shots-definition inconsistency from 2018/19 onward.

Source capability proof from the real 10-season downloads:
- EPL: `shots_complete=True`, `true_xg_pair_detected=False`;
- La Liga: `shots_complete=True`, `true_xg_pair_detected=False`;
- Serie A: `shots_complete=True`, `true_xg_pair_detected=False`.

PRIMARY historical paired result vs `CORNERS10`:
- EPL: accuracy `-0.003008`, Brier `-0.001493`, log loss `-0.001770`; Brier/log-loss wins `5/7`;
- La Liga: accuracy `+0.001880`, Brier `-0.004266`, log loss `-0.006725`; Brier/log-loss wins `7/7`.

PRIMARY historical paired result vs `MARKET_MODEL`:
- EPL: accuracy `-0.004511`, Brier `+0.002504`, log loss `+0.004006`;
- La Liga: accuracy `+0.003383`, Brier `+0.001169`, log loss `+0.001616`.

Serie A sensitivity-only result also improved `CORNERS10` on Brier/log loss but worsened `MARKET_MODEL`; it is not used to upgrade the evidence tier.

Decision: free shot/SOT profile is a **promising football-only research candidate but historically market-incremental negative**. Do not promote it or start same-sample feature/window search. **True xG remains a separate `DATA_SOURCE_GATE`** requiring a supported source plus a new preregistered evaluation; proxy data must never be relabeled as xG.

PR #293:
- head `e3252edbbda71b975b65f01d8c20b268b134d534`;
- all seven validation contours green; historical regression suite `20 passed`;
- historical run `34747980991`, job `103699296490`;
- artifact `10315020904`, digest `sha256:51e7f65f61873e318b3878eb37badd734af3c0d1a0e1893efbddcbe9ec7b387e`;
- exact-head merge `2dfc375d51a6d0c825597c1280b77d5120c0bd00`.

### Block 4 — `LINEUP_STRENGTH_CAPABILITY_V1` — DATA_GAP / FAIL-CLOSED

Current Football-Data historical schema does not provide a supported point-in-time lineup/player-strength contract. The capability audit explicitly distinguishes lineup identity and explicit lineup-strength fields from generic team-strength aggregates; a field such as `TeamStrength` must not be relabeled as lineup strength.

Experiment-ready requirements:
- identifiable starting-XI/lineup data;
- explicit player/lineup-strength information rather than team aggregates;
- temporal provenance proving the information was available before the target fixture.

Decision: current source is a **DATA_GAP**, not a negative performance result. Do not synthesize or backfill lineup strength from team-level features.

PR #295:
- head `ee3f765f4afa934d556451be7097dc0a2bc50494`;
- Historical Football Signal Lab run `34750466337`, job `103705987342`;
- all seven required validation workflows green; three-league lab and production `.pkl` hash guard green;
- exact-head merge `c6872f5fe244fb4c42175e513d7bf6be97e69dfc`.

### Block 5 — `TACTICAL_MATCHUP_CAPABILITY_V1` — DATA_GAP / FAIL-CLOSED

Ordinary shots/corners/fouls/cards are team-stat proxies and are **not** silently relabeled as tactical-matchup data. A genuine tactical experiment requires explicit tactical context such as formation, possession/passing structure or pressing-type fields plus point-in-time provenance.

Decision: current source does not satisfy that contract, so Tactical Matchup remains an explicit **DATA_GAP / capability gate**, not a performance claim.

PR #296:
- head `b26ae4b59a94657180553a883fc22d5f430ce9dc`;
- Historical Football Signal Lab run `34750626439`;
- all seven required validation workflows green;
- exact-head merge `c33fc73d7ed78a1e50403315d22cb42a325290bd`.

### Block 6 — `TRUE_XG_CAPABILITY_V1` — DATA_GAP / FAIL-CLOSED

A supported true-xG experiment requires a genuine paired home/away xG schema. Shots/SOT are never synthesized into xG, and a partial xG field pair also fails closed. Temporal provenance is still required before a detected schema can become experiment-ready.

Decision: current free historical source remains a **DATA_GAP** for true xG. `SHOT_QUALITY_PROXY_V1` stays a proxy and must never be relabeled as true xG.

PR #297:
- head `7e8cfbb3a5c1b9ca4d374ab4b814c83f53e2da1e`;
- Historical Football Signal Lab run `34750911202`, job `103707181172`;
- all seven required validation workflows green; full three-league run and production `.pkl` hash guard green;
- exact-head merge `f9dcf4576164fb92b41fb7ce3dce39d1b1d69c43`.

### Block 7 — `TRAJECTORY_SHOT_INTERACTIONS_V1` — NEGATIVE / CLOSED

This was a bounded interaction test, not an open feature search. The baseline already contained the full `TEAM_STRENGTH_TRAJECTORY_V1` + `SHOT_QUALITY_PROXY_V1` main effects. The candidate added only two fixed, predeclared moderation terms:
- `interaction_elo_delta_x_abs_sot_rate`;
- `interaction_sot_rate_x_abs_performance_residual`.

`REST_CONGESTION_V1` was intentionally excluded because that same-sample hypothesis is already CLOSED / NEGATIVE. Evidence tiers remained EPL + La Liga `PRIMARY`, Serie A `SOURCE_CAVEAT_SENSITIVITY`.

PRIMARY incremental result over football main-effect baseline:
- EPL: accuracy `-0.002256`, Brier `+0.000481`, log loss `+0.000745`; Brier/log-loss wins `3/7`;
- La Liga: accuracy `-0.001504`, Brier `+0.001188`, log loss `+0.001955`; Brier/log-loss wins `0/7`.

PRIMARY incremental result over market + main-effect baseline:
- EPL: accuracy `+0.001504`, Brier `+0.000334`, log loss `+0.000515`; Brier/log-loss wins `3/7`;
- La Liga: accuracy `-0.001504`, Brier `+0.000899`, log loss `+0.001462`; Brier wins `0/7`, log-loss wins `1/7`.

Serie A sensitivity-only rows were also negative on Brier/log loss and do not upgrade the result.

Decision: exact fixed interaction hypothesis is **NEGATIVE / CLOSED**. Do not search more same-sample interaction combinations, signs, thresholds or windows.

PR #298:
- head `87ce4a73b51c8205445168529a55f41b43b3c84a`;
- Historical Signal Interactions run `34751127490`, job `103707737220`;
- artifact `10316265623`, digest `sha256:98da9e518bc6d6ec5fd049f7db215b311521d27cacbf5d54ef7897ef5724d85c`;
- all seven validation contours green, including interaction regressions, real historical run and production `.pkl` hash guard;
- exact-head merge `63623a30441725247ba1092ec783e6b55667f174`.

Signal-discovery conclusion:
- strongest new football-only evidence = `TEAM_STRENGTH_TRAJECTORY_V1`;
- `SHOT_QUALITY_PROXY_V1` is smaller but directionally useful football-only evidence in both PRIMARY leagues;
- neither trajectory nor shot-quality proxy proved robust incremental value beyond the bookmaker market in this historical protocol;
- league-only rest/congestion proxy is negative and closed;
- lineup strength, tactical matchup and true xG are **current-source capability/data gates**, not fabricated negative performance results;
- the fixed trajectory × shot-quality interaction hypothesis is negative and closed; no same-sample interaction mining is allowed;
- no new prospective cohort was created and no frozen membership changed. Candidate V2/model promotion remains closed until the existing evidence gates permit a new, separately preregistered decision.

---

# Product contracts

## Semantics — CLOSED

Binding invariant: **forecast != value != bet != portfolio position**.

- `main_forecast` отвечает «что вероятнее?» и определяется model probability внутри допустимого maturity/reliability tier.
- `value_signal` — отдельный informational raw-EV signal и никогда не переопределяет forecast.
- Current tiers: 1X2 operational; total goals provisional/model-only; handicap research-only; corners total research-only.
- `bet_decision = no_bet` в Decision Framework v1.
- Canonical regression: Liverpool–Fulham — Liverpool ~67.5% остаётся main forecast, Fulham positive raw EV остаётся только value signal.

## Durable product pipeline — LIVE-PROVEN

Path: immutable prediction snapshot -> Supabase -> independent odds join by provider `event_id` -> server contract -> UI/API.

- First durable product publish: `pair-ledger-bootstrap:20260912T044914Z`, 20 EPL snapshots, 1X2-only.
- Stable product identity: provider event ID first; deterministic fixture fallback only when event ID absent.
- Odds and predictions remain independent sources; unsupported goal/BTTS/handicap/corner values не fabricated.
- Current durable snapshot count after the first Operational Automation runtime proof remains `20`; duplicate provider event IDs = `0`.

## Public web — LIVE, BUT LAGS REPOSITORY MAIN

Public alias: `https://football-ai-real-epl-snapshot.vercel.app`.

Last exact public production deployment is older than repository contracts #278–#298. Do not claim later Decision/Lifecycle/Reliability/Readiness/Operational-Automation or signal-research changes are live there until exact-main redeploy.

## Product Lifecycle v1 — CLOSED / LIVE RUNTIME-PROVEN

Append-only facts: `PREDICTION_REGISTERED -> MARKET_OBSERVED -> SETTLED`.

- Old probabilities never rewritten after result.
- Market observation uses already-stored pre-kickoff prices; it is not called closing line unless qualified.
- Settlement comes only from canonical finished-results source.
- P&L/ROI remain null while no actual betting policy/positions exist.
- State immediately before first Operational Automation runtime: `20 registered / 5 market-observed / 0 settled`.
- First real runtime appended `2 MARKET_OBSERVED + 7 SETTLED`; current live state is `20 registered / 7 market-observed / 7 settled = 34 lifecycle rows`.
- Live duplicate lifecycle `event_key` count = `0`; second runtime attempt wrote `0` new lifecycle rows.
- The seven settlements cover every canonical EPL result present for `2026-09-12`; provider aliases were normalized rather than exact-string matched (`Ipswich -> Ipswich Town`, `Hull -> Hull City`, `Tottenham -> Tottenham Hotspur`, `Nott'm Forest -> Nottingham Forest`).

## Reliability / Calibration v1 — CLOSED / ACCUMULATING SAMPLE

Primary claim scope: exact model artifact × league × 1X2.

Evidence-readiness gate: minimum `100` settled predictions exact scope + minimum `4` kickoff calendar months.

`REVIEWABLE != reliable != PASS != promotion`.

Current exact-scope evidence after runtime:
- `7` settled predictions, all EPL and all exact frozen model SHA `1e516fe91420fdc2d6479e9fb92b005c4a0c75c7f0f217493dd6b27fd64d99a5`;
- first/last settled-sample kickoffs are both on `2026-09-12`, so sample/time gates are not met;
- exact model+league slice is therefore `ACCUMULATING_SAMPLE / INCONCLUSIVE`;
- the automation report's aggregate `overall_history` evidence state is `DESCRIPTIVE_ONLY` by design because cross-scope overall history is not an exact model+league reliability claim;
- descriptive-only current sample metrics: accuracy `1/7` (~14.29%), mean multiclass Brier `0.8476987182`, mean log loss `1.3455261760`. These are **not** a reliability verdict and must not drive threshold/model/market promotion on this tiny sample.

## Portfolio / Risk v1 — CLOSED / STRUCTURAL ONLY

Only explicit future `bet_decision.status == bet` creates a structural position. Forecast/value alone never creates exposure. No staking/Kelly/bankroll policy exists in v1. Last live proof had zero actionable positions and `NO_ACTIONABLE_EXPOSURE`.

## Production Readiness v1 — CLOSED / LIVE-DATA-PROVEN

Current matrix:
- EPL / 1X2 = `OPERATIONAL`;
- EPL / Total Goals = `PROVISIONAL`;
- EPL / Handicap = `RESEARCH_ONLY`;
- EPL / Corners Total = `RESEARCH_ONLY`.

New scopes can automatically reach at most `REVIEWABLE`; `OPERATIONAL` requires explicit approval. Readiness never auto-promotes a model/market, changes forecast ranking, creates a bet or opens a research gate.

---

# Product Operational Automation v1 — LIVE RUNTIME-PROVEN / IDEMPOTENCY-PROVEN

Version: `product-operational-automation.v1`.

Purpose: connect already-approved durable product components into a repeatable scheduled cycle without creating a new forecasting, provider or betting system.

Cycle:
1. read already-produced outcome-free EPL AI rows from `epl_ai_market_pair_ledger`;
2. publish a product snapshot only for a provider fixture that has no product prediction yet;
3. reload durable state so lifecycle uses the real persisted prediction ID;
4. append missing lifecycle facts from stored odds and canonical finished results;
5. recompute read-only Reliability / Production Readiness summaries;
6. emit audit report.

Safety contract:
- no paid-provider call;
- no model inference/training/promotion;
- no frozen research target read;
- no bet/stake action;
- existing private Supabase write path only; public web access never becomes a write fallback;
- pair row must be EPL, exact frozen experiment, have provider event ID, be generated strictly pre-kickoff and match the frozen model SHA above.

Forecast revision guard:
- automation publishes only the **first** product forecast per provider fixture;
- newer AI generations for already-published fixtures are held for a future explicit revision/evaluation contract;
- this prevents repeated versions of one match from inflating Lifecycle/Reliability sample.

Operational hardening:
- lifecycle reads are paginated; regression covers `6001` rows and removes the old hidden `5000`-row cap;
- source states: `NO_FUTURE_EVENTS`, `COVERED`, `READY_TO_INGEST_PREDICTIONS`, `WAITING_FOR_PREDICTION_SOURCE`;
- missing model source fails closed; bookmaker probability is never substituted for model probability;
- production workflow triggers are `workflow_dispatch` plus cron `37 */2 * * *`;
- permissions remain `contents: read`; runtime receives only private Supabase credentials and does not require The Odds API key.

PR #286 — implementation:
- exact head `66a42a559f792d4f2d6fd187509c1b521c947f84`;
- all six required CI contours green: Product, Research, Serie A, Bundesliga, Ligue 1, Eredivisie;
- production artifact guard green;
- exact-head merge `680ce8a694f6f49dd83452f0e3c776593c70a5e2` at `2026-09-13T05:33:24Z`.

Pre-runtime live proof:
- future EPL odds events = `13`;
- product-covered events = `13/13`;
- future paired-AI events = `13`;
- invalid pair timing = `0`;
- one model SHA, exact frozen SHA;
- product snapshots total = `20`;
- lifecycle = `20 registered / 5 market-observed / 0 settled`.

Scheduler activation observation:
- because cron is `37 */2 * * *`, the first full natural slot after the `05:33:24Z` implementation merge was `06:37 UTC`, not `05:37 UTC`;
- by approximately `07:39 UTC`, GitHub still showed no `schedule` run for this workflow even though other scheduled workflows in the repository had executed;
- no direct Supabase inserts were used to manufacture runtime proof;
- the connector exposed no safe workflow-dispatch creation action, so a bounded path-scoped `push` bootstrap was used through the normal branch/PR/full-CI/exact-head-merge path;
- this proves the workflow executor, credentials, append-only cycle and idempotency. A natural `event=schedule` occurrence itself has not yet been separately observed and must not be falsely claimed.

PR #288 — bounded runtime bootstrap:
- branch `product-runtime-proof`, exact head `2c75d1470ba0e28bbfa8a88dd565e41d47daa9ce` from then-current main `e2cd7baa3b7572a32cbdc22c38b8839ea4ab7a9d`;
- diff: one workflow file, `+5/-0`, adding only a `main` push trigger scoped to `.github/workflows/product-operational-automation.yml`;
- no permissions, runtime code, secret contract, paid-provider or model-action change;
- all six required CI contours green;
- exact-head merge `182f0fc0a3fbd0e392b08a3c77f8579ae7b61ebd` at `2026-09-13T07:43:41Z`.

First real Actions runtime:
- workflow run ID `34745945144`, run number `1`, event `push`, head `main`, exact SHA `182f0fc0a3fbd0e392b08a3c77f8579ae7b61ebd`, created `2026-09-13T07:43:43Z`;
- first job ID `103693795481`, conclusion `success`;
- checkout proved exact main SHA; `GITHUB_TOKEN` permissions stayed read-only for contents/metadata;
- private Supabase credential contract passed with values masked;
- first cycle report `as_of_utc=2026-09-13T07:44:01.932364+00:00`, `status=HEALTHY_NOOP`, `prediction_source.state=COVERED`;
- applied: `product_prediction_snapshots=0`, `lifecycle_events=9`;
- the 9 append-only facts were exactly `2 MARKET_OBSERVED + 7 SETTLED`;
- pending after application: `0` product snapshots and `0` lifecycle events;
- future source coverage remained `13/13`, with `ready_from_pair_ledger=0`, `revision_candidates_held=0`, `waiting_for_prediction_source=0`;
- safety report: paid-provider/model inference/model training/model promotion/betting/staking/automatic forecast revision/research-target reads all `false`; lifecycle writes append-only `true`;
- first report artifact ID `10314022013`, ZIP digest `sha256:f47be94c330ea3ac315870519cae3603414cf3653af3ccd0578ae2686aa6c02b`.

Runtime idempotency proof:
- the successful job was rerun on the same exact workflow run/head; second job ID `103693963665`, conclusion `success`;
- second cycle `as_of_utc=2026-09-13T07:45:37.010832+00:00`;
- applied on rerun: `product_prediction_snapshots=0`, `lifecycle_events=0`;
- pending remained `0/0`, coverage remained `13/13`, lifecycle remained `34` rows, product predictions remained `20`;
- second report remained `HEALTHY_NOOP / COVERED`, with `7` settled predictions and no paid/model/betting actions;
- second artifact ID `10313827598`, ZIP digest `sha256:6e7f3221612c64cc0d4d041eb6b965e8343b3f9c25ec2076e1bdc944d7694c15`.

Post-runtime live Supabase proof at `2026-09-13T07:47:06.829933Z`:
- product snapshots `20`, distinct event IDs `20`, duplicate product event IDs `0`;
- lifecycle rows `34`: `20 registered / 7 market-observed / 7 settled`;
- duplicate lifecycle event keys `0`;
- latest lifecycle write remains exactly first-cycle time `2026-09-13T07:44:01.932364Z`; rows after that time = `0`, proving rerun made no durable write;
- future EPL odds/product/valid-pair events = `13/13/13`; missing product = `0`; waiting for pair = `0`;
- product-not-pre-kickoff = `0`; market source post-kickoff = `0`; pair model generation not-pre-kickoff = `0`;
- pending market observations = `0`; no matching canonical result remains unsettled.

PR #289 — bootstrap cleanup:
- exact head `d10269aa7d377e2c091043e72f3326ea44eaac2d`;
- diff: same workflow file only, `+0/-5`, removing the temporary push trigger;
- all six required CI contours green, including production-artifact guard;
- fresh-main check remained exact bootstrap merge before cleanup merge;
- exact-head merge `26608134c1cb68a6ce68da5d8c3c304870d88f4c` at `2026-09-13T07:49:08Z`;
- post-merge workflow is restored to `workflow_dispatch` + `37 */2 * * *` schedule only.

---

# Durable PR reference

Product chain: #267–#277 foundation/live pipeline; #278 Decision Framework; #279 Lifecycle; #280 lifecycle security hardening; #281 Reliability; #282 Portfolio/Risk; #283 continuity correction; #284 Production Readiness; #286 Operational Automation v1; #287 pre-runtime continuity; #288 bounded runtime bootstrap; #289 bootstrap cleanup.

Signal discovery chain: #291 `TEAM_STRENGTH_TRAJECTORY_V1`; #292 `REST_CONGESTION_V1`; #293 `SHOT_QUALITY_PROXY_V1`; #294 continuity for blocks 1–3; #295 `LINEUP_STRENGTH_CAPABILITY_V1`; #296 `TACTICAL_MATCHUP_CAPABILITY_V1`; #297 `TRUE_XG_CAPABILITY_V1`; #298 `TRAJECTORY_SHOT_INTERACTIONS_V1`.

All substantive product/runtime and signal-research PRs above passed Product + required Research/league CI; performance/capability signal PRs also passed their Historical Signal Lab/interaction workflow and production hash guard before exact-head merge.

---

# Текущий execution pointer

## Research

- `ALL_LEAGUES_MARKET_ONLY_V1_1`: **collect, don't peek / SAMPLE_CLOSED**.
- `EPL_AI_MARKET_PAIR_V1`: separate frozen experiment; do not infer cohort membership from product bootstrap.
- Any paid refresh = separate manual gate.
- Candidate V2/model promotion stays closed until corresponding evidence gate.
- `TEAM_STRENGTH_TRAJECTORY_V1`: retain as football-only candidate evidence; no production/prospective insertion without a new allowed contract.
- `REST_CONGESTION_V1`: exact league-only proxy **CLOSED / NEGATIVE**; no same-sample retuning.
- `SHOT_QUALITY_PROXY_V1`: football-only candidate evidence, market-incremental negative.
- `LINEUP_STRENGTH_CAPABILITY_V1`: **DATA_GAP / FAIL-CLOSED** until a supported point-in-time lineup/player-strength source exists.
- `TACTICAL_MATCHUP_CAPABILITY_V1`: **DATA_GAP / FAIL-CLOSED** until explicit tactical data with temporal provenance exists.
- `TRUE_XG_CAPABILITY_V1`: **DATA_GAP / FAIL-CLOSED**; shots/SOT remain proxy-only.
- `TRAJECTORY_SHOT_INTERACTIONS_V1`: exact fixed hypothesis **CLOSED / NEGATIVE**; no same-sample interaction retuning/mining.
- Signal Discovery blocks 1–7 requested/completed on 2026-09-13 do not alter any existing frozen sample or gate.

## Product

Current foundation:

`Prediction delivery -> Decision Framework -> Lifecycle -> Reliability -> Portfolio/Risk -> Production Readiness -> Operational Automation`

Operational Automation executor/runtime/idempotency block is now closed. The natural GitHub `schedule` event should still be observed when a later cron occurrence exists, but lack of that observation must not be confused with a failure of the already-proven runtime executor.

Следующая safe последовательность после завершения explicitly requested signal-research diversion:
1. **Exact-main web deployment**: redeploy the public alias from then-current exact `main`, then smoke-check `/`, `/health`, `/api/product/markets`, `/api/product/reliability`, `/api/product/portfolio`, `/api/product/readiness` and verify the deployment commit SHA equals GitHub main.
2. **Second markets through readiness gates**: goal total first. Close its live model probability, bookmaker-price, settlement, lifecycle and empirical-reliability contracts before any production activation.
3. Handicap/corners stay research-only until their own probability/price/settlement/evidence contracts exist; CORNERS10 as a 1X2 signal is not a corner-total production model.

Betting/staking policy remains a separate future contract until enough empirical evidence exists.

---

# 2026-09-13 audit trail

Today Operational Automation v1 was designed, implemented, regression-tested, merged, live-runtime-proven, idempotency-proven and returned to its intended schedule/manual trigger surface.

Key facts and decisions:
- reused existing durable sources instead of running ad-hoc inference;
- kept missing prediction source as an explicit fail-closed state;
- introduced first-prediction-only automation and held revisions to protect sample integrity;
- fixed lifecycle pagination before the current odds table could exceed the old hidden cap;
- added scheduled append-only orchestration with no paid-provider dependency;
- PR #286 passed all six CI contours and exact-head merged as `680ce8a694f6f49dd83452f0e3c776593c70a5e2`;
- PR #287 recorded the honest pre-runtime boundary and merged as `e2cd7baa3b7572a32cbdc22c38b8839ea4ab7a9d`;
- corrected the cron interpretation: after the `05:33:24Z` merge, the first full `37 */2` slot was `06:37Z`; by ~`07:39Z` no schedule-created run existed;
- did not bypass the missing schedule event with direct SQL writes;
- PR #288 added only a bounded path-scoped main push trigger, passed all six CI contours, exact-head merged as `182f0fc0a3fbd0e392b08a3c77f8579ae7b61ebd`, and created the first real runtime run `34745945144`;
- first runtime passed credential check and append-only cycle and wrote exactly `2 MARKET_OBSERVED + 7 SETTLED`, no product snapshots;
- all seven settlements were reconciled to canonical `2026-09-12` EPL results; four required existing provider alias normalization rather than exact-string matching;
- reliability moved from no settled data to a real but tiny exact-scope sample of `7`, state `ACCUMULATING_SAMPLE / INCONCLUSIVE`; aggregate overall history remains `DESCRIPTIVE_ONLY` by contract;
- same-head job rerun applied `0/0`, proving runtime idempotency;
- post-run live audit found no product duplicates, no lifecycle event-key duplicates, no post-kickoff provenance violations, no pending eligible lifecycle facts, and future coverage `13/13`;
- PR #289 removed the temporary trigger, passed all six CI contours, exact-head merged as `26608134c1cb68a6ce68da5d8c3c304870d88f4c`, restoring production workflow to `workflow_dispatch + schedule`;
- no Odds API credits, production model artifacts, training, inference, promotion, bets or stakes were used in this runtime-proof closure.

Later on 2026-09-13 the user explicitly authorized the Signal Discovery pass, completed through blocks 1–7. This bounded historical pass:
- reused the existing leakage-safe three-league Historical Football Signal Lab and a thin interaction extension over the same point-in-time inputs;
- tested trajectory, league-only rest/congestion and shot-quality proxy with fixed predeclared contracts;
- closed Lineup Strength, Tactical Matchup and True xG as explicit current-source `DATA_GAP / FAIL-CLOSED` capability gates rather than fabricating unsupported features;
- tested only two fixed trajectory × shot-quality interaction terms on top of both main-effect families and closed that exact interaction hypothesis as negative; no same-sample combination search followed;
- closed PRs #291/#292/#293/#295/#296/#297/#298 through branch -> regression tests -> full required CI -> fresh-main -> exact-head merge;
- found trajectory strongly useful as football-only state but not robustly incremental over market;
- found exact league-only rest/congestion proxy negative and closed it without same-data tuning;
- found shots/SOT proxy modestly useful football-only in both PRIMARY leagues but negative over market; confirmed no supported true-xG pair in the current source and kept true xG as a separate data-source gate;
- read no frozen prospective outcomes, made no Supabase writes, used no paid provider, and changed no production model artifact/training/promotion state.

# Current checkpoint

- Latest repository main after substantive Signal Discovery code: `63623a30441725247ba1092ec783e6b55667f174`; the following continuity update is documentation-only.
- Latest product/runtime behavior remains the previously proven Operational Automation contract; signal research did not alter product runtime or model artifacts.
- Durable product snapshots: `20` total; duplicate event IDs `0`; future EPL coverage `13/13` at last live product proof.
- Lifecycle: `20 registered / 7 market-observed / 7 settled = 34`; duplicate event keys `0`; pending eligible lifecycle facts `0` at last live product proof.
- Reliability exact frozen EPL scope: `7` settled, `ACCUMULATING_SAMPLE / INCONCLUSIVE`; do not overinterpret descriptive metrics.
- Readiness: EPL 1X2 operational; goals provisional; handicap/corners research-only.
- Operational Automation executor/runtime/idempotency is live-proven. Natural `event=schedule` occurrence is still an external scheduler observation, not an unproven runtime-code path.
- Production workflow is restored to `workflow_dispatch + cron 37 */2 * * *`, `contents: read`, no Odds API key.
- Signal Discovery status: trajectory = promising football-only / market-incremental unproven; rest proxy = negative/closed; shot-quality proxy = promising football-only / market-incremental negative; lineup/tactical/true-xG = current-source data gates; fixed trajectory-shot interactions = negative/closed.
- Public Vercel runtime still lags repository main; **exact-main redeploy resumes as the next product block**.
- Research V1.1 outcome gate remains closed; no-peek is binding.