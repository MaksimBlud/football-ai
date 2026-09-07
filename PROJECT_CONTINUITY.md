# Football AI — Project Continuity

Этот файл — постоянная память проекта между чатами.

## Как использовать этот файл

Перед началом любой новой рабочей сессии:
1. Прочитать этот файл целиком.
2. Коротко проверить текущий GitHub `main` и live Supabase как source of truth.
3. Не начинать повторный полный аудит без конкретной причины.
4. Продолжить с раздела **Текущий следующий шаг**.
5. После существенного решения, PR, merge или live-проверки обновлять этот файл.

Этот файл хранит решения и контекст. Фактическим source of truth остаются GitHub `main` и live Supabase.

## Как общаться с пользователем

- Всегда объяснять работу простым языком.
- Не предполагать знание программирования.
- В итогах прежде всего писать: что сделали, что выяснили, почему это важно и что дальше.

## Постоянные правила проекта

- Репозиторий: `MaksimBlud/football-ai`.
- Основная ветка: `main`.
- Не менять production `.pkl` как побочный эффект research/training.
- Research/training != production promotion.
- Никакого automatic model promotion.
- Не делать mass-clean/reset/mass-format.
- Не перетирать параллельные изменения в `main`.
- Существенные изменения: отдельная ветка -> tests -> PR -> полный CI -> fresh-main check -> exact-head merge.
- Frozen/preregistered contracts не обходить.
- Prospective outcomes нельзя читать раньше разрешённого gate.
- Максимально использовать бесплатные/read-only проверки.
- The Odds API credits не тратить, если доказательство можно получить бесплатно.
- Paid-provider workflows остаются manual-only.
- Найденные баги закрывать regression-тестами.
- Expected external/fail-closed red signal не делать искусственно green.

## Активные frozen / operational контуры

### EPL_AI_MARKET_PAIR_V1

Режим: **collect, don't peek**.

- primary cohort: первые 100 eligible prospective events;
- outcomes запрещено читать до 100 событий;
- затем минимум 24 часа после kickoff последнего события cohort;
- дополнительный embargo до `2026-11-01 12:16:54 UTC`;
- никаких interim primary evaluations или performance-based optional stopping.

Последнее известное состояние: около `12/100`. Перед использованием подтвердить live metadata без чтения outcomes.

### PROSPECTIVE_MARKET_PATH_V1

- Использует полную pre-cutoff market trajectory.
- Deterministic schedule revisions quarantined и исключены из frozen research sample.
- Paid h2h refresh manual-only.
- Перед любым платным refresh сначала бесплатно пересчитать league-level priority.
- Уже прошедший research cutoff нельзя дополнять задним числом.

Последний known operational issue: market snapshots были stale с 2026-09-05; future fixtures при этом существовали.

### Settlement / public results

- Serie A и La Liga используют provider-free Football-Data CSV для result sync.
- На 2026-09-07 `I1.csv` и `SP1.csv` возвращали HTTP 503.
- Правильное поведение: `SOURCE_UNAVAILABLE`, evaluator skipped, paid requests = 0.
- Не увеличивать grace period и не включать paid fallback только ради green.

### Multi-Market bookmaker corners

- Paid acquisition manual-only.
- Последний известный zero-cost quota proof: примерно 193 credits, hard reserve 100.
- Infrastructure ready, но corner market capability не доказана.
- Blocker: `PROVIDER_CORNER_CAPABILITY_UNPROVEN`.
- Bounded paid capability probe нельзя запускать автоматически.
- На 2026-09-07 live Supabase содержит 2 старых `league_multi_market_snapshots`; оба имеют только provider market keys `spreads` и `totals`.
- В обоих `total_corners = null`, `team_corners.home = null`, `team_corners.away = null`.
- `league_corner_results` содержит 0 строк.
- Следовательно, stored bookmaker corner-line evidence по-прежнему отсутствует.

## CORNERS — завершённые исследования

Важно различать:
- `CORNERS10` — football-state признак для 1X2;
- corner-total research — прогноз количества/тотала угловых;
- bookmaker corner market — отдельный внешний источник данных.

### 1. SEASON_INVARIANT_CORNERS_V1 — CLOSED / PORTABLE_STRONG

Историческая проверка `CORNERS10` против `GOALS10` на полностью held-out сезонах EPL, La Liga и Serie A:
- EPL: Brier/log-loss wins 6/7;
- La Liga: 5/7;
- Serie A: 7/7;
- всего 18/21 wins по обеим основным метрикам.

Вывод: информация об угловых — устойчивый football-state signal и не выглядит случайностью одного сезона.

`CORNERS5` поддерживает то же направление. `CORNERS15` остаётся отдельным pending robustness check и не нужен для уже принятого основного вывода.

Historical incremental test против 1X2 market показал, что `MARKET_CORNERS10` не улучшает fitted `MARKET_MODEL` в среднем. Поэтому `CORNERS10` не является доказанным дополнительным 1X2 bookmaker edge и production из-за него не менять.

Early-drift historical audit:
- 20 матчей — слишком шумно;
- около 40 — раннее предупреждение;
- около 80 — существенно более надёжная проверка.

Рабочий принцип: historical cross-season robustness = основное доказательство механизма; fresh data = drift monitor, а не новое открытие сигнала с нуля.

PR #212 merged: `f72952be44249cceceb6a81cb6ff02d885e588ff`.
Docs closure PR #213 merged: `3885922db15ec5613452c5f9dedf97601d8e6542`.

### 2. CORNER_TOTAL_SIGNAL_V1 — CLOSED / NOT_PORTABLE_TOTAL_SIGNAL

Впервые проверили сами тоталы угловых.

Фиксированная формула использовала последние 10 EPL матчей обеих команд:
- corners-for команды;
- corners-against соперника;
- сырое ожидаемое число угловых.

Held-out seasons: 2019/20–2025/26, 2581 матч.

Результат:
- weighted delta MAE = `+0.040076` против простого historical mean baseline;
- MAE wins = 2/7 сезонов;
- weighted AUC для Over 9.5 ≈ `0.5053`.

Вывод: сырое recent-corners average нельзя использовать как прямой прогноз тотала.

PR #214 merged: `92633e3f011146a533b3cdce1ab26080efe1b139`.
Post-merge CI green; production `.pkl` unchanged.

### 3. CORNER_TOTAL_CALIBRATED_V2 — CLOSED / PORTABLE_CALIBRATED_TOTAL_SIGNAL

Тот же самый V1 signal без новых признаков был честно откалиброван отдельно перед каждым test season только по более ранним сезонам.

Результат:
- weighted delta MAE ≈ `-0.007791`;
- calibrated MAE wins = 6/7 сезонов;
- fitted slopes примерно 0.03–0.24, то есть recent-corner signal нужно сильно shrink к среднему по лиге;
- weighted AUC Over 9.5 ≈ `0.5053`.

Вывод: recent corner-state содержит небольшой переносимый сигнал для **ожидаемого численного количества угловых**, но почти не умеет ранжировать конкретные Over/Under матчи.

Это research finding, не betting edge и не production model.

PR #215 merged: `8e206f4e97f8b5d0e64bc2951716ad8d971def61`.
Post-merge CI green; production `.pkl` unchanged.

### 4. CORNER_PRESSURE_SIGNAL_V3 — CLOSED / NOT_PORTABLE_PRESSURE_DISCRIMINATOR

Проверили, может ли атакующее давление отличать high-corner матчи от low-corner.

Primary = all-shots pressure по последним 10 матчам:
- weighted AUC Over 9.5 = `0.498357`;
- positive seasons = 3/7.

Secondary preregistered diagnostic = shots-on-target pressure:
- weighted AUC = `0.512793`;
- positive seasons = 5/7;
- ниже frozen strength threshold 0.52 и не может заменить primary после просмотра результата.

Вывод: простой pressure signal не является устойчивым самостоятельным discriminator.

PR #216 merged: `95386fffb6b386efa26feb0ad4860135ded99257`.
Post-merge CI green; production `.pkl` unchanged.

### 5. CORNER_COMBINED_DISCRIMINATOR_V4 — CLOSED / NOT_PORTABLE_COMBINED_DISCRIMINATOR

V4 заранее объявлен **финальным free historical combination test**.

Фиксированные inputs:
- corner-state;
- all-shots pressure;
- shots-on-target pressure.

Для каждого test season коэффициенты обучались только на более ранних сезонах. Никаких дополнительных features/windows/interactions/threshold search.

Результат на 2581 held-out matches:
- weighted AUC Over 9.5 = `0.501691`;
- positive seasons = 3/7;
- frozen requirement был AUC > 0.52 и минимум 5/7 positive seasons.

Вывод: комбинация доступных бесплатных historical signals не создаёт устойчивый Over/Under 9.5 selector.

**STOP RULE:** больше не искать новые комбинации, веса, окна или thresholds на этих же held-out seasons. Это будет data mining/overfitting, а не новое доказательство.

PR #217 merged: `9bb1e8ed244e10f53d87850cb552aa70e148e0eb`.
Post-merge `Corner Combined Discriminator V4` green; pinned evidence, tests, final audit и production `.pkl` hash check passed.

## Итог corner research простыми словами

Что доказано:
- угловые действительно несут устойчивую информацию о состоянии футбольных команд;
- эта информация переносится между сезонами и лигами для football-state/1X2 контекста;
- recent corner-state после сильной калибровки немного улучшает прогноз среднего количества угловых.

Что НЕ доказано:
- дополнительный 1X2 edge поверх букмекера;
- устойчивый выбор матчей Over/Under 9.5 corners;
- bookmaker corner edge.

Почему останавливаем historical перебор:
- V1 raw total failed;
- V2 count calibration passed, но ranking почти random;
- V3 pressure failed;
- V4 fixed combination failed;
- дальнейший поиск на тех же сезонах создаст высокий риск подгонки.

Следующая meaningful corner evidence должна прийти из **новой информации**, а не из новых комбинаций старой:
1. actual bookmaker corner lines/prices; или
2. более богатые event/territorial данные (crosses, attacks, box entries и т.п.), которых сейчас нет в historical store.

## Security notice из live Supabase

Во время read-only проверки схемы обнаружено: RLS disabled на таблицах:
- `teams`;
- `predictions`;
- `match_statistics`;
- `league_prediction_ledger`;
- `epl_ai_market_pair_ledger`.

Это потенциальный security gap, но **не исправлять автоматически**: включение RLS без корректных policies может сломать приложение или research workflows. Нужен отдельный access-policy audit перед изменениями.

## Текущий следующий шаг

1. Corner historical free-data block считать **CLOSED**. Не повторять V1–V4 и не делать новые same-data combinations без действительно нового источника информации.
2. Следующий corner-specific gate = bookmaker corner market capability. Сейчас stored evidence = 0, blocker `PROVIDER_CORNER_CAPABILITY_UNPROVEN`.
3. Bounded The Odds API corner capability probe остаётся **manual-only paid action**. Автоматически его не запускать.
4. Если пользователь намеренно разрешает manual paid probe и budget guards проходят, сначала заново сделать zero-cost quota/readiness proof, затем использовать существующий preregistered bounded probe — не создавать обходной paid scheduler.
5. Если provider подтверждает corner markets, следующий research block = сравнение football corner signal/V2 expected count с actual bookmaker corner line, с новым preregistered contract.
6. Если provider corners не поддерживает, зафиксировать negative capability proof и искать другой источник corner-market/event data, а не возвращаться к historical feature mining.
7. Отдельно от corners: провести access-policy/RLS audit пяти Supabase таблиц перед любыми security изменениями.
8. Параллельно продолжаются прежние operational priorities: provider-free settlement recovery, outcome-free sample health, existing frozen prospective collection и manual-only market refresh.

## Журнал решений

### 2026-09-07

- Пользователь попросил всегда объяснять работу простым языком.
- Создан `PROJECT_CONTINUITY.md` для сохранения решений между чатами.
- Отказались от универсального правила «каждая идея обязана сначала ждать 100 свежих матчей»; fresh data используется как drift evidence после strong historical portability work.
- `SEASON_INVARIANT_CORNERS_V1`: `PORTABLE_STRONG`.
- `CORNER_TOTAL_SIGNAL_V1`: `NOT_PORTABLE_TOTAL_SIGNAL`.
- `CORNER_TOTAL_CALIBRATED_V2`: `PORTABLE_CALIBRATED_TOTAL_SIGNAL`, но Over/Under ranking остаётся около random.
- `CORNER_PRESSURE_SIGNAL_V3`: `NOT_PORTABLE_PRESSURE_DISCRIMINATOR`.
- `CORNER_COMBINED_DISCRIMINATOR_V4`: `NOT_PORTABLE_COMBINED_DISCRIMINATOR`; activated stop-rule against further same-data feature mining.
- PR #214 merged `92633e3f011146a533b3cdce1ab26080efe1b139`.
- PR #215 merged `8e206f4e97f8b5d0e64bc2951716ad8d971def61`.
- PR #216 merged `95386fffb6b386efa26feb0ad4860135ded99257`.
- PR #217 merged `9bb1e8ed244e10f53d87850cb552aa70e148e0eb`.
- Все corner research workflows проверяли неизменность production `.pkl`; post-merge proofs green.
- Zero-cost live check подтвердил: stored Multi-Market snapshots не содержат total/team corner lines; bookmaker corner capability остаётся unproven.
- Зафиксирован отдельный Supabase security follow-up: RLS disabled на пяти таблицах; не менять без отдельного policy audit.
