# Football AI — Project Continuity

Этот файл — постоянная память проекта между чатами. Фактический source of truth всегда свежий GitHub `main` + live Supabase.

## Как пользоваться

Перед новой рабочей сессией:
1. Прочитать этот файл.
2. Коротко сверить свежий `main` и live Supabase.
3. Не повторять полный аудит без конкретной причины.
4. Продолжить с раздела **Текущий следующий шаг**.
5. После существенного решения, PR, merge или live-proof обновить этот файл.

## Стиль и приоритет работы

- Объяснять пользователю простым языком: что сделали, что выяснили, почему важно, что дальше.
- Приоритет пользователя: **максимально развивать проект без лишней технической дрочки**.
- Инфраструктуру менять только когда она снимает реальный blocker, защищает данные/production или ускоряет research.
- Без запроса подтверждения после каждого безопасного шага; останавливаться только на реальном safety/manual-paid gate.

## Постоянные правила

- Repo: `MaksimBlud/football-ai`, branch `main`.
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
- Последнее известное состояние было около `12/100`; перед использованием обновлять только metadata без чтения outcomes.

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
- Settlement и market acquisition — разные контуры: settlement восстановлен, market snapshots остаются stale.

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

PR #217 merge `9bb1e8ed244e10f53d87850cb552aa70e148e0eb`.

Итог по historical corners: угловые = устойчивый state signal; маленький calibrated expected-count signal есть; bookmaker edge, Over/Under selector и bookmaker-corner edge не доказаны. Следующая meaningful evidence должна прийти из новых bookmaker lines/prices или richer event/territorial data.

## Bookmaker corner capability

Stored bookmaker corner-line evidence = 0.

### Preregistered target

- League: `BUNDESLIGA`.
- Match: Union Berlin vs FC Schalke 04.
- Kickoff: `2026-09-11T18:30:00Z`.
- event_id: `115c6679a72c5a360640b6baaa16e78c`.
- Zero-cost rollover run `34112118221`, artifact `10014773586`.
- Artifact ZIP SHA256 `6b34164dc659bf438eea66d989890d0bfb12c8429a18f9d677af3fea4455aa7e`.
- 17 stored snapshots, exactly one identity, conflict=0.
- Observed paid capability-probe attempts before activation = 0.

PR #219 merge `46cdd4d4bd4cdcd4dd9d4d07d795d868727feb3f` — inactive rollover target preregistered.
PR #221 merge `d14465600d7a4f02280afa3561568960789ef4a9` — zero-attempt proof recorded.

### Fresh quota proof — CLOSED / READY

Scheduled `Multi-Market V2 Readiness Status` run `34210743251` completed successfully on 2026-09-08:

- remaining = `193` credits;
- used = `307`;
- zero-cost `/sports/` quota request `last_cost=0`;
- `quota_ready=true`;
- readiness threshold = `104` = hard reserve 100 + complete first event worst-case 4;
- hard reserve = 100;
- corner capability probe cap = max 1 paid request / max 2 credits;
- readiness paid provider requests = 0, paid credits = 0;
- `writes_performed=false`;
- production model hash unchanged;
- artifact `10049695923`;
- artifact ZIP SHA256 `7f9085ddb4142bd53910a7baa4ea62134e17240981ec20c2439ec6ac06d07aed`.

Infrastructure readiness is green. Provider corner capability remains unproven.

### PR #227 — target activation CLOSED / MERGED

PR #227 switched the paid probe target from expired Getafe–Celta to the previously preregistered Union Berlin–Schalke target. It did **not** call the paid provider.

Merge: `1b219e1f8dce3789dfb8efff2783ae2826846d2d`.

Safety preserved:
- probe remains `workflow_dispatch` only;
- no `schedule` or `push` trigger for the paid probe;
- max paid requests = 1;
- max paid credits = 2;
- fresh runtime quota preflight remains mandatory;
- hard reserve 100 remains mandatory;
- exact target/prospective identity checks remain mandatory;
- no Supabase writes;
- no production `.pkl` changes.

CI found two stale regression contracts during activation; neither was bypassed:

1. `Multi-Market Probe Rollover Status` still assumed the old Getafe target when testing an expired active target. Fix: rollover planner keeps the real current target by default, while tests/audits may inject an explicit synthetic expired target. Auto-switching remains disabled.
2. `Multi-Market V1/V2 PR Validation` still asserted that the preregistered rollover target must differ from the active target. That was correct before activation but wrong inside the separate activation PR. Fix: historical Getafe provenance stays immutable, while the active probe must now equal the exact previously preregistered V2 target. The preregistration file itself still cannot authorize a paid request.

Final exact head `f7d7705ab5471e2967c67fcceea9c092732980e7` passed all PR workflows, including Research PR Validation and production artifact guard.

Post-merge proof on `main`:
- only free/read-only `Multi-Market V2 Readiness Status` run `34234965186` and `Multi-Market Probe Rollover Status` run `34234965230` auto-started;
- both completed successfully;
- production model unchanged;
- **paid `Multi-Market Corner Capability Probe` did not auto-start**.

### Manual capability probe — CLOSED / CAPABILITY_MISS

User-authorized manual `Multi-Market Corner Capability Probe` run `34246732050` completed successfully on 2026-09-08 against the exact preregistered Union Berlin–Schalke target.

Observed provider result:
- status = `CAPABILITY_MISS`;
- provider request attempted = true;
- paid provider requests = 1;
- paid provider credits = `0`;
- quota before = remaining 193 / used 307 / last_cost 0;
- quota after = remaining 193 / used 307 / last_cost 0;
- corner market keys = `[]`;
- corner bookmaker count = `0`;
- target_verified = true;
- writes_performed = false;
- production model hash unchanged.

Artifact:
- id `10064303200`;
- ZIP SHA256 `5a7de8b02e1b82a29dc71c2a8a94c6154a2485bbaa32dd30d8bd6d0ef78a0cfa`.

Decision: The Odds API corner capability path for this exact target is a clean negative proof. Do not repeat the same probe against the same target. Historical corner V1–V4 remain closed.

Zero-cost source audit selected **Sportmonks** as the primary next candidate because its official market catalog explicitly includes `Alternative Corners` market id `69`, and its pre-match odds API supports fixture+market retrieval. Its forever-free token is limited to Scottish Premiership and Danish Superliga, so free coverage may be used only for capability/schema proof; any paid league coverage remains a separate explicit decision. `CORNER_MARKET_SOURCE_AUDIT_20260908.md` records the source audit. OpticOdds remains secondary because documentation proves rich corner statistics and market discovery, but not yet an equally direct zero-cost bookmaker-corner-odds proof.

## Settlement / public results

### PROVIDER_FREE_RESULTS_FALLBACK_V1 — CLOSED / LIVE_PROVEN

Problem: Football-Data current-season CSV (`SP1.csv`, `I1.csv`) repeatedly returned HTTP 503 and blocked La Liga/Serie A settlement.

Operational solution:
- Football-Data remains primary;
- ESPN keyless soccer scoreboard = fallback only after bounded transient primary exhaustion;
- La Liga `esp.1`, Serie A `ita.1`;
- only explicit `completed=true` events;
- strict score/date/home-away/team/duplicate validation;
- immutable project persistence/conflict guards remain authority;
- unknown/malformed/schema identity fails closed;
- primary validation/schema errors are never masked;
- both public sources unavailable => `SOURCE_UNAVAILABLE`, no writes;
- paid provider requests always 0.

OpenFootball/footballcsv were rejected for live settlement because current Serie A data was stale.

PR #223 merge `5befc9d53a0382a6178436ee55518a279c560e15` added the fallback. Live proof correctly exposed ESPN alias `Deportivo` and a Serie A workflow import-path defect; both failed closed with no harmful writes.

PR #224 merge `382814a00f1c04dbff776c0a5594b3c98909fe9a` closed both regressions.

**La Liga live run `34180001408`**
- primary 3x HTTP 503 -> ESPN fallback 1 request;
- source/finished rows 41/41;
- legacy inserted 10, unchanged 31;
- canonical inserted 10, unchanged 36, conflicts 0;
- paid requests 0;
- production hash unchanged.

**Serie A live run `34180001418`**
- primary 3x HTTP 503 -> ESPN fallback 1 request;
- source/finished rows 30/30;
- inserted 19, unchanged 11, conflicts 0;
- paid requests 0;
- evaluator saw 30 result rows / 19 settled fixtures;
- no production model changes.

Independent live proof:
- canonical current-season results: La Liga 46, Serie A 30, latest date 2026-09-07;
- all 13 identities that were previously already `SETTLEMENT_LATE` are now present: La Liga 7/7, Serie A 6/6, missing=0;
- rerun of the same settlement-lag audit became green: EPL late 0, La Liga late 0, Serie A late 0; no scores read, no writes, production unchanged.

Conclusion: Football-Data 503 settlement blocker is removed.

Non-blocking follow-up: La Liga-specific PR validator did not trigger on PR #224 common fallback/test path set. Add those paths next time that workflow is naturally touched; do not prioritize this over research.

## Market acquisition freshness — ZERO-COST AUDIT 2026-09-08

Settlement восстановлен, но `odds_snapshots` acquisition остаётся stale.

Read-only audit:
- **EPL:** latest snapshot `2026-09-05 15:19:42Z`, future event_ids 10; next kickoff `2026-09-12 14:00Z`.
- **La Liga:** latest `2026-09-05 15:21:32Z`, future event_ids 14; next kickoff `2026-09-11 19:00Z`.
- **Serie A:** latest `2026-09-05 15:08:05Z`, future event_ids 14; next kickoff `2026-09-11 18:45Z`.

Использована существующая PR #210 логика `prospective_market_path_refresh_priority.py`, а не новый policy. PR #210 merge `9265d90bb7c1eca806a86be874832517d694c35f`.

Current zero-cost priority:
1. **SERIE_A #1:** 12 due paths, earliest due cutoff ~82.17h.
2. **LA_LIGA #2:** 5 due paths, earliest due cutoff ~82.42h; staleness relative to fixed 2h cadence особенно высокая.
3. **EPL #3:** 10 due paths, earliest due cutoff ~101.42h.

Historical pre-cutoff coverage already exists; проблема — отсутствие **свежих** snapshots перед будущими cutoff.

Decision: priority report is not permission to spend. Paid h2h refresh remains a separate manual-only intent and must not be bundled with the corner capability probe.

## Security follow-up

Read-only audit ранее нашёл RLS disabled на:
- `teams`;
- `predictions`;
- `match_statistics`;
- `league_prediction_ledger`;
- `epl_ai_market_pair_ledger`.

Не включать RLS автоматически; сначала отдельный access-policy audit, иначе можно сломать приложение/research.

## Текущий следующий шаг

1. The Odds API corner capability probe считать **CLOSED / CAPABILITY_MISS**: run `34246732050`, exact target verified, corner markets/bookmakers = 0, provider requests 1, credits 0, quota осталось 193, writes=false, production unchanged.
2. Не повторять тот же The Odds API probe на Union Berlin–Schalke и не возвращаться к historical corner V1–V4 mining.
3. Primary next corner source = **Sportmonks free-plan capability proof**. Сначала research-only implementation + mocked regression tests; live free call возможен только при наличии отдельного `SPORTMONKS_API_TOKEN`, без покупки/апгрейда подписки.
4. Для free capability proof использовать только Scottish Premiership или Danish Superliga, затем preregister exact future fixture и проверить реальный bookmaker corner line/price для documented `Alternative Corners` market id 69. Статистика corners сама по себе capability не доказывает.
5. Если Sportmonks free capability подтвердится: отдельно провести coverage/cost audit для нужных research-лиг и не покупать paid coverage автоматически. Если miss — durable negative proof и переход к следующему документированному provider, вероятно OpticOdds.
6. Отдельный market acquisition blocker остаётся: snapshots stale с 2026-09-05; paid h2h refresh manual-only, priority = Serie A #1 -> La Liga #2 -> EPL #3.
7. Пока paid actions не разрешены, продолжать бесплатные/read-only задачи: outcome-free prospective sample health, collection metadata, settlement health, source audits и free-provider capability work без premature outcome reads.
8. Frozen `EPL_AI_MARKET_PAIR_V1`, `PROSPECTIVE_MARKET_PATH_V1`, `PROSPECTIVE_CORNERS10_INCREMENTAL_V1` продолжать без premature outcome reads/backfill.
9. RLS access-policy audit — отдельный безопасный read-only follow-up после основных research/operational blockers.

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
- Scheduled readiness run `34210743251` дал fresh zero-cost quota proof: remaining 193, used 307, last_cost 0, quota_ready=true, hard reserve 100, production unchanged.
- Fresh-quota blocker закрыт; remaining capability blocker = `PROVIDER_CORNER_CAPABILITY_UNPROVEN`.
- PR #227 активировал заранее зарегистрированный Union Berlin–Schalke target без paid provider call.
- CI #227 обнаружил два stale activation/rollover regression-контракта; оба исправлены без ослабления safety и стали зелёными.
- PR #227 merge `1b219e1f8dce3789dfb8efff2783ae2826846d2d`; post-merge автоматически запустились только бесплатные Readiness/Rollover workflows; paid corner probe не стартовал.
- Manual run `34246732050` дал clean `CAPABILITY_MISS`: The Odds API не вернул corner markets/bookmakers для exact Union Berlin–Schalke target; request=1, credits=0, remaining=193, writes=false, production unchanged; artifact `10064303200`.
- Zero-cost source audit выбрал Sportmonks как primary fallback candidate: documented `Alternative Corners` market id 69 + fixture/market pre-match odds endpoint; free proof ограничить Scottish Premiership/Danish Superliga, paid expansion не автоматизировать.
