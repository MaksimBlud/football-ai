"""League-aware fixture and odds-snapshot normalization for research code."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from league_config import EPL as EPL_CONFIG
from league_config import validate_league_identifier


EPL = EPL_CONFIG.identifier

CANONICAL_FIXTURE_IDENTITY = (
    "league",
    "home_team",
    "away_team",
    "commence_time_utc",
)

CANONICAL_SNAPSHOT_FIELDS = (
    "league",
    "event_id",
    "snapshot_time_utc",
    "commence_time_utc",
    "home_team",
    "away_team",
    "home_odds",
    "draw_odds",
    "away_odds",
)

LEGACY_UPCOMING_PATH = Path(
    "data/upcoming_matches.csv"
)


def require_league(
    frame: pd.DataFrame,
    *,
    legacy_epl: bool = False,
) -> pd.DataFrame:
    """Return a copy with valid league identity.

    League-less data is accepted only through an explicit legacy-EPL path.
    """

    result = frame.copy()

    if "league" not in result.columns:
        if not legacy_epl:
            raise ValueError(
                "League-less data requires explicit "
                "legacy EPL compatibility"
            )

        result.insert(
            0,
            "league",
            EPL,
        )

    if (
        result["league"].isna().any()
        or result[
            "league"
        ].astype(str).str.strip().eq("").any()
    ):
        raise ValueError(
            "league must be present for every row"
        )

    for identifier in (
        result["league"]
        .astype(str)
        .unique()
    ):
        validate_league_identifier(
            identifier
        )

    return result


def normalize_upcoming_fixtures(
    frame: pd.DataFrame,
    *,
    source_path: Path | None = None,
) -> pd.DataFrame:
    """Normalize fixtures.

    Only the repository's known legacy upcoming file can implicitly
    enter the explicit EPL compatibility adapter.
    """

    legacy = (
        source_path is not None
        and Path(source_path)
        == LEGACY_UPCOMING_PATH
    )

    return require_league(
        frame,
        legacy_epl=legacy,
    )


def normalize_snapshot_rows(
    frame: pd.DataFrame,
    *,
    legacy_epl: bool = False,
) -> pd.DataFrame:
    """Validate canonical snapshot rows with explicit legacy DB support."""

    result = require_league(
        frame,
        legacy_epl=legacy_epl,
    )

    missing = set(
        CANONICAL_SNAPSHOT_FIELDS
    ).difference(
        result.columns
    )

    # event_id was absent from the historical research projection.
    if legacy_epl:
        missing.discard(
            "event_id"
        )

    if missing:
        raise ValueError(
            "Odds snapshots missing columns: "
            f"{sorted(missing)}"
        )

    return result


def load_legacy_epl_history(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Explicit adapter for pre-league Challenger history CSVs."""

    return require_league(
        frame,
        legacy_epl=True,
    )
