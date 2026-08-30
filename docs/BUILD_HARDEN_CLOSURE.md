# Build & Harden Closure Protocol

## Purpose

This document defines the evidence required to close the canonical multi-league Build & Harden phase. Closure means that the operational research pipeline is behaving safely and consistently. It does **not** mean that any model, Structural V2 configuration, calibration layer, or production promotion is ready.

The canonical operational path is:

`Odds → fixtures → MARKET_ONLY shadow → durable observations → immutable prediction ledger → finished results → evaluator → calibration dataset`

Operational leagues in scope are EPL, La Liga, RPL, Serie A, Bundesliga, Ligue 1, and Eredivisie. Adding further leagues is outside this closure protocol.

## Closure criteria

Build & Harden is closed only when all of the following are evidenced on the hardened canonical code path:

1. Every operational league has at least one representative successful live cycle on a commit containing the applicable league hardening fixes.
2. Live odds collection completes and canonical fixture identity remains league-aware.
3. The live research path remains MARKET_ONLY unless a separately approved research protocol explicitly says otherwise.
4. Durable observations persist idempotently: reruns may be unchanged, but must not create conflicting duplicate identities.
5. Canonical prediction-ledger writes remain immutable and report zero conflicts for a normal repeated cycle.
6. Finished-result settlement remains league-isolated; cross-league settlement must fail closed.
7. A live cycle must not unexpectedly mutate already persisted finished results. Where a workflow records before/after counts, the expected invariant must be explicit.
8. The canonical evaluator runs read-only and fails closed on invalid canonical state, including post-kickoff predictions, foreign-league rows, invalid probabilities, and settlement identity anomalies.
9. MARKET_ONLY operational execution does not load or invoke AI, Structural V2, or production model artifacts.
10. Production `.pkl` artifacts are unchanged. Research PR Validation's no-`.pkl` gate remains mandatory for research changes.
11. The canonical data-quality audit reports `critical_failures=0` for the state used as closure evidence.
12. La Liga's legacy Structural V2 research remains explicitly separate from the canonical MARKET_ONLY ledger path. Its historical parameters are not a canonical operational readiness signal.

No numerical sample-size, calibration, performance, or promotion threshold is introduced by these criteria.

## Required evidence per league

For the representative closure run, record at minimum:

- league;
- Git commit SHA checked out by the workflow;
- GitHub Actions run ID and conclusion;
- live odds/shadow completion status;
- durable observation inserted/unchanged state where available;
- canonical ledger inserted/unchanged state and conflict count;
- finished-result before/after behavior;
- canonical results bridge status where applicable;
- evaluator completion status;
- confirmation that the path remained MARKET_ONLY and did not load AI/Structural/production models;
- any cold-start or provider-alias exceptions explicitly encountered.

A green GitHub Actions badge alone is not sufficient evidence if the run log does not establish the relevant canonical invariants.

## Current closure state

At the time this protocol was frozen, representative live validation had already succeeded for EPL, RPL, Serie A, Bundesliga, Ligue 1, and Eredivisie. The only outstanding operational gate was the first La Liga live cycle on the canonical alias fix (`45046b5e43eabcfca81e8f0fbab17ae4340c0460`) or a descendant commit.

The previous visible La Liga run started before that fix and therefore cannot be used as closure evidence.

## La Liga final gate

The first qualifying La Liga run must demonstrate the complete live path:

`live odds → MARKET_ONLY shadow → durable observation → canonical ledger → canonical results bridge → canonical evaluator`

The review must specifically confirm that the canonical aliases for Alavés, Espanyol, and Rayo Vallecano no longer trigger the strict reference guard, while Racing remains an explicit cold start rather than a silent normalization fallback.

If that run succeeds and all criteria above remain satisfied, Build & Harden may be marked closed. If it fails, diagnose the first causal failure and keep Build & Harden open; downstream symptoms must not be treated as independent root causes without evidence.

## What closure does not authorize

Build & Harden closure does not authorize:

- production model retraining or promotion;
- modification of production `.pkl` artifacts;
- activation or tuning of Structural V2 for new leagues;
- changing La Liga Structural parameters;
- selecting a calibration-readiness threshold after inspecting future outcomes;
- adding more leagues;
- treating early settled samples as evidence of model superiority.

The next phase after closure is Observe & Measure under the separately frozen runbook.
