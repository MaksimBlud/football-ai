# Football AI — Project Continuity

Этот файл — каноническая память проекта между чатами. Source of truth: **fresh GitHub `main` + live Supabase**. Git history хранит исторический detail; здесь фиксируются только binding rules, текущие contracts/gates, доказанные live facts и следующий execution pointer.

## Правила работы

- Repo: `MaksimBlud/football-ai`, default branch `main`.
- Существенный change: fresh main -> branch -> tests -> PR -> полный CI -> fresh-main compare -> exact-head merge -> post-merge/live proof -> continuity-only update.
- Production `.pkl` нельзя менять как побочный эффект research/training. Training/research != promotion. Automatic model promotion запрещён.
- Не делать mass-clean/reset/mass-format и не перетирать параллельные изменения.
- Frozen/preregistered research contracts нельзя ослаблять задним числом; prospective outcomes нельзя читать до разрешённого gate.
- Paid provider calls остаются manual-only и требуют explicit permission; сначала использовать zero-cost/read-only proof.
- Реальные дефекты закрывать regression-тестами. Fail-closed red нельзя искусственно превращать в green.
- Forecast, value, bet decision и portfolio exposure — разные сущности и не подменяют друг друга.
- Unsupported markets/results нельзя синтезировать ради полноты UI.

---

# Research state

## `ALL_LEAGUES_MARKET_ONLY_V1_1` — FROZEN / SAMPLE_CLOSED / COLLECT, DON'T PEEK

- Freeze: `2026-09-12T02:04:34Z`; first seed kickoff: `2026-09-12T12:00:00Z`.
- Frozen seed: exact `127` immutable keys across 8 leagues.
- Gate: минимум `100` eligible events **в каждой** лиге + минимум `4` UTC kickoff months **в каждой** лиге; все 8 проходят одновременно.
- Primary sample = deterministic kickoff/event/key prefix; outcomes закрыты минимум до 24h после latest primary-prefix kickoff.
- Interim outcome peeking, threshold search, subgroup selection и performance-based optional stopping запрещены.
- Primary metrics после открытия gate: multiclass log loss + multiclass Brier; secondary: argmax accuracy; report per league + pooled micro + unweighted league macro.
- До gate разрешены только outcome-blind health/identity/completeness checks и frozen future-only capture.

## `EPL_AI_MARKET_PAIR_V1` — separate frozen EPL experiment

- Не смешивать с eight-league MARKET_ONLY cohort и не backfill его product rows как research evidence.
- Production EPL model нельзя переносить на другие лиги ради ускорения sample.
- Product bootstrap использовал durable paired-AI outputs, но это не меняет frozen research membership/gates.
- Frozen model artifact SHA used by the product bridge: `1e516fe91420fdc2d6479e9fb92b005c4a0c75c7f0f217493dd6b27fd64d99a5`.

## Historical corners — CLOSED / STOP RULE

CORNERS10 остаётся полезным football-only signal для 1X2, но не доказательством качества corner-total prediction. Historical corner-total V1–V4 не переоткрывать на тех же данных без independent evidence.

---

# Product contracts

## Semantics — CLOSED

Binding invariant: **forecast != value != bet != portfolio position**.

- `main_forecast` отвечает «что вероятнее?» и определяется model probability внутри допустимого maturity/reliability tier.
- `value_signal` — отдельный informational raw-EV signal и никогда не переопределяет forecast.
- Current tiers: 1X2 operational; total goals provisional/model-only; handicap research-only; corners total research-only.
- `bet_decision = no_bet` в Decision Framework v1.
- Canonical regression: Liverpool–Fulham — Liverpool ~67.5% остаётся main forecast, Fulham positive raw EV остаётся только value signal.

## Durable product pipeline — LIVE-PROVEN

Path: immutable prediction snapshot -> Supabase -> independent odds join by provider `event_id` -> server contract -> UI/API.

- First durable product publish: `pair-ledger-bootstrap:20260912T044914Z`, 20 EPL snapshots, 1X2-only.
- Stable product identity: provider event ID first; deterministic fixture fallback only when event ID absent.
- Odds and predictions remain independent sources; unsupported goal/BTTS/handicap/corner values не fabricated.
- Current durable snapshot count after the first Operational Automation runtime proof remains `20`; duplicate provider event IDs = `0`.

## Public web — LIVE, BUT LAGS REPOSITORY MAIN

Public alias: `https://football-ai-real-epl-snapshot.vercel.app`.

Last exact public production deployment is older than repository contracts #278–#289. Do not claim later Decision/Lifecycle/Reliability/Readiness/Operational-Automation endpoints or fields are live there until exact-main redeploy.

## Product Lifecycle v1 — CLOSED / LIVE RUNTIME-PROVEN

Append-only facts: `PREDICTION_REGISTERED -> MARKET_OBSERVED -> SETTLED`.

- Old probabilities never rewritten after result.
- Market observation uses already-stored pre-kickoff prices; it is not called closing line unless qualified.
- Settlement comes only from canonical finished-results source.
- P&L/ROI remain null while no actual betting policy/positions exist.
- State immediately before first Operational Automation runtime: `20 registered / 5 market-observed / 0 settled`.
- First real runtime appended `2 MARKET_OBSERVED + 7 SETTLED`; current live state is `20 registered / 7 market-observed / 7 settled = 34 lifecycle rows`.
- Live duplicate lifecycle `event_key` count = `0`; second runtime attempt wrote `0` new lifecycle rows.
- The seven settlements cover every canonical EPL result present for `2026-09-12`; provider aliases were normalized rather than exact-string matched (`Ipswich -> Ipswich Town`, `Hull -> Hull City`, `Tottenham -> Tottenham Hotspur`, `Nott'm Forest -> Nottingham Forest`).

## Reliability / Calibration v1 — CLOSED / ACCUMULATING SAMPLE

Primary claim scope: exact model artifact × league × 1X2.

Evidence-readiness gate: minimum `100` settled predictions exact scope + minimum `4` kickoff calendar months.

`REVIEWABLE != reliable != PASS != promotion`.

Current exact-scope evidence after runtime:
- `7` settled predictions, all EPL and all exact frozen model SHA `1e516fe91420fdc2d6479e9fb92b005c4a0c75c7f0f217493dd6b27fd64d99a5`;
- first/last settled-sample kickoffs are both on `2026-09-12`, so sample/time gates are not met;
- exact model+league slice is therefore `ACCUMULATING_SAMPLE / INCONCLUSIVE`;
- the automation report's aggregate `overall_history` evidence state is `DESCRIPTIVE_ONLY` by design because cross-scope overall history is not an exact model+league reliability claim;
- descriptive-only current sample metrics: accuracy `1/7` (~14.29%), mean multiclass Brier `0.8476987182`, mean log loss `1.3455261760`. These are **not** a reliability verdict and must not drive threshold/model/market promotion on this tiny sample.

## Portfolio / Risk v1 — CLOSED / STRUCTURAL ONLY

Only explicit future `bet_decision.status == bet` creates a structural position. Forecast/value alone never creates exposure. No staking/Kelly/bankroll policy exists in v1. Last live proof had zero actionable positions and `NO_ACTIONABLE_EXPOSURE`.

## Production Readiness v1 — CLOSED / LIVE-DATA-PROVEN

Current matrix:
- EPL / 1X2 = `OPERATIONAL`;
- EPL / Total Goals = `PROVISIONAL`;
- EPL / Handicap = `RESEARCH_ONLY`;
- EPL / Corners Total = `RESEARCH_ONLY`.

New scopes can automatically reach at most `REVIEWABLE`; `OPERATIONAL` requires explicit approval. Readiness never auto-promotes a model/market, changes forecast ranking, creates a bet or opens a research gate.

---

# Product Operational Automation v1 — LIVE RUNTIME-PROVEN / IDEMPOTENCY-PROVEN

Version: `product-operational-automation.v1`.

Purpose: connect already-approved durable product components into a repeatable scheduled cycle without creating a new forecasting, provider or betting system.

Cycle:
1. read already-produced outcome-free EPL AI rows from `epl_ai_market_pair_ledger`;
2. publish a product snapshot only for a provider fixture that has no product prediction yet;
3. reload durable state so lifecycle uses the real persisted prediction ID;
4. append missing lifecycle facts from stored odds and canonical finished results;
5. recompute read-only Reliability / Production Readiness summaries;
6. emit audit report.

Safety contract:
- no paid-provider call;
- no model inference/training/promotion;
- no frozen research target read;
- no bet/stake action;
- existing private Supabase write path only; public web access never becomes a write fallback;
- pair row must be EPL, exact frozen experiment, have provider event ID, be generated strictly pre-kickoff and match the frozen model SHA above.

Forecast revision guard:
- automation publishes only the **first** product forecast per provider fixture;
- newer AI generations for already-published fixtures are held for a future explicit revision/evaluation contract;
- this prevents repeated versions of one match from inflating Lifecycle/Reliability sample.

Operational hardening:
- lifecycle reads are paginated; regression covers `6001` rows and removes the old hidden `5000`-row cap;
- source states: `NO_FUTURE_EVENTS`, `COVERED`, `READY_TO_INGEST_PREDICTIONS`, `WAITING_FOR_PREDICTION_SOURCE`;
- missing model source fails closed; bookmaker probability is never substituted for model probability;
- production workflow triggers are `workflow_dispatch` plus cron `37 */2 * * *`;
- permissions remain `contents: read`; runtime receives only private Supabase credentials and does not require The Odds API key.

PR #286 — implementation:
- exact head `66a42a559f792d4f2d6fd187509c1b521c947f84`;
- all six required CI contours green: Product, Research, Serie A, Bundesliga, Ligue 1, Eredivisie;
- production artifact guard green;
- exact-head merge `680ce8a694f6f49dd83452f0e3c776593c70a5e2` at `2026-09-13T05:33:24Z`.

Pre-runtime live proof:
- future EPL odds events = `13`;
- product-covered events = `13/13`;
- future paired-AI events = `13`;
- invalid pair timing = `0`;
- one model SHA, exact frozen SHA;
- product snapshots total = `20`;
- lifecycle = `20 registered / 5 market-observed / 0 settled`.

Scheduler activation observation:
- because cron is `37 */2 * * *`, the first full natural slot after the `05:33:24Z` implementation merge was `06:37 UTC`, not `05:37 UTC`;
- by approximately `07:39 UTC`, GitHub still showed no `schedule` run for this workflow even though other scheduled workflows in the repository had executed;
- no direct Supabase inserts were used to manufacture runtime proof;
- the connector exposed no safe workflow-dispatch creation action, so a bounded path-scoped `push` bootstrap was used through the normal branch/PR/full-CI/exact-head-merge path;
- this proves the workflow executor, credentials, append-only cycle and idempotency. A natural `event=schedule` occurrence itself has not yet been separately observed and must not be falsely claimed.

PR #288 — bounded runtime bootstrap:
- branch `product-runtime-proof`, exact head `2c75d1470ba0e28bbfa8a88dd565e41d47daa9ce` from then-current main `e2cd7baa3b7572a32cbdc22c38b8839ea4ab7a9d`;
- diff: one workflow file, `+5/-0`, adding only a `main` push trigger scoped to `.github/workflows/product-operational-automation.yml`;
- no permissions, runtime code, secret contract, paid-provider or model-action change;
- all six required CI contours green;
- exact-head merge `182f0fc0a3fbd0e392b08a3c77f8579ae7b61ebd` at `2026-09-13T07:43:41Z`.

First real Actions runtime:
- workflow run ID `34745945144`, run number `1`, event `push`, head `main`, exact SHA `182f0fc0a3fbd0e392b08a3c77f8579ae7b61ebd`, created `2026-09-13T07:43:43Z`;
- first job ID `103693795481`, conclusion `success`;
- checkout proved exact main SHA; `GITHUB_TOKEN` permissions stayed read-only for contents/metadata;
- private Supabase credential contract passed with values masked;
- first cycle report `as_of_utc=2026-09-13T07:44:01.932364+00:00`, `status=HEALTHY_NOOP`, `prediction_source.state=COVERED`;
- applied: `product_prediction_snapshots=0`, `lifecycle_events=9`;
- the 9 append-only facts were exactly `2 MARKET_OBSERVED + 7 SETTLED`;
- pending after application: `0` product snapshots and `0` lifecycle events;
- future source coverage remained `13/13`, with `ready_from_pair_ledger=0`, `revision_candidates_held=0`, `waiting_for_prediction_source=0`;
- safety report: paid-provider/model inference/model training/model promotion/betting/staking/automatic forecast revision/research-target reads all `false`; lifecycle writes append-only `true`;
- first report artifact ID `10314022013`, ZIP digest `sha256:f47be94c330ea3ac315870519cae3603414cf3653af3ccd0578ae2686aa6c02b`.

Runtime idempotency proof:
- the successful job was rerun on the same exact workflow run/head; second job ID `103693963665`, conclusion `success`;
- second cycle `as_of_utc=2026-09-13T07:45:37.010832+00:00`;
- applied on rerun: `product_prediction_snapshots=0`, `lifecycle_events=0`;
- pending remained `0/0`, coverage remained `13/13`, lifecycle remained `34` rows, product predictions remained `20`;
- second report remained `HEALTHY_NOOP / COVERED`, with `7` settled predictions and no paid/model/betting actions;
- second artifact ID `10313827598`, ZIP digest `sha256:6e7f3221612c64cc0d4d041eb6b965e8343b3f9c25ec2076e1bdc944d7694c15`.

Post-runtime live Supabase proof at `2026-09-13T07:47:06.829933Z`:
- product snapshots `20`, distinct event IDs `20`, duplicate product event IDs `0`;
- lifecycle rows `34`: `20 registered / 7 market-observed / 7 settled`;
- duplicate lifecycle event keys `0`;
- latest lifecycle write remains exactly first-cycle time `2026-09-13T07:44:01.932364Z`; rows after that time = `0`, proving rerun made no durable write;
- future EPL odds/product/valid-pair events = `13/13/13`; missing product = `0`; waiting for pair = `0`;
- product-not-pre-kickoff = `0`; market source post-kickoff = `0`; pair model generation not-pre-kickoff = `0`;
- pending market observations = `0`; no matching canonical result remains unsettled.

PR #289 — bootstrap cleanup:
- exact head `d10269aa7d377e2c091043e72f3326ea44eaac2d`;
- diff: same workflow file only, `+0/-5`, removing the temporary push trigger;
- all six required CI contours green, including production-artifact guard;
- fresh-main check remained exact bootstrap merge before cleanup merge;
- exact-head merge `26608134c1cb68a6ce68da5d8c3c304870d88f4c` at `2026-09-13T07:49:08Z`;
- post-merge workflow is restored to `workflow_dispatch` + `37 */2 * * *` schedule only.

---

# Durable PR reference

Product chain: #267–#277 foundation/live pipeline; #278 Decision Framework; #279 Lifecycle; #280 lifecycle security hardening; #281 Reliability; #282 Portfolio/Risk; #283 continuity correction; #284 Production Readiness; #286 Operational Automation v1; #287 pre-runtime continuity; #288 bounded runtime bootstrap; #289 bootstrap cleanup.

All substantive product/runtime PRs above passed Product + required Research/league CI before exact-head merge.

---

# Текущий execution pointer

## Research

- `ALL_LEAGUES_MARKET_ONLY_V1_1`: **collect, don't peek / SAMPLE_CLOSED**.
- `EPL_AI_MARKET_PAIR_V1`: separate frozen experiment; do not infer cohort membership from product bootstrap.
- Any paid refresh = separate manual gate.
- Candidate V2/model promotion stays closed until corresponding evidence gate.

## Product

Current foundation:

`Prediction delivery -> Decision Framework -> Lifecycle -> Reliability -> Portfolio/Risk -> Production Readiness -> Operational Automation`

Operational Automation executor/runtime/idempotency block is now closed. The natural GitHub `schedule` event should still be observed when a later cron occurrence exists, but lack of that observation must not be confused with a failure of the already-proven runtime executor.

Следующая safe последовательность:
1. **Exact-main web deployment**: redeploy the public alias from then-current exact `main`, then smoke-check `/`, `/health`, `/api/product/markets`, `/api/product/reliability`, `/api/product/portfolio`, `/api/product/readiness` and verify the deployment commit SHA equals GitHub main.
2. **Second markets through readiness gates**: goal total first. Close its live model probability, bookmaker-price, settlement, lifecycle and empirical-reliability contracts before any production activation.
3. Handicap/corners stay research-only until their own probability/price/settlement/evidence contracts exist; CORNERS10 as a 1X2 signal is not a corner-total production model.

Betting/staking policy remains a separate future contract until enough empirical evidence exists.

---

# 2026-09-13 audit trail

Today Operational Automation v1 was designed, implemented, regression-tested, merged, live-runtime-proven, idempotency-proven and returned to its intended schedule/manual trigger surface.

Key facts and decisions:
- reused existing durable sources instead of running ad-hoc inference;
- kept missing prediction source as an explicit fail-closed state;
- introduced first-prediction-only automation and held revisions to protect sample integrity;
- fixed lifecycle pagination before the current odds table could exceed the old hidden cap;
- added scheduled append-only orchestration with no paid-provider dependency;
- PR #286 passed all six CI contours and exact-head merged as `680ce8a694f6f49dd83452f0e3c776593c70a5e2`;
- PR #287 recorded the honest pre-runtime boundary and merged as `e2cd7baa3b7572a32cbdc22c38b8839ea4ab7a9d`;
- corrected the cron interpretation: after the `05:33:24Z` merge, the first full `37 */2` slot was `06:37Z`; by ~`07:39Z` no schedule-created run existed;
- did not bypass the missing schedule event with direct SQL writes;
- PR #288 added only a bounded path-scoped main push trigger, passed all six CI contours, exact-head merged as `182f0fc0a3fbd0e392b08a3c77f8579ae7b61ebd`, and created the first real runtime run `34745945144`;
- first runtime passed credential check and append-only cycle and wrote exactly `2 MARKET_OBSERVED + 7 SETTLED`, no product snapshots;
- all seven settlements were reconciled to canonical `2026-09-12` EPL results; four required existing provider alias normalization rather than exact-string matching;
- reliability moved from no settled data to a real but tiny exact-scope sample of `7`, state `ACCUMULATING_SAMPLE / INCONCLUSIVE`; aggregate overall history remains `DESCRIPTIVE_ONLY` by contract;
- same-head job rerun applied `0/0`, proving runtime idempotency;
- post-run live audit found no product duplicates, no lifecycle event-key duplicates, no post-kickoff provenance violations, no pending eligible lifecycle facts, and future coverage `13/13`;
- PR #289 removed the temporary trigger, passed all six CI contours, exact-head merged as `26608134c1cb68a6ce68da5d8c3c304870d88f4c`, restoring production workflow to `workflow_dispatch + schedule`;
- no Odds API credits, production model artifacts, training, inference, promotion, bets or stakes were used in this runtime-proof closure.

# Current checkpoint

- Latest product/runtime code main before this continuity-only update: `26608134c1cb68a6ce68da5d8c3c304870d88f4c`.
- Durable product snapshots: `20` total; duplicate event IDs `0`; future EPL coverage `13/13`.
- Lifecycle: `20 registered / 7 market-observed / 7 settled = 34`; duplicate event keys `0`; pending eligible lifecycle facts `0`.
- Reliability exact frozen EPL scope: `7` settled, `ACCUMULATING_SAMPLE / INCONCLUSIVE`; do not overinterpret descriptive metrics.
- Readiness: EPL 1X2 operational; goals provisional; handicap/corners research-only.
- Operational Automation executor/runtime/idempotency is live-proven. Natural `event=schedule` occurrence is still an external scheduler observation, not an unproven runtime-code path.
- Production workflow is restored to `workflow_dispatch + cron 37 */2 * * *`, `contents: read`, no Odds API key.
- Public Vercel runtime still lags repository main; **exact-main redeploy is the next product block**.
- Research V1.1 outcome gate remains closed; no-peek is binding.
