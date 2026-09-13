"""Fail-closed historical tactical-matchup source capability audit.

Research only. Standard match statistics (shots, corners, fouls, cards) are useful
team-stat proxies, but are not relabeled as formations, possession, passing structure
or pressing. A tactical-matchup experiment remains closed until explicit tactical data
with pre-kickoff/point-in-time provenance is available.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

FORMATION_PAIRS = (
    ("HomeFormation", "AwayFormation"),
    ("home_formation", "away_formation"),
)
POSSESSION_PAIRS = (
    ("HomePossession", "AwayPossession"),
    ("HPossession", "APossession"),
    ("home_possession", "away_possession"),
)
PASSING_PAIRS = (
    ("HomePasses", "AwayPasses"),
    ("HPasses", "APasses"),
    ("home_passes", "away_passes"),
)
PRESSING_PAIRS = (
    ("HomePPDA", "AwayPPDA"),
    ("HPPDA", "APPDA"),
    ("home_ppda", "away_ppda"),
)
TEAM_STAT_PROXY_PAIRS = (
    ("HS", "AS"),
    ("HST", "AST"),
    ("HC", "AC"),
    ("HF", "AF"),
    ("HY", "AY"),
    ("HR", "AR"),
)


def _first_pair(frame: pd.DataFrame, pairs: tuple[tuple[str, str], ...]):
    return next((pair for pair in pairs if pair[0] in frame.columns and pair[1] in frame.columns), None)


def source_capability(frame: pd.DataFrame) -> dict[str, object]:
    formation = _first_pair(frame, FORMATION_PAIRS)
    possession = _first_pair(frame, POSSESSION_PAIRS)
    passing = _first_pair(frame, PASSING_PAIRS)
    pressing = _first_pair(frame, PRESSING_PAIRS)
    proxy_pairs = tuple(pair for pair in TEAM_STAT_PROXY_PAIRS if pair[0] in frame.columns and pair[1] in frame.columns)
    dynamic = any(pair is not None for pair in (possession, passing, pressing))
    if formation is not None and dynamic:
        status = "TACTICAL_SCHEMA_DETECTED_TEMPORAL_PROVENANCE_REQUIRED"
    elif any(pair is not None for pair in (formation, possession, passing, pressing)):
        status = "PARTIAL_TACTICAL_SCHEMA_INSUFFICIENT"
    elif proxy_pairs:
        status = "TEAM_STATS_ONLY_NOT_TACTICAL_MATCHUP"
    else:
        status = "DATA_GAP"
    return {
        "formation_columns": formation,
        "possession_columns": possession,
        "passing_columns": passing,
        "pressing_columns": pressing,
        "team_stat_proxy_pairs": proxy_pairs,
        "explicit_tactical_schema_detected": formation is not None and dynamic,
        "status": status,
        # Column names alone cannot prove that tactical information was available pre-kickoff.
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


def write_tactical_capability_report(raw_root: Path, output_dir: Path) -> pd.DataFrame:
    output_dir.mkdir(parents=True, exist_ok=True)
    report = audit_downloaded_sources(raw_root)
    report.to_csv(output_dir / "tactical_matchup_source_capability.csv", index=False)
    return report
