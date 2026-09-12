# Football AI — Project Continuity

Этот файл — постоянная память проекта между чатами. Фактический source of truth всегда свежий GitHub `main` + live Supabase. Git history сохраняет полный исторический detail; здесь держим текущие контракты, доказанные решения, закрытые блоки и официальный порядок дальнейшей работы.

## Как пользоваться

Перед новой рабочей сессией:
1. Прочитать этот файл.
2. Коротко сверить свежий `main` и live Supabase.
3. Не повторять полный аудит без конкретной причины.
4. Найти раздел **MASTER ROADMAP** и **Текущий execution pointer**.
5. Продолжать текущий roadmap item до его закрытия или реального documented gate/blocker.
6. После существенного решения, PR, merge или live-proof обновить этот файл.

## Стиль и приоритет работы

- Объяснять пользователю простым языком: что сделали, что выяснили, почему важно, что дальше.
- Приоритет пользователя: **максимально развивать проект без лишней технической дрочки**.
- Инфраструктуру менять только когда она снимает реальный blocker, защищает данные/production или ускоряет research.
- Без запроса подтверждения после каждого безопасного шага; останавливаться только на реальном safety/manual-paid/external/time gate.
- Safe и однозначные шаги выполнять в одном цикле: проверка -> изменение -> regression tests -> branch -> PR -> полный CI -> fresh-main -> exact-head merge -> post-merge/live proof -> continuity.

## Постоянные правила

- Repo: `MaksimBlud/football-ai`, branch `main`.
- Source of truth: свежий GitHub `main` + live Supabase.
- Production `.pkl` нельзя менять как побочный эффект research/training.
- Research/training != production promotion; automatic promotion запрещён.
- Не делать mass-clean/reset/mass-format и не перетирать параллельные изменения.
- Существенные изменения: branch -> tests -> PR -> полный CI -> fresh-main -> exact-head merge -> post-merge/live proof.
- Frozen/preregistered contracts не ослаблять задним числом.
- Prospective outcomes нельзя читать до разрешённого gate.
- Максимально использовать free/read-only proof; The Odds API credits не тратить при наличии бесплатной проверки.
- Paid-provider workflows остаются manual-only. Priority/readiness/status report никогда не является разрешением на расход credits.
- Реальные баги закрывать regression-тестами.
- Fail-closed red не превращать искусственно в green.
- Если point-in-time history нельзя честно восстановить, не делать retrospective production replay.
- Closed historical/research блоки не переоткрывать без нового внешнего evidence или реального blocker.

---

# MASTER ROADMAP

## Главная цель проекта

Football AI должен стать системой, которая:
1. регулярно получает корректные pre-match данные;
2. строит прогнозы без leakage;
3. честно сравнивает AI с букмекерским рынком;
4. доказывает улучшения только на untouched prospective/OOS данных;
5. переносит доказанные сигналы между лигами;
6. выпускает в production только отдельно validated candidate;
7. после promotion продолжает следить за calibration, drift и market-relative edge.

Главная линия проекта сейчас не «искать ещё фичи для XGBoost», а:

**качественные prospective данные -> честное market-relative evidence -> portable signals -> Candidate V2 -> отдельное production decision.**

## Правило последовательности / anti-jump contract

Это обязательный рабочий порядок:

- Не начинать lower-priority roadmap item, пока у более высокого priority есть безопасная и исполнимая работа.
- Переключаться ниже можно только если текущий item:
  1. `CLOSED`;
  2. упёрся в явный `MANUAL_PAID_GATE`;
  3. упёрся во `EXTERNAL_CREDENTIAL_GATE`;
  4. упёрся в `TIME/FROZEN_GATE`;
  5. имеет другой конкретный blocker, который зафиксирован здесь.
- Generic «продолжай» не разрешает paid/external действие.
- При временном gate работаем по следующему безопасному item, но не объявляем gated item закрытым.
- После каждого merge/live proof execution pointer обновляется.
- Любое существенное отклонение от порядка фиксируется в этом файле с причиной.
- `CLOSED` блоки не пересматриваем «на всякий случай».

## P0 — непосредственная основная работа

### P0-A. Prospective data acquisition / market freshness — ACTIVE / MANUAL_PAID_GATE

Цель: получать свежие pre-cutoff odds snapshots без двойного refresh и без бессмысленного расхода credits.

Уже закрыто:
- revision safety;
- `SUPERSEDED` -> inactive/not-due;
- tied-current ambiguous event ids -> `QUARANTINED_REVISION`;
- единый read-only `prospective_market_status.py`;
- fixture-level `live_refresh_priority.csv`;
- deterministic priority на существующем cadence;
- PR #232 merge `a895012fdd65148672b9cfa4bc83ea229145346d`;
- continuity PR #233 merge `7ca38b6b4c886e6ff6aed5142fa8756a781778e2`.

Fresh free/read-only proof 2026-09-09:
- Supabase checked at `2026-09-09 15:57:28.777877 UTC`;
- latest snapshots remain stale: EPL `2026-09-05 15:19:42.729192 UTC`, LA_LIGA `2026-09-05 15:21:32.513020 UTC`, SERIE_A `2026-09-05 15:08:05.114487 UTC`;
- actionable due paths = `23`: SERIE_A `8`, LA_LIGA `5`, EPL `10`;
- current priority = **SERIE_A -> LA_LIGA -> EPL**;
- top current path = **Torino vs Napoli**, kickoff `2026-09-11 18:45 UTC`, cutoff `2026-09-11 12:45 UTC`, status `READY`, 32 pre-cutoff snapshots, path span ~163.12h;
- revision-danger paths remain excluded by the existing `SUPERSEDED` / `QUARANTINED_REVISION` rules;
- fresh zero-cost quota proof via rerun of the already-proven read-only status job: remaining `193`, used `307`, last_cost `0`, hard reserve `100`;
- paid provider requests `0`, provider credits spent `0`, Supabase writes `0`, production model hash unchanged before/after.

Следующая стадия P0-A:
- **free proof завершён**;
- actual paid h2h refresh остаётся `MANUAL_PAID_GATE`;
- только при отдельном явном разрешении пользователя выполнить controlled refresh по свежему priority и existing budget/safety guards;
- после refresh — live verification и continuity.

Важно: отсутствие explicit paid permission = gate, а не разрешение автоматически запускать collector.

### P0-B. EPL_AI_MARKET_PAIR_V1 — ACTIVE / TIME-FROZEN_GATE

Режим: **collect, don't peek**.

- Frozen cohort = первые 100 eligible prospective EPL events.
- Fresh outcome-free health 2026-09-09: `12/100`, 12 unique `pair_key`, 12 unique `event_id`, только EPL.
- Integrity: history cutoff, model generation и market snapshot находятся до kickoff; invalid probability rows = 0; probability sums нормализованы.
- Current cohort kickoff span: `2026-09-06 13:00 UTC` -> `2026-09-14 19:00 UTC`.
- Cohort использует один model artifact SHA256 `1e516fe91420fdc2d6479e9fb92b005c4a0c75c7f0f217493dd6b27fd64d99a5` и один code commit `4c1bc43ff6157382a83fe467d33fa8fe54adf897`.
- Outcomes запрещены до 100 событий.
- После 100: минимум 24h после kickoff последнего cohort event.
- Дополнительный embargo до `2026-11-01 12:16:54 UTC`.
- Никакого interim primary evaluation или performance-based optional stopping.
- В fresh health pass outcome/result tables не читались.

Цель: ответить на главный вопрос проекта — добавляет ли AI predictive value относительно рынка на честном prospective sample.

До gate: только collection/identity/sample-health metadata.

### P0-C. PROSPECTIVE_MARKET_PATH_V1 — ACTIVE / DATA-GROWTH + P0-A FRESHNESS GATED

Цель: исследовать полную pre-cutoff market trajectory, а не один closing price.

Контракт:
- full pre-cutoff trajectory;
- deterministic schedule revisions quarantined;
- paid h2h refresh manual-only;
- прошедший cutoff нельзя backfill;
- outcome peeking запрещён;
- acquisition и settlement — разные контуры.

Frozen activation contract:
- `FREEZE_UTC = 2026-09-04 14:25:00 UTC`;
- minimum 100 fixtures per league;
- minimum 4 kickoff calendar months per league;
- minimum 3 pre-cutoff snapshots and 12h path span for `READY` path quality.

Fresh outcome-free trajectory health 2026-09-09:
- raw frozen universe = `68` event ids: EPL `20`, LA_LIGA `24`, SERIE_A `24`;
- each league currently spans only `1` kickoff calendar month versus required `4`;
- actionable trajectory refresh due = `23`: EPL `10`, LA_LIGA `5`, SERIE_A `8`;
- current acquisition priority remains **SERIE_A -> LA_LIGA -> EPL**;
- source snapshots are still stale from 2026-09-05, so P0-A freshness is the immediate data-quality limiter;
- activation gate `100 fixtures + 4 months per league` is not reached;
- no outcome/result tables were read in this health pass.

Зависимость: качество этого эксперимента напрямую зависит от P0-A freshness.

---

## P1 — parallel block exhausted to documented gates / 2026-09-10 pass complete

### P1-A. SportsGameOdds bookmaker-corner capability — AUTHORIZED / EXECUTION_SURFACE_GATE

The Odds API corner capability уже закрыт как **CAPABILITY_MISS**.

Manual The Odds API probe:
- target: BUNDESLIGA Union Berlin vs FC Schalke 04;
- kickoff `2026-09-11T18:30:00Z`;
- event_id `115c6679a72c5a360640b6baaa16e78c`;
- one provider request;
- 0 credits charged;
- quota remained 193;
- no corner market keys/bookmakers;
- no Supabase writes;
- production model unchanged;
- same-target rerun запрещён без нового evidence.

Следующий candidate source = **SportsGameOdds**.

PR #230 merge `fdc7a4064fd4fd97b6a98af27b97931e593fc85b` уже добавил fail-closed manual-only capability probe:
- `workflow_dispatch` only;
- exact Union Berlin–Schalke target;
- requested odd ids `cornerKicks-all-game-ou-over/under`;
- max 1 authenticated provider request;
- capability только при same-bookmaker Over+Under на одной numeric line с явными prices;
- no Supabase writes;
- no production `.pkl` changes.

Fresh P1 pass 2026-09-10:
- пользователь явно разрешил внешний SportsGameOdds live capability probe как часть выполнения всего P1;
- safety contract PR #230 не ослаблялся и manual-only trigger не менялся;
- доступный connected GitHub execution surface не предоставляет операцию `workflow_dispatch`;
- локального авторизованного `gh`/другого штатного authenticated execution path в рабочем окружении нет;
- обход через изменение workflow trigger запрещён и не выполнялся;
- SportsGameOdds provider requests = `0`;
- Supabase writes = `0`;
- production artifact changes = `0`;
- capability остаётся unresolved до появления поддерживаемого execution surface для исходного manual-only workflow.

Fallback order при miss/access failure: SportsGameOdds -> Sportmonks -> Betfair Exchange.

### P1-B. Outcome-free health всех frozen experiments — PASS COMPLETE / HEALTHY

Fresh outcome-free live pass 2026-09-10:
- authoritative `EPL_AI_MARKET_PAIR_V1` checked at `2026-09-10 14:25:10.395125 UTC`;
- cohort остаётся `12/100`: 12 rows, 12 unique `pair_key`, 12 unique `event_id`, non-EPL rows `0`;
- bad history cutoff/model generation/market snapshot timing = `0/0/0`;
- invalid model/market probability rows = `0/0`; probability sums нормализованы до floating-point precision;
- один model artifact hash и один code commit; kickoff span остаётся `2026-09-06 13:00 UTC` -> `2026-09-14 19:00 UTC`;
- статус frozen EPL experiment остаётся `HEALTHY / 12/100 / TIME-FROZEN_GATE`.

Cross-league outcome-free health:
- `league_prediction_ledger` имеет live rows для **7 лиг**: BUNDESLIGA `26`, EPL `30`, EREDIVISIE `27`, LA_LIGA `36`, LIGUE_1 `26`, RPL `16`, SERIE_A `28` unique events;
- во всех 7 лигах `prediction_time > kickoff = 0`, `snapshot_time > kickoff = 0`, invalid market probabilities = `0`; probability sums нормализованы до floating-point precision;
- general structural storage `league_structural_v2_observations` тоже охватывает 7 лиг и имеет `snapshot_time > commence_time = 0` во всех лигах;
- La Liga остаётся в transition/compatibility split: general structural storage `25 rows / 12 events` плюс `la_liga_structural_v2_observations` `726 rows / 40 events`; оба слоя temporal-safe (`bad_snapshot_time=0`);
- stale latest core snapshots около 2026-09-05 классифицируются как уже известный P0-A freshness blocker, а не как новый P1 integrity failure;
- outcome/result/settlement rows для prospective evaluation в этом P1 pass не читались.

### P1-C. Multi-league portability / operational coverage — CORE HEALTHY / CROSS-LEAGUE MULTI-MARKET NOT YET LIVE-PROVEN

Fresh 2026-09-10 portability audit:
- core prediction contract реально работает на 7 live leagues, включая RPL, без обнаруженного temporal/probability leakage;
- structural observation contract тоже live-healthy на 7 лигах; La Liga legacy/general split остаётся compatibility/migration distinction, не evidence model failure;
- actual `league_multi_market_snapshots` footprint пока только EREDIVISIE: `2 rows / 2 events`, оба snapshots до kickoff (`bad_snapshot_time=0`);
- это **не hardcoded Eredivisie-only limitation**: `multi_market_policy.py` разрешает collection-ready EPL, LA_LIGA, SERIE_A, BUNDESLIGA, LIGUE_1, EREDIVISIE и PRIMEIRA_LIGA; Turkey Super Lig fail-closed из-за unpublished current corner source;
- `multi-market-cycle.yml` допускает paid collection только через manual `workflow_dispatch`, ограничивает request/credit budget, требует collection leagues быть subset policy и проверяет production model hash before/after;
- следовательно core multi-league portability сейчас **HEALTHY**, но cross-league Multi-Market V2 collection ещё **NOT LIVE-PROVEN** за пределами двух Eredivisie events;
- расширять лиги только ради количества по-прежнему запрещено; следующий cross-league canary имеет смысл только когда roadmap/data/permission gate даёт практическую цель.

P1 safety summary 2026-09-10: external provider requests `0`; paid credits spent `0`; Supabase writes `0`; prospective outcome/settlement reads `0`; production artifact changes `0`.

---

## P2 — открыть только после достаточного нового sample / frozen gates

### P2-A. Frozen EPL AI-vs-Market evaluation — FUTURE / GATED

После выполнения всех EPL gates:
- открыть outcomes;
- frozen evaluation;
- AI vs market baseline;
- calibration/log loss/Brier/accuracy;
- market-relative value;
- принять evidence-based решение без retrospective tuning.

### P2-B. Market trajectory evaluation — FUTURE / GATED

После достаточного trajectory sample:
- early line;
- movement direction/magnitude;
- convergence;
- AI-market disagreement;
- timing signals;
- untouched prospective evaluation.

### P2-C. PROSPECTIVE_CORNERS10_INCREMENTAL_V1 — FUTURE / GATED

Вопрос: добавляет ли `CORNERS10` prospective 1X2 information сверх market baseline.

Frozen contract:
- historical incremental result не использовать для tuning;
- minimum 100 settled eligible fixtures на лигу;
- минимум 4 calendar months;
- bookmaker capability — отдельный gate;
- outcome scoring до activation запрещён.

### P2-D. Bookmaker corner-line prospective experiment — CONDITIONAL FUTURE

Только если внешний source реально подтвердит corner lines/prices.

Тогда отдельно preregister:
- наш expected corners;
- bookmaker total-corner line;
- same-bookmaker prices;
- sample size;
- metrics;
- evaluation gate;
- no-peek policy.

Historical corner V1–V4 не переоткрывать.

---

## P3 — model decision после evidence

### P3-A. Candidate V2 construction — FUTURE

Не начинать, пока P2 не даёт достаточного prospective evidence.

Candidate должен включать только сигналы, которые пережили честную OOS/prospective проверку.

### P3-B. Candidate V2 validation — FUTURE

Сравнить:
- current production baseline;
- football-only candidate;
- market-aware candidate;
- candidate + доказанные новые signals.

Обязательное validation:
- temporal / walk-forward;
- nested selection где нужно;
- league splits;
- untouched seasons/sample;
- calibration;
- log loss;
- Brier;
- accuracy;
- ROI/value simulation там, где методологически уместно;
- drawdown;
- sample size/stability;
- `NO BET` как допустимый результат.

### P3-C. Production promotion decision — FUTURE / MANUAL_GATE

Даже доказанный candidate не становится production автоматически.

Порядок:
research result -> candidate artifact -> independent validation -> compatibility/hash/metadata proof -> отдельное explicit promotion решение пользователя.

Automatic promotion запрещён.

---

## P4 — product/platform hardening после model decision или при отдельном blocker

### P4-A. Production API / web application modernization — FUTURE

После определения следующего production model contract:
- API contract audit;
- model/version metadata;
- league support;
- upcoming fixtures;
- odds freshness display;
- graceful no-odds mode;
- calibration outputs;
- health/status endpoints;
- user-facing explanation.

Не делать большой UI/API refactor раньше model contract без отдельной причины.

### P4-B. Production monitoring / drift — FUTURE

После нового production decision:
- prediction ledger;
- calibration drift;
- feature drift;
- league drift;
- market-relative drift;
- rolling OOS metrics;
- candidate-vs-production shadow evaluation;
- alerts/status.

### P4-C. Supabase security / RLS — BACKLOG / READ-ONLY FIRST

Ранее RLS был disabled на:
- `teams`;
- `predictions`;
- `match_statistics`;
- `league_prediction_ledger`;
- `epl_ai_market_pair_ledger`.

Не включать автоматически.

Порядок:
access-policy audit -> определить public/server-only flows -> service-role requirements -> regression tests -> staged RLS policies.

### P4-D. Documentation / architecture / runbook — BACKLOG

README исторически описывает проект как EPL web app и отстаёт от реальной multi-league research platform.

После стабилизации основных evidence/data контуров:
- README v2;
- architecture diagram;
- workflow/runbook;
- production/research lifecycle;
- operator instructions.

Этот `MASTER ROADMAP` является текущим навигатором до такой консолидации.

---

# Закрытые research/operational блоки — не переоткрывать без новой причины

## Historical corners — CLOSED

### SEASON_INVARIANT_CORNERS_V1 — PORTABLE_STRONG
- CORNERS10 vs GOALS10: EPL 6/7, La Liga 5/7, Serie A 7/7; total 18/21.
- PR #212 merge `f72952be44249cceceb6a81cb6ff02d885e588ff`.

### CORNER_TOTAL_SIGNAL_V1 — NOT_PORTABLE_TOTAL_SIGNAL
- 2581 held-out;
- weighted delta MAE `+0.040076`;
- wins 2/7;
- Over 9.5 AUC ~0.5053.
- PR #214 merge `92633e3f011146a533b3cdce1ab26080efe1b139`.

### CORNER_TOTAL_CALIBRATED_V2 — PORTABLE_CALIBRATED_TOTAL_SIGNAL
- weighted delta MAE ~`-0.007791`;
- wins 6/7;
- small portable expected-count signal;
- Over 9.5 AUC still ~0.5053.
- PR #215 merge `8e206f4e97f8b5d0e64bc2951716ad8d971def61`.

### CORNER_PRESSURE_SIGNAL_V3 — NOT_PORTABLE_PRESSURE_DISCRIMINATOR
- all-shots AUC 0.498357;
- SOT AUC 0.512793;
- frozen 0.52 threshold missed.
- PR #216 merge `95386fffb6b386efa26feb0ad4860135ded99257`.

### CORNER_COMBINED_DISCRIMINATOR_V4 — NOT_PORTABLE_COMBINED_DISCRIMINATOR
- weighted AUC 0.501691;
- positive 3/7;
- frozen pass failed.
- PR #217 merge `9bb1e8ed244e10f53d87850cb552aa70e148e0eb`.

**STOP RULE:** не перебирать новые windows/weights/thresholds/combinations на тех же historical seasons.

## Settlement / public results — CLOSED / LIVE_PROVEN

Football-Data remains primary; ESPN keyless scoreboard is bounded fallback for La Liga/Serie A.

Safety:
- explicit completed-only;
- strict score/date/home-away/team validation;
- immutable persistence/conflict guards;
- malformed/unknown -> fail closed;
- paid provider requests = 0.

PR #223 merge `5befc9d53a0382a6178436ee55518a279c560e15`.
PR #224 merge `382814a00f1c04dbff776c0a5594b3c98909fe9a`.

Live proof:
- La Liga run `34180001408`: primary 3x503 -> ESPN; canonical inserted 10; conflicts 0; paid 0; model unchanged.
- Serie A run `34180001418`: primary 3x503 -> ESPN; inserted 19; unchanged 11; conflicts 0; paid 0.
- settlement-late audit became EPL=0, La Liga=0, Serie A=0.

Не возвращаться к settlement без нового failure.

## Market Status / revision safety — CLOSED / MERGED / LIVE_PROVEN

PR #232:
- exact head `e6a08fa3b1399fc07c31564fb04982aacaa3a0a6`;
- all 6 PR workflows green;
- focused `Prospective Market Path Coverage PR Validation` run `34366488263` = 24 passed;
- production `.pkl` hash guard unchanged;
- merge `a895012fdd65148672b9cfa4bc83ea229145346d`.

Revision contract:
- old event id same normalized pair -> `SUPERSEDED`, inactive, not due;
- tied-current event ids -> all `QUARANTINED_REVISION`, inactive, not due;
- no guessing canonical identity;
- hard conflicts remain fail-closed.

Post-merge live proof 2026-09-09:
- 23 actionable due paths;
- 4 pair-quarantined event ids;
- priority `SERIE_A -> LA_LIGA -> EPL`;
- no writes/provider spend/outcome reads/model changes.

Continuity follow-up PR #233 merge `7ca38b6b4c886e6ff6aed5142fa8756a781778e2`.

---

# Текущий execution pointer

**Primary item remains `P0-A Prospective data acquisition / market freshness` — `MANUAL_PAID_GATE`; P1 safe work is exhausted to documented gates.**

Состояние после P1 pass 2026-09-10:
- P0-A = `MANUAL_PAID_GATE`; separate explicit paid-h2h permission всё ещё отсутствует, и P1 external-probe permission его не заменяет;
- P0-B = `HEALTHY / 12/100 / TIME-FROZEN_GATE`;
- P0-C = `68 raw frozen event ids / 1 kickoff month per league / DATA-GROWTH + P0-A FRESHNESS GATED`;
- P1-A = `AUTHORIZED / EXECUTION_SURFACE_GATE`: permission на SportsGameOdds probe получен, но supported workflow-dispatch execution surface недоступен; provider request не выполнялся;
- P1-B fresh outcome-free health = `PASS COMPLETE / HEALTHY`;
- P1-C = `CORE HEALTHY / CROSS-LEAGUE MULTI-MARKET NOT YET LIVE-PROVEN`;
- P2-A/P2-B/P2-C всё ещё `FUTURE / GATED`; P2-D conditional на подтверждение bookmaker corner capability.

Что делать дальше по roadmap:
1. Не открывать P2 outcomes/performance до frozen sample/time activation gates.
2. Если появляется поддерживаемый execution surface для уже разрешённого SportsGameOdds manual-only workflow, выполнить ровно исходный bounded one-request P1-A probe без изменения safety contract и сразу зафиксировать capability result.
3. P0-A paid h2h refresh остаётся отдельным `MANUAL_PAID_GATE`: только отдельное явное разрешение пользователя, затем fresh priority/quota -> минимальный controlled refresh -> live proof.
4. Пока P0/P1/P2 стоят на gates, допустимы только outcome-free collection/health и operational checks, которые сохраняют frozen/no-peek contracts; не начинать Candidate V2/API/RLS без нового roadmap основания.

---

# Журнал ключевых решений

## 2026-09-07
- Создан `PROJECT_CONTINUITY.md` как durable project memory.
- Принят season-invariant principle: historical portability first, fresh prospective evidence second.
- Historical corner V1–V4 закрыты; STOP RULE против same-data feature mining.
- Bookmaker corner capability оставлен external/manual gate.
- RLS вынесен в отдельный future access-policy audit.

## 2026-09-08
- Settlement blocker La Liga/Serie A закрыт через Football-Data primary + ESPN fallback; PR #224 live-proven.
- Zero-cost acquisition audit подтвердил snapshot staleness с 2026-09-05.
- Fresh zero-cost quota proof: remaining 193, used 307, hard reserve 100.
- Union Berlin–Schalke target activated without paid call.
- The Odds API corner probe завершился `CAPABILITY_MISS`: 1 request, 0 credits, quota 193->193, no writes/model changes.
- Альтернативный source order: SportsGameOdds -> Sportmonks -> Betfair.
- PR #230 merged SportsGameOdds manual-only capability infrastructure; provider call not performed.

## 2026-09-09
- PR #232 закрыл revision safety: stale ids deactivate; tied-current ids quarantine fail-closed.
- Добавлены unified read-only Market Status и deterministic live refresh queue.
- Exact head `e6a08fa3b1399fc07c31564fb04982aacaa3a0a6`: 6/6 PR workflows green, focused 24 passed, production hashes unchanged.
- PR #232 merge `a895012fdd65148672b9cfa4bc83ea229145346d`.
- Post-merge live Supabase proof: 23 due paths, 4 ambiguous ids quarantined, priority Serie A -> La Liga -> EPL, top path Venezia–Fiorentina.
- PR #233 continuity merge `7ca38b6b4c886e6ff6aed5142fa8756a781778e2`.
- Пользователь утвердил переход к единой master roadmap для всего проекта и запрет хаотичного переключения между областями; этот файл теперь определяет execution order.
- Fresh P0-A free proof на current main `8bca2b71c49eecf3c9692a3800cd3079696465b0`: latest snapshots по EPL/La Liga/Serie A всё ещё 2026-09-05; 23 actionable due (`8/5/10`), current priority Serie A -> La Liga -> EPL, fresh top path Torino–Napoli.
- Fresh zero-cost quota proof: rerun read-only status job `102543884064` в workflow run `34335760026`; quota `193 remaining / 307 used / last_cost 0`, hard reserve `100`; paid requests `0`, credits spent `0`, Supabase writes `0`, production hash unchanged.
- P0-A free proof завершён и формально остановлен на `MANUAL_PAID_GATE`; paid h2h refresh не выполнялся и по-прежнему требует отдельного explicit permission.
- P0-B outcome-free health: `EPL_AI_MARKET_PAIR_V1 = 12/100`, 12 unique pair/event ids, temporal/probability invariants green, один model hash и один code commit; outcomes не читались; статус `HEALTHY / TIME-FROZEN_GATE`.
- P0-C outcome-free trajectory health: frozen raw universe `68` event ids (`EPL 20 / LA_LIGA 24 / SERIE_A 24`), только 1 kickoff month per league; activation `100 + 4 months` не достигнут; 23 trajectory paths refresh-due; outcomes не читались.
- Весь pass был read-only относительно Supabase и outcome-free; paid provider requests/credits = `0/0`; production model не изменён.
- Post-merge live recheck at `2026-09-09 16:16:03 UTC` confirmed P0-A still has no snapshots newer than `2026-09-05 15:21:32.513020 UTC` and P0-B remains `12/100`; corrected authoritative P0-B metadata is last kickoff `2026-09-14 19:00 UTC` and model SHA256 `1e516fe91420fdc2d6479e9fb92b005c4a0c75c7f0f217493dd6b27fd64d99a5`.

## 2026-09-10
- Пользователь явно разрешил пройти весь P1, включая SportsGameOdds live capability probe; P1-A не был запущен только из-за отсутствия поддерживаемого `workflow_dispatch` execution surface, safety contract не ослаблялся.
- P1-A зафиксирован как `AUTHORIZED / EXECUTION_SURFACE_GATE`; SportsGameOdds requests `0`, Supabase writes `0`, production changes `0`.
- Fresh P1-B outcome-free check подтвердил `EPL_AI_MARKET_PAIR_V1 = 12/100`, temporal/probability integrity green, статус `HEALTHY / TIME-FROZEN_GATE`; prospective outcomes/settlements не читались.
- Core `league_prediction_ledger` и structural observations live-healthy по 7 лигам (BUNDESLIGA, EPL, EREDIVISIE, LA_LIGA, LIGUE_1, RPL, SERIE_A) без post-kickoff timing violations; La Liga general/legacy structural split подтверждён как temporal-safe compatibility distinction.
- P1-C: actual Multi-Market V2 live storage = только `2` EREDIVISIE events, оба pre-kickoff; policy при этом collection-ready для EPL/LA_LIGA/SERIE_A/BUNDESLIGA/LIGUE_1/EREDIVISIE/PRIMEIRA_LIGA. Итог: `CORE HEALTHY / CROSS-LEAGUE MULTI-MARKET NOT YET LIVE-PROVEN`.
- P1 pass не расходовал provider credits, не писал в Supabase, не читал prospective outcomes и не менял production `.pkl`.

---

## 2026-09-10 addendum — P1-D Multi-league AI-vs-market readiness closure

Status: **CLOSED / INTENTIONAL FAIL-CLOSED BOUNDARY**.

Кейс `12 paired EPL events` против `~190 multi-league operational events` закрыт полностью и не является потерей 178 матчей.

Fresh live outcome-free proof после merge PR #238:
- `league_prediction_ledger` = `190` unique operational league-events: BUNDESLIGA `26`, EPL `30`, EREDIVISIE `30`, LA_LIGA `30`, LIGUE_1 `26`, RPL `15`, SERIE_A `33`;
- все `190/190` находятся в `prediction_mode=MARKET_ONLY` и `structural_status=CALIBRATION_REQUIRED`;
- `structural_applied_events=0` во всех 7 лигах;
- `epl_ai_market_pair_ledger` = `12` paired-AI events, все EPL;
- все `12/12` имеют валидный pre-kickoff timing, normalized model probabilities, `model_artifact_sha256` и `code_commit_sha`;
- ни одна non-EPL league сейчас не имеет эквивалентного paired-AI provenance.

Code-level root cause:
- `league_prediction_ledger.build_market_only_predictions()` намеренно фиксирует `CALIBRATION_REQUIRED`, `MARKET_ONLY`, `structural_applied=False` и пустые structural probabilities;
- `epl_ai_market_pair_collector.py` — отдельный EPL-only production-model replay path с `LEAGUE="EPL"` и tracked production-model provenance;
- следовательно 190 operational events и 12 paired-AI events — два разных evidence layers.

Закрывающее решение:
- frozen `EPL_AI_MARKET_PAIR_V1` остаётся неизменным `12/100`; multi-league backfill в него запрещён;
- уже собранные MARKET_ONLY rows нельзя задним числом считать prospective AI evidence;
- EPL production model нельзя переносить на другие лиги только ради ускорения sample;
- новый multi-league paired-AI primary experiment допустим только future-only после league-specific historical/OOS readiness и отдельного frozen activation manifest с model/hash/feature/history/calibration/market-cutoff/sample/no-peek/metric contracts;
- `PROSPECTIVE_MARKET_PATH_V1` остаётся отдельным market-trajectory experiment и не переопределяется как AI-vs-market primary cohort.

Guard/proof:
- `multi_league_ai_market_readiness.py` добавляет outcome-free readiness audit и fail-closed запрет на самовольную activation нового primary cohort;
- regression tests: `tests/test_multi_league_ai_market_readiness.py`;
- contract: `research/MULTI_LEAGUE_AI_MARKET_READINESS_V1.md`;
- PR #238 exact head `497af381c99d6eaaebdc257b4a1f8b48b088a8b0`;
- 5/5 PR workflows green;
- production-artifact guard green;
- exact-head merge `97bddbb9c54f5233ef5a12e5944867bdcffee981`;
- post-merge live proof совпал с readiness contract;
- provider requests `0`, paid credits `0`, Supabase writes `0`, prospective outcome/settlement reads `0`, production `.pkl` changes `0`.

### Execution pointer override after P1-D closure

Этот addendum является более свежим pointer, чем расположенный выше `# Текущий execution pointer`.

- Primary item по общей roadmap остаётся `P0-A Prospective data acquisition / market freshness — MANUAL_PAID_GATE`; отдельного explicit разрешения на paid h2h refresh в этом кейсе нет.
- `P0-B EPL_AI_MARKET_PAIR_V1 = HEALTHY / 12/100 / TIME-FROZEN_GATE`; `12` — именно paired EPL AI sample, не общий multi-league operational count.
- `P1-D = CLOSED / INTENTIONAL FAIL-CLOSED BOUNDARY`.
- Для ускорения именно AI-vs-market evidence следующий safe research unblocker: league-specific AI/model-calibration readiness на completed historical/OOS data; после доказательства пригодности хотя бы одной non-EPL league — отдельная future-only preregistration multi-league paired cohort.
- Уже накопленные 190 MARKET_ONLY operational events могут использоваться для infrastructure/readiness validation, но не backfill в новый prospective primary cohort.
- P2 prospective outcomes/performance остаются закрыты до frozen sample/time gates; Candidate V2/API/RLS не открывать без roadmap основания.

---

## 2026-09-11 / 2026-09-12 UTC addendum — eight-league MARKET_ONLY readiness and common T0

Status: **CLOSED / 8-OF-8 LIVE-PROVEN / COMMON MARKET_ONLY CAPTURE ACTIVE AFTER T0**.

### Paid/manual eight-league pass

Пользователь явно разрешил исходный bounded pass командой «запускай 8 лиг». Итоговый свежий набор 2026-09-11:
- EPL `20`;
- LA_LIGA `20`;
- SERIE_A `20`;
- BUNDESLIGA `18`;
- LIGUE_1 `18`;
- EREDIVISIE `19`;
- TURKEY_SUPER_LIG `9`;
- PRIMEIRA_LIGA `9`;
- всего `133` provider events.

The Odds API quota прошла `193 -> 185`: суммарная стоимость pass = `8` credits. Production model не изменён. Этот набор является bootstrap/readiness proof для общего восьмилигового контракта и **не** включается в новый common cohort задним числом.

### Closing PR chain

- PR #254 — Turkey/Portugal quota gate: удалён stale internal floor `500`; scheduler переведён на shared hard reserve `100` + полный двухкредитный envelope, effective minimum `102`; merge `b2b027944872571eb1745bcc72de1e5a4b8b4675`.
- PR #255 — La Liga temporal canonicality + zero-cost ledger catch-up; merge `0b9adaafca8b8501ba2c994a16c2dd7e2c4120a3`. Live audit обнаружил `13` duplicated temporal identities / `19` extra structural reconstructions / `0` market-state conflicts. При structural-only drift сохраняется первая durable observation; market drift под той же temporal identity fail-closed.
- PR #256 — deterministic all-leagues capture completeness gate; merge `c18a6fdc564ad62e95c6e888c35137af061349e2`. Gate network-free, работает по canonical provider event IDs, `MISSING/UNEXPECTED` fail-closed, raw DB row count не является coverage proof.
- PR #257 — EPL newest-first Supabase window; merge `0a9e5ec648fae1b0917cd5465ed63d46b23ca157`. Исправлен PostgREST capped-window failure mode: market shadow читает newest-first, затем локально восстанавливает chronological order.
- PR #258 — zero-cost EPL ledger catch-up; merge `ab96dc72c8102094117aff667ed993af18281e68`; push run `34665769480`, job `103477214341`. Workflow использовал только Supabase secrets, без Odds API credential; записал `20` новых EPL durable observations и `20` canonical predictions. Parity audit: `future_orphan_snapshot_rows=0`, `critical_failures=0`.
- PR #259 — frozen common eight-league protocol `ALL_LEAGUES_MARKET_ONLY_V1`; merge/T0 `663806f6f57aa4faba6b303e6952f86d163892db`.

### Final live readiness proof

После EPL zero-cost catch-up read-only Supabase proof подтвердил exact fresh odds/ledger parity по всем восьми лигам:
- BUNDESLIGA `18/18`;
- EPL `20/20`;
- EREDIVISIE `19/19`;
- LA_LIGA `20/20`;
- LIGUE_1 `18/18`;
- PRIMEIRA_LIGA `9/9`;
- SERIE_A `20/20`;
- TURKEY_SUPER_LIG `9/9`.

Итого: `133/133` fresh event IDs имеют canonical MARKET_ONLY ledger запись; `bad_timing=0` во всех восьми лигах; `non_market_only=0` во всех восьми лигах. La Liga/EPL recovery не делали новых provider requests и не тратили дополнительные credits. Production `.pkl` не изменён.

### Common T0 / no-peek contract

- `T0_COMMIT = 663806f6f57aa4faba6b303e6952f86d163892db`.
- `T0_UTC = 2026-09-12T01:51:19Z`.
- Общий cohort `ALL_LEAGUES_MARKET_ONLY_V1` начинается **строго после** `T0_UTC`.
- 133 rows от 2026-09-11 остаются readiness/bootstrap evidence и не backfill в common cohort.
- `expected_event_ids` для completeness должны быть frozen **до persistence-completeness evaluation** из authoritative pre-kickoff provider/fixture manifest и не могут копироваться из уже сохранённых `odds_snapshots`; circular completeness запрещён.
- Capture = `MARKET_ONLY`, `structural_applied=false`, exact immutable provenance, prediction/snapshot strictly pre-kickoff.
- Outcome/result source нельзя читать для решения capture/exclusion/retry/relabelling или tuning до applicable frozen evaluation gate.
- Этот protocol не даёт paid-provider permission; paid refresh остаётся manual-only с existing budget guards.
- После разрешённого evaluation gate frozen metrics: multiclass log loss, multiclass Brier score, 1X2 argmax accuracy — per league + pooled; более строгий existing league-specific gate всегда имеет приоритет.
- Production promotion остаётся отдельным explicit/manual decision и не следует автоматически из research evidence.

### Execution pointer override after eight-league activation

Этот addendum является самым свежим execution pointer и переопределяет stale status выше только там, где статус изменился.

- `ALL_LEAGUES_MARKET_ONLY_V1 = CAPTURE_READY / ACTIVE AFTER T0`.
- Общая eight-league MARKET_ONLY infrastructure readiness = **CLOSED / 8-OF-8 LIVE-PROVEN**.
- Следующая работа по этому common cohort: только future capture строго после T0 с no-peek, immutable provenance и non-circular completeness manifest.
- Common cohort не оценивать до отдельно применимого frozen sample/time evaluation gate; interim outcome/performance peeking запрещён.
- Existing `EPL_AI_MARKET_PAIR_V1` остаётся отдельным frozen EPL AI-vs-market experiment и не расширяется/backfill этим common market-only cohort.
- P2 outcome/performance blocks остаются gated.
- Любой следующий реальный paid refresh требует отдельного explicit permission; сам T0/protocol такого разрешения не создаёт.

---

## 2026-09-12 addendum — 127-event all-leagues successor seed freeze

Status: **FROZEN / 127-SEED LIVE-PROVEN BEFORE FIRST KICKOFF / FUTURE CAPTURE ACTIVE**.

После активации консервативного `ALL_LEAGUES_MARKET_ONLY_V1` read-only проверка показала, что из 133 readiness events только 6 матчей 2026-09-11 уже успели начаться, а 127 матчей всё ещё были полностью future относительно нового freeze. Чтобы не терять эти валидные untouched predictions, V1 не переписывался: создан отдельный successor protocol `ALL_LEAGUES_MARKET_ONLY_V1_1`.

Frozen successor facts:
- original V1 T0 = `2026-09-12T01:51:19Z`;
- V1.1 freeze = `2026-09-12T02:04:34Z`;
- first seed kickoff = `2026-09-12T12:00:00Z`;
- seed membership = exact 127 immutable `prediction_key` values in `research/ALL_LEAGUES_MARKET_ONLY_V1_1_MANIFEST.json`;
- league counts = BUNDESLIGA `17`, EPL `20`, EREDIVISIE `18`, LA_LIGA `19`, LIGUE_1 `17`, PRIMEIRA_LIGA `9`, SERIE_A `19`, TURKEY_SUPER_LIG `8`;
- six already-started 2026-09-11 matches remain excluded and must never be backfilled into V1.1.

Scientific guard:
- no outcome/result/settlement source was read to select, filter, rank or relabel the 127 seed events;
- all 127 exact keys already existed immutably before their kickoffs;
- read-only live proof at `2026-09-12 02:09:06 UTC`: `127` immutable keys, `8` leagues, first kickoff `12:00 UTC`, `mode_violations=0`, `timing_violations=0`;
- V1 remains frozen historical provenance; V1.1 is a successor, not a retroactive edit;
- future V1.1 membership = exact 127-key seed + qualifying MARKET_ONLY captures created after V1.1 freeze;
- paid provider permission is unchanged/manual-only;
- interim outcome/performance peeking remains forbidden;
- production `.pkl` remains outside this path.

PR/CI/merge proof:
- PR #261 exact head `31ca44ce457dca5a2d229f8c578a05cb93563cbd`;
- all 5 PR validation workflows green, including expanded `tests/test_all_leagues_prospective_protocol.py` and production-artifact guard;
- exact-head merge `ba3a99be3a8710b54fa3f85a160aae5238844050` at `2026-09-12T02:09:34Z`, still ~9h50m before first seed kickoff.

### Execution pointer override after V1.1 freeze

Этот раздел является самым свежим execution pointer для common eight-league MARKET_ONLY cohort.

- `ALL_LEAGUES_MARKET_ONLY_V1` остаётся frozen historical predecessor.
- `ALL_LEAGUES_MARKET_ONLY_V1_1 = FROZEN / 127-SEED + FUTURE CAPTURE`.
- Common cohort currently starts with `127` untouched pre-kickoff MARKET_ONLY predictions across all 8 leagues.
- Следующие новые common observations добавляются только future-only после `2026-09-12T02:04:34Z` и должны пройти исходные V1 no-peek/identity/completeness rules.
- Шесть матчей 2026-09-11 не входят в V1.1.
- До applicable frozen evaluation gate читать outcomes/performance для common cohort запрещено.
- Любой следующий paid odds refresh требует отдельного explicit permission; V1.1 freeze его не даёт.
