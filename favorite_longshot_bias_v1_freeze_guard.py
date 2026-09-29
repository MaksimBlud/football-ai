"""Semantic freeze guard for FAVORITE_LONGSHOT_BIAS_V1."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def projection(report: dict) -> dict:
    result = report["result"]

    if "negative_bias_leagues" in result.get("standard", {}):
        standard = result["standard"]
        temporal = {}
        for split in ("discovery", "validation", "test"):
            row = standard["temporal"][split]
            temporal[split] = {
                "favorite_roi": row["favorite_roi"],
                "longshot_roi": row["longshot_roi"],
                "bias_delta": row["bias_delta"],
            }
        temporal["overall"] = standard["temporal"]["overall"]

        return {
            "experiment_id": report["experiment_id"],
            "source_rows": report["source_rows"],
            "package_versions": report["package_versions"],
            "result": {
                "eligible_leagues": result["eligible_leagues"],
                "standard": {
                    "side_offers": standard["side_offers"],
                    "fixtures": standard["fixtures"],
                    "temporal": temporal,
                    "by_league": standard["by_league"],
                    "negative_bias_leagues": standard["negative_bias_leagues"],
                    "bootstrap": standard["bootstrap"],
                    "bands": standard["bands"],
                },
                "closing_diagnostic": result["closing_diagnostic"],
                "max_line_shopping_diagnostic":
                    result["max_line_shopping_diagnostic"],
                "supported": result["supported"],
                "interpretation": result["interpretation"],
            },
        }

    standard = result["standard"]
    compact_temporal = {}
    for split in ("discovery", "validation", "test"):
        row = standard["temporal"][split]
        compact_temporal[split] = {
            "favorite_roi": row["favorite"]["roi"],
            "longshot_roi": row["longshot"]["roi"],
            "bias_delta": row["bias_delta_longshot_minus_favorite"],
        }

    overall = standard["temporal"]["overall"]
    compact_temporal["overall"] = {
        "favorite": overall["favorite"],
        "longshot": overall["longshot"],
        "bias_delta": overall["bias_delta_longshot_minus_favorite"],
    }

    bands = {}
    for band, row in standard["bands"].items():
        bands[band] = {
            "offers": row["offers"],
            "roi": row["roi"],
            "calibration_gap": row["calibration_gap"],
        }

    by_league = {
        league: row["bias_delta_longshot_minus_favorite"]
        for league, row in standard["by_league"].items()
    }

    closing = result["closing_diagnostic"]
    closing_compact = {
        "overall": {
            "favorite_roi": closing["overall"]["favorite"]["roi"],
            "longshot_roi": closing["overall"]["longshot"]["roi"],
            "bias_delta":
                closing["overall"]["bias_delta_longshot_minus_favorite"],
        },
        "by_league": {
            league: row["bias_delta_longshot_minus_favorite"]
            for league, row in closing["by_league"].items()
        },
    }

    max_diag = result["max_line_shopping_diagnostic"]
    max_compact = {
        "overall": {
            "favorite_roi": max_diag["overall"]["favorite"]["roi"],
            "longshot_roi": max_diag["overall"]["longshot"]["roi"],
            "bias_delta":
                max_diag["overall"]["bias_delta_longshot_minus_favorite"],
        },
    }

    return {
        "experiment_id": report["experiment_id"],
        "source_rows": report["source_rows"],
        "package_versions": report["package_versions"],
        "result": {
            "eligible_leagues": result["eligible_leagues"],
            "standard": {
                "side_offers": standard["side_offers"],
                "fixtures": standard["fixtures"],
                "temporal": compact_temporal,
                "by_league": by_league,
                "negative_bias_leagues":
                    standard["negative_bias_leagues"],
                "bootstrap": standard["bootstrap"],
                "bands": bands,
            },
            "closing_diagnostic": closing_compact,
            "max_line_shopping_diagnostic": max_compact,
            "supported": result["supported"],
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
            float(expected),
            float(actual),
            rel_tol=0.0,
            abs_tol=atol,
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
        print("FAVORITE_LONGSHOT_BIAS_V1 freeze mismatch:")
        for error in errors:
            print("-", error)
        return 1

    print("PASS: FAVORITE_LONGSHOT_BIAS_V1 semantic result reproduced.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
