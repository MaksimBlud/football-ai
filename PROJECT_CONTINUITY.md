# Football AI — Project Continuity

Этот файл — постоянная память проекта между чатами. Его задача — не заставлять заново проводить полный аудит при каждом новом чате.

## Как пользоваться

Перед новой рабочей сессией:
1. Прочитать этот файл.
2. Коротко сверить текущий GitHub `main` и live Supabase.
3. Не делать полный повторный аудит без конкретной причины.
4. Продолжить с раздела **Текущий следующий шаг**.
5. После существенного решения, PR, merge или live-проверки обновить этот файл.

GitHub `main` и live Supabase остаются фактическим source of truth. Этот файл хранит правила, решения и направление работы.

## Как общаться с пользователем

- Всегда писать простым языком.
- Не предполагать, что пользователь разбирается в программировании.
- В обновлениях прежде всего объяснять: что сделали, что выяснили, почему это важно и что дальше.
- Приоритет пользователя: **максимально развивать проект без лишней технической дрочки**. Инфраструктурные улучшения делать только когда они реально снимают блокер, защищают данные/production или ускоряют исследование.

## Постоянные правила проекта

- Репозиторий: `MaksimBlud/football-ai`.
- Основная ветка: `main`.
- Source of truth: свежий GitHub `main` + live Supabase.
- Не менять production `.pkl` как побочный эффект research/training.
- Research/training != production promotion.
- Никакого automatic model promotion.
- Не делать mass-clean/reset/mass-format и не удалять чужие/untracked изменения без необходимости.
- Не перетирать параллельные изменения в `main`.
- Существенные изменения: отдельная ветка -> tests -> PR -> полный CI -> fresh-main check -> exact-head merge -> post-merge/live proof.
- Frozen/preregistered contracts не обходить и не ослаблять задним числом.
- Prospective outcomes нельзя читать раньше разрешённого gate.
- Максимально использовать бесплатные/read-only проверки.
- The Odds API credits не тратить, если доказательство можно получить бесплатно.
- Paid-provider workflows остаются manual-only; не добавлять автоматический paid scheduler.
- Найденные реальные баги закрывать regression-тестами.
- Expected external/fail-closed red signal не делать искусственно green.
- Если point-in-time history нельзя честно восстановить, не делать retrospective production replay; работать future-only с точной provenance.

## Активные frozen / operational контуры

### EPL_AI_MARKET_PAIR_V1

Режим: **collect, don't peek**.

- Primary cohort: первые 100 eligible prospective events.
- Outcomes запрещено читать до 100 событий.
- Затем минимум 24 часа после kickoff последнего события cohort.
- Дополнительный embargo до `2026-11-01 12:16:54 UTC`.
- Никаких interim primary evaluations или performance-based optional stopping.
- Последнее известное состояние было около `12/100`; перед использованием подтвердить live metadata без чтения outcomes.

### PROSPECTIVE_CORNERS10_INCREMENTAL_V1

- Проверяет, добавляет ли `CORNERS10` prospective 1X2 информацию сверх market baseline.
- Historical incremental evidence против рынка было неблагоприятным, поэтому это confirmation, а не tuning.
- Provider bookmaker-corner capability должен быть отдельно доказан и одобрен.
- До этого sample не eligible и evaluator не должен читать outcomes.
- Frozen minimum: 100 settled eligible fixtures на лигу + минимум 4 calendar months.
- Этот контракт нельзя ускорять задним числом только потому, что в новых исследованиях мы используем более быстрый season-invariant подход.

### PROSPECTIVE_MARKET_PATH_V1

- Использует полную pre-cutoff market trajectory.
- Deterministic schedule revisions quarantined и исключены из frozen sample.
- Paid h2h refresh manual-only.
- Перед платным refresh сначала бесплатно пересчитать league-level priority.
- Уже прошедший research cutoff нельзя дополнять задним числом.
- Последнее известное operational issue: market snapshots были stale с 2026-09-05 при наличии future fixtures.

## CORNERS — завершённый historical/free-data блок

Важно различать:
- `CORNERS10` — football-state признак для 1X2;
- corner-total research — прогноз количества/тотала угловых;
- bookmaker corner market — отдельный внешний источник данных.

### SEASON_INVARIANT_CORNERS_V1 — CLOSED / PORTABLE_STRONG

`CORNERS10` проверялся на полностью held-out сезонах EPL, La Liga и Serie A.

Против `GOALS10`:
- EPL: 6/7 сезонных побед;
- La Liga: 5/7;
- Serie A: 7/7;
- всего 18/21 по обеим основным метрикам.

Вывод: угловые несут устойчивую football-state информацию, которая переживает смену сезонов и лиг.

Но historical `MARKET + CORNERS10` не улучшил fitted 1X2 market model в среднем. Поэтому `CORNERS10` не является доказанным bookmaker edge и production из-за него не менять.

Early drift historical audit:
- 20 матчей слишком шумно;
- около 40 — раннее предупреждение;
- около 80 — уже серьёзная проверка.

Рабочий принцип: сильное historical cross-season доказательство = основа; свежий сезон = drift monitor, а не повторное открытие сигнала с нуля.

PR #212 merge `f72952be44249cceceb6a81cb6ff02d885e588ff`.

### CORNER_TOTAL_SIGNAL_V1 — CLOSED / NOT_PORTABLE_TOTAL_SIGNAL

Прямая формула recent corners за 10 матчей не прошла:
- held-out 2019/20–2025/26, 2581 матч;
- weighted delta MAE `+0.040076` против простого historical mean;
- победы только 2/7 сезонов;
- Over 9.5 AUC ≈ `0.5053`.

PR #214 merge `92633e3f011146a533b3cdce1ab26080efe1b139`.

### CORNER_TOTAL_CALIBRATED_V2 — CLOSED / PORTABLE_CALIBRATED_TOTAL_SIGNAL

Тот же signal был откалиброван только на предыдущих сезонах перед каждым test season.

- weighted delta MAE ≈ `-0.007791`;
- лучше baseline в 6/7 сезонов;
- fitted slopes ~0.03–0.24: raw recent-corner estimate нужно сильно тянуть к среднему;
- Over 9.5 AUC всё ещё ≈ `0.5053`.

Вывод: есть небольшой переносимый сигнал для **среднего ожидаемого количества угловых**, но почти нет умения выбирать конкретные Over/Under матчи.

PR #215 merge `8e206f4e97f8b5d0e64bc2951716ad8d971def61`.

### CORNER_PRESSURE_SIGNAL_V3 — CLOSED / NOT_PORTABLE_PRESSURE_DISCRIMINATOR

- all-shots pressure AUC `0.498357`, positive 3/7;
- shots-on-target AUC `0.512793`, positive 5/7, но ниже заранее заданного 0.52 и не может заменить primary после просмотра результата.

PR #216 merge `95386fffb6b386efa26feb0ad4860135ded99257`.

### CORNER_COMBINED_DISCRIMINATOR_V4 — CLOSED / NOT_PORTABLE_COMBINED_DISCRIMINATOR

Финальный заранее объявленный free historical combination test:
- corner-state;
- all-shots pressure;
- shots-on-target pressure.

Каждый test season обучался только на предыдущих сезонах.

Результат:
- weighted Over 9.5 AUC `0.501691`;
- positive 3/7 сезонов;
- frozen success requirement: AUC > 0.52 и минимум 5/7.

**STOP RULE:** больше не перебирать новые окна, веса, thresholds или комбинации на этих же historical seasons. Это будет data mining, а не новое доказательство.

PR #217 merge `9bb1e8ed244e10f53d87850cb552aa70e148e0eb`.

### Итог по угловым простыми словами

Доказано:
- угловые отражают реальное устойчивое состояние команд;
- небольшой сигнал для ожидаемого среднего количества угловых существует после сильной калибровки.

Не доказано:
- дополнительный 1X2 edge поверх рынка;
- стабильный выбор Over/Under 9.5;
- bookmaker corner edge.

Следующая meaningful corner evidence должна прийти из **новой информации**: реальных bookmaker corner lines/prices или более богатых event/territorial данных.

## Bookmaker corner capability

Historical stored bookmaker corner-line evidence = 0.

В двух старых Multi-Market snapshots были только `spreads` и `totals`; `total_corners` и team corners были `null`.

Следующая preregistered inactive capability target:
- BUNDESLIGA;
- Union Berlin vs FC Schalke 04;
- kickoff `2026-09-11T18:30:00Z`;
- event_id `115c6679a72c5a360640b6baaa16e78c`;
- zero-cost rollover run `34112118221`;
- artifact `10014773586`;
- ZIP SHA256 `6b34164dc659bf438eea66d989890d0bfb12c8429a18f9d677af3fea4455aa7e`;
- live check: 17 stored snapshots, exactly one identity, conflict=0.

GitHub history подтвердил 0 запусков `Multi-Market Corner Capability Probe` по старой цели, следовательно observed provider attempts = 0.

PR #219 merge `46cdd4d4bd4cdcd4dd9d4d07d795d868727feb3f` — новая inactive target preregistered.
PR #221 merge `d14465600d7a4f02280afa3561568960789ef4a9` — zero-attempt proof закреплён.

Оставшийся blocker перед activation: **fresh zero-cost quota proof**.
Старое значение ~193 credits от 2026-09-06 считается stale и не разрешает paid action.
Hard reserve = 100; bounded future probe = максимум 1 request / 2 credits; manual-only.

## Settlement / public results

### Почему этот блок сейчас приоритетный

La Liga и Serie A накопили завершённые матчи, которые нельзя нормально settlement/evaluate, пока основной бесплатный источник результатов недоступен. Это реальный research blocker, поэтому его исправление важнее косметической инфраструктуры.

До нового решения:
- primary source = Football-Data current-season CSV;
- La Liga `SP1.csv`, Serie A `I1.csv`;
- при 429/5xx три bounded attempts;
- на 2026-09-07 оба источника возвращали HTTP 503;
- правильное старое поведение: `SOURCE_UNAVAILABLE`, evaluator skipped, paid requests = 0;
- не увеличивать grace period и не включать paid fallback ради green.

### PROVIDER_FREE_RESULTS_FALLBACK_V1 — IN PROGRESS

Рабочая ветка: `fix/provider-free-results-fallback-v1`, создана от main `d14465600d7a4f02280afa3561568960789ef4a9`.

Решение:
- Football-Data остаётся **primary** и всегда вызывается первым;
- бесплатный ESPN soccer scoreboard используется **только после transient exhaustion primary**;
- ESPN не требует API key и не расходует The Odds API credits;
- La Liga slug `esp.1`, Serie A slug `ita.1`;
- запрашивается current-season date range одним scoreboard request, с bounded retries;
- завершённым считается только событие с явным `completed=true`;
- счёт, home/away identity, дата и team names проходят строгую проверку;
- используются существующие project normalization/persistence contracts;
- неизвестное имя, malformed score/schema или конфликтующий duplicate => fail closed, никаких записей;
- если primary и fallback оба недоступны => `SOURCE_UNAVAILABLE`, no writes;
- fallback не используется при schema/validation error primary — такие ошибки остаются hard failures;
- paid provider requests всегда 0.

Почему не OpenFootball/footballcsv:
- они бесплатные, но текущие файлы Serie A на момент проверки отставали и ещё не содержали свежие сыгранные результаты; для live settlement это неприемлемо.

Почему ESPN выбран как fallback:
- единый источник для обеих лиг;
- keyless JSON scoreboard;
- поддерживает запрос по дате/диапазону;
- отдаёт home/away, score и явный completed status;
- неофициальный endpoint, поэтому используется только как fallback и обёрнут fail-closed проверками.

На ветке уже добавлены:
- общий `espn_current_results_fallback.py`;
- fallback в La Liga sync;
- fallback в Serie A sync;
- regression tests для primary-first, fallback-after-503, both-unavailable, malformed/conflicting data;
- обновлённые result workflows для понимания fallback status.

Следующий шаг этого блока: PR -> полный CI -> fresh-main/exact-head merge -> live result sync proof -> проверить, сколько late La Liga/Serie A fixtures реально settlement -> записать финальный итог сюда.

## Security notice из live Supabase

Read-only проверка ранее показала RLS disabled на:
- `teams`;
- `predictions`;
- `match_statistics`;
- `league_prediction_ledger`;
- `epl_ai_market_pair_ledger`.

Это отдельный потенциальный security gap. **Не включать RLS автоматически**: без правильных policies можно сломать приложение/research. Нужен отдельный access-policy audit.

## Текущий следующий шаг

1. Закончить `PROVIDER_FREE_RESULTS_FALLBACK_V1`: PR, CI, merge и live proof.
2. Проверить, снят ли settlement blocker La Liga/Serie A и сколько поздних матчей закрылись.
3. После settlement recovery вернуться к bookmaker corners, когда fresh zero-cost quota proof будет доступен.
4. Если corner capability подтвердится — новый preregistered block: сравнение V2 expected corners с actual bookmaker line. Не возвращаться к historical feature mining V1–V4.
5. Параллельно сохранять frozen prospective collection без premature outcome reads.
6. RLS audit — отдельная задача после основных research/operational blockers, если не возникнет более срочная security-проблема.

## Журнал решений

### 2026-09-07

- Пользователь попросил всегда объяснять работу простым языком.
- Создан `PROJECT_CONTINUITY.md` для сохранения решений между чатами.
- Отказались от универсального правила «каждая идея обязана ждать 100 свежих матчей»: сильное historical portability evidence используется первым, fresh data — как independent confirmation/drift monitor.
- `SEASON_INVARIANT_CORNERS_V1 = PORTABLE_STRONG`.
- Corner total V1 failed; calibrated V2 дал маленький переносимый count signal; V3 pressure failed; V4 combined failed.
- Активирован STOP RULE против дальнейшего same-data corner feature mining.
- Stored bookmaker corner lines не найдены; capability остаётся внешним manual gate.
- Обнаружен отдельный RLS follow-up; security settings не менялись.

### 2026-09-08

- Пользователь подтвердил приоритет: максимально развивать проект без лишней технической дрочки.
- После закрытия historical corners выбран следующий полезный blocker: восстановить provider-free settlement La Liga и Serie A.
- Проверены варианты бесплатного fallback source. OpenFootball/footballcsv отвергнуты как слишком stale для live settlement.
- Выбран ESPN keyless soccer scoreboard как **fallback only**, Football-Data остаётся primary.
- Зафиксировано правило: fallback включается только после bounded transient outage primary; validation/schema failures primary не маскируются.
- Начат `PROVIDER_FREE_RESULTS_FALLBACK_V1` в ветке `fix/provider-free-results-fallback-v1`.
- Paid API не использовались, Supabase writes в этом implementation-шаге не выполнялись, production `.pkl` не менялись.
