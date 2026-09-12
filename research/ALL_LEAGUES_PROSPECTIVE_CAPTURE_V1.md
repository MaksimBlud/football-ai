# All-Leagues Prospective MARKET_ONLY Capture V1

Status: FROZEN ON FIRST MERGE TO `main`
Protocol: `ALL_LEAGUES_MARKET_ONLY_V1`
Scope: 8 leagues

Leagues:
- `EPL`
- `LA_LIGA`
- `SERIE_A`
- `BUNDESLIGA`
- `LIGUE_1`
- `EREDIVISIE`
- `TURKEY_SUPER_LIG`
- `PRIMEIRA_LIGA`

## Purpose

Freeze one common prospective recording contract for the eight operational MARKET_ONLY leagues without weakening, rewriting or backdating any existing league-specific preregistration.

This is a research capture protocol. It does not authorize production-model promotion, Structural V2 activation, retrospective AI labeling, paid odds collection, or outcome-driven tuning.

## Atomic T0

`T0_COMMIT` is the merge commit that first introduces this file into `main`.

`T0_UTC` is the GitHub commit timestamp of `T0_COMMIT`.

The common eight-league prospective cohort begins strictly after `T0_UTC`. The 2026-09-11 readiness/bootstrap snapshots and ledger rows are retained as immutable audit evidence but are not retroactively admitted into this common cohort. Earlier league-specific frozen protocols remain governed by their own original activation rules.

An observation is eligible for this common protocol only when its immutable durable record is created strictly after `T0_UTC`, its source market snapshot is strictly before kickoff, and all rules below pass.

## Frozen evidence rules

- League must be exactly one of the eight identifiers listed above.
- Evidence class is `MARKET_ONLY` only.
- `structural_applied` must be false.
- Every prediction/observation and its exact source snapshot must be immutable before kickoff.
- `prediction_time_utc < kickoff_utc` and `snapshot_time_utc < kickoff_utc` are mandatory.
- Canonical provider `event_id`, UTC kickoff, home team, away team and exact snapshot time are required provenance.
- 1X2 probabilities must be finite, non-negative, normalized and generated from a valid pre-kickoff market snapshot.
- Outcome, score, winner, settlement and any equivalent result-derived field are forbidden inputs at capture time.
- No result/outcome source may be queried to decide whether an observation is captured, excluded, retried or relabeled.
- Existing production `.pkl` artifacts are read-only for this protocol; model promotion is outside scope.
- No historical or prospective outcome may be used to tune league inclusion, thresholds, snapshot selection, weighting, sample rules or evaluation metrics after T0.
- Conflicting immutable identities fail closed; no overwrite or silent replacement is permitted.
- Missing required provenance fails closed.

## Completeness manifest contract

Every capture batch evaluated under the common protocol must use `all_leagues_capture_gate.py` with all eight league entries.

For each league, `expected_event_ids` must be frozen before persistence-completeness evaluation from an authoritative pre-kickoff fixture/provider-response manifest. The expected list may be produced from the provider response or another authoritative fixture export before database persistence, but it must be independent of the rows later read back from `odds_snapshots` as `captured_event_ids`.

It is forbidden to construct `expected_event_ids` by querying the already-persisted captured rows and copying those event IDs into the expected side of the gate. That would make the completeness check circular.

The gate remains fail-closed:
- any expected event missing from captured storage => `MISSING` and no completeness pass;
- any captured event outside the frozen expected manifest => `UNEXPECTED` and no completeness pass;
- duplicate event IDs, duplicate league entries, malformed IDs or missing leagues => hard input failure;
- raw database row counts may not substitute for canonical provider event IDs.

A provider or fixture source being temporarily unavailable does not authorize inventing, shrinking or retrospectively editing the expected manifest.

## Separation from previous evidence

The 133 fresh 2026-09-11 market events across the eight leagues are bootstrap/readiness proof for infrastructure only under this common protocol. They prove that all eight collection and immutable-ledger paths can operate, but they do not become common prospective observations by retroactive declaration.

Existing league-specific prospective ledgers/contracts remain immutable and keep their original counters, T0 rules and evaluation gates. This file does not broaden `NON_EPL_MARKET_ONLY_V1`, `BUNDESLIGA_MARKET_ONLY_V1`, EPL AI-vs-market experiments, or any Structural V2 protocol.

## Paid-provider rule

This protocol grants no paid API permission. Paid odds collection remains separately authorized and budget-guarded. Supabase-only mirror/catch-up operations may run without provider authorization when they consume already durable pre-kickoff snapshots and do not access outcomes.

## Evaluation contract

Capture and evaluation are separate phases.

When a separately satisfied frozen sample/time evaluation gate permits outcome access, the common MARKET_ONLY evaluation uses these fixed 1X2 metrics:
- multiclass log loss;
- multiclass Brier score;
- 1X2 argmax accuracy.

Metrics must be reported per league and pooled across the eligible common cohort. Pooled reporting may not hide a failed league-level integrity gate.

No prospective outcome may be read merely to decide whether the sample is promising enough to continue, stop, retune or redefine this protocol. If an existing league-specific contract has a stricter evaluation gate, the stricter gate wins.

## Operational readiness gate

Before declaring this protocol operationally ready, live read-only proof must show for all eight leagues:
- at least one current/fresh durable market snapshot path is working;
- canonical MARKET_ONLY prediction-ledger persistence is working;
- no post-kickoff timing violation in the canonical ledger;
- no non-MARKET_ONLY/Structural V2 activation in the common capture path;
- production model artifacts remain unchanged by research capture/catch-up.

The readiness proof itself does not move T0 backwards.

## Scientific status

After this file is merged into `main` and the operational readiness gate is green:

`ALL_LEAGUES_MARKET_ONLY_V1 = CAPTURE_READY`

This does not imply:
- `MODEL_READY=true` for every league;
- `PROSPECTIVE_AI_READY=true` for every league;
- Structural V2 activation;
- production promotion;
- permission to inspect outcomes before an applicable evaluation gate.
