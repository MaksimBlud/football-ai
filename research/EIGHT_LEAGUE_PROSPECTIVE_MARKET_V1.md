# EIGHT_LEAGUE_PROSPECTIVE_MARKET_V1

Status: **PREREGISTERED / NOT YET ACTIVATED**

This document freezes the cross-league prospective market experiment before its activation commit is merged to `main`.

## Scope

Collection-ready leagues:

- EPL
- LA_LIGA
- SERIE_A
- BUNDESLIGA
- LIGUE_1
- EREDIVISIE
- TURKEY_SUPER_LIG
- PRIMEIRA_LIGA

The experiment is research-only and does not authorize model promotion, production `.pkl` mutation, paid provider calls, or retrospective reconstruction of observations.

## T0

`T0` is **not** a wall-clock value written in advance. It is defined immutably as the Git commit time of the merge commit that first places this preregistration on `main`.

Only observations whose durable persistence time and market snapshot time are at or after that merge commit time are members of this experiment. Any data captured before T0 is bootstrap/readiness evidence only, even when it is otherwise valid and pre-kickoff.

This definition prevents back-dating the experiment and makes activation independently auditable from Git history.

## Primary prospective unit

The canonical fixture identity is:

`(league, event_id, commence_time_utc)`

A qualifying observation must satisfy all of the following:

1. league is one of the eight frozen leagues above;
2. provider `event_id` is non-empty and unambiguous;
3. `snapshot_time_utc < commence_time_utc`;
4. observation/prediction persistence is at or after T0;
5. market probabilities are finite, non-negative and normalized within existing repository tolerance;
6. the immutable canonical ledger has no conflicting payload for the same canonical prediction key;
7. any temporal duplicate is resolved only by an existing frozen/canonical rule; contradictory market state fails closed;
8. no result/outcome field is required or read during acquisition/readiness checks.

## Frozen treatment

The common treatment for the experiment is the already-existing `MARKET_ONLY` prediction state for each league. League-specific frozen contracts remain authoritative where they are stricter. This protocol does **not** activate Structural V2, corners, injuries, availability, or any model candidate.

No league-specific feature may be silently added to the common treatment after T0. Any future treatment change requires a new versioned experiment.

## Capture completeness

The repository's deterministic `all_leagues_capture_gate.py` is the frozen completeness evaluator for explicit manifests.

Completeness is based on canonical provider event IDs, never raw row counts. A manifest fails closed on:

- a missing required league;
- missing expected event IDs;
- unexpected captured event IDs;
- duplicate expected/captured IDs;
- duplicate league entries;
- malformed or stale manifest schema.

The gate is validation-only and must remain network/provider-free.

## Acquisition / paid-provider rule

Paid The Odds API collection remains manual-only and must continue through existing league-specific budget/safety guards. This preregistration is **not authorization** to spend provider credits.

If a league has no fresh qualifying snapshot after T0 because no paid collection was authorized, the experiment records that as a data-acquisition gap; it must not backfill the missed pre-kickoff state later.

## Immutable recording rule

A qualifying prediction/observation may be appended once through the canonical league ledger path. Re-running the same persistence must be idempotent. A payload conflict is a hard failure and must not be overwritten.

For La Liga, historical temporal structural reconstructions are not allowed to replace the first durable prospective observation for an identical `(league, event_id, snapshot_time_utc)` identity. Market-state disagreement remains a hard conflict.

## Outcome embargo

Until an explicit evaluation gate for this experiment is separately preregistered and reached:

- do not join outcomes/results to experiment members;
- do not compute accuracy, log loss, Brier score, ROI, calibration, edge, or league ranking from experiment outcomes;
- do not use outcome-aware stopping or sample selection;
- do not change acquisition priorities because of observed performance.

Operational result-sync workflows may continue for other existing project contracts, but this experiment's membership/readiness checks must not consume those outcome fields.

## Evaluation gate

This V1 activation freezes acquisition and membership rules only. It does **not** invent a new sample-size or performance threshold. Evaluation remains closed until a later, separate preregistered evaluation contract defines the cohort size/time embargo without looking at this experiment's outcomes.

That later contract may not retroactively alter T0, membership, market treatment, or canonical identities.

## Readiness proof required at activation

Before declaring this experiment `ACTIVE / COLLECTING`, the activation change must have all of the following evidence:

1. all eight leagues had a successful live pre-kickoff market snapshot/readiness proof before T0;
2. Turkey and Primeira Liga are confirmed to use the common budget policy rather than the retired `500`-credit floor;
3. La Liga temporal canonicality fix is merged and zero-cost ledger catch-up succeeds with zero conflicts;
4. deterministic all-eight-league completeness gate is merged and green on `main`;
5. production model artifacts were not modified by the readiness work;
6. `PROJECT_CONTINUITY.md` records the activation commit and today's operational evidence.

## Interpretation

`ACTIVE / COLLECTING` means that future observations after T0 can accumulate under this frozen protocol. It does **not** mean that all eight leagues will automatically make a paid provider request at the same cadence, and it does not mean the experiment is ready for outcome evaluation.
