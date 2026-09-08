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
- Приоритет: максимально развивать проект без лишней технической дрочки. Инфраструктуру менять только когда она снимает реальный blocker, защищает данные/production или ускоряет research.

## Постоянные правила

- Repo: `MaksimBlud/football-ai`, branch `main`.
- Production `.pkl` нельзя менять как побочный эффект research/training.
- Research/training != production promotion; automatic promotion запрещён.
- Не делать mass-clean/reset/mass-format и не перетирать параллельные изменения.
- Существенные изменения: branch -> tests -> PR -> полный CI -> fresh-main -> exact-head merge -> post-merge/live proof.
- Frozen/preregistered contracts не ослаблять задним числом.
- Prospective outcomes нельзя читать до разрешённого gate.
- Максимально использовать free/read-only proof; The Odds API credits не тратить при наличии бесплатной проверки.
- Paid-provider workflows остаются manual-only. Никогда не превращать priority/readiness report в автоматический paid trigger.
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
- Перед любым платным refresh сначала бесплатный league-level priority + fresh quota proof.
- Прошедший cutoff нельзя backfill.
- Settlement и market acquisition — разные контуры: settlement восстановлен, market snapshots остаются stale.

## CORNERS — historical/free-data block CLOSED

Важно различать:
- `CORNERS10` = football-state feature для 1X2;
- corner-total research = прогноз числа/тотала угловых;
- bookmaker corner market = отдельный внешний источник.

### SEASON_INVARIANT_CORNERS_V1 — PORTABLE_STRONG

Held-out `CORNERS10` vs `GOALS10`:
- EPL 6/7;
- La Liga 5/7;
- Serie A 7/7;
- всего 18/21 wins по основным метрикам.

Вывод: угловые несут устойчивую football-state информацию через сезоны/лиги. Но historical `MARKET + CORNERS10` не улучшил market baseline в среднем, поэтому дополнительный bookmaker 1X2 edge не доказан.

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

### PR #223 — initial fallback

Merge `5befc9d53a0382a6178436ee55518a279c560e15`.
PR CI green, but live proof correctly found:
- La Liga run `34179722049`: primary 3x503, ESPN activated, then safe `UnknownTeamError` on ESPN `Deportivo`; no writes, production hash unchanged; artifact `10038463816`.
- Serie A run `34179722040`: production workflow test import-path error; sync never started.

Decision: validation не ослаблять. Добавить только live-proven alias `Deportivo -> Dep. A Coruna` (existing normalizer -> `Deportivo La Coruña`) + regression test; Serie A production test command -> `PYTHONPATH=.`.

### PR #224 — live regression fixes

Merge `382814a00f1c04dbff776c0a5594b3c98909fe9a`.
Full CI green; production `.pkl` checks green.

**La Liga Results Sync run `34180001408` — SUCCESS**
- primary: 3x HTTP 503;
- ESPN fallback: 1 request;
- source/finished rows 41/41;
- legacy inserted 10, unchanged 31;
- canonical inserted 10, unchanged 36, conflicts 0;
- public requests 4; paid requests 0;
- status `WRITTEN`; production hash unchanged;
- artifact `10038564675`, ZIP SHA256 `e912b26ec46dc034b8651c08a3bea00fd2314a50dd3354f478f48d090c2ce992`.

**Serie A Results Sync run `34180001418` — SUCCESS**
- primary: 3x HTTP 503;
- ESPN fallback: 1 request;
- source/finished rows 30/30;
- inserted 19, unchanged 11, conflicts 0;
- public requests 4; paid requests 0;
- evaluator saw 30 result rows / 19 settled fixtures;
- MARKET_ONLY diagnostic: 19 fixtures, accuracy `0.6315789474`, log loss `0.89514645696`, Brier `0.52100247085`; operational diagnostic only, not promotion/research decision;
- evaluator no writes, no production model;
- artifact `10038563495`, ZIP SHA256 `9459ff69c5e18f3d047ef906c16f971fc0c475333bd2f118e55dc93455584b78`.

**Independent Supabase proof**
- current-season canonical results: La Liga 46, Serie A 30, latest date 2026-09-07;
- prior settlement-lag audit `34122752130` had 13 already-late identities: 7 LL + 6 SA;
- identity-only recheck: LL 7/7 present, SA 6/6 present, missing=0.

**Direct red -> green rerun of same settlement-lag audit**
- run `34122752130`, rerun job `101917806223` on 2026-09-08;
- SUCCESS: `PASS: no late prospective market-path settlement identities`;
- EPL `20 eligible / 10 settled / 10 awaiting / 0 late`;
- La Liga `18 / 10 / 8 / 0`;
- Serie A `22 / 9 / 13 / 0`;
- scores not queried, Supabase writes=0, production hashes unchanged;
- artifact `10038654571`, ZIP SHA256 `c04cdee0f6de6276f6e72ced9ea56bac040763f2d59109f9927abd23ba39409f`.

Conclusion: Football-Data 503 settlement blocker removed; fallback live-proven; current settlement late=0 for EPL/La Liga/Serie A.

Non-blocking follow-up: La Liga-specific PR validator did not trigger on PR #224 common fallback/test path set. Add those paths next time that workflow is naturally touched; do not prioritize over research.

## Market acquisition freshness — ZERO-COST AUDIT 2026-09-08

Settlement восстановлен, но `odds_snapshots` acquisition остаётся stale. Read-only Supabase audit подтвердил:

- **EPL:** 1111 snapshot rows, 40 event_ids, latest snapshot `2026-09-05 15:19:42.729192+00`, future event_ids 10; next kickoff `2026-09-12 14:00Z`.
- **La Liga:** 786 rows, 42 event_ids, latest `2026-09-05 15:21:32.51302+00`, future event_ids 14; next kickoff `2026-09-11 19:00Z`.
- **Serie A:** 585 rows, 33 event_ids, latest `2026-09-05 15:08:05.114487+00`, future event_ids 14; next kickoff `2026-09-11 18:45Z`.

Использована существующая PR #210 логика `prospective_market_path_refresh_priority.py`, а не новый policy. PR #210 merge `9265d90bb7c1eca806a86be874832517d694c35f`.

Эта логика read-only/provider-free и ранжирует только already-persisted coverage diagnostics: earliest active due cutoff -> больше due paths -> staleness ratio. Quarantined/superseded revisions не создают paid priority. Она **не разрешает расход credits**.

Live priority на 2026-09-08:
1. **SERIE_A — rank 1:** `priority_due_paths=12`, earliest due cutoff ~`82.17h`, max staleness ratio ~`4.95`.
2. **LA_LIGA — rank 2:** `priority_due_paths=5`, earliest due cutoff ~`82.42h`, max staleness ratio ~`29.61` (fixed 2h cadence делает staleness особенно высокой).
3. **EPL — rank 3:** `priority_due_paths=10`, earliest due cutoff ~`101.42h`, max staleness ratio ~`4.94`.

Все перечисленные due fixtures уже имеют много pre-cutoff snapshots (обычно EPL/Serie A ~19, La Liga ~28), то есть frozen historical path coverage не потеряна. Проблема — именно отсутствие **свежих** market snapshots перед будущими cutoff, а не нехватка старой траектории.

Ближайшие due paths:
- Serie A: Venezia–Fiorentina, kickoff `2026-09-11 18:45Z`, cutoff `12:45Z`;
- La Liga: Sevilla–Valencia, kickoff `2026-09-11 19:00Z`, cutoff `13:00Z`;
- EPL: первые due fixtures kickoff `2026-09-12 14:00Z`, cutoff `08:00Z`.

**Decision:** acquisition blocker подтверждён, но automatic paid refresh запрещён. Если пользователь отдельно разрешит manual paid h2h action, сначала нужен fresh zero-cost quota proof и existing budget/safety guards. Текущий order для одного осознанного refresh decision: Serie A -> La Liga -> EPL. Не объединять это автоматически с corner capability probe: это два разных paid intents.

## Security follow-up

Read-only audit ранее нашёл RLS disabled на:
- `teams`;
- `predictions`;
- `match_statistics`;
- `league_prediction_ledger`;
- `epl_ai_market_pair_ledger`.

Не включать RLS автоматически; сначала отдельный access-policy audit.

## Текущий следующий шаг

1. Settlement recovery считать CLOSED / LIVE_PROVEN; settlement late=0 во всех трёх market-path лигах.
2. Market acquisition blocker подтверждён: snapshots stale с 2026-09-05; priority = Serie A #1, La Liga #2, EPL #3.
3. **Не запускать paid h2h refresh автоматически.** Перед любым manual paid refresh нужен fresh zero-cost quota proof + existing reserve/safety guards.
4. Отдельно от h2h acquisition: bookmaker-corner capability target остаётся inactive до fresh quota proof; corner paid probe manual-only и не должен «заодно» запускаться с h2h refresh.
5. Frozen `EPL_AI_MARKET_PAIR_V1`, `PROSPECTIVE_MARKET_PATH_V1`, `PROSPECTIVE_CORNERS10_INCREMENTAL_V1` продолжать без premature outcome reads/backfill.
6. Если paid action не разрешён, следующий полезный бесплатный шаг — проверить outcome-free collection/sample metadata и наличие новых zero-cost public/event data; не заниматься новым historical corner feature mining.
7. RLS audit — отдельный follow-up после основных research/operational priorities.

## Журнал решений

### 2026-09-07

- Создан `PROJECT_CONTINUITY.md`; пользователь попросил сохранять решения между чатами и объяснять работу просто.
- Принят season-invariant research principle: historical portability first, fresh data as independent confirmation/drift monitor; универсальное правило «каждая идея ждёт 100 свежих матчей» отвергнуто для новых research blocks, existing frozen gates сохранены.
- Historical corner V1–V4 закрыты; включён STOP RULE против same-data feature mining.
- Bookmaker corner capability остался external manual gate.
- Зафиксирован отдельный RLS follow-up.

### 2026-09-08

- Приоритет подтверждён: развивать проект, не раздувая инфраструктуру без пользы.
- ESPN выбран как keyless settlement fallback-only; Football-Data сохранён primary.
- PR #223 merged; live proof выявил `Deportivo` alias gap и Serie A production workflow import issue.
- PR #224 merged `382814a00f1c04dbff776c0a5594b3c98909fe9a`; оба live sync успешно прошли через ESPN после 3x503 primary.
- La Liga добавила 10 canonical results, Serie A 19; conflicts=0, paid=0.
- Exact 13 previously late identities закрыты; rerun того же settlement-lag audit стал green: late=0 EPL/LL/SA, no scores/no writes/production unchanged.
- `PROVIDER_FREE_RESULTS_FALLBACK_V1` закрыт как `LIVE_PROVEN`.
- Zero-cost market acquisition audit подтвердил staleness с 2026-09-05 и recomputed existing PR #210 priority: Serie A #1 (12 due), La Liga #2 (5), EPL #3 (10).
- Решение: priority report не является permission to spend. Paid h2h refresh и bookmaker-corner probe остаются отдельными manual-only действиями после fresh quota proof.
