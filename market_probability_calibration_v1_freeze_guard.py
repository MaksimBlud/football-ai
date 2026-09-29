"""Semantic freeze guard for MARKET_PROBABILITY_CALIBRATION_V1."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def projection(report: dict) -> dict:
    result = report["result"]

    pooled_metrics = {}
    for method, metrics in result["pooled_metrics"].items():
        pooled_metrics[method] = {
            "logloss": metrics["logloss"],
            "brier": metrics["brier"],
            "accuracy": metrics["accuracy"],
        }

    decisions = {}
    for method, decision in result["candidate_decisions"].items():
        decisions[method] = {
            "pooled_delta_vs_raw": decision["pooled_delta_vs_raw"],
            "joint_season_wins": decision["joint_season_wins"],
            "paired_bootstrap": {
                key: {
                    "ci95_low": value["ci95_low"],
                    "ci95_high": value["ci95_high"],
                    "bootstrap_probability_candidate_better":
                        value["bootstrap_probability_candidate_better"],
                }
                for key, value in decision["paired_bootstrap"].items()
            },
            "supported": decision["supported"],
        }

    return {
        "experiment_id": report["experiment_id"],
        "source_rows": report["source_rows"],
        "package_versions": report["package_versions"],
        "result": {
            "pooled_oos_matches": result["pooled_oos_matches"],
            "outer_test_seasons": result["outer_test_seasons"],
            "pooled_metrics": pooled_metrics,
            "candidate_decisions": decisions,
            "supported_candidates": result["supported_candidates"],
            "active_method": result["active_method"],
            "interpretation": result["interpretation"],
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
                compare(
                    expected[key],
                    actual[key],
                    f"{path}.{key}",
                    atol,
                )
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
                f"{path}: expected={expected!r} actual={actual!r} atol={atol}"
            )
        return errors

    if expected != actual:
        errors.append(
            f"{path}: expected={expected!r} actual={actual!r}"
        )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("frozen", type=Path)
    parser.add_argument("runtime", type=Path)
    parser.add_argument("--atol", type=float, default=1e-12)
    args = parser.parse_args()

    frozen = json.loads(args.frozen.read_text(encoding="utf-8"))
    runtime = json.loads(args.runtime.read_text(encoding="utf-8"))

    errors = compare(
        projection(frozen),
        projection(runtime),
        atol=args.atol,
    )

    if errors:
        print("MARKET_PROBABILITY_CALIBRATION_V1 freeze mismatch:")
        for error in errors:
            print("-", error)
        return 1

    print("PASS: MARKET_PROBABILITY_CALIBRATION_V1 semantic result reproduced.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
