# Continuity Addendum — Serie A + La Liga prospective capture ready

Date: 2026-09-11
PR: #243 — Freeze non-EPL prospective market capture for Serie A and La Liga
Branch: `research/serie-a-la-liga-prospective-capture-v1`
Implementation proof head before this continuity commit: `c1533bbfcdceb8c30ed483fe6da30fc38e8afcb6`

## Frozen protocol

`NON_EPL_MARKET_ONLY_V1`

- leagues: `SERIE_A`, `LA_LIGA`
- target: 100 prospective observations per league
- observation counter starts at `1/100` for the first valid pre-kickoff row
- canonical fixture identity: league + normalized home team + normalized away team + UTC kickoff + protocol
- capture must occur strictly before kickoff
- finite positive 1X2 decimal odds are required
- outcome, score, settlement and other post-match fields are rejected at capture time
- AI/model fields are rejected unless a separate league-specific frozen AI eligibility contract exists
- duplicate canonical rows are idempotent; conflicting rewrites fail closed
- malformed/non-contiguous existing counters fail closed
- no production `.pkl` dependency or write path
- no Supabase dependency and no Odds API dependency in the capture tool
- no paid Odds API authorization is created by this protocol

## State after PR #243 implementation

### Serie A

- `CAPTURE_READY=true` for prospective `MARKET_ONLY` observations under `NON_EPL_MARKET_ONLY_V1`.
- `PROSPECTIVE_AI_READY=false`.
- `MODEL_READY=false` until the independent Serie A league-specific candidate/readiness protocol supplies admissible evidence and a frozen eligibility manifest.

### La Liga

- `CAPTURE_READY=true` for prospective `MARKET_ONLY` observations under `NON_EPL_MARKET_ONLY_V1`.
- `PROSPECTIVE_AI_READY=false`.
- Existing La Liga pure-AI v1, frozen hybrid v1, and nested historical v1 remain `CLOSED/REJECTED`; PR #243 does not reopen or retune them.

## CI proof

At implementation head `c1533bbfcdceb8c30ed483fe6da30fc38e8afcb6`:

- `Non-EPL Prospective Capture V1`: SUCCESS
- `Serie A PR Validation`: SUCCESS
- `Bundesliga PR Validation`: SUCCESS
- `Ligue 1 PR Validation`: SUCCESS
- `Eredivisie PR Validation`: SUCCESS
- `Research PR Validation`: was still running when this continuity commit was prepared; the PR must not merge until all exact-head required workflows are green.

The dedicated capture workflow compiles the tool, runs the fail-closed regression tests, and proves no `.pkl` changes.

## Safety proof

No paid Odds API request, prospective result/settlement read, Supabase write, production `.pkl` modification, or production model promotion was performed in this implementation.

## Next executable step

After exact-head CI and merge, use only already-available pre-kickoff fixture/market snapshots to create the first valid `1/100` observation(s). Never fabricate odds and never convert a historical or post-kickoff row into prospective evidence.

In parallel, continue the independent Serie A candidate-development/readiness path. A Serie A historical pass may only make a future AI protocol eligible for freezing; it cannot retroactively add AI predictions to already captured MARKET_ONLY rows. La Liga AI remains closed unless a genuinely new preregistered hypothesis with a defensible new evidence boundary is introduced.
