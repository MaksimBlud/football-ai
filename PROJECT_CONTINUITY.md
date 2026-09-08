# Football AI — Project Continuity

Этот файл — постоянная память проекта между чатами. Его задача — не заставлять заново проводить полный аудит при каждом новом чате.

## Как пользоваться

Перед новой рабочей сессией:
1. Прочитать этот файл.
2. Коротко сверить свежий GitHub `main` и live Supabase.
3. Не повторять полный аудит без конкретной причины.
4. Продолжить с раздела **Текущий следующий шаг**.
5. После существенного решения, PR, merge или live-проверки обновить этот файл.

GitHub `main` и live Supabase остаются фактическим source of truth. Этот файл хранит правила, решения и направление работы.

## Как общаться с пользователем

- Всегда писать простым языком.
- Не предполагать знание программирования.
- В обновлениях прежде всего объяснять: что сделали, что выяснили, почему это важно и что дальше.
- Приоритет: **максимально развивать проект без лишней технической дрочки**. Инфраструктуру улучшать только когда она снимает реальный blocker, защищает данные/production или ускоряет исследование.

## Постоянные правила проекта

- Репозиторий: `MaksimBlud/football-ai`; основная ветка `main`.
- Source of truth: свежий GitHub `main` + live Supabase.
- Не менять production `.pkl` как побочный эффект research/training.
- Research/training != production promotion; automatic promotion запрещён.
- Не делать mass-clean/reset/mass-format и не перетирать параллельные изменения.
- Существенные изменения: отдельная ветка -> tests -> PR -> полный CI -> fresh-main check -> exact-head merge -> post-merge/live proof.
- Frozen/preregistered contracts не обходить и не ослаблять задним числом.
- Prospective outcomes нельзя читать раньше разрешённого gate.
- Максимально использовать бесплатные/read-only проверки.
- The Odds API credits не тратить, если доказательство можно получить бесплатно.
- Paid-provider workflows остаются manual-only; не добавлять автоматический paid scheduler.
- Реальные баги закрывать regression-тестами.
- External/fail-closed red signal не делать искусственно green.
- Если point-in-time history нельзя честно восстановить, не делать retrospective production replay; работать future-only с точной provenance.

## Активные frozen / operational контуры

### EPL_AI_MARKET_PAIR_V1

Режим: **collect, don't peek**.

- Первые 100 eligible prospective events = frozen primary cohort.
- Outcomes запрещено читать до 100 событий.
- Затем минимум 24 часа после kickoff последнего события cohort.
- Дополнительный embargo до `2026-11-01 12:16:54 UTC`.
- Никаких interim primary evaluations или performance-based optional stopping.
- Последнее известное состояние было около `12/100`; перед использованием подтвердить metadata без чтения outcomes.

### PROSPECTIVE_CORNERS10_INCREMENTAL_V1

- Проверяет, добавляет ли `CORNERS10` prospective 1X2 информацию сверх market baseline.
- Historical incremental evidence против рынка было неблагоприятным, поэтому это confirmation, а не tuning.
- Bookmaker corner capability должен быть отдельно доказан и одобрен.
- До этого sample не eligible и evaluator не читает outcomes.
- Frozen minimum: 100 settled eligible fixtures на лигу + минимум 4 calendar months.
- Контракт нельзя ускорять задним числом.

### PROSPECTIVE_MARKET_PATH_V1

- Использует полную pre-cutoff market trajectory.
- Deterministic schedule revisions quarantined и исключены из frozen sample.
- Paid h2h refresh manual-only.
- Перед платным refresh сначала бесплатно пересчитать league-level priority.
- Прошедший research cutoff нельзя дополнять задним числом.
- Последнее известное issue: market snapshots stale с 2026-09-05 при наличии future fixtures.

## CORNERS — закрытый historical/free-data блок

Важно различать:
- `CORNERS10` — football-state признак для 1X2;
- corner-total research — прогноз количества/тотала угловых;
- bookmaker corner market — отдельный внешний источник данных.

### SEASON_INVARIANT_CORNERS_V1 — CLOSED / PORTABLE_STRONG

`CORNERS10` проверялся на fully held-out seasons EPL, La Liga, Serie A.

Против `GOALS10`:
- EPL 6/7;
- La Liga 5/7;
- Serie A 7/7;
- всего 18/21 сезонных побед по обеим основным метрикам.

Вывод: угловые несут устойчивую football-state информацию, которая переносится между сезонами и лигами.

Но historical `MARKET + CORNERS10` не улучшил fitted 1X2 market model в среднем. Значит, bookmaker edge поверх рынка не доказан и production менять нельзя.

Early-drift historical audit:
- 20 матчей слишком шумно;
- около 40 = раннее предупреждение;
- около 80 = уже серьёзная проверка.

Рабочий принцип: strong historical cross-season evidence = основа; свежий сезон = drift monitor.

PR #212 merge `f72952be44249cceceb6a81cb6ff02d885e588ff`.

### CORNER_TOTAL_SIGNAL_V1 — CLOSED / NOT_PORTABLE_TOTAL_SIGNAL

На 2581 held-out matches 2019/20–2025/26:
- weighted delta MAE `+0.040076` против historical mean;
- победы 2/7;
- Over 9.5 AUC ≈ `0.5053`.

PR #214 merge `92633e3f011146a533b3cdce1ab26080efe1b139`.

### CORNER_TOTAL_CALIBRATED_V2 — CLOSED / PORTABLE_CALIBRATED_TOTAL_SIGNAL

- weighted delta MAE ≈ `-0.007791`;
- лучше baseline 6/7 сезонов;
- fitted slopes ~0.03–0.24, raw recent-corner estimate требует сильного shrink к среднему;
- Over 9.5 AUC всё ещё ≈ `0.5053`.

Вывод: есть небольшой переносимый signal для среднего ожидаемого числа угловых, но почти нет способности выбирать конкретные Over/Under матчи.

PR #215 merge `8e206f4e97f8b5d0e64bc2951716ad8d971def61`.

### CORNER_PRESSURE_SIGNAL_V3 — CLOSED / NOT_PORTABLE_PRESSURE_DISCRIMINATOR

- all-shots pressure AUC `0.498357`, positive 3/7;
- shots-on-target pressure AUC `0.512793`, positive 5/7, но ниже preregistered 0.52.

PR #216 merge `95386fffb6b386efa26feb0ad4860135ded99257`.

### CORNER_COMBINED_DISCRIMINATOR_V4 — CLOSED / NOT_PORTABLE_COMBINED_DISCRIMINATOR

Финальный free historical combination test:
- corner-state;
- all-shots pressure;
- shots-on-target pressure.

Результат:
- weighted Over 9.5 AUC `0.501691`;
- positive 3/7;
- frozen success requirement: AUC > 0.52 и минимум 5/7.

**STOP RULE:** больше не перебирать окна, веса, thresholds или combinations на этих же historical seasons.

PR #217 merge `9bb1e8ed244e10f53d87850cb552aa70e148e0eb`.

### Итог по угловым

Доказано:
- угловые отражают устойчивое состояние команд;
- небольшой signal для ожидаемого среднего количества угловых существует после сильной calibration.

Не доказано:
- дополнительный 1X2 edge поверх рынка;
- стабильный Over/Under 9.5 selector;
- bookmaker corner edge.

Следующая meaningful evidence должна прийти из **новой информации**: actual bookmaker corner lines/prices или более богатых event/territorial данных.

## Bookmaker corner capability

Historical stored bookmaker corner-line evidence = 0.

Preregistered inactive target:
- BUNDESLIGA;
- Union Berlin vs FC Schalke 04;
- kickoff `2026-09-11T18:30:00Z`;
- event_id `115c6679a72c5a360640b6baaa16e78c`;
- zero-cost rollover run `34112118221`;
- artifact `10014773586`;
- ZIP SHA256 `6b34164dc659bf438eea66d989890d0bfb12c8429a18f9d677af3fea4455aa7e`;
- live check: 17 stored snapshots, one identity, conflict=0.

GitHub history подтвердил 0 запусков старого paid capability probe.

PR #219 merge `46cdd4d4bd4cdcd4dd9d4d07d795d868727feb3f`.
PR #221 merge `d14465600d7a4f02280afa3561568960789ef4a9`.

Оставшийся blocker перед activation: **fresh zero-cost quota proof**.
Старое значение ~193 credits от 2026-09-06 считается stale.
Hard reserve = 100; bounded future probe = максимум 1 request / 2 credits; manual-only.

## Settlement / public results

### PROVIDER_FREE_RESULTS_FALLBACK_V1

Причина: Football-Data `SP1.csv` и `I1.csv` возвращали HTTP 503, из-за чего La Liga и Serie A settlement блокировался.

Решение:
- Football-Data остаётся primary и всегда вызывается первым;
- ESPN keyless soccer scoreboard = fallback only после bounded transient exhaustion primary;
- La Liga slug `esp.1`, Serie A `ita.1`;
- completed event принимается только при явном `completed=true`;
- score, date, home/away identity, team names, duplicate identity проходят строгую validation;
- существующая immutable persistence/conflict detection остаётся authority;
- malformed/schema/unknown identity => fail closed;
- primary validation/schema error не маскируется fallback;
- оба источника недоступны => `SOURCE_UNAVAILABLE`, no writes;
- paid provider requests всегда 0.

Почему не OpenFootball/footballcsv:
- бесплатные, но на момент проверки текущие Serie A files отставали и не содержали свежих сыгранных результатов.

PR #223:
- title `Add provider-free fallback for La Liga and Serie A results`;
- merge `5befc9d53a0382a6178436ee55518a279c560e15`;
- все PR validations были green: La Liga, Serie A, Research, Bundesliga, Eredivisie, Ligue 1;
- production `.pkl` checks green.

### Post-merge live proof PR #223 — IMPORTANT

Live proof обнаружил два реальных defects; это подтверждает правило «PR CI недостаточно без live proof».

**La Liga run `34179722049`:**
- Football-Data primary действительно дал HTTP 503 после 3 attempts;
- ESPN fallback действительно активировался;
- fallback вернул ESPN team display name `Deportivo`;
- existing normalizer не знал это имя и корректно остановился с `UnknownTeamError`;
- никаких Supabase writes не произошло;
- production model hash before/after совпал;
- artifact `la-liga-results-status`, id `10038463816`;
- статус = `FAILED`, а не искусственный green.

Fix decision:
- добавить **только подтверждённый live alias** `Deportivo -> Dep. A Coruna`, который существующий La Liga normalizer затем канонизирует в `Deportivo La Coruña`;
- добавить regression test именно на ESPN display name `Deportivo`;
- неизвестные будущие names по-прежнему должны fail closed.

**Serie A run `34179722040`:**
- production sync не стартовал, потому что regression step завершился collection error;
- `pytest tests/test_serie_a_results_source_availability.py ...` не видел root module `update_serie_a_results.py`;
- это production-workflow path issue, а не data/provider problem;
- PR-specific Serie A validation раньше проходил, то есть обнаружено расхождение между PR workflow и production workflow.

Fix decision:
- production workflow regression command должен явно использовать `PYTHONPATH=.`, не менять сам module layout;
- после этого live sync должен снова дойти до provider/fallback path.

Текущая fix-ветка: `fix/results-fallback-live-regressions-v1`, создана от exact main `5befc9d53a0382a6178436ee55518a279c560e15`.

На ней уже:
- добавлен live-proven alias `Deportivo`;
- добавлен regression test на этот alias;
- исправлен Serie A production test command через `PYTHONPATH=.`;
- никаких paid calls, ручных Supabase writes или production `.pkl` изменений не выполнялось.

Следующий шаг: PR -> полный CI -> fresh-main/exact-head merge -> повторный live La Liga + Serie A Results Sync -> проверить фактические inserted/unchanged/conflicts -> read-only Supabase settlement audit -> обновить этот файл финальным live результатом.

## Security notice из live Supabase

Ранее read-only проверка показала RLS disabled на:
- `teams`;
- `predictions`;
- `match_statistics`;
- `league_prediction_ledger`;
- `epl_ai_market_pair_ledger`.

Не включать RLS автоматически: без правильных policies можно сломать приложение/research. Нужен отдельный access-policy audit.

## Текущий следующий шаг

1. Завершить `fix/results-fallback-live-regressions-v1` через PR/CI/merge.
2. Повторить live result sync для La Liga и Serie A и доказать реальные writes/idempotence либо честный fail-closed blocker.
3. Проверить live Supabase: сколько late fixtures settlement стало доступно после recovery.
4. Только после закрытия settlement blocker вернуться к bookmaker corners, если fresh zero-cost quota proof доступен.
5. Corner capability probe остаётся manual-only paid action.
6. Frozen prospective collection продолжать без premature outcome reads.
7. RLS audit — отдельная задача после основных research/operational blockers.

## Журнал решений

### 2026-09-07

- Пользователь попросил всегда объяснять работу простым языком.
- Создан `PROJECT_CONTINUITY.md` для сохранения решений между чатами.
- Отказались от универсального правила «каждая идея обязана ждать 100 свежих матчей»: strong historical portability evidence используется первым, fresh data — как independent confirmation/drift monitor.
- `SEASON_INVARIANT_CORNERS_V1 = PORTABLE_STRONG`.
- Corner total V1 failed; calibrated V2 дал маленький переносимый count signal; V3 pressure failed; V4 combined failed.
- Активирован STOP RULE против дальнейшего same-data corner feature mining.
- Stored bookmaker corner lines не найдены; capability остаётся external manual gate.
- Обнаружен отдельный RLS follow-up; security settings не менялись.

### 2026-09-08

- Пользователь подтвердил приоритет: максимально развивать проект без лишней технической дрочки.
- Выбран следующий реальный blocker: provider-free settlement La Liga/Serie A.
- OpenFootball/footballcsv отвергнуты как stale для live settlement.
- ESPN выбран как keyless **fallback only**, Football-Data остаётся primary.
- PR #223 merged `5befc9d53a0382a6178436ee55518a279c560e15`; полный PR CI green.
- Post-merge live proof La Liga подтвердил primary 3x503 и фактическую активацию ESPN, затем безопасный stop на неизвестном `Deportivo`; no writes, production model unchanged.
- Post-merge Serie A выявил workflow import-path regression до sync step.
- Создана ветка `fix/results-fallback-live-regressions-v1`; добавлены точечные regression fixes.
- Paid API не использовались; manual Supabase writes не выполнялись; production `.pkl` не менялись.
