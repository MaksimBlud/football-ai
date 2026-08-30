# OOS Evaluation Protocol

Status: research-only protocol, frozen before Structural V2 calibration for calibration-required leagues.

## Purpose

Evaluate whether a football-structure candidate adds information beyond the market without choosing metrics, snapshots, or acceptance rules after seeing favorable outcomes.

## Primary evaluation unit

The primary unit is exactly one **latest immutable pre-kickoff prediction per fixture** from the canonical prediction ledger. All-snapshot rows are diagnostic only and must not be treated as independent matches.

## Primary baseline

The baseline is the canonical MARKET_ONLY 1X2 probability vector recorded before kickoff. Market probabilities must be normalized and sum to one.

## Primary metrics

1. **Multiclass log loss** — primary probability-quality metric; lower is better.
2. **Multiclass Brier score** — co-primary calibration/sharpness metric; lower is better.

Accuracy and mean probability assigned to the realized outcome are descriptive secondary metrics, not promotion criteria by themselves.

## Calibration diagnostics

For MARKET_ONLY and any Structural candidate, report:

- reliability/calibration by probability bins when sample size permits;
- home/draw/away outcome counts and per-outcome probability quality;
- prediction horizon (`hours_to_kickoff`) distribution;
- performance by predeclared time slices and league;
- performance by predeclared edge buckets once an edge definition is frozen.

Sparse bins must be reported as sparse rather than merged opportunistically after outcomes are observed.

## OOS discipline

- Parameter fitting and acceptance evaluation must use disjoint fixtures.
- Splits must respect time order; no random future-to-past leakage.
- A fixture may appear only once in the primary latest-pre-kickoff evaluation view.
- Historical features must be computable using information available before the fixture kickoff.
- Finished results must come from the immutable canonical results authority.
- Post-kickoff predictions are invalid and fail closed.
- Cross-league rows are invalid and fail closed.

## Structural comparison

A Structural candidate must be evaluated against the MARKET_ONLY probability recorded for the **same fixture and evaluation snapshot policy**. Comparisons across different fixture sets are diagnostic only.

No Structural parameter may be activated merely because accuracy or ROI is positive. The candidate must demonstrate probability-quality improvement against the market baseline under the frozen OOS protocol.

## Readiness gate: deliberately not numeric yet

No arbitrary minimum such as 50, 100, or 200 fixtures is declared by this document. Before calibration begins for a league, a separate reviewed gate must freeze:

- minimum settled fixture count;
- minimum calendar/time coverage;
- minimum representation of H/D/A outcomes;
- acceptable missing/unlinked-result rate;
- required absence of critical canonical data-quality failures;
- fitting window and untouched OOS evaluation window;
- uncertainty method for metric differences.

The numerical gate must be committed **before** candidate parameters are selected from those data.

## Promotion boundary

This protocol authorizes research evaluation only. It does not authorize model training side effects, production `.pkl` mutation, Structural V2 activation, automatic parameter promotion, or betting decisions.
