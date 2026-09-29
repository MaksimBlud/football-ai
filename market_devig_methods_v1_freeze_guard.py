"""Semantic freeze guard for MARKET_DEVIG_METHODS_V1."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


ALTERNATIVES = ("ADDITIVE", "POWER", "SHIN")
METHODS = ("MULTIPLICATIVE",) + ALTERNATIVES
HOLDOUT_SEASONS = ("2024/2025", "2025/2026")


def semantic_projection(report: dict) -> dict:
    result = report["result"]
    methods = result["all_methods"]

    discovery_alternatives = {}
    for method in ALTERNATIVES:
        row = result["discovery"]["alternatives"][method]
        discovery_alternatives[method] = {
            "logloss": row["logloss"],
            "brier": row["brier"],
            "delta_logloss_vs_multiplicative":
                row["delta_logloss_vs_multiplicative"],
            "delta_brier_vs_multiplicative":
                row["delta_brier_vs_multiplicative"],
            "joint_season_wins": row["joint_season_wins"],
            "eligible": row["eligible"],
        }

    holdouts = {}
    for season in HOLDOUT_SEASONS:
        holdouts[season] = {
            method: {
                "logloss": methods[method]["by_season"][season]["logloss"],
                "brier": methods[method]["by_season"][season]["brier"],
            }
            for method in METHODS
        }

    overall = {}
    for method in METHODS:
        row = methods[method]["overall"]
        calibration = row["calibration"]
        overall[method] = {
            "logloss": row["logloss"],
            "brier": row["brier"],
            "favorite_calibration_gap":
                calibration[
                    "favorite_calibration_gap_observed_minus_predicted"
                ],
            "draw_calibration_gap":
                calibration[
                    "draw_calibration_gap_observed_minus_predicted"
                ],
            "longshot_calibration_gap":
                calibration[
                    "longshot_calibration_gap_observed_minus_predicted"
                ],
        }

    bootstrap = {}
    for method in ALTERNATIVES:
        bootstrap[method] = {}
        for metric in ("logloss", "brier"):
            row = result["alternative_bootstrap_all_2660"][method][metric]
            bootstrap[method][metric] = {
                "ci95_low": row["ci95_low"],
                "ci95_high": row["ci95_high"],
                "bootstrap_probability_candidate_better":
                    row["bootstrap_probability_candidate_better"],
            }

    return {
        "experiment_id": report["experiment_id"],
        "source_rows": report["source_rows"],
        "package_versions": report["package_versions"],
        "result": {
            "selected_on_discovery": result["selected_on_discovery"],
            "discovery": {
                "baseline": result["discovery"]["baseline"],
                "alternatives": discovery_alternatives,
            },
            "holdout_method_metrics": holdouts,
            "overall_method_metrics": overall,
            "overall_deltas_vs_multiplicative":
                result["overall_deltas_vs_multiplicative"],
            "alternative_bootstrap_all_2660": bootstrap,
            "mean_method_parameters": {
                "POWER_k":
                    methods["POWER"]["overall"]["parameters"]["mean_k"],
                "SHIN_z":
                    methods["SHIN"]["overall"]["parameters"]["mean_z"],
                "market_overround":
                    methods["MULTIPLICATIVE"]["overall"]["parameters"][
                        "mean_overround"
                    ],
            },
            "robust_support": result["robust_support"],
            "interpretation": result["interpretation"],
            "active_method": result["active_method"],
        },
    }


def compare(expected, actual, path: str = "$", atol: float = 1e-12) -> list[str]:
    errors: list[str] = []

    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return [f"{path}: expected dict, got {type(actual).__name__}"]
        if set(expected) != set(actual):
            return [
                f"{path}: key mismatch expected={sorted(expected)} "
                f"actual={sorted(actual)}"
            ]
        for key in expected:
            errors.extend(
                compare(expected[key], actual[key], f"{path}.{key}", atol)
            )
        return errors

    if isinstance(expected, list):
        if not isinstance(actual, list):
            return [f"{path}: expected list, got {type(actual).__name__}"]
        if len(expected) != len(actual):
            return [
                f"{path}: length mismatch {len(expected)} != {len(actual)}"
            ]
        for index, (left, right) in enumerate(zip(expected, actual)):
            errors.extend(
                compare(left, right, f"{path}[{index}]", atol)
            )
        return errors

    if isinstance(expected, bool) or expected is None or isinstance(expected, str):
        if expected != actual:
            errors.append(
                f"{path}: expected={expected!r} actual={actual!r}"
            )
        return errors

    if isinstance(expected, (int, float)):
        if not isinstance(actual, (int, float)):
            errors.append(
                f"{path}: expected numeric, got {type(actual).__name__}"
            )
        elif not math.isclose(
            float(expected),
            float(actual),
            rel_tol=0.0,
            abs_tol=atol,
        ):
            errors.append(
                f"{path}: expected={expected!r} "
                f"actual={actual!r} atol={atol}"
            )
        return errors

    if expected != actual:
        errors.append(f"{path}: expected={expected!r} actual={actual!r}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("frozen", type=Path)
    parser.add_argument("runtime", type=Path)
    parser.add_argument("--atol", type=float, default=1e-12)
    args = parser.parse_args()

    frozen = json.loads(args.frozen.read_text(encoding="utf-8"))
    runtime = json.loads(args.runtime.read_text(encoding="utf-8"))

    expected = frozen.copy()
    expected.pop("frozen_result_schema", None)
    expected.pop("first_run", None)

    actual = semantic_projection(runtime)

    errors = compare(expected, actual, atol=args.atol)
    if errors:
        print("MARKET_DEVIG_METHODS_V1 freeze mismatch:")
        for error in errors:
            print("-", error)
        return 1

    print("PASS: MARKET_DEVIG_METHODS_V1 semantic result reproduced.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
