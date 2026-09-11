# Serie A + La Liga prospective capture v1

Status: FROZEN RESEARCH CONTRACT
Date frozen: 2026-09-11

## Goal

Enable pre-match prospective capture for Serie A and La Liga without overstating model readiness.

## Scientific boundary

- Research only. No production promotion and no production model artifact writes.
- EPL production models must not be used as a substitute model for either league.
- Existing completed historical results remain development evidence only.
- La Liga pure-AI v1, hybrid v1, and nested historical v1 remain closed/rejected and are not reopened by this protocol.
- Serie A historical candidate-development work remains independent; prospective capture does not itself make Serie A AI-ready.
- MARKET_ONLY observations may be captured prospectively for both leagues when the source market snapshot and the ledger capture both occur before kickoff.
- Every observation must preserve immutable source provenance: `source_event_id` and `source_snapshot_time_utc`.
- AI observations may be captured only when a league-specific frozen candidate manifest explicitly reports AI eligibility for the league. If not eligible, the capture tool must fail closed for AI while still allowing MARKET_ONLY capture.
- A captured row must never be converted retrospectively from MARKET_ONLY into AI evidence after kickoff or after outcomes are known.
- Outcome/settlement fields are forbidden at capture time.
- No paid Odds API request is authorized by this contract. Capture must operate only on already-available fixture/snapshot inputs unless a separate explicit paid authorization exists.

## Prospective counter semantics

The first pre-match row written under this contract is observation 1/100 for that league/protocol. The denominator is frozen at 100 prospective observations. Rows count only if all capture-time invariants pass.

## Required capture-time invariants

1. Canonical league is one of `SERIE_A` or `LA_LIGA`.
2. Canonical fixture identity includes league, normalized home team, normalized away team, and UTC kickoff.
3. `source_event_id` is present and non-empty.
4. `source_snapshot_time_utc` is timezone-aware and strictly before kickoff.
5. `source_snapshot_time_utc <= captured_at_utc < commence_time_utc`.
6. Market 1X2 prices are present, finite, and positive.
7. No result, score, settlement, realized outcome, or post-kickoff field is accepted.
8. Duplicate canonical fixture/protocol rows are idempotent only when market values and source provenance are identical; conflicting rewrites fail closed.
9. AI fields are forbidden unless a league-specific frozen eligibility manifest says AI is eligible.
10. Production `.pkl` files are never read or written by this capture protocol.

## Interpretation

A MARKET_ONLY row is valid prospective market evidence, not prospective AI evidence. Passing this protocol therefore means `CAPTURE_READY=true`, not `MODEL_READY=true` or `PROSPECTIVE_AI_READY=true`.
