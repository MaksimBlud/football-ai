# Football AI — Project Continuity

Этот файл — постоянная память проекта между чатами. Фактический source of truth всегда свежий GitHub `main` + live Supabase.

## Как пользоваться

Перед новой сессией:
1. Прочитать этот файл.
2. Коротко сверить свежий `main` и live Supabase.
3. Не повторять полный аудит без конкретной причины.
4. Продолжить с **Текущий следующий шаг**.
5. После существенного решения, PR, merge или live-proof обновить этот файл.

## Стиль работы с пользователем

- Объяснять простым языком, без предположения знания программирования.
- Писать: что сделали, что выяснили, почему важно, что дальше.
- Приоритет: максимально развивать проект без лишней технической дрочки. Инфраструктуру менять только когда она снимает blocker, защищает данные/production или ускоряет research.

## Постоянные правила

- Repo: `MaksimBlud/football-ai`, branch `main`.
- Production `.pkl` нельзя менять как побочный эффект research/training.
- Research/training != production promotion; automatic promotion запрещён.
- Не делать mass-clean/reset/mass-format и не перетирать параллельные изменения.
- Существенные изменения: branch -> tests -> PR -> полный CI -> fresh-main -> exact-head merge -> post-merge/live proof.
- Frozen/preregistered contracts не ослаблять задним числом.
- Prospective outcomes нельзя читать до разрешённого gate.
- Максимально использовать free/read-only proof; The Odds API credits не тратить при наличии бесплатной проверки.
- Paid-provider workflows остаются manual-only.
- Реальные баги закрывать regression-тестами.
- Fail-closed red не превращать искусственно в green.
- Если point-in-time history нельзя честно восстановить, не делать retrospective production replay.

## Активные frozen / operational контуры

### EPL_AI_MARKET_PAIR_V1

Режим **collect, don't peek**.
- frozen cohort = первые 100 eligible prospective events;
- outcomes запрещены до 100 событий;
- затем минимум 24h после последнего kickoff;
- дополнительный embargo до `2026-11-01 12:16:54 UTC`;
- никакого interim primary evaluation или performance-based optional stopping.

Последнее известное состояние было около `12/100`; перед использованием обновлять только metadata без чтения outcomes.

### PROSPECTIVE_CORNERS10_INCREMENTAL_V1

- Вопрос: добавляет ли `CORNERS10` prospective 1X2 информацию сверх market baseline.
- Historical incremental evidence против market было неблагоприятным; это confirmation, не tuning.
- Bookmaker corner capability должен быть доказан отдельно.
- До activation sample не eligible, outcome scoring запрещён.
- Frozen minimum: 100 settled eligible fixtures на лигу + 4 calendar months.
- Этот контракт нельзя ускорять задним числом.

### PROSPECTIVE_MARKET_PATH_V1

- Полная pre-cutoff market trajectory.
- Deterministic schedule revisions quarantined и исключены из frozen sample.
- Paid h2h refresh manual-only.
- Перед платным refresh сначала бесплатный league-level priority check.
- Прошедший cutoff нельзя backfill.
- Market snapshots последнее время stale с 2026-09-05; это отдельный acquisition issue, не settlement issue.

## CORNERS — historical/free-data block CLOSED

Важно различать:
- `CORNERS10` = football-state feature для 1X2;
- corner-total research = прогноз числа/тотала угловых;
- bookmaker corner market = отдельный внешний источник.

### SEASON_INVARIANT_CORNERS_V1 — PORTABLE_STRONG

Held-out seasonal comparison `CORNERS10` vs `GOALS10`:
- EPL 6/7;
- La Liga 5/7;
- Serie A 7/7;
- всего 18/21 wins по основным метрикам.

Вывод: угловые несут устойчивую football-state информацию через сезоны/лиги.
Но historical `MARKET + CORNERS10` не улучшил market baseline в среднем, поэтому дополнительный bookmaker 1X2 edge не доказан.

Early drift rule of thumb from historical audit:
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
- fitted slopes ~0.03–0.24: recent-corner estimate требует strong shrink к среднему;
- Over 9.5 AUC всё ещё ~`0.5053`.

Вывод: небольшой portable signal для среднего expected corner count есть, но устойчивого match ranking нет.

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

Итог: угловые = устойчивый state signal; маленький calibrated expected-count signal есть; bookmaker edge, Over/Under selector и bookmaker-corner edge не доказаны. Следующая meaningful evidence должна прийти из новых bookmaker lines/prices или richer event/territorial data.

## Bookmaker corner capability

Stored bookmaker corner-line evidence = 0.

Inactive preregistered target:
- BUNDESLIGA, Union Berlin vs FC Schalke 04;
- kickoff `2026-09-11T18:30:00Z`;
- event_id `115c6679a72c5a360640b6baaa16e78c`;
- rollover run `34112118221`, artifact `10014773586`;
- ZIP SHA256 `6b34164dc659bf438eea66d989890d0bfb12c8429a18f9d677af3fea4455aa7e`;
- 17 stored snapshots, one identity, conflict=0;
- observed paid capability-probe attempts = 0.

PR #219 merge `46cdd4d4bd4cdcd4dd9d4d07d795d868727feb3f`.
PR #221 merge `d14465600d7a4f02280afa3561568960789ef4a9`.

Blocker before activation = **fresh zero-cost quota proof**. Old ~193 credits from 2026-09-06 is stale. Hard reserve 100; future bounded probe max 1 request / 2 credits; manual-only.

## Settlement / public results

### PROVIDER_FREE_RESULTS_FALLBACK_V1 — CLOSED / LIVE_PROVEN

Problem: Football-Data current-season CSV (`SP1.csv`, `I1.csv`) repeatedly returned HTTP 503 and blocked La Liga/Serie A settlement.

Frozen operational solution:
- Football-Data remains primary and is always tried first;
- ESPN keyless soccer scoreboard is fallback **only after bounded transient primary exhaustion**;
- La Liga slug `esp.1`, Serie A `ita.1`;
- only explicit `completed=true` events;
- strict score/date/home-away/team/duplicate validation;
- immutable project persistence/conflict guards remain authority;
- unknown/malformed/schema identity fails closed;
- primary schema/validation errors are never masked by fallback;
- both public sources unavailable => `SOURCE_UNAVAILABLE`, no writes;
- paid provider requests always 0.

OpenFootball/footballcsv were rejected for live settlement because current Serie A data was stale.

### PR #223 — initial fallback implementation

Merge `5befc9d53a0382a6178436ee55518a279c560e15`.
All PR CI green, but post-merge live proof found two real defects:
- La Liga run `34179722049`: primary 3x503, ESPN activated, then safe `UnknownTeamError` on ESPN display name `Deportivo`; no writes; production model unchanged; artifact `10038463816`.
- Serie A run `34179722040`: production workflow test path could not import root `update_serie_a_results.py`; sync never started.

Decision: do not weaken validation. Add only the live-proven alias `Deportivo -> Dep. A Coruna` (then existing normalizer -> `Deportivo La Coruña`) and regression-test it. Fix Serie A production workflow with `PYTHONPATH=.`.

### PR #224 — live regression fixes

Merge `382814a00f1c04dbff776c0a5594b3c98909fe9a`.
Full PR CI green; production `.pkl` checks green.

Post-merge live proof:

**La Liga Results Sync run `34180001408` — SUCCESS**
- primary Football-Data: HTTP 503 after 3 attempts;
- fallback ESPN: 1 request;
- source rows / finished rows: 41 / 41;
- legacy inserted 10, unchanged 31;
- canonical inserted 10, unchanged 36;
- canonical conflicts 0;
- total public HTTP requests 4;
- paid provider requests 0;
- status `WRITTEN`;
- production model hash unchanged;
- status artifact `10038564675`;
- artifact ZIP SHA256 `e912b26ec46dc034b8651c08a3bea00fd2314a50dd3354f478f48d090c2ce992`.

**Serie A Results Sync run `34180001418` — SUCCESS**
- primary Football-Data: HTTP 503 after 3 attempts;
- fallback ESPN: 1 request;
- source rows / finished rows: 30 / 30;
- inserted 19, unchanged 11, conflicts 0;
- total public HTTP requests 4;
- paid provider requests 0;
- status `WRITTEN`;
- evaluator then saw 30 finished-result rows and 19 settled fixtures;
- latest-pre-kickoff MARKET_ONLY diagnostic: 19 fixtures, accuracy `0.6315789474`, log loss `0.89514645696`, multiclass Brier `0.52100247085`; this is an operational diagnostic, not a new research decision/promotion;
- evaluator performed no Supabase writes and used no production model;
- status artifact `10038563495`;
- artifact ZIP SHA256 `9459ff69c5e18f3d047ef906c16f971fc0c475333bd2f118e55dc93455584b78`.

**Independent live Supabase proof after both runs:**
- current-season canonical `league_finished_results`: La Liga 46 fixtures, Serie A 30 fixtures, latest date 2026-09-07;
- exact prior settlement-lag audit run `34122752130` had 13 already-late identities: 7 La Liga + 6 Serie A;
- identity-only recheck after recovery: La Liga `7/7 present, 0 missing`; Serie A `6/6 present, 0 missing`;
- no outcome scores were needed for this closure check.

Conclusion: the specific external settlement blocker from Football-Data 503 is **removed**. ESPN fallback is live-proven for both leagues while preserving fail-closed behavior and zero paid-provider usage.

Non-blocking follow-up: La Liga-specific PR validator did not trigger on PR #224 path set; do not let this distract from research, but include common fallback/test paths in that validator the next time its workflow is touched or if another fallback regression appears.

## Security follow-up

Read-only audit previously found RLS disabled on:
- `teams`;
- `predictions`;
- `match_statistics`;
- `league_prediction_ledger`;
- `epl_ai_market_pair_ledger`.

Do not enable RLS automatically; first perform a separate access-policy audit so current app/research flows are not broken.

## Текущий следующий шаг

1. Пересчитать **outcome-free** prospective market-path sample health после settlement recovery; использовать только result identities/statuses, не scores.
2. Убедиться, что settlement-late blocker теперь 0 для восстановленных identities и понять новый settled sample size по EPL/La Liga/Serie A.
3. Market snapshot staleness остаётся отдельной acquisition problem; paid h2h refresh manual-only.
4. После outcome-free health check вернуться к bookmaker-corner capability только при наличии fresh zero-cost quota proof. Не запускать paid probe автоматически.
5. Frozen EPL_AI_MARKET_PAIR_V1 и PROSPECTIVE_CORNERS10_INCREMENTAL_V1 продолжать без premature outcomes.
6. RLS audit — отдельный follow-up после основных research/operational priorities.

## Журнал решений

### 2026-09-07

- Создан `PROJECT_CONTINUITY.md`; пользователь попросил сохранять решения между чатами и объяснять работу просто.
- Принят season-invariant research principle: historical portability first, fresh data as independent confirmation/drift monitor; универсальное правило «каждая идея ждёт 100 свежих матчей» отвергнуто для новых research blocks, но existing frozen gates сохранены.
- Historical corner V1–V4 закрыты; включён STOP RULE против same-data feature mining.
- Bookmaker corner capability остался external manual gate.
- Зафиксирован отдельный RLS follow-up.

### 2026-09-08

- Приоритет подтверждён: развивать проект, не раздувая инфраструктуру без пользы.
- Выбран реальный blocker: provider-free settlement La Liga/Serie A.
- ESPN выбран как keyless fallback-only; Football-Data сохранён primary.
- PR #223 merged; post-merge live proof честно выявил `Deportivo` identity gap и Serie A workflow import-path regression.
- PR #224 merged `382814a00f1c04dbff776c0a5594b3c98909fe9a`; оба live result sync успешно прошли через ESPN fallback после 3x503 primary.
- La Liga добавила 10 canonical results, Serie A 19; conflicts=0, paid requests=0.
- Exact 13 previously late market-path identities из run `34122752130` теперь все присутствуют: 7/7 La Liga, 6/6 Serie A, missing=0.
- `PROVIDER_FREE_RESULTS_FALLBACK_V1` закрыт как `LIVE_PROVEN`.
- Следующий приоритет: outcome-free sample-health recalculation на восстановленном settlement.
