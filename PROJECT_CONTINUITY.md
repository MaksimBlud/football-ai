# Football AI — Project Continuity

Этот файл — постоянная память проекта между чатами.

## Как использовать этот файл

Перед началом новой рабочей сессии:
1. Прочитать этот файл целиком.
2. Коротко проверить текущий GitHub `main` и live Supabase как source of truth.
3. Не начинать полный повторный аудит без конкретной причины.
4. Продолжить с раздела **Текущий следующий шаг**.
5. После существенного решения, PR, merge или live-проверки обновлять этот файл.

GitHub `main` и live Supabase всегда важнее этого файла, если состояние разошлось.

## Как общаться с пользователем

- Всегда объяснять работу простым языком.
- Не предполагать знание программирования.
- В итогах прежде всего писать: что сделали, что выяснили, почему это важно и что дальше.

## Постоянные правила проекта

- Репозиторий: `MaksimBlud/football-ai`.
- Основная ветка: `main`.
- Source of truth: текущий GitHub `main` + live Supabase.
- Не менять production `.pkl` как побочный эффект research/training.
- Research/training != production promotion; никакого automatic promotion.
- Не делать mass-clean/reset/mass-format и не перетирать параллельную работу.
- Существенные изменения: отдельная ветка -> tests -> PR -> полный CI -> fresh-main check -> exact-head merge.
- Frozen/preregistered contracts не обходить.
- Prospective outcomes нельзя читать раньше разрешённого gate.
- Максимально использовать бесплатные/read-only проверки.
- The Odds API credits не тратить, если доказательство можно получить бесплатно.
- Paid-provider workflows остаются manual-only.
- Найденные ошибки закрывать regression-тестами.
- Expected external/fail-closed red signal не делать искусственно green.
- Если PR head неожиданно изменился, не merge вслепую: сначала проверить параллельные изменения.

## Активные frozen / operational контуры

### EPL_AI_MARKET_PAIR_V1

Режим: **collect, don't peek**.
- Primary cohort: первые 100 eligible prospective events.
- Outcomes запрещено читать до 100 событий.
- Затем минимум 24 часа после kickoff последнего события cohort.
- Дополнительный embargo до `2026-11-01 12:16:54 UTC`.
- Никаких interim primary evaluations или performance-based optional stopping.

Последнее известное состояние: около `12/100`. Перед использованием подтвердить live metadata без чтения outcomes.

### PROSPECTIVE_MARKET_PATH_V1

- Использует полную pre-cutoff market trajectory.
- Deterministic schedule revisions quarantined и исключены из frozen sample.
- Paid h2h refresh manual-only.
- Перед платным refresh сначала бесплатно пересчитать league-level priority.
- Прошедший research cutoff нельзя дополнять задним числом.

Последний known issue: market snapshots были stale с 2026-09-05, хотя future fixtures существовали.

### Settlement / public results

- Serie A и La Liga используют provider-free Football-Data CSV.
- На 2026-09-07 `I1.csv` и `SP1.csv` возвращали HTTP 503.
- Правильное поведение: `SOURCE_UNAVAILABLE`, evaluator skipped, paid requests = 0.
- Не увеличивать grace period и не включать paid fallback только ради green.

## CORNERS — завершённые исследования

Важно различать:
- `CORNERS10` — football-state признак для 1X2;
- corner-total research — прогноз количества/тотала угловых;
- bookmaker corner market — отдельный внешний источник данных.

### SEASON_INVARIANT_CORNERS_V1 — CLOSED / PORTABLE_STRONG

Held-out EPL, La Liga, Serie A:
- EPL: `CORNERS10` лучше `GOALS10` 6/7 сезонов по Brier и log-loss;
- La Liga: 5/7;
- Serie A: 7/7;
- всего 18/21 wins.

Вывод: информация об угловых — устойчивый football-state signal, а не случайность одного сезона.

Но historical incremental test показал, что `MARKET_CORNERS10` в среднем не улучшает fitted 1X2 `MARKET_MODEL`. Поэтому дополнительный 1X2 bookmaker edge не доказан и production из-за этого не менять.

Early drift historical audit:
- 20 матчей — слишком шумно;
- около 40 — раннее предупреждение;
- около 80 — существенно более надёжная проверка.

PR #212 merged `f72952be44249cceceb6a81cb6ff02d885e588ff`.
Docs closure PR #213 merged `3885922db15ec5613452c5f9dedf97601d8e6542`.

### CORNER_TOTAL_SIGNAL_V1 — CLOSED / NOT_PORTABLE_TOTAL_SIGNAL

EPL 2019/20–2025/26, 2581 held-out matches.
- weighted delta MAE `+0.040076` против historical mean baseline;
- MAE wins 2/7;
- weighted AUC Over 9.5 ≈ `0.5053`.

Вывод: сырое recent-corners average нельзя использовать как прямой прогноз тотала.
PR #214 merged `92633e3f011146a533b3cdce1ab26080efe1b139`.

### CORNER_TOTAL_CALIBRATED_V2 — CLOSED / PORTABLE_CALIBRATED_TOTAL_SIGNAL

Тот же V1 signal откалиброван перед каждым test season только на более ранних сезонах.
- weighted delta MAE ≈ `-0.007791`;
- wins 6/7;
- fitted slopes примерно 0.03–0.24;
- weighted AUC Over 9.5 ≈ `0.5053`.

Вывод: recent corner-state даёт небольшой переносимый сигнал для ожидаемого **численного количества угловых**, но почти не ранжирует конкретные Over/Under матчи.
PR #215 merged `8e206f4e97f8b5d0e64bc2951716ad8d971def61`.

### CORNER_PRESSURE_SIGNAL_V3 — CLOSED / NOT_PORTABLE_PRESSURE_DISCRIMINATOR

- all-shots pressure AUC `0.498357`, positive 3/7;
- shots-on-target diagnostic AUC `0.512793`, positive 5/7, ниже frozen threshold 0.52.

Вывод: простой pressure signal не является устойчивым discriminator.
PR #216 merged `95386fffb6b386efa26feb0ad4860135ded99257`.

### CORNER_COMBINED_DISCRIMINATOR_V4 — CLOSED / NOT_PORTABLE_COMBINED_DISCRIMINATOR

Финальный free historical combination test: corner-state + shots + shots-on-target; каждый test season обучался только на более ранних сезонах.
- weighted AUC Over 9.5 `0.501691`;
- positive seasons 3/7;
- frozen success rule был AUC > 0.52 и минимум 5/7 positive seasons.

**STOP RULE:** больше не искать новые комбинации, веса, окна или thresholds на этих же held-out seasons. Это будет data mining/overfitting.

PR #217 merged `9bb1e8ed244e10f53d87850cb552aa70e148e0eb`.
Docs closure PR #218 merged `80de764865adf653c6b76329922a87ac38c5c78f`.
Все corner research workflows проверяли неизменность production `.pkl`.

## Multi-Market bookmaker corners — текущее состояние

Цель следующего шага: получить **реальную букмекерскую линию на угловые**, а затем сравнивать её с football corner signal / calibrated V2 expected count.

Что подтверждено бесплатно:
- stored bookmaker corner-line evidence = 0;
- 2 старых `league_multi_market_snapshots` содержат только `spreads` и `totals`;
- `total_corners = null` и team-corners = null;
- `league_corner_results` = 0;
- blocker остаётся `PROVIDER_CORNER_CAPABILITY_UNPROVEN`.

### Старый активный probe target

`multi_market_corner_capability_probe.py` всё ещё указывает на:
- LA_LIGA;
- Getafe — Celta Vigo;
- event_id `0817220a8e0794e15ecba51338bb6cf8`;
- kickoff `2026-09-07T17:00:00Z`.

Матч уже прошёл. Поэтому runtime fail-closed не позволит использовать его как prospective paid probe.

### Новый preregistered target — INACTIVE

Новый target выбран только из сохранённых `odds_snapshots` по существующему zero-cost rollover policy:
- BUNDESLIGA;
- Union Berlin — FC Schalke 04;
- event_id `115c6679a72c5a360640b6baaa16e78c`;
- kickoff `2026-09-11T18:30:00Z`.

Live read-only identity proof:
- 17 stored snapshots;
- ровно 1 distinct identity;
- identity conflict = false;
- provider requests = 0;
- writes = 0.

Machine-readable record:
`research/multi_market_corner_capability_probe_rollover_v2.json`.

Критически важно:
- `active = false`;
- automatic activation = false;
- automatic target switching = false;
- этот record сам не разрешает paid request;
- требуется отдельная activation PR;
- требуется fresh zero-cost quota preflight;
- max paid requests = 1;
- max paid credits = 2;
- hard reserve = 100.

Последнее сохранённое значение квоты: `remaining=193`, timestamp `2026-09-06T03:09:57.315423Z`.
Оно **устарело и не разрешает paid action**.

### PR / parallel-work history 2026-09-08

При rollover возник полезный safety case:
- initial PR #219 после green неожиданно получил параллельные commits;
- exact-head merge guard остановил blind merge;
- среди промежуточных изменений был временный `.tmp` placeholder;
- был создан clean PR #220 от известного проверенного SHA `f86196aea6612e02a638ea6774e9d076e34c8e61`;
- параллельная ветка затем сама очистила временные файлы и сделала более строгий вариант: новый target остаётся inactive, старый expired probe target не заменяется автоматически;
- финальный head `011cf5e463200a6998351bf411d2f30f1e333c7d` прошёл Multi-Market, Bundesliga, Ligue 1, Serie A, Eredivisie и Research PR Validation;
- `main` после merge: `46cdd4d4bd4cdcd4dd9d4d07d795d868727feb3f`.

На текущем `main` временный `research/multi_market_corner_capability_probe_rollover_v2.json.tmp` отсутствует, промежуточный `multi_market_corner_capability_probe_fallback_v2.json` отсутствует.

## Security notice из live Supabase

Read-only проверка показала RLS disabled на:
- `teams`;
- `predictions`;
- `match_statistics`;
- `league_prediction_ledger`;
- `epl_ai_market_pair_ledger`.

Это отдельный security follow-up. **Не включать RLS автоматически** без access-policy audit: можно сломать приложение/research workflows.

## Текущий следующий шаг

1. Historical corner block считать **CLOSED**; не повторять V1–V4 и не делать same-data mining.
2. Дождаться/получить свежий zero-cost `Multi-Market V2 Readiness Status` на `main`.
3. Fresh proof должен подтвердить `paid_provider_requests=0`, `paid_provider_credits=0`, `writes=false`, свежие quota fields и сохранение hard reserve.
4. Проверить, что Union Berlin — Schalke всё ещё prospective и `active=false` до отдельной активации.
5. Только после свежего безопасного quota proof можно готовить отдельную activation PR для нового target.
6. Даже после activation paid capability probe остаётся **manual-only** и требует отдельного явного разрешения пользователя.
7. Если разрешение дано: максимум 1 provider request / 2 credits, hard reserve 100, никаких Supabase writes или model changes.
8. Если provider отдаёт corner markets — новый preregistered research block сравнивает football corner signal/V2 expected count с actual bookmaker line.
9. Если provider corners не поддерживает — зафиксировать negative capability proof и искать другой источник, не возвращаясь к historical feature mining.
10. Параллельно сохраняются прежние operational priorities: provider-free settlement recovery, outcome-free sample health, existing frozen prospective collection и manual-only market refresh.

## Журнал решений

### 2026-09-07

- Пользователь попросил всегда объяснять работу простым языком.
- Создан `PROJECT_CONTINUITY.md` для сохранения решений между чатами.
- Отказались от универсального правила «каждая идея обязана сначала ждать 100 свежих матчей»; fresh data используется как drift evidence после strong historical portability work.
- `SEASON_INVARIANT_CORNERS_V1`: `PORTABLE_STRONG`.
- `CORNER_TOTAL_SIGNAL_V1`: `NOT_PORTABLE_TOTAL_SIGNAL`.
- `CORNER_TOTAL_CALIBRATED_V2`: `PORTABLE_CALIBRATED_TOTAL_SIGNAL`, но Over/Under ranking около random.
- `CORNER_PRESSURE_SIGNAL_V3`: `NOT_PORTABLE_PRESSURE_DISCRIMINATOR`.
- `CORNER_COMBINED_DISCRIMINATOR_V4`: `NOT_PORTABLE_COMBINED_DISCRIMINATOR`; установлен stop-rule против дальнейшего same-data feature mining.
- PR #214/#215/#216/#217 merged; все production `.pkl` guards green.
- Zero-cost live check подтвердил отсутствие stored bookmaker corner lines.
- Зафиксирован отдельный Supabase RLS follow-up.

### 2026-09-08

- Старый Getafe — Celta capability target подтверждён как expired и fail-closed.
- Zero-cost rollover выбрал Union Berlin — FC Schalke 04 на 2026-09-11 как следующий clean prospective candidate.
- Live Supabase identity recheck: 17 snapshots, 1 identity, conflict=0.
- Новая цель preregistered, но оставлена `active=false`; отдельная activation PR обязательна.
- Последнее `remaining=193` признано stale и не используется как разрешение на paid action.
- Regression failure старого fallback provenance не обходился: исторический Getafe–Celta record сохранён, для нового target создан отдельный record.
- Exact-head guard поймал параллельное изменение PR; blind merge не выполнялся.
- Финальное параллельное состояние очищено от временных файлов и прошло полный CI.
- Текущий `main`: `46cdd4d4bd4cdcd4dd9d4d07d795d868727feb3f`.
- Readiness workflow имеет scheduled run `05:12 UTC`, manual dispatch через текущую GitHub-связь недоступен.
- Создана одноразовая автоматическая **read-only** проверка после scheduled readiness; она не имеет права запускать paid capability probe.
