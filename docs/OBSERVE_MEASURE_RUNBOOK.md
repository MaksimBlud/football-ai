# Observe & Measure Runbook

## Purpose

Observe & Measure begins only after the canonical multi-league Build & Harden closure criteria are satisfied. Its purpose is to accumulate and describe trustworthy out-of-sample canonical evidence before any calibration, Structural tuning, model training, or promotion decision.

This phase is research-only. It introduces no numerical readiness threshold.

## Canonical health observations

Use the existing read-only reports as the operational source of truth:

- `report_multi_league_health.py` for consolidated league health;
- `report_league_calibration_coverage.py` for canonical coverage counts;
- `audit_league_canonical_data_quality.py` for fail-closed data-quality checks.

Track, by league:

- canonical ledger rows;
- canonical finished-result rows;
- settled fixtures;
- fixtures with a latest eligible pre-kickoff prediction;
- current data stage;
- duplicate prediction identities;
- duplicate finished-result identities;
- missing event IDs;
- unlinked finished results;
- canonical critical failures.

Counts are descriptive. They are not readiness thresholds.

## OOS eligibility contract

A fixture is eligible for future out-of-sample evaluation only when all of the following are true:

1. League and fixture identity are canonical and league-aware.
2. The prediction was created before the canonical kickoff timestamp.
3. If multiple eligible predictions exist, evaluation uses only the latest eligible pre-kickoff prediction according to the frozen OOS protocol.
4. The prediction probability vector is finite, non-negative, bounded, and valid under the canonical evaluator's tolerance rules.
5. The finished result belongs to the same canonical league and fixture identity.
6. Settlement is unique and does not conflict with another finished-result identity.
7. No cross-league fallback, league-less compatibility shortcut, or post-kickoff information is used to make the row eligible.
8. The row passes the canonical data-quality audit and evaluator fail-closed checks.
9. Future evaluation outcomes were not used to change the prediction, eligibility rule, or selection logic for that same evaluation sample.

Rows that fail the contract remain diagnosable operational data but are not silently repaired into the OOS evaluation sample.

## Evaluation views

Once settled OOS data exists, report descriptive metrics without using them as automatic promotion gates:

- multiclass log loss;
- multiclass Brier score;
- empirical calibration by probability bins when sample size permits a meaningful descriptive view;
- sample counts behind every metric;
- per-league results;
- aggregate results only when the aggregation is methodologically justified and the league composition is disclosed.

Market or other research baselines may be compared only when their timestamp and eligibility rules are compatible with the same OOS contract. A better point estimate on a small sample is not sufficient evidence of superiority.

## Temporal discipline

The OOS protocol must remain frozen before inspecting the future outcomes it governs. Changes to eligibility, metric definitions, binning rules, or selection logic after outcomes are visible must be versioned and evaluated prospectively rather than retroactively presented as the original protocol.

Training, calibration fitting, Structural parameter selection, and promotion decisions must use explicitly separated data windows. The future evaluation interval must not leak into feature construction, fitting, tuning, threshold selection, or model selection.

## Operational cadence

During Observe & Measure:

1. Let scheduled collectors, live cycles, result bridges, and evaluators accumulate canonical state.
2. Periodically run the consolidated health report and canonical data-quality audit.
3. Investigate any `critical_failures > 0` before interpreting performance metrics.
4. Record settled and latest-pre-kickoff coverage together with any performance summary.
5. Keep production models and Structural parameters unchanged unless a separate future decision explicitly opens that work.

The cadence may be increased or decreased for operational convenience, but changing cadence must not change the OOS eligibility definition.

## Readiness and promotion boundary

This runbook intentionally defines no minimum settled sample, no required log-loss improvement, no Brier threshold, no calibration-error cutoff, and no promotion rule.

A future calibration or promotion gate may be proposed only after enough canonical settled evidence has accumulated to justify a predeclared decision protocol. That future proposal must be reviewed separately and must not rewrite this OOS sample retrospectively.

Until then, the correct state is to observe, measure, diagnose data quality, and preserve the evidence trail.
