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

### Manual corner capability probe — CLOSED / CAPABILITY_MISS

User-triggered `Multi-Market Corner Capability Probe` run `34246732050` completed successfully on `main` SHA `aaca74ff724378cce39b2ae2c6501a6a9d854f1b`.

Exact target remained the preregistered BUNDESLIGA Union Berlin vs FC Schalke 04 identity (`event_id=115c6679a72c5a360640b6baaa16e78c`, kickoff `2026-09-11T18:30:00+00:00`).

Observed result:
- `provider_request_attempted=true`;
- `paid_provider_requests=1`;
- `paid_provider_credits=0`, cost known;
- quota `193 -> 193`, hard reserve 100 preserved;
- `corner_market_keys=[]`;
- `corner_bookmaker_count=0`;
- status `CAPABILITY_MISS`;
- `writes_performed=false`;
- production model hash unchanged;
- no production `.pkl` changes;
- artifact `10064303200`;
- artifact ZIP SHA256 `5a7de8b02e1b82a29dc71c2a8a94c6154a2485bbaa32dd30d8bd6d0ef78a0cfa`.

A green workflow means the fail-closed probe contract passed; it does **not** mean corner capability was confirmed.

Decision: The Odds API is not treated as a usable bookmaker corner-line source for this target at probe time. Do not rerun the same target merely to hunt for a different result.

### Alternative corner-line source audit — ZERO-COST / READ-ONLY

Public provider documentation was checked without signup, API keys, trial activation or paid calls.

Priority:
1. **SportsGameOdds** — strongest next candidate. Public docs explicitly expose `cornerKicks-all-game-ou-over/under`, full-match total-corner line/price fields and bookmaker breakdown; the soccer API lists `BUNDESLIGA` among supported league IDs. Exact live Union–Schalke availability still requires authenticated API access.
2. **Sportmonks** — credible backup. Public odds catalogue documents corner markets including `Corner Match Bet`, `Corner Handicap`, `Team Corners` and `Alternative Corners`, and pre-match odds expose bookmaker/market/price fields. Exact Bundesliga live odds proof requires an API token and appropriate coverage.
3. **Betfair Exchange** — structural fallback. Official developer material exposes corner market types such as `CORNER_ODDS`, corner over/under variants and `CORNER_MATCH_BET`, but account/app-key access and exchange-specific integration add friction.

No account was created, no trial started and no provider credits were spent during this audit.

Decision: if a new external capability probe is authorized later, SportsGameOdds is the first source to test. Do not return to historical corner V1–V4 mining while source capability is the blocker.

### SportsGameOdds probe implementation — CLOSED / MERGED

PR #230 added a separate fail-closed SportsGameOdds capability path without performing an authenticated provider call.

Merge: `fdc7a4064fd4fd97b6a98af27b97931e593fc85b`.
Exact PR head: `f70d9232403fa50434129f61db0ce188ff8302b8`.

Contract:
- `SportsGameOdds Corner Capability Probe` remains `workflow_dispatch` only; no `push` or `schedule` trigger;
- exact prospective target remains BUNDESLIGA Union Berlin vs FC Schalke 04, kickoff `2026-09-11T18:30:00+00:00`;
- fixed requested odd ids: `cornerKicks-all-game-ou-over` and `cornerKicks-all-game-ou-under`;
- max authenticated provider requests = 1;
- API key is supplied only through secret `SPORTSGAMEODDS_API_KEY` and sent in the `x-api-key` header, never committed or placed in query parameters;
- capability requires one **available same bookmaker** offering both Over and Under at the same numeric total-corner line with explicit prices;
- consensus-only line/price, one-sided markets, unavailable bookmakers, mismatched lines, missing exact target and ambiguous identity do not confirm capability;
- no Supabase writes;
- no production `.pkl` changes;
- no account creation, trial activation or subscription change is implemented.

CI proof:
- all 6 PR workflows passed on exact head `f70d9232403fa50434129f61db0ce188ff8302b8`;
- `Multi-Market V1/V2 PR Validation` run `34249514873` compiled the new probe and included `test_multi_market_sportsgameodds_corner_capability_probe.py` in focused tests;
- focused result = **104 passed**;
- production artifact guard passed.

Fresh-main check immediately before merge confirmed `main=7cdd083425b4314f291712f4edc13803a1832626`, the same base against which PR CI ran. Merge used exact-head protection.

Post-merge proof:
- `main` became `fdc7a4064fd4fd97b6a98af27b97931e593fc85b`;
- GitHub Actions reported 0 runs for the merge SHA and 0 push runs after the merge for these paths;
- the workflow file on `main` still has only `workflow_dispatch`;
- therefore SportsGameOdds provider requests = 0, external account/subscription actions = 0, Supabase writes = 0, production `.pkl` changes = 0, prospective outcomes read = 0.

Current blocker is no longer implementation. It is the **external credential/live capability gate**: obtaining a SportsGameOdds account/API key and dispatching the one-request authenticated probe require separate explicit user permission and must not happen automatically.

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

### Prospective Market Status + live refresh priority — CLOSED / MERGED / LIVE_PROVEN 2026-09-09

PR #232 closed revision-safety gaps and made the existing market-path coverage cycle operator-ready without adding any provider call, spend policy or outcome access.

Merge: `a895012fdd65148672b9cfa4bc83ea229145346d`.
Exact PR head: `e6a08fa3b1399fc07c31564fb04982aacaa3a0a6`.
Branch base/fresh-main before merge: `2f13ba207d5cde19db55b9bf35a2b2eec54e707f`.

Revision safety:
- an older event id for the same normalized league/home/away pair is now `SUPERSEDED`, `operationally_active=false`, `refresh_due=false`, with explicit refresh reason `SUPERSEDED_PROVIDER_REVISION`;
- live proof exposed a second edge case: tied-current provider event ids for one fixture pair can share the same latest observation time, so a last-seen winner cannot be chosen honestly;
- tied-current ids are now all `QUARANTINED_REVISION`, inactive and not due; no canonical kickoff/event id is guessed;
- the live examples were two Serie A pairs: Torino–AS Roma and Como–Parma, four event ids total;
- internal hard `CONFLICT` remains fail-closed and is not masked by superseded logic.

Market Status / live priority:
- new `prospective_market_status.py` composes frozen fixture coverage, revision classification and existing league refresh priority;
- it is explicitly read-only/provider-free and does not change frozen eligibility;
- fixture live queue uses only already-existing `operationally_active`, `refresh_due` and collector cadence signals;
- deterministic ordering is earliest cutoff, then higher staleness ratio, then stable league/kickoff/event identity tie-breakers;
- `prospective_market_path_coverage_cycle.py` now emits existing coverage outputs plus `live_refresh_priority.csv` and prints a compact `PROSPECTIVE MARKET STATUS` operator view;
- Supabase client creation was moved to the actual `_fetch_snapshots()` I/O boundary so the complete cycle can be regression-tested without network/secrets.

CI proof on exact head `e6a08fa3b1399fc07c31564fb04982aacaa3a0a6`:
- all 6 PR workflows passed;
- focused `Prospective Market Path Coverage PR Validation` run `34366488263` passed;
- focused tests = **24 passed**;
- all 5 coverage/status modules compiled;
- production `.pkl` before/after hash guard passed unchanged.

Post-merge live read-only proof against Supabase `odds_snapshots` at `2026-09-09T14:56:23.614899Z`:
- actionable refresh due = **23**;
- pair-quarantined event ids = **4**;
- league priority = **SERIE_A #1 (8 due) -> LA_LIGA #2 (5 due) -> EPL #3 (10 due)**;
- top live fixture #1 = Serie A Venezia–Fiorentina (`event_id=a9656d25ca6b06be9e477a098333bd70`, kickoff `2026-09-11T18:45:00Z`);
- #2 = La Liga Sevilla–Valencia (`event_id=79bc2eff76fa09664659765d5b1ded1a`);
- #3 = La Liga Real Racing Club de Santander–Alavés (`event_id=50cc233d42943dcf77315adb0aaa6c09`);
- no Supabase writes, no provider requests, no paid credits, no prospective outcome reads, no production `.pkl` changes.

Decision: this status/priority is an operator signal only and **never authorizes paid h2h refresh**. A paid refresh still requires a separate explicit user instruction and existing quota/budget guards.

## Security follow-up

Read-only audit ранее нашёл RLS disabled на:
- `teams`;
- `predictions`;
- `match_statistics`;
- `league_prediction_ledger`;
- `epl_ai_market_pair_ledger`.

Не включать RLS автоматически; сначала отдельный access-policy audit, иначе можно сломать приложение/research.

## Текущий следующий шаг

1. The Odds API corner capability probe считать **CLOSED / CAPABILITY_MISS**; same-target rerun не делать.
2. SportsGameOdds capability implementation считать **CLOSED / MERGED** через PR #230; workflow manual-only, provider call ещё не выполнялся.
3. Следующий corner-specific gate = внешний credential/live proof: получение SportsGameOdds account/API key и один authenticated run требуют отдельного явного разрешения пользователя; автоматически не создавать account/key и не dispatch workflow.
4. Если пользователь отдельно разрешит этот внешний шаг: использовать exact Union Berlin–Schalke target и максимум 1 provider request; capability подтверждать только по same-bookmaker paired Over/Under на одной corner line с явными ценами.
5. Если SportsGameOdds live capability подтвердится: сохранить durable artifact/attestation, затем открыть отдельный preregistered `V2 expected corners vs bookmaker corner line` experiment. Если miss/нет доступа — durable negative proof и переход к Sportmonks, затем Betfair Exchange; historical corner V1–V4 STOP RULE не нарушать.
6. Market Status/live priority считать **CLOSED / MERGED / LIVE_PROVEN** через PR #232. Acquisition всё ещё stale с 2026-09-05; paid h2h refresh manual-only. Текущий read-only priority = Serie A -> La Liga -> EPL, 23 actionable paths после fail-closed revision quarantine.
7. Frozen `EPL_AI_MARKET_PAIR_V1`, `PROSPECTIVE_MARKET_PATH_V1`, `PROSPECTIVE_CORNERS10_INCREMENTAL_V1` продолжать без premature outcome reads/backfill.
8. Пока внешний SportsGameOdds gate закрыт, продолжать бесплатные/read-only задачи: outcome-free prospective sample health, collection metadata, settlement health и source/access audits.
9. RLS access-policy audit — отдельный read-only follow-up после основных research/operational blockers.

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
- User manually dispatched corner capability probe run `34246732050`; exact preregistered target verified.
- Probe result `CAPABILITY_MISS`: one provider request, 0 credits, quota stayed 193, no corner market keys/bookmakers, no writes, production model unchanged.
- The Odds API same-target corner probing is closed; do not rerun merely to hunt.
- Zero-cost public source audit ranked SportsGameOdds first, Sportmonks second, Betfair Exchange third; no signup/trial/paid calls were performed.
- PR #230 implemented the SportsGameOdds fallback probe as manual-only research infrastructure. Exact head `f70d9232403fa50434129f61db0ce188ff8302b8` passed all 6 PR workflows; Multi-Market validation run `34249514873` reported 104 focused tests passed and production artifact guard green.
- PR #230 merged as `fdc7a4064fd4fd97b6a98af27b97931e593fc85b` after fresh-main/exact-head checks. Post-merge merge SHA had 0 Actions runs and the new workflow remained `workflow_dispatch` only, so no SportsGameOdds request/account/subscription/Supabase/model action occurred.

### 2026-09-09

- PR #232 closed two market revision safety gaps: stale event ids now deactivate fail-closed, and tied-current event ids for one normalized fixture pair are all quarantined rather than guessed or double-refreshed.
- Added read-only `prospective_market_status.py` and deterministic fixture-level live refresh queue using only existing cadence/due signals; operational coverage cycle now writes `live_refresh_priority.csv`.
- Exact head `e6a08fa3b1399fc07c31564fb04982aacaa3a0a6` passed all 6 PR workflows; focused run `34366488263` = 24 passed and production hash guard green.
- PR #232 exact-head merged as `a895012fdd65148672b9cfa4bc83ea229145346d` after fresh-main remained `2f13ba207d5cde19db55b9bf35a2b2eec54e707f`.
- Post-merge Supabase read-only proof at `2026-09-09T14:56:23.614899Z`: 23 actionable due paths, 4 ambiguous event ids quarantined; priority Serie A -> La Liga -> EPL; top fixture Venezia–Fiorentina. No writes/provider spend/outcome reads/model changes.
