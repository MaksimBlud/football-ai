"""Semantic freeze guard for MARKET_MAX_AVG_SPREAD_REPLICATION_V2."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def projection(report: dict) -> dict:
    result = report["result"]

    if "raw_brier_by_league" in result:
        raw_by_league = result["raw_brier_by_league"]
        excess_by_league = result["excess_brier_by_league"]
        favorite_by_league = result["favorite_probability_diagnostic"]["by_league"]
        raw = result["raw_brier"]
        excess = result["excess_brier"]
        return {
            "experiment_id": report["experiment_id"],
            "package_versions": report["package_versions"],
            "result": {
                "eligible_leagues": result["eligible_leagues"],
                "prepared_rows": result["prepared_rows"],
                "matched_rows": result["matched_rows"],
                "matched_cell_count": result["matched_cell_count"],
                "raw_brier": raw,
                "excess_brier": excess,
                "favorite_probability_diagnostic": {
                    "pooled_high_minus_low":
                        result["favorite_probability_diagnostic"]["pooled_high_minus_low"],
                    "by_league": favorite_by_league,
                },
                "raw_brier_by_league": raw_by_league,
                "excess_brier_by_league": excess_by_league,
                "signals_supported": result["signals_supported"],
                "interpretation": result["interpretation"],
            },
        }

    raw_breakdown = result["raw_brier"]["breakdown"]
    raw_bootstrap = result["raw_brier"]["bootstrap"]
    excess_breakdown = result["excess_brier"]["breakdown"]
    excess_bootstrap = result["excess_brier"]["bootstrap"]
    favorite_breakdown = result["favorite_probability_diagnostic"]["breakdown"]

    return {
        "experiment_id": report["experiment_id"],
        "package_versions": report["package_versions"],
        "result": {
            "eligible_leagues": result["eligible_leagues"],
            "prepared_rows": result["prepared_rows"],
            "matched_rows": result["matched_rows"],
            "matched_cell_count": result["matched_cell_count"],
            "raw_brier": {
                "pooled_high_minus_low":
                    raw_breakdown["pooled_high_minus_low"],
                "negative_leagues":
                    raw_breakdown["negative_leagues"],
                "league_count":
                    raw_breakdown["league_count"],
                "negative_cells":
                    raw_breakdown["negative_cells"],
                "negative_cell_fraction":
                    raw_breakdown["negative_cell_fraction"],
                "ci95_low":
                    raw_bootstrap["ci95_low"],
                "ci95_high":
                    raw_bootstrap["ci95_high"],
                "bootstrap_probability_negative":
                    raw_bootstrap["bootstrap_probability_negative"],
                "supported":
                    result["raw_brier"]["supported"],
            },
            "excess_brier": {
                "pooled_high_minus_low":
                    excess_breakdown["pooled_high_minus_low"],
                "negative_leagues":
                    excess_breakdown["negative_leagues"],
                "league_count":
                    excess_breakdown["league_count"],
                "negative_cells":
                    excess_breakdown["negative_cells"],
                "negative_cell_fraction":
                    excess_breakdown["negative_cell_fraction"],
                "ci95_low":
                    excess_bootstrap["ci95_low"],
                "ci95_high":
                    excess_bootstrap["ci95_high"],
                "bootstrap_probability_negative":
                    excess_bootstrap["bootstrap_probability_negative"],
                "supported":
                    result["excess_brier"]["supported"],
            },
            "favorite_probability_diagnostic": {
                "pooled_high_minus_low":
                    favorite_breakdown["pooled_high_minus_low"],
                "by_league": {
                    league: row["high_minus_low"]
                    for league, row in favorite_breakdown["by_league"].items()
                },
            },
            "raw_brier_by_league": {
                league: row["high_minus_low"]
                for league, row in raw_breakdown["by_league"].items()
            },
            "excess_brier_by_league": {
                league: row["high_minus_low"]
                for league, row in excess_breakdown["by_league"].items()
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
            return [
                f"{path}: key mismatch expected={sorted(expected)} "
                f"actual={sorted(actual)}"
            ]
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
        print("MARKET_MAX_AVG_SPREAD_REPLICATION_V2 freeze mismatch:")
        for error in errors:
            print("-", error)
        return 1

    print("PASS: MARKET_MAX_AVG_SPREAD_REPLICATION_V2 semantic result reproduced.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
