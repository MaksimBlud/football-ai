"""Build the EPL offline research foundation.

No training.
No Supabase writes.
No operational activation.
"""

from __future__ import annotations

from pathlib import Path

from league_offline_features import (
    build_temporal_elo_features,
)

from league_offline_history import (
    load_configured_history,
)

from league_runtime_config import (
    EPL_RUNTIME_CONFIG,
)


def main() -> None:
    config = EPL_RUNTIME_CONFIG

    config.validate()

    normalized = load_configured_history(
        config=config,
        raw_directory=Path(
            "data/raw"
        ),
        file_prefix="epl",
        require_complete=True,
    )

    if len(normalized) != 3800:
        raise SystemExit(
            f"Expected 3800 normalized matches, "
            f"got {len(normalized)}"
        )

    config.paths.historical_normalized.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    normalized.to_csv(
        config.paths.historical_normalized,
        index=False,
    )

    temporal = build_temporal_elo_features(
        normalized,
        config,
    )

    temporal.to_csv(
        config.paths.temporal_features,
        index=False,
    )

    trainable = (
        temporal.loc[
            temporal[
                "trainable"
            ]
        ]
        .reset_index(
            drop=True
        )
    )

    trainable.to_csv(
        config.paths.trainable_features,
        index=False,
    )

    print(
        "league:",
        config.identity.identifier,
    )

    print(
        "normalized:",
        len(normalized),
    )

    print(
        "temporal:",
        len(temporal),
    )

    print(
        "trainable:",
        len(trainable),
    )

    teams = sorted(
        set(
            normalized[
                "home_team"
            ]
        )
        |
        set(
            normalized[
                "away_team"
            ]
        )
    )

    print(
        "canonical teams:",
        len(teams),
    )

    print(
        "calibration status:",
        config
        .structural_v2
        .calibration_status,
    )

    print(
        "normalized path:",
        config
        .paths
        .historical_normalized,
    )

    print(
        "temporal path:",
        config
        .paths
        .temporal_features,
    )

    print(
        "trainable path:",
        config
        .paths
        .trainable_features,
    )


if __name__ == "__main__":
    main()
