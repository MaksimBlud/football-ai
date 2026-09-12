# Football AI — Project Continuity

Этот файл — постоянная память проекта между чатами. Фактический source of truth всегда свежий GitHub `main` + live Supabase. Git history сохраняет полный исторический detail; здесь держим **текущие контракты, доказанные решения, активные gates и официальный execution pointer**.

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
- Source of truth: свежий GitHub `main` + live Supabase.
- Production `.pkl` нельзя менять как побочный эффект research/training.
- Research/training != production promotion; automatic promotion запрещён.
- Не делать mass-clean/reset/mass-format и не перетирать параллельные изменения.
- Существенные изменения: fresh main -> branch -> tests -> PR -> полный CI -> fresh-main compare -> exact-head merge -> post-merge/live proof -> continuity.
- Frozen/preregistered contracts не ослаблять задним числом.
- Prospective outcomes нельзя читать до разрешённого frozen gate.
- Максимально использовать free/read-only proof; Odds API credits не тратить при наличии zero-cost проверки.
- Paid-provider workflows остаются manual-only и требуют отдельного explicit permission.
- Реальные баги закрывать regression-тестами.
- Fail-closed red нельзя превращать искусственно в green.
- Point-in-time history нельзя восстанавливать ретроспективно, если её нет в durable source.
- Training is not promotion; research artifacts не становятся production автоматически.
- Forecast, value, betting decision и portfolio exposure — разные сущности и не должны подменять друг друга.

---

# MASTER ROADMAP — текущая структура проекта

Football AI развивается по двум параллельным линиям, которые нельзя смешивать:

1. **Research / evidence line** — prospective collection, frozen experiments, model/market evidence, future candidate validation.
2. **Product line** — durable prediction delivery, decision semantics, lifecycle, reliability evidence, portfolio/risk and later product readiness/operations.

Research gates имеют приоритет над желанием быстрее получить performance-результаты. Product layer может развиваться безопасно поверх уже существующих immutable forecasts, но не имеет права читать forbidden prospective outcomes или автоматически менять research/model status.

---

# RESEARCH STATE — действующие контракты

## R0. Paid market freshness / provider collection — MANUAL_PAID_GATE

- Paid odds refresh не запускается без отдельного explicit user permission.
- Existing budget/safety guards и hard reserve обязательны.
- Read-only health/status/readiness не является разрешением тратить provider credits.
- Последний большой eight-league readiness pass был явно разрешён пользователем и стоил 8 Odds API credits (`193 -> 185`).
- Production `.pkl` при provider collection не меняются.

## R1. `ALL_LEAGUES_MARKET_ONLY_V1_1` — FROZEN / SAMPLE_CLOSED / COLLECT, DON'T PEEK

Это основной общий eight-league MARKET_ONLY prospective cohort.

Frozen facts:
- predecessor V1 T0: `2026-09-12T01:51:19Z`;
- V1.1 freeze: `2026-09-12T02:04:34Z`;
- first seed kickoff: `2026-09-12T12:00:00Z`;
- exact seed: `127` immutable `prediction_key` из `research/ALL_LEAGUES_MARKET_ONLY_V1_1_MANIFEST.json`;
- seed leagues/counts: BUNDESLIGA `17`, EPL `20`, EREDIVISIE `18`, LA_LIGA `19`, LIGUE_1 `17`, PRIMEIRA_LIGA `9`, SERIE_A `19`, TURKEY_SUPER_LIG `8`;
- six already-started 2026-09-11 fixtures не входят и никогда не backfill в V1.1.

Frozen evaluation gate:
- минимум `100` unique eligible events **в каждой из 8 лиг**;
- минимум `4` distinct UTC kickoff calendar months **в каждой лиге**;
- все 8 лиг должны пройти sample gate одновременно;
- primary sample = deterministic prefix `kickoff_utc ASC, event_id ASC, prediction_key ASC`;
- outcomes остаются закрыты минимум `24h` после latest kickoff среди frozen primary prefixes;
- более строгие league-specific gates всегда имеют приоритет;
- outcome/performance peeking, threshold search, subgroup selection, interim primary evaluation и performance-based optional stopping запрещены.

Frozen metrics после открытия gate:
- primary: multiclass log loss, multiclass Brier;
- secondary: 1X2 argmax accuracy;
- reporting: per league + pooled micro + unweighted league macro + sample size + outcome class counts.

Operational monitor:
- `all_leagues_market_only_v1_1_status.py`;
- `.github/workflows/all-leagues-v1-1-sample-health.yml`;
- daily read-only run at `05:37 UTC` + relevant main pushes/manual;
- no Odds API credential, no write permission;
- missing seed/conflicting duplicate/gate-invalid metadata fail closed.

Last frozen baseline proof recorded before product build:
- `127/127` seed keys matched;
- `0` post-freeze selected events at that proof;
- all eight leagues = `1` kickoff month;
- `sample_ready=false` for all;
- `SAMPLE_CLOSED`, `outcome_read_allowed=false`.

Не считать повторный ad-hoc read-only check прогрессом, если sample не изменился.

## R2. `EPL_AI_MARKET_PAIR_V1` — SEPARATE FROZEN EPL AI-vs-market EXPERIMENT

- Не смешивать с eight-league MARKET_ONLY cohort.
- Не backfill multi-league MARKET_ONLY rows как AI evidence.
- EPL production model нельзя переносить на другие лиги только ради ускорения sample.
- Prior authoritative frozen health before today's product bootstrap: `12/100 / TIME-FROZEN_GATE`.
- Product bootstrap 2026-09-12 использовал 20 future EPL rows из `epl_ai_market_pair_ledger`, но **это не разрешает автоматически переопределить frozen cohort count**; authoritative research monitor/contract остаётся отдельным source of truth для membership.
- Outcomes/primary evaluation не открывать до existing frozen sample/time/embargo rules.

## R3. Historical corners — CLOSED / STOP RULE

- `SEASON_INVARIANT_CORNERS_V1`: portable strong football-only signal.
- `CORNER_TOTAL_SIGNAL_V1`: not portable total signal.
- `CORNER_TOTAL_CALIBRATED_V2`: small portable expected-count signal; не равно proven Over/Under discriminator.
- `CORNER_PRESSURE_SIGNAL_V3`: not portable pressure discriminator.
- `CORNER_COMBINED_DISCRIMINATOR_V4`: not portable combined discriminator.
- Не делать новый search windows/weights/thresholds/combinations на тех же historical seasons без нового independent evidence.
- `CORNERS10` для 1X2 не является доказательством качества corner-total prediction.

## R4. SportsGameOdds corner capability — EXECUTION_SURFACE_GATE

- The Odds API corner capability probe: `CAPABILITY_MISS`, 1 provider request, 0 credits charged.
- SportsGameOdds manual-only bounded probe infrastructure существует.
- Existing connected GitHub surface до сих пор не предоставляет безопасный `workflow_dispatch` action.
- Не обходить gate изменением workflow trigger.
- Fallback order при реальном miss/access failure: SportsGameOdds -> Sportmonks -> Betfair Exchange.

---

# PRODUCT STATE — 2026-09-12

## P0. Product semantics — CLOSED / CONTRACTED

Ключевое правило:

**forecast != value != bet != portfolio position**

### Forecast / value

- `main_forecast` — прогноз модели.
- `value_signal` — отдельный informational price/EV signal.
- Value/raw EV никогда не переопределяет forecast.
- Canonical regression: Liverpool–Fulham — Liverpool ~67.5% остаётся main forecast, Fulham ~16.8% с positive raw EV остаётся только value signal.

### Cross-market ranking

`product-decision.v1`:
- сначала учитывается `decision_tier`/market maturity;
- внутри одного допустимого tier — probability;
- provisional market с большей голой probability не вытесняет operational market автоматически;
- alternatives берутся из других markets, а не просто из 2-го/3-го исхода 1X2.

Current readiness:
- `1x2`: tier 2 / `operational` / forecast + value eligible / bet recommendation disabled;
- `total_goals`: tier 1 / `provisional` / model-only / value disabled;
- `handicap`: tier 0 / research-only;
- `corners_total`: tier 0 / research-only.

`bet_decision` в Product Decision Framework v1 = `no_bet`.

PR #275 закрепил `forecast != value`; merge после него вошёл в product chain.
PR #278 добавил `product-decision.v1`; merge `1d0dfd568274fd06f436bf39ff4f8062edfe93ee`.

## P1. Durable live product pipeline — CLOSED / LIVE-PROVEN

Основной путь:

immutable prediction snapshot -> Supabase -> independent odds join by `event_id` -> server product contract -> UI/API.

### Durable prediction snapshots

Table: `product_prediction_snapshots`.

Safety:
- append-only product snapshots;
- RLS enabled;
- public web uses Supabase publishable key, not service-role secret;
- raw model provenance не открывается public SELECT;
- service role keeps append-only write path.

First real durable product publish:
- run: `pair-ledger-bootstrap:20260912T044914Z`;
- inserted `20/20` EPL prediction snapshots;
- source = already durable `epl_ai_market_pair_ledger` model probabilities, not new inference;
- artifact SHA `1e516fe91420fdc2d6479e9fb92b005c4a0c75c7f0f217493dd6b27fd64d99a5`;
- all 20 event IDs had independent stored bookmaker odds;
- bootstrap was intentionally `1X2-only`; unsupported goal/handicap/corner fields were not fabricated.

PR #276 added stable ID/public read/bootstrap path and merged to main.
PR #277 added clean-deploy public Supabase config; merge `17abfb65dd75324809e7a93f35c3647bb53900da`.

### Stable match identity

- primary: `event_<provider event_id>`;
- fallback: deterministic hash of league + model teams + kickoff;
- detail endpoint resolves stable ID, not list index;
- legacy numeric `/product-market-view/0` returns 404.

## P2. Public product web

Public alias:

`https://football-ai-real-epl-snapshot.vercel.app`

Important deployment state:
- production alias was last deployed from exact product main `17abfb65dd75324809e7a93f35c3647bb53900da` (deployment `dpl_5bWN15LSoByRPNURBotsk3TN3vnH`);
- later repository product contracts (#278–#282) are **ahead of that production deployment**;
- therefore do not claim `/portfolio-risk-view` or all later framework fields are already live on the main public alias until an exact-main production redeploy is performed;
- separate proof deployments/projects are not substitutes for main product deployment.

Current live product feed proof from the existing public product reader at ~2026-09-12 15:34 UTC:
- future `match_count = 15` (five earlier fixtures already passed kickoff and correctly left future-window);
- `main_forecast_count = 15`;
- `value_signal_count = 14`;
- all 15 `bet_decision = no_bet`.

## P3. Product Prediction Lifecycle — CLOSED / LIVE INITIALIZED

Version: `product-lifecycle.v1`.

Lifecycle is append-only facts:

`PREDICTION_REGISTERED -> MARKET_OBSERVED -> SETTLED`

Principles:
- never rewrite old forecast probabilities after result;
- source prediction timestamp and lifecycle recording timestamp are separate facts;
- historical/bootstrap product snapshots are marked honestly as legacy bootstrap;
- current Decision Framework is not retroactively attached to old snapshots;
- stored pre-kickoff market price is not called closing line without explicit qualification;
- CLV remains null until closing qualification exists;
- betting P&L/ROI remain null because no betting policy/actual bets exist.

Live initialization after PR #279/#280:
- `PREDICTION_REGISTERED = 20`;
- `MARKET_OBSERVED = 5`;
- `SETTLED = 0` at last direct lifecycle proof;
- no synthetic settlements;
- canonical EPL finished-results source at launch ended at `2026-09-06`.

Permissions:
- lifecycle table RLS enabled;
- `service_role` final table grants = exactly `SELECT + INSERT`;
- anon/authenticated = no lifecycle access;
- inherited extra privileges discovered in live proof were fixed by PR #280 before bootstrap continued.

PR #279 merge `dfed5784215717c93c60561dbbb58f03009badea`.
PR #280 final grant hardening; main after it `1f5bf8bc13e976f50450f42be9c7491f26164b27`.

## P4. Reliability / Calibration Layer — CLOSED / WAITING FOR SETTLED SAMPLE

Version: `product-reliability.v1`.

Primary claim scope:

`exact model_1x2_sha256 × league × 1X2`

Evidence-readiness gate preregistered before product settlements:
- minimum `100` settled predictions in exact scope;
- minimum `4` calendar months from first to last kickoff.

States:
- `NO_SETTLED_DATA`;
- `ACCUMULATING_SAMPLE`;
- `ACCUMULATING_TIME`;
- `REVIEWABLE`;
- mixed model/league aggregates = `DESCRIPTIVE_ONLY`.

Critical semantic:

**REVIEWABLE != reliable != PASS != promotion**

v1 deliberately has no post-outcome Brier/ECE/log-loss PASS threshold. Even reviewable slice remains `INCONCLUSIVE` until a later separately preregistered review.

Metrics available once settlement exists:
- top-pick accuracy;
- multiclass Brier;
- multiclass log loss;
- Brier skill vs uniform 1X2;
- log-loss improvement vs uniform 1X2;
- 10pp calibration buckets;
- empirical hit rate + Wilson 95% interval;
- weighted top-pick ECE.

Reliability recalculates scoring from frozen registration probabilities + outcome and fail-closes on mismatch or duplicate settlement facts.

Last live exact EPL product state:
- product lifecycle `SETTLED = 0`;
- reliability = `NO_SETTLED_DATA / INCONCLUSIVE`.

PR #281 exact head `5fa3bb213b724d7d100a5af56b2f8efe6f61e5ec`;
merge `4640a412c438f1ec5c23dc49b0fe7627b32a0dea`.

## P5. Portfolio / Risk Layer — CLOSED / STRUCTURAL ONLY

Version: `product-portfolio-risk.v1`.

Risk exists only from explicit future `bet_decision.status == "bet"`.

Therefore:
- forecast != position;
- positive raw EV/value != position;
- one fixture = max `1` actionable structural risk slot until within-fixture covariance is validated;
- exact duplicate actionable position -> block;
- conflicting selections same fixture/market -> block;
- multiple actionable positions same fixture -> block;
- probabilities/EV across correlated signals cannot be summed;
- league/team concentration is descriptive count only.

No staking policy in v1:
- bankroll size undefined;
- stake amount/units undefined;
- Kelly disabled;
- league/team money caps undefined;
- monetary exposure unavailable;
- fields such as `stake`, `bankroll_fraction`, `kelly_fraction` are blocked as unapproved input.

Live invariant proof on real product feed:
- source `product-market-view.v1`;
- matches `15`;
- main forecasts `15`;
- value signals `14`;
- `bet_status_counts = {no_bet: 15}`;
- actionable positions `0`;
- `status = NO_ACTIONABLE_EXPOSURE`;
- monetary exposure unavailable, `total_stake = null`.

Proof was run in isolated Vercel project only:
- project `football-ai-portfolio-risk-proof`;
- project id `prj_cbd59y6UCM7Xlx2B1mEDPnOFTHGq`;
- deployment `dpl_G1LT3MWkBPcZfeVXFaR9uHhqvhaj`;
- public alias `https://football-ai-portfolio-risk-proof.vercel.app`;
- HTTP 200 / READY.

Main product production alias was intentionally **not** switched to the proof runtime.

PR #282 exact head `33e4818ce590d378ff0a841eaa427eb4840d1f9c`;
merge `b057466362ec2b99f58cd392d7e289bdefaf82d8`.

---

# Product PR chain — durable reference

Product foundation sequence:
- #267 — product market dashboard;
- #268 — match card alignment;
- #269 — unified product market contract;
- #270 — product API + Vercel entrypoint;
- #271 — UI consumes server market contract;
- #272 — durable product prediction snapshots;
- #273 — Data API grant hardening;
- #274 — Vercel preview readiness;
- #275 — forecast/value separation;
- #276 — stable product identity + live Supabase read + ledger bootstrap path;
- #277 — public clean-deploy Supabase config;
- #278 — Product Decision Framework v1;
- #279 — Product Lifecycle v1;
- #280 — lifecycle grant hardening after live proof;
- #281 — Reliability / Calibration v1;
- #282 — Portfolio / Risk v1.

All substantive product PRs in this chain passed the required product + research/league CI contours before exact-head merge.

---

# Supabase product security boundary

Current product-specific rules:
- public web reads with publishable key, never service-role secret;
- public RLS only exposes product-required future-window columns;
- public users have no product write permission;
- product prediction snapshots are append-only;
- lifecycle is service-role `SELECT + INSERT` only, no update/delete/truncate/trigger/reference privileges;
- odds and predictions remain separate sources, joined by provider `event_id`;
- synthetic unsupported markets/results are forbidden.

Separate historical Supabase security backlog still exists on older tables (`teams`, `predictions`, `match_statistics`, `league_prediction_ledger`, `epl_ai_market_pair_ledger`, etc.). Do not mix that broad RLS migration into unrelated product work; audit access flows first.

---

# Текущий execution pointer

## Research pointer

- `ALL_LEAGUES_MARKET_ONLY_V1_1`: **collect, don't peek / SAMPLE_CLOSED**.
- До frozen gate разрешены только outcome-blind health/identity/completeness checks и future-only capture по frozen rules.
- `EPL_AI_MARKET_PAIR_V1` остаётся отдельным frozen experiment; не backfill и не выводить membership из product bootstrap.
- Любой paid provider refresh = отдельный `MANUAL_PAID_GATE`.
- Candidate V2/model promotion не открывать до соответствующего evidence gate.

## Product pointer

Product foundation now contains:

`Prediction delivery -> Decision Framework -> Lifecycle -> Reliability evidence -> Portfolio/Risk`

Все эти слои уже contracted/merged. Safe product work, которое не требует ждать research outcomes:

1. **Product Production-Readiness Framework** — стандартизировать критерии, когда market/league может перейти из research/provisional в operational product status.
2. **Operational automation** — future fixture/prediction publish, lifecycle advance, result settlement and monitoring без ручного вмешательства, сохраняя paid/manual gates.
3. **Exact-main web deployment** — основной public product site сейчас отстаёт от repository contracts #278–#282; при следующем deployment публиковать exact current main, а не proof runtime.
4. После evidence — подключать полноценные second markets (goal total first), затем handicap/corners согласно readiness gates.

Betting/staking policy **не является следующим автоматическим шагом**: он остаётся отдельным future contract и не должен включаться до достаточного empirical reliability/evidence.

## UI pointer

UI можно шлифовать параллельно, но UI не должен менять server-owned semantics:
- main forecast = forecast, not value;
- maturity/tier before cross-market probability ranking;
- value separate;
- research-only unavailable state must remain explicit;
- no-bet and no-data are valid product states.

---

# Closed historical/operational reference — не переоткрывать без новой причины

- Historical corners V1–V4: closed under stop rule.
- Canonical public results / settlement fallback: live-proven; reopen only on new failure.
- Market revision safety / canonical event identity: closed/live-proven.
- Eight-league MARKET_ONLY infrastructure readiness: 8-of-8 live-proven.
- V1.1 freeze/evaluation gate/sample-health automation: frozen/operational; do not modify using outcomes.
- Production model promotion: always explicit/manual, never implied by research/product results.

---

# 2026-09-12 key decisions / audit trail

Research side:
- eight-league MARKET_ONLY readiness closed 8-of-8;
- common V1 T0 frozen;
- V1.1 successor frozen with 127 untouched future seed events;
- evaluation gate frozen before first seed kickoff;
- daily outcome-blind sample-health operationalized;
- outcome read remains forbidden.

Product side:
- product dashboard/API/durable snapshot pipeline completed;
- forecast/value semantic bug fixed: value cannot become main forecast;
- stable `product_match_id` replaced array-index detail identity;
- first 20 real EPL durable product snapshots published from existing paired-AI ledger with provenance;
- live product reader works through Supabase publishable key/RLS;
- Decision Framework v1 formalized forecast/alternatives/value/confidence/no-bet;
- Lifecycle v1 added immutable prediction/market/settlement facts;
- live lifecycle inherited service-role privilege defect was discovered before bootstrap and fixed by separate PR #280;
- Reliability/Calibration v1 preregistered exact-scope evidence gates before first product settlement;
- Portfolio/Risk v1 separated signals from positions and proves current actionable exposure = 0.

Continuity correction:
- during the product build the assistant incorrectly updated the historical MASTER BACKUP instead of updating this file after each substantial merge/live proof;
- on 2026-09-12 this was detected and corrected by consolidating the full current durable state back into `PROJECT_CONTINUITY.md`;
- future substantial blocks must update this file as part of completion, not only the backup.

Repository hygiene note:
- while preparing this continuity correction an accidental root file `noop` was created directly on `main` in commit `3e92ab1ec6e2c350f4af8d556698d82ed6374c1e`;
- it was immediately deleted in `f0cd0193fea4c64e0d77b080a0c8d0c05e096ace`;
- net repository tree after the cleanup returned to the PR #282 product state; no product/research/model/data file was changed by those two commits.

---

# Current source-of-truth checkpoint before this continuity PR

- Product code merge: `b057466362ec2b99f58cd392d7e289bdefaf82d8` (PR #282).
- Net-clean main after accidental noop add/remove: `f0cd0193fea4c64e0d77b080a0c8d0c05e096ace`.
- Product snapshot table: 20 durable EPL snapshots from first bootstrap run.
- Lifecycle last direct proof: 20 registered / 5 market-observed / 0 settled.
- Reliability: `NO_SETTLED_DATA / INCONCLUSIVE`.
- Portfolio live proof: 15 future matches / 14 value signals / 0 actionable positions / `NO_ACTIONABLE_EXPOSURE`.
- Research V1.1 outcome gate: closed; no-peek remains binding.
