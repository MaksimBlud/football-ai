"""Secondary retrospective portability audit for FAIR_CENTRE timing policy.

Research-only. Uses only already-opened immutable cohorts and the previously
frozen original-55 FAIR_CENTRE risk predictor. No provider/network transport.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import corner_repricing_direction_replication_v1 as replication

EXPERIMENT_ID = "CORNER_REPRICING_TIMING_POLICY_V1"
EXPECTED_ROWS = {
    "FRESH_50": 50,
    "V1_46": 46,
    "V2B_43": 43,
}
GROUP_WAIT = "WAIT"
GROUP_STABLE = "STABLE_OPEN"
HIGH_RISK_FRACTION = 0.25
EPS = 1e-12


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _validate_frame(frame: pd.DataFrame, *, label: str, expected_rows: int | None) -> pd.DataFrame:
    required = {"fixture_id", "league", "opening_lambda", "movement_magnitude", "centre_delta"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"{label}: missing columns {sorted(missing)}")

    out = frame.copy()
    out["fixture_id"] = out["fixture_id"].astype(str)
    out["league"] = out["league"].astype(str)
    for column in ("opening_lambda", "movement_magnitude", "centre_delta"):
        out[column] = pd.to_numeric(out[column], errors="coerce")

    if expected_rows is not None and len(out) != expected_rows:
        raise ValueError(f"{label}: expected {expected_rows} rows, got {len(out)}")
    if out["fixture_id"].duplicated().any():
        raise ValueError(f"{label}: duplicate fixture IDs")
    if out["league"].isna().any() or (out["league"].str.len() == 0).any():
        raise ValueError(f"{label}: missing league")
    numeric = out[["opening_lambda", "movement_magnitude", "centre_delta"]].to_numpy(float)
    if not np.isfinite(numeric).all():
        raise ValueError(f"{label}: non-finite market values")
    if (out["movement_magnitude"] < -EPS).any():
        raise ValueError(f"{label}: negative movement magnitude")
    if not np.allclose(
        out["movement_magnitude"].to_numpy(float),
        np.abs(out["centre_delta"].to_numpy(float)),
        atol=1e-9,
        rtol=1e-9,
    ):
        raise ValueError(f"{label}: movement_magnitude != abs(centre_delta)")
    return out.reset_index(drop=True)


def fit_frozen_predictor(discovery: pd.DataFrame):
    discovery = _validate_frame(discovery, label="DISCOVERY_55", expected_rows=55)
    model, threshold, baseline = replication.fit_frozen_v1_predictor(discovery)
    return discovery, model, float(threshold), float(baseline)


def apply_timing_policy(
    frame: pd.DataFrame,
    *,
    label: str,
    model,
    material_threshold: float,
) -> pd.DataFrame:
    expected_rows = EXPECTED_ROWS[label]
    out = _validate_frame(frame, label=label, expected_rows=expected_rows)
    out["cohort"] = label
    out["risk_probability"] = model.predict_proba(out[["opening_lambda"]])[:, 1]
    out["material_move"] = (
        out["movement_magnitude"].to_numpy(float) >= float(material_threshold)
    ).astype(int)
    out["timing_policy"] = GROUP_STABLE

    for league in sorted(out["league"].unique()):
        idx = out.index[out["league"] == league].tolist()
        ranked = out.loc[idx].sort_values(
            ["risk_probability", "fixture_id"],
            ascending=[False, True],
            kind="stable",
        )
        take = int(math.ceil(len(ranked) * HIGH_RISK_FRACTION))
        if take:
            out.loc[ranked.head(take).index, "timing_policy"] = GROUP_WAIT

    return out


def _group_metrics(frame: pd.DataFrame, group: str) -> dict[str, Any]:
    g = frame[frame["timing_policy"] == group]
    n = int(len(g))
    material_count = int(g["material_move"].sum())
    return {
        "rows": n,
        "mean_movement_magnitude": float(g["movement_magnitude"].mean()) if n else None,
        "median_movement_magnitude": float(g["movement_magnitude"].median()) if n else None,
        "material_move_count": material_count,
        "material_move_prevalence": float(material_count / n) if n else None,
        "nonzero_movement_count": int((g["centre_delta"].abs() > EPS).sum()),
        "nonzero_movement_prevalence": float((g["centre_delta"].abs() > EPS).mean()) if n else None,
    }


def summarize_cohort(frame: pd.DataFrame) -> dict[str, Any]:
    wait = _group_metrics(frame, GROUP_WAIT)
    stable = _group_metrics(frame, GROUP_STABLE)
    wait_prev = wait["material_move_prevalence"]
    stable_prev = stable["material_move_prevalence"]
    risk_ratio = (
        float(wait_prev / stable_prev)
        if wait_prev is not None and stable_prev not in (None, 0.0)
        else None
    )
    mean_diff = float(
        wait["mean_movement_magnitude"] - stable["mean_movement_magnitude"]
    )
    prevalence_diff = float(wait_prev - stable_prev)
    consistent = bool(mean_diff > 0.0 and prevalence_diff > 0.0)
    return {
        "rows": int(len(frame)),
        "wait": wait,
        "stable_open": stable,
        "wait_minus_stable_mean_movement_magnitude": mean_diff,
        "wait_minus_stable_material_move_prevalence": prevalence_diff,
        "wait_to_stable_material_move_risk_ratio": risk_ratio,
        "directionally_consistent_with_wait_policy": consistent,
    }


def evaluate(
    discovery: pd.DataFrame,
    fresh_50: pd.DataFrame,
    v1_46: pd.DataFrame,
    v2b_43: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    _, model, material_threshold, baseline = fit_frozen_predictor(discovery)

    cohorts = {
        "FRESH_50": apply_timing_policy(
            fresh_50,
            label="FRESH_50",
            model=model,
            material_threshold=material_threshold,
        ),
        "V1_46": apply_timing_policy(
            v1_46,
            label="V1_46",
            model=model,
            material_threshold=material_threshold,
        ),
        "V2B_43": apply_timing_policy(
            v2b_43,
            label="V2B_43",
            model=model,
            material_threshold=material_threshold,
        ),
    }
    cohort_reports = {label: summarize_cohort(frame) for label, frame in cohorts.items()}
    combined = pd.concat(cohorts.values(), ignore_index=True)
    pooled = summarize_cohort(combined)

    all_consistent = all(
        report["directionally_consistent_with_wait_policy"]
        for report in cohort_reports.values()
    )
    classification = (
        "DESCRIPTIVELY_PORTABLE_WAIT_FILTER"
        if all_consistent
        else "NOT_PORTABLE_AS_SIMPLE_WAIT_FILTER"
    )

    report = {
        "experiment_id": EXPERIMENT_ID,
        "research_only": True,
        "secondary_reuse_of_opened_data": True,
        "confirmatory_replication": False,
        "betting_enabled": False,
        "production_promotion_authorized": False,
        "provider_calls": 0,
        "training_source": "ORIGINAL_55_ONLY",
        "primary_feature": "FAIR_CENTRE_ONLY",
        "high_risk_fraction_per_league": HIGH_RISK_FRACTION,
        "material_move_threshold_from_original_55_q75": material_threshold,
        "original_55_material_move_prevalence": baseline,
        "later_cohorts": cohort_reports,
        "pooled_descriptive": pooled,
        "all_later_cohorts_directionally_consistent": all_consistent,
        "classification": classification,
        "interpretation": (
            "Secondary descriptive portability audit only. Opened cohorts were not "
            "used to fit the FAIR_CENTRE predictor or select the top-25% rule."
        ),
    }
    return combined, report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--discovery", type=Path, required=True)
    parser.add_argument("--fresh-50", type=Path, required=True)
    parser.add_argument("--v1-46", type=Path, required=True)
    parser.add_argument("--v2b-43", type=Path, required=True)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/corner_repricing_timing_policy_v1"),
    )
    args = parser.parse_args()

    rows, report = evaluate(
        pd.read_csv(args.discovery),
        pd.read_csv(args.fresh_50),
        pd.read_csv(args.v1_46),
        pd.read_csv(args.v2b_43),
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    rows.to_csv(args.output_dir / "policy_rows.csv", index=False)
    _write_json(args.output_dir / "report.json", report)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
