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

## P1 — параллельная работа, только когда P0 item реально gated

### P1-A. SportsGameOdds bookmaker-corner capability — EXTERNAL_CREDENTIAL_GATE

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
- workflow_dispatch only;
- exact Union Berlin–Schalke target;
- requested odd ids `cornerKicks-all-game-ou-over/under`;
- max 1 authenticated provider request;
- capability только при same-bookmaker Over+Under на одной numeric line с явными prices;
- no Supabase writes;
- no production `.pkl` changes.

Следующий шаг требует отдельного явного разрешения на внешний credential/live probe. Generic «продолжай» этого не разрешает.

Fallback order при miss/access failure: SportsGameOdds -> Sportmonks -> Betfair Exchange.

### P1-B. Outcome-free health всех frozen experiments — ACTIVE / FREE

Когда P0-A или P1-A blocked manual/external gate:
- проверять только metadata/sample health;
- identity conflicts;
- cutoff/freshness;
- settlement availability;
- workflow health;
- production hashes;
- никакого premature outcome evaluation.

### P1-C. Multi-league portability / operational coverage — ACTIVE

Цель: доказать, что проект строит football signals, а не только EPL-specific model.

Основные лиги/контуры уже включают EPL, La Liga, Serie A, Bundesliga, Ligue 1, Eredivisie.

Что важно:
- league-aware identity;
- season robustness;
- calibration by league;
- market-relative performance;
- drift differences;
- переносимость сигналов.

Не расширять число лиг само по себе без research/operational цели.

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

**Primary item: `P0-A Prospective data acquisition / market freshness` — `MANUAL_PAID_GATE`.**

Текущая ситуация после fresh pass 2026-09-09:
- P0-A free/read-only status + quota proof завершён;
- snapshots всё ещё stale с 2026-09-05;
- fresh queue = 23 actionable due paths (`SERIE_A 8 / LA_LIGA 5 / EPL 10`);
- priority = **SERIE_A -> LA_LIGA -> EPL**;
- fresh top path = **Torino vs Napoli**;
- quota = `193 remaining / 307 used / last_cost 0`, hard reserve `100`;
- actual paid h2h refresh остаётся `MANUAL_PAID_GATE` и не запускался;
- P0-B outcome-free health = `HEALTHY / 12/100 / TIME-FROZEN_GATE`;
- P0-C outcome-free trajectory health = `68 raw frozen event ids / 1 kickoff month per league / DATA-GROWTH + P0-A FRESHNESS GATED`.

Что делать дальше по roadmap:
1. Без отдельного paid permission P0-A остаётся на `MANUAL_PAID_GATE`; не запускать paid collector автоматически.
2. Продолжать только safe outcome-free collection/health P0-B и P0-C, сохраняя no-peek contract.
3. При отдельном явном разрешении пользователя на paid h2h refresh вернуться к P0-A, сначала пересчитать fresh priority/quota, затем выполнить минимальный controlled refresh с existing guards и post-refresh live proof.
4. Не переходить к SportsGameOdds, новым features, Candidate V2, API refactor или RLS, пока roadmap ordering не даёт для этого основания.

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
- P0-C outcome-free trajectory health: frozen raw universe `68` event ids (`EPL 20 / LA_LIGA 24 / SERIE_A 24`), только 1 kickoff month на лигу; activation `100 + 4 months` не достигнут; 23 trajectory paths refresh-due; outcomes не читались.
- Весь pass был read-only относительно Supabase и outcome-free; paid provider requests/credits = `0/0`; production model не изменён.
- Post-merge live recheck at `2026-09-09 16:16:03 UTC` confirmed P0-A still has no snapshots newer than `2026-09-05 15:21:32.513020 UTC` and P0-B remains `12/100`; corrected authoritative P0-B metadata is last kickoff `2026-09-14 19:00 UTC` and model SHA256 `1e516fe91420fdc2d6479e9fb92b005c4a0c75c7f0f217493dd6b27fd64d99a5`.