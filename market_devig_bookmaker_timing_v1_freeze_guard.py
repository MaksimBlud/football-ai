"""Semantic freeze guard for MARKET_DEVIG_BOOKMAKER_TIMING_V1."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


SOURCES = (
    "AVG_STANDARD",
    "BET365_STANDARD",
    "PINNACLE_STANDARD",
    "AVG_CLOSING",
    "BET365_CLOSING",
    "PINNACLE_CLOSING",
)
TEST_SEASON = "2025/2026"


def semantic_projection(report: dict) -> dict:
    result = report["result"]

    availability = {}
    for source in SOURCES:
        row = result["availability"][source]
        availability[source] = {
            "eligible": row["eligible"],
            "valid_rows_total": row["valid_rows_total"],
            "test_coverage": row["by_season"][TEST_SEASON]["coverage"],
        }

    decisions = {}
    for source in SOURCES:
        row = result["source_reports"][source]
        decisions[source] = {
            "selected": row.get("selected_on_discovery"),
            "robust_support": row.get("robust_support"),
            "interpretation": row["interpretation"],
        }

    avg_closing = result["source_reports"]["AVG_CLOSING"]
    power_discovery = avg_closing["discovery"]["alternatives"]["POWER"]

    common = result["common_fixture_diagnostic"]
    common_projection = {
        "common_rows": common["common_rows"],
    }
    for source in (
        "AVG_STANDARD",
        "BET365_STANDARD",
        "AVG_CLOSING",
        "BET365_CLOSING",
    ):
        row = common["by_source"][source]
        common_projection[source] = {
            "logloss": row["logloss"],
            "brier": row["brier"],
            "accuracy": row["accuracy"],
            "mean_overround": row["mean_overround"],
        }

    return {
        "experiment_id": report["experiment_id"],
        "source_rows": report["source_rows"],
        "package_versions": report["package_versions"],
        "result": {
            "availability": availability,
            "source_decisions": decisions,
            "avg_closing_power": {
                "discovery_delta_logloss":
                    power_discovery["delta_logloss_vs_multiplicative"],
                "discovery_delta_brier":
                    power_discovery["delta_brier_vs_multiplicative"],
                "joint_season_wins":
                    power_discovery["joint_season_wins"],
                "validation_baseline":
                    avg_closing["validation"]["baseline"],
                "validation_candidate":
                    avg_closing["validation"]["candidate"],
                "validation_passed":
                    avg_closing["validation"]["passed"],
                "test_baseline":
                    avg_closing["test"]["baseline"],
                "test_candidate":
                    avg_closing["test"]["candidate"],
                "test_passed":
                    avg_closing["test"]["passed"],
                "bootstrap_logloss": {
                    key: avg_closing["selected_bootstrap"]["logloss"][key]
                    for key in (
                        "ci95_low",
                        "ci95_high",
                        "bootstrap_probability_candidate_better",
                    )
                },
                "bootstrap_brier": {
                    key: avg_closing["selected_bootstrap"]["brier"][key]
                    for key in (
                        "ci95_low",
                        "ci95_high",
                        "bootstrap_probability_candidate_better",
                    )
                },
            },
            "common_fixture_multiplicative": common_projection,
            "supported_sources": result["supported_sources"],
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
        print("MARKET_DEVIG_BOOKMAKER_TIMING_V1 freeze mismatch:")
        for error in errors:
            print("-", error)
        return 1

    print("PASS: MARKET_DEVIG_BOOKMAKER_TIMING_V1 semantic result reproduced.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
