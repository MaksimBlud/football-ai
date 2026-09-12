# Football AI — Project Continuity

Этот файл — постоянная память проекта между чатами. Фактический source of truth всегда свежий GitHub `main` + live Supabase. Git history хранит полный исторический detail; здесь держим только текущие контракты, доказанные решения, активные gates и официальный execution pointer.

## Как пользоваться

Перед новой рабочей сессией:
1. Прочитать этот файл.
2. Коротко сверить свежий `main` и live Supabase.
3. Не повторять полный аудит без конкретной причины.
4. Продолжать с раздела **Текущий execution pointer**.
5. После существенного решения, PR, merge или live-proof обновить этот файл отдельным continuity-only change/PR.

`FOOTBALL_AI_MASTER_BACKUP_2026-08-19.md` — исторический backup/context, но не замена этому файлу. При конфликте приоритет: **fresh GitHub main + live Supabase -> PROJECT_CONTINUITY.md -> historical backup/reports**.

---

# Постоянные правила

- Repo: `MaksimBlud/football-ai`, default branch `main`.
- Source of truth: fresh GitHub `main` + live Supabase.
- Production `.pkl` нельзя менять как побочный эффект research/training.
- Research/training != production promotion; automatic promotion запрещён.
- Не делать mass-clean/reset/mass-format и не перетирать параллельные изменения.
- Существенные изменения: fresh main -> branch -> tests -> PR -> полный CI -> fresh-main compare -> exact-head merge -> post-merge/live proof -> continuity.
- Frozen/preregistered contracts нельзя ослаблять задним числом.
- Prospective outcomes нельзя читать до разрешённого frozen gate.
- Максимально использовать zero-cost/read-only proof; Odds API credits не тратить при наличии бесплатной проверки.
- Paid-provider workflows остаются manual-only и требуют отдельного explicit user permission.
- Реальные баги закрывать regression-тестами.
- Fail-closed red нельзя искусственно превращать в green.
- Point-in-time history нельзя восстанавливать ретроспективно, если durable source её не сохранил.
- Training is not promotion; research artifacts не становятся production автоматически.
- Forecast, value, betting decision и portfolio exposure — разные сущности и не должны подменять друг друга.

---

# MASTER ROADMAP — текущая структура

Football AI развивается по двум параллельным линиям:

1. **Research / evidence line** — prospective collection, frozen experiments, model/market evidence, future Candidate V2 validation.
2. **Product line** — durable prediction delivery, decision semantics, lifecycle, reliability, portfolio/risk, production readiness, затем operational automation и exact-main deployment.

Research gates имеют приоритет над желанием быстрее увидеть performance. Product layer может развиваться поверх уже существующих immutable forecasts, но не имеет права читать forbidden prospective outcomes или автоматически менять research/model status.

---

# RESEARCH STATE — действующие контракты

## R0. Paid market freshness / provider collection — MANUAL_PAID_GATE

- Paid odds refresh не запускается без отдельного explicit user permission.
- Existing budget/safety guards и hard reserve обязательны.
- Read-only health/status/readiness не является разрешением тратить provider credits.
- Последний eight-league readiness pass был явно разрешён и стоил 8 Odds API credits (`193 -> 185`).
- Production `.pkl` при provider collection не меняются.

## R1. `ALL_LEAGUES_MARKET_ONLY_V1_1` — FROZEN / SAMPLE_CLOSED / COLLECT, DON'T PEEK

Frozen facts:
- predecessor V1 T0: `2026-09-12T01:51:19Z`;
- V1.1 freeze: `2026-09-12T02:04:34Z`;
- first seed kickoff: `2026-09-12T12:00:00Z`;
- seed: exact `127` immutable `prediction_key` из `research/ALL_LEAGUES_MARKET_ONLY_V1_1_MANIFEST.json`;
- counts: BUNDESLIGA `17`, EPL `20`, EREDIVISIE `18`, LA_LIGA `19`, LIGUE_1 `17`, PRIMEIRA_LIGA `9`, SERIE_A `19`, TURKEY_SUPER_LIG `8`;
- шесть уже начавшихся 2026-09-11 fixtures исключены навсегда из V1.1.

Frozen evaluation gate:
- минимум `100` unique eligible events в каждой из 8 лиг;
- минимум `4` distinct UTC kickoff calendar months в каждой лиге;
- все 8 лиг должны пройти gate одновременно;
- primary sample = deterministic prefix `kickoff_utc ASC, event_id ASC, prediction_key ASC`;
- outcomes закрыты минимум до `24h` после latest primary-prefix kickoff;
- более строгие league-specific gates всегда имеют приоритет;
- interim outcome/performance peeking, threshold search, subgroup selection и performance-based optional stopping запрещены.

Frozen metrics после открытия gate:
- primary: multiclass log loss, multiclass Brier;
- secondary: 1X2 argmax accuracy;
- report: per league + pooled micro + unweighted league macro + sample size + outcome-class counts.

Operational monitor:
- `all_leagues_market_only_v1_1_status.py`;
- `.github/workflows/all-leagues-v1-1-sample-health.yml`;
- daily read-only `05:37 UTC` + relevant main pushes/manual;
- no Odds API credential, no write permission;
- missing seed/conflicting duplicate/gate-invalid metadata fail closed.

Last frozen baseline recorded before current product work:
- `127/127` seed keys matched;
- `0` post-freeze selected events at that proof;
- all leagues = one kickoff month;
- `sample_ready=false` for all;
- `SAMPLE_CLOSED`, `outcome_read_allowed=false`.

Не считать повторный ad-hoc read-only check прогрессом, если sample не изменился.

## R2. `EPL_AI_MARKET_PAIR_V1` — SEPARATE FROZEN EPL AI-vs-market EXPERIMENT

- Не смешивать с eight-league MARKET_ONLY cohort.
- Не backfill MARKET_ONLY rows как paired-AI evidence.
- EPL production model нельзя переносить на другие лиги ради ускорения sample.
- Prior authoritative frozen health before product bootstrap: `12/100 / TIME-FROZEN_GATE`.
- Product bootstrap 2026-09-12 использовал 20 future EPL rows из `epl_ai_market_pair_ledger`, но это **не переопределяет research cohort membership**.
- Outcomes/primary evaluation не открывать до existing sample/time/embargo rules.

## R3. Historical corners — CLOSED / STOP RULE

- `SEASON_INVARIANT_CORNERS_V1`: portable strong football-only signal.
- `CORNER_TOTAL_SIGNAL_V1`: not portable total signal.
- `CORNER_TOTAL_CALIBRATED_V2`: small portable expected-count signal; не proven Over/Under discriminator.
- `CORNER_PRESSURE_SIGNAL_V3`: not portable pressure discriminator.
- `CORNER_COMBINED_DISCRIMINATOR_V4`: not portable combined discriminator.
- Не делать новый same-data search windows/weights/thresholds/combinations без independent evidence.
- `CORNERS10` для 1X2 не является доказательством corner-total prediction quality.

## R4. SportsGameOdds corner capability — EXECUTION_SURFACE_GATE

- The Odds API corner probe: `CAPABILITY_MISS`, 1 provider request, 0 credits.
- SportsGameOdds bounded manual-only probe infrastructure существует.
- Текущий connected GitHub surface не даёт безопасный `workflow_dispatch` action.
- Не обходить gate изменением trigger.
- Fallback при реальном miss/access failure: SportsGameOdds -> Sportmonks -> Betfair Exchange.

---

# PRODUCT STATE — 2026-09-12

## P0. Product semantics — CLOSED / CONTRACTED

Ключевой инвариант:

**forecast != value != bet != portfolio position**

`product-decision.v1`:
- `main_forecast` отвечает «что вероятнее?»;
- `value_signal` — независимый informational price/raw-EV signal;
- value никогда не переопределяет forecast;
- cross-market ranking: сначала `decision_tier`/market maturity, затем probability;
- provisional market с большей raw probability не вытесняет operational market автоматически;
- alternatives идут из других forecast-eligible markets;
- `bet_decision = no_bet` в Framework v1.

Canonical regression: Liverpool–Fulham — Liverpool ~67.5% остаётся main forecast, Fulham ~16.8% с positive raw EV остаётся только value.

Current decision tiers:
- `1x2`: tier 2 / operational;
- `total_goals`: tier 1 / provisional/model-only;
- `handicap`: tier 0 / research-only;
- `corners_total`: tier 0 / research-only.

PR #275 закрепил forecast/value separation.
PR #278 merge `1d0dfd568274fd06f436bf39ff4f8062edfe93ee` добавил Product Decision Framework v1.

## P1. Durable live product pipeline — CLOSED / LIVE-PROVEN

Path:

immutable prediction snapshot -> Supabase -> independent odds join by `event_id` -> server contract -> UI/API.

`product_prediction_snapshots`:
- append-only;
- RLS enabled;
- public web uses publishable key, never service-role secret;
- raw provenance не открыт public SELECT;
- service role сохраняет append-only write path.

First real durable publish:
- run `pair-ledger-bootstrap:20260912T044914Z`;
- inserted `20/20` EPL snapshots;
- source = existing durable paired-AI ledger, не новый inference;
- artifact SHA `1e516fe91420fdc2d6479e9fb92b005c4a0c75c7f0f217493dd6b27fd64d99a5`;
- all 20 event IDs had independent stored 1X2 odds;
- bootstrap intentionally 1X2-only; unsupported markets не fabricated.

Stable match identity:
- primary `event_<provider event_id>`;
- fallback deterministic hash of league + model teams + kickoff;
- detail endpoint uses stable ID, not list index;
- legacy numeric detail ID returns 404.

PR #276 added stable ID/public read/bootstrap path.
PR #277 merge `17abfb65dd75324809e7a93f35c3647bb53900da` added clean-deploy public Supabase config.

## P2. Public product web — LIVE, BUT DEPLOYMENT LAGS MAIN

Public alias:
`https://football-ai-real-epl-snapshot.vercel.app`

Last exact production deployment remains from product main `17abfb65dd75324809e7a93f35c3647bb53900da`, deployment `dpl_5bWN15LSoByRPNURBotsk3TN3vnH`.

Repository contracts #278–#284 are ahead of that production runtime. Therefore:
- do not claim `/portfolio-risk-view` or `/production-readiness-view` are already live on the main alias;
- do not claim later Decision/Lifecycle/Readiness fields are deployed there until exact-main redeploy;
- isolated proof deployments are not substitutes for production deployment.

Fresh public feed proof `2026-09-12 16:03:36 UTC`:
- `prediction_snapshot_count = 15` future EPL matches;
- `priced_event_count = 15`;
- all current 15 have stable product IDs;
- all current 15 have full 1X2 model probabilities + stored 1X2 bookmaker prices;
- goal-total model probabilities are currently absent from bootstrap rows;
- handicap/corners selections remain absent.

## P3. Product Prediction Lifecycle — CLOSED / LIVE INITIALIZED

Version: `product-lifecycle.v1`.

Append-only facts:
`PREDICTION_REGISTERED -> MARKET_OBSERVED -> SETTLED`

Rules:
- old probabilities never rewritten after result;
- source prediction timestamp != lifecycle recorded timestamp;
- legacy bootstrap marked honestly;
- current Decision Framework not retroactively attached to old snapshot;
- stored pre-kickoff market observation is not called closing line without qualification;
- CLV remains null until closing qualification exists;
- P&L/ROI remain null while no betting policy/actual bets exist.

Last direct live proof:
- `PREDICTION_REGISTERED = 20`;
- `MARKET_OBSERVED = 5`;
- `SETTLED = 0`;
- no synthetic settlements.

Lifecycle table:
- RLS enabled;
- final `service_role` table grants exactly `SELECT + INSERT`;
- anon/authenticated no lifecycle access.

PR #279 merge `dfed5784215717c93c60561dbbb58f03009badea`.
PR #280 fixed inherited excess service-role privileges before bootstrap continued.

## P4. Reliability / Calibration Layer — CLOSED / WAITING FOR SAMPLE

Version: `product-reliability.v1`.

Primary claim scope:
`exact model_1x2_sha256 × league × 1X2`

Prerecorded evidence-readiness gate:
- minimum `100` settled predictions exact scope;
- minimum `4` calendar months first-to-last kickoff.

States: `NO_SETTLED_DATA`, `ACCUMULATING_SAMPLE`, `ACCUMULATING_TIME`, `REVIEWABLE`; mixed scopes = `DESCRIPTIVE_ONLY`.

Binding meaning:
**REVIEWABLE != reliable != PASS != promotion**

v1 deliberately defines no post-outcome Brier/ECE/log-loss PASS threshold. Even reviewable slice stays `INCONCLUSIVE` until a later preregistered review.

Metrics once settlements exist:
- accuracy;
- multiclass Brier/log loss;
- Brier skill vs uniform 1X2;
- log-loss improvement vs uniform;
- calibration buckets + Wilson 95%;
- top-pick ECE.

Reliability re-computes scoring from frozen probabilities + actual outcome and fail-closes on mismatch/duplicate settlement.

Current product state: `SETTLED = 0` -> `NO_SETTLED_DATA / INCONCLUSIVE`.

PR #281 merge `4640a412c438f1ec5c23dc49b0fe7627b32a0dea`.

## P5. Portfolio / Risk Layer — CLOSED / STRUCTURAL ONLY

Version: `product-portfolio-risk.v1`.

Risk exists only from explicit future `bet_decision.status == "bet"`.

Rules:
- forecast != position;
- value/raw EV != position;
- one fixture = max one actionable structural risk slot until covariance is validated;
- exact duplicate actionable position -> block;
- conflicting selections same fixture/market -> block;
- multiple actionable positions same fixture -> block;
- correlated probabilities/EV cannot be summed;
- team/league concentration descriptive only.

No staking policy in v1: bankroll/stake/Kelly/caps/monetary exposure remain undefined.

Live proof on real feed:
- matches `15`;
- forecasts `15`;
- value signals `14`;
- all `bet_decision=no_bet`;
- actionable positions `0`;
- `NO_ACTIONABLE_EXPOSURE`;
- `total_stake=null`.

Proof project only: `football-ai-portfolio-risk-proof`, deployment `dpl_G1LT3MWkBPcZfeVXFaR9uHhqvhaj`; main product alias intentionally not switched.

PR #282 merge `b057466362ec2b99f58cd392d7e289bdefaf82d8`.

## P6. Product Production-Readiness Framework — CLOSED / MERGED / LIVE-DATA-PROVEN

Version: `product-production-readiness.v1`.

Purpose: one governance answer per concrete `league × market` scope — is it research-only, provisional, reviewable, operational, or blocked, and which gate is still open?

Status vocabulary:
- `RESEARCH_ONLY` — no approved production probability/price/settlement contract; good-looking results cannot bypass it;
- `PROVISIONAL` — product/model contract exists but objective production gates remain open;
- `REVIEWABLE` — all objective gates for a new scope are satisfied, but explicit approval is still required;
- `OPERATIONAL` — scope is explicitly recorded as approved operational and current critical technical/live gates are healthy;
- `BLOCKED` — an approved operational scope lost a critical required technical/live function.

Governance invariants:
- new scopes can automatically reach at most `REVIEWABLE`;
- `REVIEWABLE` never auto-promotes to `OPERATIONAL`;
- `OPERATIONAL` requires explicit approval/registry;
- readiness never automatically changes `MARKET_READINESS`, `decision_tier`, forecast ranking, model promotion, market promotion, bet recommendation or stake;
- Reliability evidence can be consumed only as already-approved summary; this layer itself does not read research outcomes or open frozen gates.

Objective gates, as applicable:
- production probability contract;
- current live probability availability + coverage ratio;
- complete stable `product_match_id` coverage;
- bookmaker price contract;
- current live bookmaker price availability + coverage ratio;
- deterministic settlement contract;
- immutable lifecycle contract;
- empirical reliability reviewability for any new scope.

Coverage semantics:
- zero availability of a required live function is a blocker;
- partial coverage is reported via `coverage_warnings`;
- v1 deliberately does not invent an 80%/90% market pass threshold without evidence;
- stable identity remains a strict complete structural gate.

Existing baseline exception:
- only `EPL × 1X2` is registered as pre-existing approved operational scope;
- this preserves the already-live product contract while Product Reliability sample accumulates;
- it is **not** a reliability PASS, not model promotion, not approval for another league/model artifact, and not betting readiness;
- if required 1X2 live functionality disappears system-wide or stable identity regresses, approved EPL/1X2 fails closed to `BLOCKED`.

Current v1 market policy:
- 1X2 has probability + bookmaker-price + settlement + lifecycle contracts; new league/model scopes additionally require reviewable empirical reliability and explicit approval;
- goal total has probability contract but does not yet have production bookmaker-price, product settlement or lifecycle contracts -> `PROVISIONAL`;
- handicap -> `RESEARCH_ONLY` until model/price/Asian settlement contracts exist;
- corners total -> `RESEARCH_ONLY`; CORNERS10 is not a corner-total production model.

API/repository:
- `product-market-view.v1` now carries `production_readiness_version` and `production_readiness`;
- `web_app.py` contains read-only `GET /production-readiness-view`;
- endpoint is in GitHub main but is **not yet claimed live on the lagging public production alias**.

PR/CI/merge:
- PR #284 exact head `c14f2b8a68f522f7f8cb7117aeef10279192121a`;
- all 6 required CI contours green: Product, Research, Serie A, Bundesliga, Ligue 1, Eredivisie;
- production `.pkl` guard green;
- fresh-main before merge remained `b0b52cd601ffc0d91c17c0b7d3c9d8ee9847962e`, branch behind `0`;
- exact-head merge `815904e6bada808f76edfc5a33850b4af1d2e2b2`.

Outcome-blind live-data proof against the real public product feed at `2026-09-12 16:03:36 UTC`:
- EPL future fixtures = `15`;
- priced 1X2 events = `15`;
- stable IDs = `15/15`;
- complete 1X2 probability + price availability exists across the current window;
- goal-total bootstrap probabilities/prices absent;
- no research outcome/performance source was read.

Resulting current readiness matrix:
- `EPL / 1X2 = OPERATIONAL`;
- `EPL / Total Goals = PROVISIONAL`;
- `EPL / Handicap = RESEARCH_ONLY`;
- `EPL / Corners Total = RESEARCH_ONLY`;
- counts: `OPERATIONAL 1 / PROVISIONAL 1 / RESEARCH_ONLY 2 / REVIEWABLE 0 / BLOCKED 0`.

---

# Product PR chain — durable reference

- #267 product market dashboard
- #268 match card alignment
- #269 unified market contract
- #270 product API + Vercel entrypoint
- #271 UI server-contract consumption
- #272 durable prediction snapshots
- #273 Data API grant hardening
- #274 Vercel preview readiness
- #275 forecast/value separation
- #276 stable product identity + live Supabase read + bootstrap path
- #277 public clean-deploy Supabase config
- #278 Product Decision Framework v1
- #279 Product Lifecycle v1
- #280 lifecycle grant hardening after live proof
- #281 Reliability / Calibration v1
- #282 Portfolio / Risk v1
- #283 continuity consolidation/correction
- #284 Product Production-Readiness Framework v1

All substantive product PRs passed required Product + Research/league CI before exact-head merge.

---

# Supabase product security boundary

- Public web reads with publishable key, never service-role secret.
- Public RLS exposes only product-required future-window columns.
- Public users have no product write permission.
- Product prediction snapshots are append-only.
- Lifecycle is service-role `SELECT + INSERT` only; no update/delete/truncate/trigger/reference privileges.
- Odds and predictions remain separate sources joined by provider `event_id`.
- Synthetic unsupported markets/results are forbidden.

Separate historical security backlog remains on older tables (`teams`, `predictions`, `match_statistics`, `league_prediction_ledger`, `epl_ai_market_pair_ledger`, etc.). Do not mix broad RLS migration into unrelated work; audit access flows first.

---

# Текущий execution pointer

## Research pointer

- `ALL_LEAGUES_MARKET_ONLY_V1_1`: **collect, don't peek / SAMPLE_CLOSED**.
- До frozen gate разрешены только outcome-blind health/identity/completeness checks и future-only capture по frozen rules.
- `EPL_AI_MARKET_PAIR_V1` остаётся separate frozen experiment; не backfill и не выводить membership из product bootstrap.
- Любой paid provider refresh = отдельный `MANUAL_PAID_GATE`.
- Candidate V2/model promotion не открывать до соответствующего evidence gate.

## Product pointer

Current product foundation:

`Prediction delivery -> Decision Framework -> Lifecycle -> Reliability evidence -> Portfolio/Risk -> Production Readiness`

Все эти слои contracted/merged. Следующая safe работа, не требующая research outcomes:

1. **Operational Automation v1** — автоматизировать future fixture/prediction publish, lifecycle advance, canonical result settlement, reliability/readiness refresh и monitoring, сохраняя paid/manual и no-peek gates.
2. **Exact-main web deployment** — основной public alias отстаёт от repository contracts #278–#284; при следующем deployment публиковать exact current main, а не proof runtime.
3. Затем подключать second markets по readiness gates: goal total first, потом handicap/corners только после их собственных model/price/settlement/evidence contracts.

Betting/staking policy не является следующим автоматическим шагом и остаётся отдельным future contract до достаточного empirical evidence.

## UI pointer

UI можно шлифовать параллельно, но он не должен менять server-owned semantics:
- main forecast = forecast, not value;
- maturity/tier before cross-market probability ranking;
- value separate;
- readiness states and blockers explicit;
- research-only/provisional/no-bet/no-data — нормальные product states, а не ошибки UI.

---

# Closed historical/operational reference

Не переоткрывать без новой причины:
- historical corners V1–V4 — closed under stop rule;
- canonical public results/settlement fallback — live-proven;
- market revision safety/canonical event identity — closed/live-proven;
- eight-league MARKET_ONLY infrastructure readiness — 8-of-8 live-proven;
- V1.1 freeze/evaluation gate/sample-health — frozen/operational, не менять по outcomes;
- product Decision/Lifecycle/Reliability/Portfolio/Production-Readiness v1 — merged contracts;
- production model promotion — всегда explicit/manual.

---

# 2026-09-12 key decisions / audit trail

Research:
- eight-league MARKET_ONLY readiness closed 8-of-8;
- V1 T0 + V1.1 127-event successor seed frozen;
- evaluation gate frozen before first seed kickoff;
- daily outcome-blind sample-health operationalized;
- outcome read remains forbidden.

Product:
- durable product snapshot pipeline + public Supabase read live-proven;
- forecast/value semantic bug fixed;
- stable match identity enabled;
- first 20 real EPL durable snapshots published from existing paired-AI ledger;
- Decision Framework v1 merged;
- Lifecycle v1 merged and live initialized;
- inherited lifecycle service-role privilege defect caught and fixed before continuing bootstrap;
- Reliability/Calibration v1 gates preregistered before first product settlement;
- Portfolio/Risk v1 proves current value signals do not create positions;
- Production-Readiness v1 now gives explicit league/market governance statuses and never auto-promotes new scopes.

Continuity:
- earlier product work was mistakenly written only to MASTER BACKUP; PR #283 corrected that and restored `PROJECT_CONTINUITY.md` as canonical durable memory;
- future substantial work is incomplete until this file is updated via continuity-only change/PR.

Repository hygiene:
- accidental temporary root `noop` was created in `3e92ab1ec6e2c350f4af8d556698d82ed6374c1e` and immediately removed in `f0cd0193fea4c64e0d77b080a0c8d0c05e096ace`; net tree returned to the intended product state.

---

# Current source-of-truth checkpoint before this continuity PR

- Product code main after PR #284: `815904e6bada808f76edfc5a33850b4af1d2e2b2`.
- Product snapshots: 20 durable EPL rows from first bootstrap; current future public window = 15.
- Current public 1X2 priced events = 15/15.
- Lifecycle last direct proof: 20 registered / 5 market-observed / 0 settled.
- Reliability: `NO_SETTLED_DATA / INCONCLUSIVE`.
- Portfolio: 15 future matches / 14 value signals / 0 actionable positions / `NO_ACTIONABLE_EXPOSURE`.
- Production Readiness live-data matrix: EPL 1X2 operational; goals provisional; handicap/corners research-only.
- Public Vercel production runtime still lags GitHub main; exact-main deployment remains a separate next operational step.
- Research V1.1 outcome gate remains closed; no-peek is still binding.
