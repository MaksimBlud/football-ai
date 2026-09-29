"""Semantic freeze guard for MARKET_MAX_AVG_SPREAD_V1."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def projection(report: dict) -> dict:
    result = report["result"]

    if "repricing" in result and "mean_high_minus_low" in result["repricing"]:
        repricing = result["repricing"]
        error = result["error"]
        return {
            "experiment_id": report["experiment_id"],
            "source_rows": report["source_rows"],
            "package_versions": report["package_versions"],
            "result": {
                "usable_rows": result["usable_rows"],
                "thresholds": result["thresholds"],
                "spread_summary": result["spread_summary"],
                "repricing": {
                    "positive_seasons_all": repricing["positive_seasons_all"],
                    "positive_discovery_seasons": repricing["positive_discovery_seasons"],
                    "mean_high_minus_low": repricing["mean_high_minus_low"],
                    "ci95_low": repricing["ci95_low"],
                    "ci95_high": repricing["ci95_high"],
                    "supported": repricing["supported"],
                },
                "error": {
                    "positive_seasons_all": error["positive_seasons_all"],
                    "positive_discovery_seasons": error["positive_discovery_seasons"],
                    "mean_high_minus_low": error["mean_high_minus_low"],
                    "ci95_low": error["ci95_low"],
                    "ci95_high": error["ci95_high"],
                    "supported": error["supported"],
                },
                "signals_supported": result["signals_supported"],
                "interpretation": result["interpretation"],
            },
        }

    repricing = result["repricing"]
    error = result["error"]
    return {
        "experiment_id": report["experiment_id"],
        "source_rows": report["source_rows"],
        "package_versions": report["package_versions"],
        "result": {
            "usable_rows": result["usable_rows"],
            "thresholds": result["thresholds"],
            "spread_summary": result["spread_summary"],
            "repricing": {
                "positive_seasons_all":
                    repricing["effects"]["positive_seasons_all"],
                "positive_discovery_seasons":
                    repricing["effects"]["positive_discovery_seasons"],
                "mean_high_minus_low":
                    repricing["bootstrap"]["mean_high_minus_low"],
                "ci95_low":
                    repricing["bootstrap"]["ci95_low"],
                "ci95_high":
                    repricing["bootstrap"]["ci95_high"],
                "supported": repricing["supported"],
            },
            "error": {
                "positive_seasons_all":
                    error["effects"]["positive_seasons_all"],
                "positive_discovery_seasons":
                    error["effects"]["positive_discovery_seasons"],
                "mean_high_minus_low":
                    error["bootstrap"]["mean_high_minus_low"],
                "ci95_low":
                    error["bootstrap"]["ci95_low"],
                "ci95_high":
                    error["bootstrap"]["ci95_high"],
                "supported": error["supported"],
            },
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
            errors.extend(compare(expected[key], actual[key], f"{path}.{key}", atol))
        return errors
    if isinstance(expected, list):
        if not isinstance(actual, list) or len(expected) != len(actual):
            return [f"{path}: list mismatch"]
        for index, (left, right) in enumerate(zip(expected, actual)):
            errors.extend(compare(left, right, f"{path}[{index}]", atol))
        return errors
    if isinstance(expected, bool) or expected is None or isinstance(expected, str):
        if expected != actual:
            errors.append(f"{path}: expected={expected!r} actual={actual!r}")
        return errors
    if isinstance(expected, (int, float)):
        if not isinstance(actual, (int, float)):
            errors.append(f"{path}: expected numeric")
        elif not math.isclose(float(expected), float(actual), rel_tol=0.0, abs_tol=atol):
            errors.append(f"{path}: expected={expected!r} actual={actual!r}")
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
    errors = compare(projection(frozen), projection(runtime), atol=args.atol)

    if errors:
        print("MARKET_MAX_AVG_SPREAD_V1 freeze mismatch:")
        for error in errors:
            print("-", error)
        return 1

    print("PASS: MARKET_MAX_AVG_SPREAD_V1 semantic result reproduced.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
