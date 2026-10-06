# Direction 2 closure — team change faster than market

Status: **PROGRAM_DONE / BLOCKED_BY_TIMESTAMP_SAFE_SOURCE_AND_DUPLICATE_PROXY_EVIDENCE**

This roadmap direction was audited after Direction 1 reached its terminal V5 result. No new
match outcomes were opened for this closure.

## Research question

Can a genuinely abrupt change in a team be known before kickoff and improve 1X2
probabilities beyond the bookmaker market before that change is fully priced?

The permitted mechanisms were:

- manager or head-coach change;
- key-player absence or return;
- confirmed lineup or squad shift;
- explicit tactical shift;
- sharp football-process shift.

## Repository duplicate and source audit

### Manager, lineup, availability and tactics

The repository has already completed the relevant capability work:

- `LINEUP_STRENGTH_CAPABILITY_V1` found no supported historical point-in-time
  lineup/player-strength inputs.
- `TACTICAL_MATCHUP_CAPABILITY_V1` found no explicit formation, possession/passing
  structure or pressing fields with point-in-time provenance.
- `COACH_LINEUP_AVAILABILITY_REGIME_CHANGE_V1` detected no manager, coach, lineup,
  starting-XI, injury or suspension fields in the existing Football-Data schemas.
- The historical signal-lab closure prohibits reconstructing injury availability from
  later start/end dates because event-time dates do not prove information-time
  availability.

This is a source-feasibility result, not evidence that those mechanisms are useless.

### Prospective availability

`PROSPECTIVE_AVAILABILITY_SIGNAL_LAB` already freezes the valid prospective
`MARKET_MODEL` versus `MARKET_AVAILABILITY` experiment. Its engineering contract is
complete, but its scientific experiment remains externally gated:

- the two required additive Supabase tables are absent;
- the available API-Football free-plan credential has no current-season injury coverage
  for all frozen leagues;
- applying the migration requires external database-management access;
- collection would require Supabase writes, which this Research Brain is explicitly
  forbidden to perform.

Creating another availability child would duplicate this frozen experiment and would
not remove its external dependencies.

### Sharp process-shift proxies

The zero-cost match-stat proxies are not fresh independent information:

- `TEAM_STRENGTH_TRAJECTORY_V1` already tested five-match Elo trajectory and
  performance-versus-expectation residuals. It was strong football-only evidence but
  did not prove stable improvement over `MARKET_MODEL`.
- `SHOT_QUALITY_PROXY_V1` already tested leakage-safe shots/SOT process and was
  market-incremental negative.
- `TRAJECTORY_SHOT_INTERACTIONS_V1` was negative and closed.
- Issue #562 tested a distinct points-versus-SOT-process divergence on independent
  Bundesliga/Ligue 1 temporal OOS data; its untouched-test gate failed.

Recasting these opened continuous trajectories as an “abrupt” threshold, alternate
window, sign, interaction or change-point selected after the existing results would be
proxy relabelling and post-hoc family expansion, not a genuinely independent source.

## Decision

No allowed mechanism is both:

1. genuinely point-in-time;
2. available from a zero-cost source under current authority;
3. independent of already tested trajectory/process families; and
4. executable without prohibited Supabase writes, paid data or post-hoc proxy design.

Direction 2 is therefore closed as
**BLOCKED_BY_TIMESTAMP_SAFE_SOURCE_AND_DUPLICATE_PROXY_EVIDENCE**.

This closure authorizes no betting, model promotion or production change. A future
reopening requires a genuinely new archived pre-kickoff source or an already-authorized
prospective dataset that passes its frozen readiness gate. It must not be reopened by
renaming historical aggregate proxies.
