"""Fail-closed historical lineup-strength source capability audit.

Research only. The current Historical Football Signal Lab uses Football-Data match CSVs.
This module never fabricates player/lineup strength from team-level aggregates. It only
records whether downloaded historical sources expose explicit pre-match lineup/strength
fields that could support a separately designed leakage-safe experiment.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

LINEUP_COLUMN_PAIRS = (
    ("HomeLineup", "AwayLineup"),
    ("HomeStartingXI", "AwayStartingXI"),
    ("home_lineup", "away_lineup"),
    ("home_starting_xi", "away_starting_xi"),
)
LINEUP_STRENGTH_COLUMN_PAIRS = (
    ("HomeLineupStrength", "AwayLineupStrength"),
    ("HomeXIStrength", "AwayXIStrength"),
    ("home_lineup_strength", "away_lineup_strength"),
    ("home_xi_strength", "away_xi_strength"),
)


def _first_pair(frame: pd.DataFrame, pairs: tuple[tuple[str, str], ...]):
    return next((pair for pair in pairs if pair[0] in frame.columns and pair[1] in frame.columns), None)


def source_capability(frame: pd.DataFrame) -> dict[str, object]:
    """Detect explicit lineup/lineup-strength schema without inferring missing data."""
    lineup_pair = _first_pair(frame, LINEUP_COLUMN_PAIRS)
    strength_pair = _first_pair(frame, LINEUP_STRENGTH_COLUMN_PAIRS)
    if strength_pair is not None:
        status = "STRENGTH_SCHEMA_DETECTED_TEMPORAL_PROVENANCE_REQUIRED"
    elif lineup_pair is not None:
        status = "LINEUP_IDENTITY_ONLY_PLAYER_STRENGTH_SOURCE_REQUIRED"
    else:
        status = "DATA_GAP"
    return {
        "lineup_pair_detected": lineup_pair is not None,
        "lineup_columns": lineup_pair,
        "lineup_strength_pair_detected": strength_pair is not None,
        "lineup_strength_columns": strength_pair,
        "status": status,
        # Schema presence alone never proves that values were known before kickoff.
        "experiment_ready": False,
    }


def audit_downloaded_sources(raw_root: Path) -> pd.DataFrame:
    """Audit already-downloaded raw CSVs; performs no provider calls or writes outside artifacts."""
    rows: list[dict[str, object]] = []
    for path in sorted(raw_root.glob("*/*.csv")):
        frame = pd.read_csv(path, nrows=5)
        capability = source_capability(frame)
        rows.append(
            {
                "league": path.parent.name.upper(),
                "source_file": path.name,
                "columns": len(frame.columns),
                **capability,
            }
        )
    if not rows:
        raise RuntimeError(f"no downloaded historical CSVs found under {raw_root}")
    return pd.DataFrame(rows)


def write_lineup_capability_report(raw_root: Path, output_dir: Path) -> pd.DataFrame:
    output_dir.mkdir(parents=True, exist_ok=True)
    report = audit_downloaded_sources(raw_root)
    report.to_csv(output_dir / "lineup_strength_source_capability.csv", index=False)
    return report
