"""Fail-closed true-xG source feasibility audit for Historical Football Signal Lab.

Research only. Shot and shot-on-target statistics are not xG. This module reuses the
existing schema detector and records whether downloaded historical source files contain
an explicit home/away xG pair. Even a detected pair remains non-experiment-ready until
its definition and pre-kickoff/point-in-time provenance are validated.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from historical_shot_quality_profile import source_capability as shot_source_capability


def source_capability(frame: pd.DataFrame) -> dict[str, object]:
    detected = shot_source_capability(frame)
    xg_pair = detected["true_xg_columns"]
    return {
        "true_xg_pair_detected": bool(detected["true_xg_pair_detected"]),
        "true_xg_columns": xg_pair,
        "status": (
            "TRUE_XG_SCHEMA_DETECTED_TEMPORAL_PROVENANCE_REQUIRED"
            if xg_pair is not None
            else "TRUE_XG_DATA_GAP"
        ),
        # Schema presence is not evidence that xG was generated/available before kickoff.
        "experiment_ready": False,
    }


def audit_downloaded_sources(raw_root: Path) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for path in sorted(raw_root.glob("*/*.csv")):
        frame = pd.read_csv(path, nrows=5)
        rows.append(
            {
                "league": path.parent.name.upper(),
                "source_file": path.name,
                "columns": len(frame.columns),
                **source_capability(frame),
            }
        )
    if not rows:
        raise RuntimeError(f"no downloaded historical CSVs found under {raw_root}")
    return pd.DataFrame(rows)


def write_true_xg_capability_report(raw_root: Path, output_dir: Path) -> pd.DataFrame:
    output_dir.mkdir(parents=True, exist_ok=True)
    report = audit_downloaded_sources(raw_root)
    report.to_csv(output_dir / "true_xg_source_capability.csv", index=False)
    return report
