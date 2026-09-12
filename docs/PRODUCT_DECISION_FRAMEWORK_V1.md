# Football AI — Product Decision Framework v1

Status: product contract  
Version: `product-decision.v1`

## Зачем существует этот framework

Football AI не должен превращаться в таблицу из десятков несвязанных процентов. Его задача — из всех доступных рынков матча сформировать понятное решение, не смешивая прогноз события, цену букмекера и доказанность модели.

Framework v1 формально определяет пять независимых продуктовых сущностей:

1. **Главный прогноз** — что система считает основным прогнозом матча среди рынков, допущенных к product decision.
2. **Альтернативы** — лучшие прогнозы из других допущенных рынков.
3. **Value** — отдельный индикатор расхождения model probability и bookmaker price.
4. **Уверенность** — состояние зрелости product/research gate выбранного рынка.
5. **Нет ставки** — отдельное решение о том, что прогноз нельзя автоматически превращать в рекомендацию поставить деньги.

## Неподвижные правила

### Forecast и Value — разные вещи

Главный прогноз никогда не выбирается по raw EV. Положительный EV не делает маловероятный исход главным прогнозом.

Пример: Liverpool — Fulham.

- модель: Liverpool ~67.5%, Fulham ~16.8%;
- главный прогноз: Liverpool;
- если цена БК на Fulham создаёт положительный raw EV, Fulham может отображаться только как отдельный Value-сигнал;
- Value не меняет Forecast.

### Сначала зрелость рынка, потом вероятность

Вероятности разных рынков можно сравнивать для выбора главного прогноза только после учёта их product/research readiness.

Ranking Framework v1:

1. `decision_tier` рынка;
2. model probability внутри доступных кандидатов;
3. детерминированный market key только для стабильного tie-break.

Таким образом, более высокий процент из менее зрелого рынка не вытесняет проверенный operational market автоматически.

Пример:

- 1X2 operational: П1 = 67%;
- Total Goals model-only: ТБ 2.5 = 72%.

Пока Total Goals остаётся `model_only`, главный прогноз — П1 67%, а ТБ 2.5 является provisional alternative. После прохождения Total Goals нужного research/validation gate и перевода в тот же operational tier ТБ 2.5 72% сможет стать главным прогнозом.

## Текущая матрица рынков

| Рынок | Status | Decision tier | Confidence state | Main forecast | Value | Bet recommendation |
|---|---|---:|---|---|---|---|
| 1X2 | `comparison_ready` | 2 | `operational` | да | да | нет |
| Total Goals | `model_only` | 1 | `provisional` | да, как fallback/alternative | нет | нет |
| Handicap | `research_only` | 0 | `unavailable` | нет | нет | нет |
| Corners Total | `research_only` | 0 | `unavailable` | нет | нет | нет |

Изменять tier или eligibility можно только отдельным осознанным product/research решением. Наличие высокой вероятности само по себе не является основанием для promotion.

## 1. Главный прогноз

Для каждого forecast-eligible рынка берётся только его лучший model selection (`display_selection`).

Затем кандидаты сортируются по `decision_tier`, после чего по model probability.

Главный прогноз содержит:

- market;
- market label;
- decision tier;
- selection;
- model probability;
- fair odds;
- bookmaker odds, если они существуют;
- raw EV, если цена существует.

Но bookmaker odds и raw EV не участвуют в выборе главного прогноза.

Если forecast-eligible кандидатов нет, `main_forecast.status = unavailable`.

## 2. Альтернативы

Альтернативы — не второй и третий исход того же 1X2 рынка.

Framework берёт лучшие кандидаты **из других forecast-eligible рынков**, исключая главный. Это позволяет в будущем получить структуру вроде:

- Главный: П1;
- Альтернатива 1: ТБ 2.5;
- Альтернатива 2: Фора -0.5;
- Альтернатива 3: ТБ угловых 9.5.

Каждый alternative сохраняет собственный tier и confidence state.

Framework v1 ограничивает список тремя альтернативами.

## 3. Value

Value — отдельный price signal.

В расчёт попадают только рынки с `eligible_for_value = true` и только selections, у которых есть bookmaker price.

Для простого no-push исхода:

`raw EV = probability × bookmaker odds − 1`

Из положительных raw EV выбирается максимальный.

Важно:

- `raw EV > 0` не доказывает прибыльность;
- Value не повышает decision tier;
- Value не меняет Main Forecast;
- Value не создаёт Bet Recommendation.

Сегодня value-eligible только 1X2.

## 4. Уверенность

Framework v1 сознательно не придумывает псевдостатистический confidence score.

`confidence` отражает **product/research maturity** рынка главного прогноза:

- `operational` — рынок допущен в основной operational product contour;
- `provisional` — model output существует, но рынок ещё не прошёл полный product/research gate;
- `unavailable` — подходящего прогнозного кандидата нет.

Это не calibration score, не confidence interval и не обещание accuracy.

Когда prospective research даст достаточные данные, empirical calibration/reliability может быть добавлена отдельным слоем, не меняя смысл текущего поля.

## 5. Нет ставки

Framework v1 **никогда автоматически не формирует betting recommendation**.

Текущий результат: `bet_decision.status = no_bet`.

Причина принципиальная: ни высокая model probability, ни positive raw EV не должны автоматически превращаться в инструкцию поставить деньги.

Чтобы в будущем рынок мог участвовать в betting recommendation, требуется отдельный gate и отдельный утверждённый recommendation/staking policy. Это не является model promotion и не должно происходить неявно.

## Связь Forecast, Alternatives, Value и No Bet

Эти сущности могут одновременно существовать без противоречия.

Например:

- Главный прогноз: Liverpool 67.5%;
- Альтернатива: ТБ 2.5 61%;
- Value: Fulham +8.0% raw EV;
- Confidence: operational;
- Bet decision: Нет ставки.

Смысл:

- модель считает Liverpool наиболее сильным operational прогнозом;
- тотал является другим сценарным прогнозом;
- цена Fulham выглядит математически завышенной относительно model probability;
- ни одно из этих наблюдений само по себе не прошло отдельный betting recommendation gate.

## Поведение при неполных данных

### Нет bookmaker odds

Forecast сохраняется. Value отсутствует.

### Нет operational market, но есть provisional market

Provisional market может стать главным прогнозом как fallback, но confidence будет `provisional`.

### Нет forecast-eligible probability

- Main Forecast: unavailable;
- Alternatives: пусто;
- Confidence: unavailable;
- Bet Decision: no_bet.

### Есть высокий positive raw EV в research-only рынке

Он не должен отображаться как product Value, пока рынок не станет `eligible_for_value`.

## Как подключать новый рынок

Новый рынок не становится частью decision engine автоматически после появления чисел.

Перед подключением нужно явно определить:

1. prediction target и settlement semantics;
2. источник model probability;
3. источник bookmaker line/price;
4. research/validation status;
5. `decision_tier`;
6. `decision_confidence`;
7. `eligible_for_main_forecast`;
8. `eligible_for_value`;
9. `eligible_for_bet_recommendation` — по умолчанию false;
10. regression tests против cross-market semantic errors.

Только после этого рынок подключается к общей логике без специальных исключений.

## Что Framework v1 намеренно не решает

До результатов соответствующих исследований framework не придумывает:

- empirical calibration score;
- league-specific reliability multiplier;
- bankroll/stake sizing;
- portfolio correlation;
- exposure limits;
- автоматическую betting recommendation;
- promotion thresholds для новых рынков.

Эти слои должны добавляться только после отдельного доказательного и продуктового решения.

## Product invariants для regression tests

1. Value никогда не меняет Main Forecast.
2. Более низкий decision tier не вытесняет более высокий tier только из-за большей probability.
3. Внутри одинакового tier побеждает более высокая model probability.
4. Alternatives берутся из других рынков, а не из конкурирующих selections того же рынка.
5. Research-only рынок не попадает в Main Forecast, Alternatives или Value без explicit eligibility.
6. Confidence — maturity state, а не empirical accuracy claim.
7. Positive raw EV не создаёт Bet Recommendation.
8. При отсутствии прогнозных кандидатов система возвращает `unavailable + no_bet`, а не выдумывает прогноз.
9. Все product decisions должны быть воспроизводимы из сохранённого snapshot и readiness contract.
10. Изменение decision tier/eligibility является отдельным product/research change и должно проходить regression tests + PR/CI.
