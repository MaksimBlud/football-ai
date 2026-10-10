# Signal Scout — BSD consensus odds point-in-time audit (2026-10-10)

Status: **BLOCKED_BY_SOURCE**. Outcome-free. No hypothesis promoted; no new Scout Issue.

## Scope and source of truth
- Fresh `main`: `research/programs/registry.json` (14 programs: 13 PROGRAM_DONE, 1 BLOCKED), `PROJECT_CONTINUITY.md` (frozen cohorts, outcome-peeking and no-paid-data rules).
- Issue search for `SIGNAL-SCOUT` returned no matching existing candidate issues. No new family or OOT reuse is authorized.
- This note audits the previously proposed BSD data source, **not** a new independent signal or a test of football outcomes.

## Official evidence (read on 2026-10-10)
1. https://sports.bzzoiro.com/docs/football/odds-predictions/ — free `/api/v2/odds/` gives one consensus row per event × market × outcome (three rows for 1X2); named-bookmaker quotes and comparison are paid.
2. Same documentation: `updated_at` is **last observation**, not last price change; `opening_decimal_odds`/`opening_at` denote **first observed** quote; `previous_decimal_odds` is the immediately previous price step, not a complete event history. There is no documented as-of parameter or historical-snapshot endpoint in this interface. Thus a currently returned opening/current row **cannot** be treated as a verified 48h pre-kickoff full 1X2 snapshot.
3. https://sports.bzzoiro.com/pricing/ — free football tier: 7,500 requests/day, consensus only; named-bookmaker odds paid.
4. https://sports.bzzoiro.com/docs/api-license/ — API data may be retained for internal research and historical snapshot archives; derived forecasts may be published, with restrictions on raw-data redistribution.
5. https://sports.bzzoiro.com/docs/football/ — free `/api/v2/coverage/` is documented as unauthenticated and provides forward fixture coverage.

## Verification boundary
- Documentation/schema: **confirmed**.
- Real 1X2 row response: **not confirmed** (API requires a user token; web access could not retrieve the API endpoint, and the container has no external DNS). Do not invent counts or odds.
- Real 48h pre-kickoff complete trio coverage, historical timestamps, and matching weather forecast availability: **not confirmed**.
- Retrospective use of `opening_at` as a fixed 48h checkpoint: **invalid** without proof it is exactly the target decision-time quote.
- Free prospective collection may be possible with a valid free token, but it must be owned by the appropriate data/backend process; Scout does not configure cron, write Supabase, or modify another agent.

## Strict outcome-free feasibility gate (future owner: Research Brain after source evidence)
1. On a predeclared future fixture universe, capture all three `HOME/DRAW/AWAY` consensus rows in **one immutable request window** at decision time `T = kickoff - 48h` (predeclared tolerance, e.g. ±15 min), with collector receipt UTC timestamp, event id, kickoff UTC, provider `updated_at`, `opening_at`, source license version and response hash. Do not backfill later values.
2. Require all 3 positive finite odds and `provider_updated_at <= receipt_utc < kickoff`; reject mismatched event identity and changed kickoff without an immutable version trail.
3. Count coverage per league, season, and fixed decision-time window without reading outcomes; preregister minimum acceptable coverage before sample collection.
4. Align with a historical single-run weather forecast whose **publication availability time**, not just model init, is before decision time. Missing/late weather fails closed.
5. Only Research Brain may freeze training/validation/untouched-OOT cohorts and assess multiclass Brier/log-loss against contemporaneous de-vigged market baseline. Negative controls: shuffled weather between fixtures within frozen league/time strata, future-weather leakage detector, missingness-only feature, and market-only comparator. No outcomes may be accessed in Scout.
6. STOP if the timestamp/provenance/rights/coverage gate fails; do not weaken the horizon or select leagues post hoc.

## Decision
BSD is a promising **future capture** source, not verified free **historical 48h odds**. Prior source optimism is corrected. Existing weather hypothesis remains BLOCKED_BY_SOURCE; no new candidate Issue and no Research Brain handoff.

## Operational integrity
No paid API requests, Supabase writes, production artifacts, reserved-outcome reads, model training, registry changes, or production deployment. GitHub scout branch only.

## 24-hour productivity experiment — evidence available
In this run: 0 nonduplicate data-feasible hypotheses transferred, 0 new Scout Issues, 1 source contract corrected. Previous visible Scout reports likewise state 0 handoffs, but do not expose reliable per-run wall-clock durations. Therefore duration acceleration **cannot** be quantified from available evidence; do not infer a speedup.
