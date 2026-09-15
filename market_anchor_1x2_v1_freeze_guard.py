"""Strict semantic freeze guard for MARKET_ANCHOR_1X2_V1 reports.

The frozen report is immutable. Re-runs must match its complete JSON structure and
all non-floating values exactly. Finite floating-point values may differ only within
an extremely small numerical tolerance to allow platform/library last-bit drift.
This guard does not change model selection, acceptance rules, or frozen metrics.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

DEFAULT_ATOL = 1e-12


class FreezeMismatch(AssertionError):
    pass


def _compare(expected: Any, actual: Any, *, path: str, atol: float) -> None:
    if isinstance(expected, bool) or isinstance(actual, bool):
        if type(expected) is not type(actual) or expected != actual:
            raise FreezeMismatch(f"{path}: boolean mismatch: {expected!r} != {actual!r}")
        return

    if isinstance(expected, dict) or isinstance(actual, dict):
        if not isinstance(expected, dict) or not isinstance(actual, dict):
            raise FreezeMismatch(f"{path}: type mismatch: {type(expected).__name__} != {type(actual).__name__}")
        if set(expected) != set(actual):
            missing = sorted(set(expected) - set(actual))
            extra = sorted(set(actual) - set(expected))
            raise FreezeMismatch(f"{path}: key mismatch; missing={missing}, extra={extra}")
        for key in expected:
            _compare(expected[key], actual[key], path=f"{path}.{key}", atol=atol)
        return

    if isinstance(expected, list) or isinstance(actual, list):
        if not isinstance(expected, list) or not isinstance(actual, list):
            raise FreezeMismatch(f"{path}: type mismatch: {type(expected).__name__} != {type(actual).__name__}")
        if len(expected) != len(actual):
            raise FreezeMismatch(f"{path}: list length mismatch: {len(expected)} != {len(actual)}")
        for index, (left, right) in enumerate(zip(expected, actual)):
            _compare(left, right, path=f"{path}[{index}]", atol=atol)
        return

    if isinstance(expected, int) or isinstance(actual, int):
        if type(expected) is not int or type(actual) is not int or expected != actual:
            raise FreezeMismatch(f"{path}: integer/type mismatch: {expected!r} != {actual!r}")
        return

    if isinstance(expected, float) or isinstance(actual, float):
        if type(expected) is not float or type(actual) is not float:
            raise FreezeMismatch(f"{path}: float/type mismatch: {type(expected).__name__} != {type(actual).__name__}")
        if not math.isfinite(expected) or not math.isfinite(actual):
            raise FreezeMismatch(f"{path}: non-finite float is forbidden")
        if abs(expected - actual) > atol:
            raise FreezeMismatch(
                f"{path}: float mismatch {expected!r} != {actual!r}; "
                f"abs_delta={abs(expected-actual):.17g} > atol={atol:.17g}"
            )
        return

    if type(expected) is not type(actual) or expected != actual:
        raise FreezeMismatch(f"{path}: value/type mismatch: {expected!r} != {actual!r}")


def assert_reports_equivalent(expected: dict[str, Any], actual: dict[str, Any], *, atol: float = DEFAULT_ATOL) -> None:
    if not math.isfinite(atol) or atol < 0.0:
        raise ValueError("atol must be finite and non-negative")
    _compare(expected, actual, path="$", atol=atol)


def assert_report_files_equivalent(expected_path: Path, actual_path: Path, *, atol: float = DEFAULT_ATOL) -> None:
    expected = json.loads(expected_path.read_text(encoding="utf-8"))
    actual = json.loads(actual_path.read_text(encoding="utf-8"))
    if not isinstance(expected, dict) or not isinstance(actual, dict):
        raise FreezeMismatch("$: both report roots must be JSON objects")
    assert_reports_equivalent(expected, actual, atol=atol)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("expected", type=Path)
    parser.add_argument("actual", type=Path)
    parser.add_argument("--atol", type=float, default=DEFAULT_ATOL)
    args = parser.parse_args()
    assert_report_files_equivalent(args.expected, args.actual, atol=args.atol)
    print(f"FROZEN_REPORT_SEMANTIC_MATCH atol={args.atol:.1e}")


if __name__ == "__main__":
    main()
