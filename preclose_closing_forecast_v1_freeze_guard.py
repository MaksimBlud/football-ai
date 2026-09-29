"""Semantic freeze guard for 1X2_PRECLOSE_CLOSING_FORECAST_V1."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


HOLDOUTS = ("2024/2025", "2025/2026")


def semantic_projection(report: dict) -> dict:
    result = report["result"]
    selected = result["selected_candidate"]
    validation_zero = result["validation_zero"]

    validation = {
        "zero_close_mae": validation_zero["close_mae"],
        "candidate_close_mae": selected["close_mae"],
        "delta_close_mae":
            selected["close_mae"] - validation_zero["close_mae"],
        "zero_close_cross_entropy":
            validation_zero["close_cross_entropy"],
        "candidate_close_cross_entropy":
            selected["close_cross_entropy"],
        "delta_close_cross_entropy":
            selected["close_cross_entropy"]
            - validation_zero["close_cross_entropy"],
        "zero_outcome_logloss": validation_zero["outcome_logloss"],
        "candidate_outcome_logloss": selected["outcome_logloss"],
        "passed": result["validation_passed"],
    }

    holdouts = {}
    for season in HOLDOUTS:
        row = result["holdouts"][season]
        zero = row["zero"]
        candidate = row["candidate"]
        delta = row["delta_candidate_minus_zero"]
        holdouts[season] = {
            "zero_close_mae": zero["close_mae"],
            "candidate_close_mae": candidate["close_mae"],
            "delta_close_mae": delta["close_mae"],
            "zero_close_cross_entropy": zero["close_cross_entropy"],
            "candidate_close_cross_entropy":
                candidate["close_cross_entropy"],
            "delta_close_cross_entropy":
                delta["close_cross_entropy"],
            "outcome_logloss_delta": delta["outcome_logloss"],
            "outcome_brier_delta": delta["outcome_brier"],
            "max_move_mae_delta": delta["max_move_mae"],
            "candidate_direction_accuracy":
                candidate["direction_accuracy"],
            "actual_mean_max_abs_move":
                candidate["actual_mean_max_abs_move"],
            "actual_argmax_change_rate":
                candidate["actual_argmax_change_rate"],
            "passed_primary_gate": row["passed_primary_gate"],
        }

    bootstrap = {}
    for metric in ("close_mae", "close_cross_entropy"):
        row = result["paired_bootstrap_760_holdout_matches"][metric]
        bootstrap[metric] = {
            key: row[key]
            for key in (
                "mean_delta_candidate_minus_zero",
                "ci95_low",
                "ci95_high",
                "bootstrap_probability_candidate_better",
            )
        }

    return {
        "experiment_id": report["experiment_id"],
        "source_rows": report["source_rows"],
        "package_versions": report["package_versions"],
        "result": {
            "selected_candidate": {
                "candidate_id": selected["candidate_id"],
                "spec": selected["spec"],
            },
            "validation": validation,
            "holdouts": holdouts,
            "paired_bootstrap_760_holdout_matches": bootstrap,
            "robust_support": result["robust_support"],
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
                f"{path}: expected={expected!r} actual={actual!r} atol={atol}"
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

    expected = dict(frozen)
    expected.pop("frozen_result_schema", None)
    expected.pop("first_run", None)

    actual = semantic_projection(runtime)
    errors = compare(expected, actual, atol=args.atol)

    if errors:
        print("1X2_PRECLOSE_CLOSING_FORECAST_V1 freeze mismatch:")
        for error in errors:
            print("-", error)
        return 1

    print("PASS: 1X2_PRECLOSE_CLOSING_FORECAST_V1 semantic result reproduced.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
