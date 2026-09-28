"""Semantic freeze guard for GOAL_MODEL_TIME_DECAY_V1."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


RESULT_KEYS = (
    "outer_fold_count",
    "outer_test_seasons",
    "selection_counts",
    "positive_folds",
    "pooled",
    "paired_bootstrap",
    "signal_supported",
    "interpretation",
)


def semantic_projection(report: dict) -> dict:
    result = report["result"]
    folds = result.get("folds")
    if folds is not None:
        selected_by_fold = [
            {
                "test_season": row["test_season"],
                "selected_half_life_days": row["selected_half_life_days"],
            }
            for row in folds
        ]
    else:
        selected_by_fold = result["selected_by_fold"]

    return {
        "experiment_id": report["experiment_id"],
        "source_rows": report["source_rows"],
        "feature_rows": report["feature_rows"],
        "package_versions": report["package_versions"],
        "result": {
            **{key: result[key] for key in RESULT_KEYS},
            "selected_by_fold": selected_by_fold,
        },
    }


def compare(expected, actual, path: str = "$", atol: float = 1e-12) -> list[str]:
    errors: list[str] = []

    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return [f"{path}: expected dict, got {type(actual).__name__}"]
        if set(expected) != set(actual):
            errors.append(
                f"{path}: key mismatch expected={sorted(expected)} "
                f"actual={sorted(actual)}"
            )
            return errors
        for key in expected:
            errors.extend(compare(expected[key], actual[key], f"{path}.{key}", atol))
        return errors

    if isinstance(expected, list):
        if not isinstance(actual, list):
            return [f"{path}: expected list, got {type(actual).__name__}"]
        if len(expected) != len(actual):
            return [f"{path}: length mismatch {len(expected)} != {len(actual)}"]
        for index, (left, right) in enumerate(zip(expected, actual)):
            errors.extend(compare(left, right, f"{path}[{index}]", atol))
        return errors

    if isinstance(expected, bool) or expected is None or isinstance(expected, str):
        if expected != actual:
            errors.append(f"{path}: expected={expected!r} actual={actual!r}")
        return errors

    if isinstance(expected, (int, float)):
        if not isinstance(actual, (int, float)):
            errors.append(
                f"{path}: expected numeric, got {type(actual).__name__}"
            )
        elif not math.isclose(float(expected), float(actual), rel_tol=0.0, abs_tol=atol):
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

    expected = semantic_projection(frozen)
    actual = semantic_projection(runtime)
    errors = compare(expected, actual, atol=args.atol)

    if errors:
        print("GOAL_MODEL_TIME_DECAY_V1 freeze mismatch:")
        for error in errors:
            print("-", error)
        return 1

    print("PASS: GOAL_MODEL_TIME_DECAY_V1 semantic result reproduced.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
