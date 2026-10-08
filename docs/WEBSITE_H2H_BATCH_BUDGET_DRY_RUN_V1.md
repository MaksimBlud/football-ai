# Football AI — H2H league-wide credit budget (draft, no activation)

Issue: #580; parent #578. This proposal is **OFFLINE_DRY_RUN_ONLY**. It does not modify `.github/workflows/odds-snapshots.yml`, make HTTP requests, trigger GitHub Actions, write Supabase, train models, or authorize using credits.

## What already exists (do not rewrite)
- The Odds API `GET /v4/sports/{sport}/odds/?regions=uk&markets=h2h` returns **all provider-available future fixtures for one league** in a single request. `the_odds_service.py` and `save_epl_odds_snapshot_with_bookmakers.py` already use that.
- Price for a single market/region is typically **1 credit per league batch**, not per fixture. Never assume the provider returned the full next round: horizon and bookmaker coverage vary.
- `odds_api_budget_guard.py` checks the provider's free `/sports/` endpoint and protects the existing **100 credit hard reserve**.
- Existing paid workflows are deliberately **manual only**. `tests/test_paid_provider_workflow_budget_contract.py` requires that. Their authorization gate must not be relaxed by an unrelated MVP patch.

## Conservative candidate (NOT LIVE)
- Evaluate at **Monday and Friday, 12:00 UTC**, not every 2–12 hours. Initial public MVP default = **EPL only**.
- One market `h2h` and one region `uk` per league: one paid sport-level batch if separately authorized.
- Optional eight-league candidate scope is supported for dry-run comparison. Two candidate windows/week across eight leagues yields at most **80** H2H league-batch credits in a five-week interval (not 80 HTTP calls to individual fixtures). With EPL only, at most **10** in a five-week interval. These are ceiling illustrations, not observed usage.
- Shared provider billing-cycle ceiling: **80 used credits** (counts OTHER research/market calls too); separate hard reserve **100 remaining**. If either quota header is missing, block.
- Wait at least **48 h** after the last persisted snapshot for the league. Do not assume old snapshots imply new odds.
- Do not equate calendar month with provider billing period. Provider `x-requests-used` / `x-requests-remaining` are authoritative for the quota cycle; an external automation would also need safe persisted idempotency and billing-period verification before activation.
- Research-only corners/alternate market requests remain per-event or different market costs and are NOT covered by this H2H plan.

## Dry-run examples
```bash
python odds_h2h_batch_dry_run.py --now-utc 2026-10-09T12:00:00Z
python odds_h2h_batch_dry_run.py --now-utc 2026-10-09T12:00:00Z --provider-used 11 --provider-remaining 489 --leagues EPL,LA_LIGA
```

The second command uses **illustrative** external inputs, not real account counters. It only prints JSON with `paid_provider_requests=0`, `paid_provider_credits=0`, and `paid_collection_authorized=false`. It is impossible for this script to spend a credit.

## Actual activation prerequisite
A separate explicit user permission covering number of credits and frequency; verify current provider quota without spending credits; prove server-side shared billing-cycle budget, hard reserve, collector idempotency, event/quote timestamps, schedule gate and complete CI. Only after that could a future PR change manual-only collector scheduling. Until then, continue public read-only API/site work independently.
