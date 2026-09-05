# Multi-Market Card V1 — Operational Status

Status: **IMPLEMENTATION COMPLETE / RESEARCH-ONLY / ACTIVATION EXTERNALLY GATED**

## Scope

One match card exposes market-backed no-vig probabilities for:

- 1X2;
- handicap / spread;
- total goals (2.5 preferred when quoted);
- total match corners;
- home-team corner total;
- away-team corner total.

No missing probability is synthesized. If a bookmaker market is unavailable, the viewer displays `Нет данных`.

## Data contract

The canonical additional-market store is `public.league_multi_market_snapshots`, defined by migration `supabase/migrations/202609050001_league_multi_market_snapshots.sql`.

Rows are immutable, research-only, pre-kickoff snapshots keyed by `league + event_id + snapshot_time`. Existing `odds_snapshots`, `league_prediction_ledger`, production inference, calibrators, thresholds and `.pkl` artifacts remain untouched.

The viewer reads only the latest valid pre-kickoff multi-market snapshot for the same canonical `league + event_id` as the 1X2 ledger row.

## Provider coverage proof

A live read-only audit on 2026-09-05 confirmed that The Odds API currently exposes spread, goal-total and football corner markets for sampled events in multiple supported leagues. Coverage is event/bookmaker dependent; samples in Eredivisie/RPL did not expose all corner markets, so absence is a first-class state rather than an error.

The live audit also established the team-corner outcome contract used by the parser: `name = Over/Under`, `description = team`.

## Quota safety

Additional football markets are event-level and quota-sensitive. Multi-Market V1 therefore:

- never calls The Odds API from the viewer;
- uses existing `odds_snapshots.event_id` for event discovery;
- collects only fixtures within 24 hours of kickoff;
- collects no more often than once per six hours per event;
- performs a zero-cost `/sports` quota preflight;
- makes no paid market request when remaining quota is below `500`;
- stops before the hard reserve of `100` remaining requests.

The first post-hardening live status observed `remaining=215`, so paid collection is intentionally blocked.

## Activation gates

Two external gates must both be true:

1. `league_multi_market_snapshots` migration has been applied to Supabase;
2. provider quota is at least the frozen collection-start threshold of `500` remaining requests.

`.github/workflows/multi-market-activation-status.yml` checks these gates daily using read-only DB access and a zero-cost provider request. It never applies DDL, writes snapshots, or activates production behavior.

Once both gates become ready, `.github/workflows/multi-market-cycle.yml` can collect append-only research snapshots automatically. The production viewer is already schema-compatible and requires no model change to display them.

## Production isolation

Multi-Market V1 is a market-observation/display block. It does not promote a model, change production probabilities, retrain artifacts, or claim incremental predictive value.
