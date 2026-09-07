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

Последнее известное состояние: около `12/100`. Перед использованием всегда подтвердить live metadata без чтения outcomes.

### PROSPECTIVE_MARKET_PATH_V1

- Использует полную pre-cutoff market trajectory.
- Schedule revisions с deterministic provider revision quarantined и исключены из frozen research sample.
- Paid h2h refresh manual-only.
- Перед любым платным refresh сначала бесплатно пересчитать league-level priority.
- Уже прошедший research cutoff нельзя дополнять задним числом.

Последний known operational issue: market snapshots были stale с 2026-09-05; live future fixtures при этом существовали.

### Settlement / public results

- Serie A и La Liga используют provider-free Football-Data CSV для result sync.
- На 2026-09-07 `I1.csv` и `SP1.csv` возвращали HTTP 503.
- Правильное поведение: `SOURCE_UNAVAILABLE`, evaluator skipped, paid requests = 0.
- Не увеличивать grace period и не включать paid fallback только ради green.

### Multi-Market corners

- Paid acquisition manual-only.
- Последний zero-cost quota proof: примерно 193 credits, hard reserve 100.
- Infrastructure ready, но stored corner market capability evidence = 0.
- Blocker: `PROVIDER_CORNER_CAPABILITY_UNPROVEN`.
- Bounded paid capability probe нельзя запускать автоматически.

## CORNERS10 — что теперь известно

Важно различать:
- `CORNERS10` — football-state признак для 1X2 модели;
- букмекерский corner market из Multi-Market — отдельная ветка.

### Historical football-only portability

Блок: `SEASON_INVARIANT_CORNERS_V1`.

Источник: ранее сохранённый Historical Football Signal Lab artifact PR #57. Использованы EPL, La Liga и Serie A, по 7 полностью held-out сезонов на лигу — суммарно 21 season test.

Основной сравнительный baseline: `GOALS10`.

Результат:
- EPL: CORNERS10 лучше по Brier 6/7 сезонов, по log-loss 6/7;
- La Liga: 5/7 и 5/7;
- Serie A: 7/7 и 7/7;
- суммарно: 18/21 выигрышей по Brier и 18/21 по log-loss.

Итоговая historical portability classification: **PORTABLE_STRONG**.

Простыми словами: информация об угловых действительно повторяется между сезонами и лигами и не выглядит случайностью одного сезона.

### Window robustness

- `CORNERS5` также поддерживает то же направление в EPL, La Liga и Serie A.
- Это снижает риск, что эффект существует только при магическом окне ровно 10 матчей.
- Fixed `CORNERS15` check остаётся pending, потому что старый artifact его не содержал, а текущий Football-Data source был недоступен (503).
- Нельзя подменять источник или подбирать другое окно только ради завершения проверки.

### Market incremental result

Ранее PR #58 показал:
- `MARKET_CORNERS10` не улучшил fitted `MARKET_MODEL` исторически;
- EPL и La Liga: 0/7 season wins по Brier/log-loss;
- Serie A: 2/7, но средний результат всё равно хуже рынка.

Вывод: `CORNERS10` — реальный football signal, но **не доказанный дополнительный 1X2 edge поверх букмекерского рынка**.

Production модель из-за этого результата не менять.

### Early drift — новая схема вместо слепого ожидания 100 матчей

На тех же старых held-out сезонах проведена historical pseudo-live проверка: смотрели результат после первых 20/40/80/160 матчей, при этом модель обучалась только на более ранних сезонах.

Для `CORNERS10` vs `GOALS10`:
- 20 матчей: направление совпадало с итогом сезона примерно 67% по Brier / 76% по log-loss;
- 40 матчей: примерно 67% / 76%; это полезный early warning, но ещё шумный;
- 80 матчей: примерно **81% / 90%**; это уже materially stronger checkpoint;
- 160 матчей: примерно 81% / 86%; больше матчей не гарантирует монотонного улучшения каждого показателя.

Новый рабочий принцип:
- historical cross-season/cross-league robustness = основное доказательство существования устойчивого механизма;
- fresh data = drift monitor, а не повторное открытие сигнала с нуля;
- около 40 матчей можно использовать как раннее предупреждение;
- около 80 матчей — как более серьёзную проверку;
- это не automatic promotion gate и не разрешение обходить frozen prospective embargo.

## Текущий PR

PR #212: `Add season-invariant CORNERS10 validation and early drift audit`.

Он должен содержать:
- один canonical invariant audit (`season_invariant_corners_audit.py`);
- pinned PR57 historical evidence;
- pinned early-drift summary;
- regression tests против leakage;
- отдельный provider-free CI;
- этот continuity file.

Он не должен зависеть от live Football-Data, Supabase writes или Odds API.

## Текущий следующий шаг

1. Довести PR #212 до green CI.
2. Проверить fresh `main` и exact PR head, затем merge.
3. Post-merge подтвердить artifact/status и неизменность production `.pkl`.
4. После закрытия этого блока НЕ строить новую production модель автоматически.
5. Следующий реальный corner-related research step — отдельный corners-specific target/market experiment, где portable football corner signal может дать информацию, не поглощённую 1X2 market.
6. Multi-Market bookmaker corners остаётся blocked до намеренного manual paid capability probe.
7. Current-season drift monitor создавать только как отдельный prospective contract, который не пересекается с запрещённым outcome-peeking существующих frozen cohorts.

## Журнал решений

### 2026-09-07

- Пользователь попросил всегда объяснять работу простым языком.
- Создан `PROJECT_CONTINUITY.md` для сохранения решений между чатами.
- Принято решение отказаться от универсального правила «любая новая идея ждёт 100 свежих матчей».
- Проверен `CORNERS10` на переносимость между сезонами и тремя лигами: historical result `PORTABLE_STRONG`.
- Подтверждено, что `CORNERS10` не показал historical incremental edge поверх fitted 1X2 market.
- Historical early-drift audit показал: 20 матчей слишком шумно, 40 — early warning, около 80 — существенно более надёжный checkpoint.
- Для reproducibility используются pinned prior artifacts, потому что Football-Data сейчас отдаёт 503; outage не маскируется.
