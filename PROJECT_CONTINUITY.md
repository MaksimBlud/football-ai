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

## Public web — LIVE, BUT LAGS REPOSITORY MAIN

Public alias: `https://football-ai-real-epl-snapshot.vercel.app`.

Last exact public production deployment is older than repository contracts #278–#286. Do not claim later Decision/Lifecycle/Reliability/Readiness/Operational-Automation endpoints or fields are live there until exact-main redeploy.

## Product Lifecycle v1 — CLOSED / LIVE INITIALIZED

Append-only facts: `PREDICTION_REGISTERED -> MARKET_OBSERVED -> SETTLED`.

- Old probabilities never rewritten after result.
- Market observation uses already-stored pre-kickoff prices; it is not called closing line unless qualified.
- Settlement comes only from canonical finished-results source.
- P&L/ROI remain null while no actual betting policy/positions exist.
- Live state immediately before first Operational Automation runtime proof: `20 registered / 5 market-observed / 0 settled`.

## Reliability / Calibration v1 — CLOSED / WAITING FOR SAMPLE

Primary claim scope: exact model artifact × league × 1X2.

Evidence-readiness gate: minimum `100` settled predictions exact scope + minimum `4` kickoff calendar months.

`REVIEWABLE != reliable != PASS != promotion`.

Current state: `NO_SETTLED_DATA / INCONCLUSIVE`. Metrics after settlements include accuracy, multiclass Brier/log loss, skill/improvement vs uniform, calibration buckets and top-pick ECE.

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

# Product Operational Automation v1 — MERGED / CI-PROVEN / FIRST RUNTIME PROOF PENDING

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
- scheduled at minute `37` every two hours, after the existing EPL AI pair cycle and before the older EPL live-cycle.

PR #286:
- exact head `66a42a559f792d4f2d6fd187509c1b521c947f84`;
- all six required CI contours green: Product, Research, Serie A, Bundesliga, Ligue 1, Eredivisie;
- production artifact guard green;
- exact-head merge `680ce8a694f6f49dd83452f0e3c776593c70a5e2` at `2026-09-13T05:33:24Z`.

Live pre-runtime proof after merge:
- future EPL odds events = `13`;
- product-covered events = `13/13`;
- future paired-AI events = `13`;
- invalid pair timing = `0`;
- one model SHA, exact frozen SHA;
- product snapshots total = `20`;
- lifecycle = `20 registered / 5 market-observed / 0 settled`;
- equivalent plan found `0` missing registrations and `2` legitimate missing market observations;
- canonical EPL finished-results source reaches `2026-09-12`.

Runtime-proof boundary:
- merge landed only ~4 minutes before the first `05:37 UTC` cron slot;
- no durable effect appeared in that short activation window, so no successful scheduled run is claimed yet;
- no manual lifecycle write was used to manufacture a green proof;
- bounded follow-up verification is scheduled after the next cron window; success or failure must be verified from GitHub/live Supabase and this file updated again.

---

# Durable PR reference

Product chain: #267–#277 foundation/live pipeline; #278 Decision Framework; #279 Lifecycle; #280 lifecycle security hardening; #281 Reliability; #282 Portfolio/Risk; #283 continuity correction; #284 Production Readiness; #286 Operational Automation v1.

All substantive product PRs passed Product + required Research/league CI before exact-head merge.

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

Следующая safe последовательность:
1. **Close first real Operational Automation runtime proof** after the next scheduled cycle. This is an external time-gate only: do not fabricate proof, manually insert lifecycle rows for optics or weaken safety/research gates. If runtime fails, fix the real cause through branch -> regression -> PR -> full CI -> exact-head merge.
2. **Exact-main web deployment**: public alias must be redeployed from then-current exact `main`, not from a proof runtime.
3. **Second markets** through readiness gates: goal total first; handicap/corners only after their own model/price/settlement/evidence contracts.

Betting/staking policy remains a separate future contract until enough empirical evidence exists.

---

# 2026-09-13 audit trail

Today Operational Automation v1 was designed, implemented, regression-tested, merged and live-data-audited.

Key decisions:
- reused existing durable sources instead of running ad-hoc inference;
- kept missing prediction source as an explicit fail-closed state;
- introduced first-prediction-only automation and held revisions to protect sample integrity;
- fixed lifecycle pagination before the current odds table could exceed the old hidden cap;
- added scheduled append-only orchestration with no paid-provider dependency;
- PR #286 passed all six CI contours and exact-head merged as `680ce8a694f6f49dd83452f0e3c776593c70a5e2`;
- live coverage after merge remained `13/13`, with zero invalid pair timing and exact frozen model provenance;
- two market-observation lifecycle facts are legitimately waiting for the first successful scheduled cycle;
- first short cron activation window is not being misreported as success;
- a bounded follow-up check will close or repair the runtime proof and update continuity again.

# Current checkpoint

- GitHub product-code main: `680ce8a694f6f49dd83452f0e3c776593c70a5e2`.
- Durable product snapshots: `20` total; current future EPL coverage `13/13`.
- Lifecycle: `20 registered / 5 market-observed / 0 settled`; `2` market observations pending equivalent plan.
- Reliability: `NO_SETTLED_DATA / INCONCLUSIVE`.
- Readiness: EPL 1X2 operational; goals provisional; handicap/corners research-only.
- Operational Automation implementation is merged and CI-proven; first scheduled runtime execution is the only unclosed proof item in this block.
- Public Vercel runtime still lags repository main.
- Research V1.1 outcome gate remains closed; no-peek is binding.
