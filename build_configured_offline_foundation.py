"""Build league offline research foundations from validated historical CSVs.

No training.
No Supabase writes.
No runtime activation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

from league_offline_features import build_temporal_elo_features
from league_offline_history import load_configured_history
from league_runtime_config import LeagueRuntimeConfig


def build_configured_offline_foundation(
    *,
    config: LeagueRuntimeConfig,
    raw_directory: Path,
    file_prefix: str,
    season_codes: Mapping[str, str],
) -> dict[str, object]:
    config.validate()
    if not season_codes:
        raise ValueError("No completed seasons selected for offline foundation")

    normalized = load_configured_history(
        config=config,
        raw_directory=raw_directory,
        file_prefix=file_prefix,
        require_complete=True,
        season_codes=season_codes,
    )

    config.paths.historical_normalized.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    normalized.to_csv(config.paths.historical_normalized, index=False)

    temporal = build_temporal_elo_features(normalized, config)
    temporal.to_csv(config.paths.temporal_features, index=False)

    trainable = temporal.loc[temporal["trainable"]].reset_index(drop=True)
    trainable.to_csv(config.paths.trainable_features, index=False)

    teams = sorted(
        set(normalized["home_team"]) | set(normalized["away_team"])
    )
    return {
        "league": config.identity.identifier,
        "seasons": list(season_codes.values()),
        "normalized": len(normalized),
        "temporal": len(temporal),
        "trainable": len(trainable),
        "canonical_teams": len(teams),
        "calibration_status": config.structural_v2.calibration_status,
        "normalized_path": str(config.paths.historical_normalized),
        "temporal_path": str(config.paths.temporal_features),
        "trainable_path": str(config.paths.trainable_features),
        "production_artifacts_touched": False,
    }
