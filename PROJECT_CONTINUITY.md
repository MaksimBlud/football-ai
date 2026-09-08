# Football AI — Project Continuity

Этот файл — постоянная рабочая память проекта между чатами. Фактический source of truth всегда свежий GitHub `main` + live Supabase.

## Как пользоваться

Перед новой рабочей сессией:
1. Прочитать этот файл.
2. Коротко сверить свежий `main` и live Supabase.
3. Не повторять полный аудит без конкретной причины.
4. Продолжить с раздела **Текущий следующий шаг**.
5. После существенного решения, PR, merge или live-proof обновить этот файл.

## Стиль и приоритет работы

- Объяснять пользователю простым языком: что сделали, что выяснили, почему важно, что дальше.
- Приоритет: **максимально развивать проект без лишней технической дрочки**.
- Инфраструктуру менять только когда она снимает реальный blocker, защищает данные/production или ускоряет research.
- Без запроса подтверждения после каждого безопасного шага; останавливаться только на реальном safety/manual-paid gate.

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
- Paid-provider workflows остаются manual-only. Priority/readiness report никогда не является разрешением на расход credits.
- Реальные баги закрывать regression-тестами.
- Fail-closed red не превращать искусственно в green.
- Если point-in-time history нельзя честно восстановить, не делать retrospective production replay.

## Активные frozen / operational контуры

### EPL_AI_MARKET_PAIR_V1

Режим **collect, don't peek**.

- Frozen cohort = первые 100 eligible prospective events.
- Outcomes запрещены до 100 событий.
- Затем минимум 24h после kickoff последнего события cohort.
- Дополнительный embargo до `2026-11-01 12:16:54 UTC`.
- Никакого interim primary evaluation или performance-based optional stopping.

Свежий outcome-free status run `34222168180` (2026-09-08):
- collected events = **12/100**;
- remaining = 88;
- future snapshot events = 10;
- unpaired future snapshot events = 0;
- `collection_status=DEFER_PAID_REFRESH`;
- reason = `ALL_KNOWN_FUTURE_SNAPSHOT_EVENTS_ALREADY_PAIRED`;
- latest snapshot `2026-09-05T15:19:42Z`;
- `automatic_paid_calls=false`;
- `paid_refresh_recommended=false`;
- outcome reads = 0.

Вывод: EPL paired cohort сейчас не сломан. Stale market data ухудшает свежесть траектории, но все известные future events уже paired; отдельный EPL paid refresh только ради pair-count сейчас не нужен.

### PROSPECTIVE_CORNERS10_INCREMENTAL_V1

- Вопрос: добавляет ли `CORNERS10` prospective 1X2 информацию сверх market baseline.
- Historical incremental evidence против рынка было неблагоприятным; это confirmation, не tuning.
- Bookmaker corner capability должен быть доказан отдельно.
- До activation sample не eligible, outcome scoring запрещён.
- Frozen minimum: 100 settled eligible fixtures на лигу + минимум 4 calendar months.
- Этот контракт нельзя ускорять задним числом.

### PROSPECTIVE_MARKET_PATH_V1

- Используется полная pre-cutoff market trajectory.
- Deterministic schedule revisions quarantined и исключены из frozen sample.
- Paid h2h refresh manual-only.
- Перед любым платным refresh: бесплатный league-level priority + fresh quota proof + existing budget/safety guards.
- Прошедший cutoff нельзя backfill.

Свежий outcome-free sample-growth run `34222392771`:
- EPL settled **10/100**;
- La Liga settled **10/100**;
- Serie A settled **9/100**;
- у каждой лиги пока только 1 календарный месяц;
- valid test blocks = 0;
- settlement late = 0;
- outcome-performance evaluation не запускалась.

Вывод: sample здоров, но ещё ранний. Settlement больше не blocker; главный operational bottleneck — дальнейший рост свежей market trajectory.

## CORNERS — historical/free-data block CLOSED

Важно различать:
- `CORNERS10` = football-state feature для 1X2;
- corner-total research = прогноз числа/тотала угловых;
- bookmaker corner market = отдельный внешний источник.

### SEASON_INVARIANT_CORNERS_V1 — PORTABLE_STRONG

Held-out `CORNERS10` vs `GOALS10`:
- EPL 6/7 seasonal wins;
- La Liga 5/7;
- Serie A 7/7;
- всего 18/21 по основным метрикам.

Вывод: угловые несут устойчивую football-state информацию через сезоны и лиги. Но historical `MARKET + CORNERS10` не улучшил market baseline в среднем, поэтому дополнительный bookmaker 1X2 edge не доказан.

Early drift historical guide:
- 20 матчей слишком шумно;
- ~40 = early warning;
- ~80 = серьёзная drift check.

PR #212 merge `f72952be44249cceceb6a81cb6ff02d885e588ff`.

### CORNER_TOTAL_SIGNAL_V1 — NOT_PORTABLE_TOTAL_SIGNAL

2019/20–2025/26, 2581 held-out matches:
- weighted delta MAE `+0.040076` vs historical mean;
- wins 2/7;
- Over 9.5 AUC ~`0.5053`.

PR #214 merge `92633e3f011146a533b3cdce1ab26080efe1b139`.

### CORNER_TOTAL_CALIBRATED_V2 — PORTABLE_CALIBRATED_TOTAL_SIGNAL

- weighted delta MAE ~`-0.007791`;
- wins 6/7;
- slopes ~0.03–0.24: recent-corner estimate требует strong shrink к среднему;
- Over 9.5 AUC всё ещё ~`0.5053`.

Вывод: небольшой portable signal для среднего expected corner count есть, но устойчивого выбора конкретных Over/Under матчей нет.

PR #215 merge `8e206f4e97f8b5d0e64bc2951716ad8d971def61`.

### CORNER_PRESSURE_SIGNAL_V3 — NOT_PORTABLE_PRESSURE_DISCRIMINATOR

- all-shots AUC `0.498357`, positive 3/7;
- shots-on-target AUC `0.512793`, positive 5/7, ниже frozen 0.52.

PR #216 merge `95386fffb6b386efa26feb0ad4860135ded99257`.

### CORNER_COMBINED_DISCRIMINATOR_V4 — NOT_PORTABLE_COMBINED_DISCRIMINATOR

Fixed inputs: corner-state + all-shots pressure + SOT pressure.
- weighted AUC `0.501691`;
- positive 3/7;
- frozen pass = AUC >0.52 и >=5/7.

**STOP RULE:** не перебирать новые windows/weights/thresholds/combinations на тех же historical seasons.

Итог: угловые = устойчивый state signal; маленький calibrated expected-count signal есть; bookmaker edge, Over/Under selector и bookmaker-corner edge не доказаны. Следующая meaningful evidence должна прийти из новых bookmaker lines/prices или richer event/territorial data.

PR #217 merge `9bb1e8ed244e10f53d87850cb552aa70e148e0eb`.

## Bookmaker corner capability

Stored bookmaker corner-line evidence = 0.

### Preregistered target

- League: `BUNDESLIGA`.
- Match: Union Berlin vs FC Schalke 04.
- Kickoff: `2026-09-11T18:30:00Z`.
- event_id: `115c6679a72c5a360640b6baaa16e78c`.
- Zero-cost rollover run `34112118221`, artifact `10014773586`.
- ZIP SHA256 `6b34164dc659bf438eea66d989890d0bfb12c8429a18f9d677af3fea4455aa7e`.
- 17 stored snapshots, exactly one identity, conflict=0.
- Observed paid capability-probe attempts before activation = 0.

PR #219 merge `46cdd4d4bd4cdcd4dd9d4d07d795d868727feb3f` — inactive target preregistered.
PR #221 merge `d14465600d7a4f02280afa3561568960789ef4a9` — zero-attempt proof recorded.

### Fresh quota proof — CLOSED / READY

Scheduled `Multi-Market V2 Readiness Status` run `34210743251`:
- remaining = **193** credits;
- used = 307;
- zero-cost quota request `last_cost=0`;
- `quota_ready=true`;
- threshold = 104 = hard reserve 100 + complete first event worst-case 4;
- corner capability probe cap = max 1 paid request / max 2 credits;
- readiness paid requests/credits = 0;
- writes = false;
- production model unchanged;
- artifact `10049695923`;
- ZIP SHA256 `7f9085ddb4142bd53910a7baa4ea62134e17240981ec20c2439ec6ac06d07aed`.

### PR #227 — target activation CLOSED / LIVE-PROVEN

PR #227 switched the probe from expired Getafe–Celta to the exact previously preregistered Union Berlin–Schalke target. It did **not** call the paid provider.

Merge: `1b219e1f8dce3789dfb8efff2783ae2826846d2d`.

Safety preserved:
- probe remains `workflow_dispatch` only;
- no schedule/push trigger;
- max 1 paid request / max 2 credits;
- fresh runtime quota preflight remains mandatory;
- hard reserve 100 remains mandatory;
- exact target/prospective checks remain mandatory;
- no Supabase writes;
- no production `.pkl` changes.

CI #227 found two stale activation/rollover contracts and both were fixed without bypassing safety:
1. rollover expiry regression no longer hardcodes the old Getafe target; synthetic expired target is injected only for the test, while live planner still uses real `TARGET`;
2. activation regression now requires active probe target to equal the exact preregistered V2 target while preserving immutable historical Getafe provenance.

Final exact head `f7d7705ab5471e2967c67fcceea9c092732980e7` passed all PR workflows.

Post-merge:
- free/read-only Readiness run `34234965186` success;
- free/read-only Rollover run `34234965230` success;
- production model unchanged;
- **paid `Multi-Market Corner Capability Probe` did not auto-start**.

### Multi-Market V2 current state

Outcome-free Multi-Market V2 Cycle run `34222152574` confirmed:
- infrastructure collection ready = true;
- schema ready = true;
- corner-result sources ready for configured leagues = true;
- quota 193, hard reserve 100;
- stored corner capability evidence = 0;
- reviewed capability attestation = absent;
- action = `NOOP_BLOCKED`;
- collection called = false;
- paid requests/credits = 0;
- **only blocker = `PROVIDER_CORNER_CAPABILITY_UNPROVEN`**.

Вывод: бесплатными/read-only проверками corner capability доведён до реальной внешней границы. Следующее новое знание возможно только через отдельный manual-only capability probe.

## Settlement / public results — CLOSED / LIVE_PROVEN

Football-Data current-season CSV (`SP1.csv`, `I1.csv`) давал HTTP 503 и блокировал La Liga/Serie A settlement.

Решение:
- Football-Data остаётся primary;
- ESPN keyless scoreboard = fallback only after bounded transient exhaustion;
- strict completed/score/date/team/duplicate validation;
- schema/identity ошибки не маскируются;
- оба public source недоступны => `SOURCE_UNAVAILABLE`, no writes;
- paid provider requests = 0.

PR #223 merge `5befc9d53a0382a6178436ee55518a279c560e15`.
Live proof выявил alias `Deportivo` и Serie A workflow import-path defect; оба закрыты regression’ами в PR #224.

PR #224 merge `382814a00f1c04dbff776c0a5594b3c98909fe9a`.

La Liga run `34180001408`:
- 3x503 -> ESPN 1 request;
- canonical inserted 10, conflicts 0;
- paid 0; production unchanged.

Serie A run `34180001418`:
- 3x503 -> ESPN 1 request;
- inserted 19, conflicts 0;
- paid 0; production unchanged.

Independent proof:
- all 13 identities that had been `SETTLEMENT_LATE` are now present: LL 7/7, SA 6/6;
- rerun settlement-lag: EPL late 0, La Liga late 0, Serie A late 0;
- no outcome scores read in lag audit, no writes, production unchanged.

## Market acquisition freshness — ZERO-COST STATUS 2026-09-08

Snapshots remain stale since 2026-09-05:
- EPL latest ~15:19Z;
- La Liga latest ~15:21Z;
- Serie A latest ~15:08Z.

Latest outcome-free coverage run `34222399149`:
- **EPL:** 20 fixtures seen, 20 ready, 10 manual-refresh-due, irrecoverable/conflict 0;
- **La Liga:** 24 seen, 15 ready, 5 manual-refresh-due, 5 quarantined revisions, irrecoverable/conflict 0;
- **Serie A:** 24 seen, 21 ready, **12 manual-refresh-due**, irrecoverable/conflict 0.

Existing PR #210 priority logic remains authoritative:
1. **Serie A #1**;
2. **La Liga #2**;
3. **EPL #3**.

Important nuance from EPL paired status: although EPL snapshots are stale, all 10 known future EPL snapshot events are already paired, so EPL pair collection itself says `DEFER_PAID_REFRESH`. Staleness primarily affects trajectory freshness, not current pair existence.

Decision: no automatic paid refresh. Paid h2h refresh is a separate manual-only intent and must never be bundled with the corner capability probe.

## Security follow-up

Read-only audit ранее нашёл RLS disabled на:
- `teams`;
- `predictions`;
- `match_statistics`;
- `league_prediction_ledger`;
- `epl_ai_market_pair_ledger`.

Не включать RLS автоматически; сначала отдельный access-policy audit, иначе можно сломать приложение/research.

## Текущий следующий шаг

1. Corner activation считать **CLOSED / LIVE-PROVEN**.
2. Free/read-only corner work исчерпан до external capability evidence. Actual `Multi-Market Corner Capability Probe` остаётся **manual-only paid action** и автоматически не запускается.
3. Если пользователь явно разрешит paid corner probe: runtime снова проверяет quota/reserve; максимум 1 request / 2 credits. После результата сначала durable artifact + reviewed attestation, затем новый preregistered bookmaker-line-vs-V2 research block.
4. Если capability miss: зафиксировать negative proof и искать другой bookmaker/event source; не возвращаться к historical V1–V4 mining.
5. Market-path sample health: EPL 10/100 settled, La Liga 10/100, Serie A 9/100; late=0. Продолжать outcome-free monitoring без premature evaluation.
6. EPL AI-vs-Market pair cohort: 12/100, все известные future snapshot events уже paired; не тратить credits только ради pair-count.
7. Market acquisition staleness остаётся operational blocker для свежести trajectory; manual h2h priority = Serie A -> La Liga -> EPL, но paid action требует отдельного явного разрешения.
8. Пока paid actions не разрешены, следующий полезный бесплатный follow-up — read-only RLS/access-policy audit и остальные source/collection health checks, не затрагивающие frozen outcomes.

## Журнал ключевых решений

### 2026-09-07

- Создан `PROJECT_CONTINUITY.md`; решения должны сохраняться между чатами.
- Принят season-invariant research principle: historical portability first, fresh data as independent confirmation/drift monitor; existing frozen gates сохранены.
- Historical corner V1–V4 закрыты; включён STOP RULE против same-data feature mining.
- Bookmaker corner capability оставлен external manual gate.
- Зафиксирован отдельный RLS follow-up.

### 2026-09-08

- Приоритет подтверждён: развивать проект без лишней технической дрочки.
- ESPN выбран как keyless settlement fallback-only; Football-Data сохранён primary.
- PR #224 live-proven: La Liga +10 canonical results, Serie A +19, conflicts=0, paid=0; settlement late=0.
- Zero-cost acquisition audit подтвердил staleness с 2026-09-05; priority Serie A -> La Liga -> EPL.
- Fresh zero-cost quota proof: 193 credits, quota-ready, hard reserve 100, paid=0.
- PR #227 активировал заранее зарегистрированный Union Berlin–Schalke target без paid provider call; post-merge paid probe не автостартовал.
- Outcome-free market-path sample health: EPL 10/100, La Liga 10/100, Serie A 9/100; late=0.
- EPL AI-vs-Market pair status: 12/100; 10 future snapshot events already paired; paid refresh deferred.
- Multi-Market V2 free cycle подтвердил единственный remaining blocker: `PROVIDER_CORNER_CAPABILITY_UNPROVEN`.
