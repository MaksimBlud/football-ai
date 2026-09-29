"""Semantic freeze guard for MARKET_BOOKMAKER_DISPERSION_V1."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


BOOKMAKERS = (
    "BET365",
    "BETWAY",
    "INTERWETTEN",
    "PINNACLE",
    "WILLIAM_HILL",
    "VCBET",
)


def projection(report: dict) -> dict:
    result = report["result"]
    if "availability_summary" in result:
        availability_summary = result["availability_summary"]
    else:
        availability_summary = {}
        for bookmaker in BOOKMAKERS:
            info = result["bookmaker_availability"][bookmaker]
            minimum = min(
                row["coverage"]
                for row in info["by_season"].values()
            )
            availability_summary[bookmaker] = {
                "eligible": info["eligible"],
                "valid_rows_total": info["valid_rows_total"],
                "min_season_coverage": minimum,
            }

    return {
        "experiment_id": report["experiment_id"],
        "source_rows": report["source_rows"],
        "package_versions": report["package_versions"],
        "result": {
            "eligible_bookmakers": result["eligible_bookmakers"],
            "availability_summary": availability_summary,
            "common_rows": result["common_rows"],
            "signals_supported": result["signals_supported"],
            "interpretation": result["interpretation"],
        },
    }


def compare(expected, actual, path="$", atol=1e-12):
    errors = []
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return [f"{path}: expected dict"]
        if set(expected) != set(actual):
            return [f"{path}: key mismatch"]
        for key in expected:
            errors.extend(
                compare(expected[key], actual[key], f"{path}.{key}", atol)
            )
        return errors
    if isinstance(expected, list):
        if not isinstance(actual, list) or len(expected) != len(actual):
            return [f"{path}: list mismatch"]
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
            errors.append(f"{path}: expected numeric")
        elif not math.isclose(
            float(expected), float(actual), rel_tol=0.0, abs_tol=atol
        ):
            errors.append(
                f"{path}: expected={expected!r} actual={actual!r}"
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
        print("MARKET_BOOKMAKER_DISPERSION_V1 freeze mismatch:")
        for error in errors:
            print("-", error)
        return 1

    print("PASS: MARKET_BOOKMAKER_DISPERSION_V1 semantic result reproduced.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
