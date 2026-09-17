# FIVE_DOLLAR_CORNERS_BACKFILL_PREFLIGHT_RESULT_V1

## Status

`HISTORY_ACCESS_BLOCKED_BY_PLAN`

Date: 2026-09-17.

This record captures the one-request live preflight for the already-frozen `CORNERS10_BET365_MARKET_V1` historical backfill.

## What was tested

The repository used the configured `FIVE_DOLLAR_FOOTBALL_API_KEY` to request the earliest frozen historical window:

- league: EPL;
- season: `2016-17`;
- endpoint family: official 5DollarFootballAPI league fixtures;
- `status=finished`;
- `include=odds`;
- request count: exactly 1.

No full backfill was started.

## Result

The provider rejected the frozen historical bulk-odds window because the current account plan does not expose it.

Recorded live result:

- status: `HISTORY_ACCESS_BLOCKED_BY_PLAN`;
- reason: `provider plan does not expose frozen historical bulk odds window`;
- provider requests: `1`;
- model evaluation performed: `false`;
- betting enabled: `false`.

GitHub Actions run: `35240146876`.

Artifact:

- name: `five-dollar-corners-backfill-preflight`;
- artifact id: `10504899633`;
- digest: `sha256:0dfc538c2ce051a95be2ac73c2f83e5aca1a699642842d3ebd2a30c466030d74`.

## Interpretation

This is a data-access result, not a predictive result.

It does **not** mean `CORNERS10_TOTAL` failed, and it does **not** change the frozen V1 methodology. The direct Bet365 corner-market evaluation remains unopened because the required 2016-17 through 2025-26 provider history has not been acquired.

The repository must not substitute a shorter Free/Pro history window and present it as the preregistered V1 test.

## Next gate

The full frozen backfill may run only after the configured provider account exposes the preregistered historical window back to at least 2016-17 with bulk odds access.

Once that access exists:

1. rerun the preflight;
2. require `HISTORY_ACCESS_CONFIRMED` / preflight `PASS`;
3. execute the frozen backfill once and persist raw plus normalized artifacts;
4. audit coverage before opening validation/OOT model metrics;
5. run the already-frozen evaluator without retuning.

A provider subscription purchase or upgrade remains an explicit external user action and is not authorized by this record.

## Safety proof

The preflight workflow completed with the production `.pkl` hash guard unchanged. No Supabase writes, The Odds API calls, production promotion, model evaluation, ROI calculation, or betting action occurred.
