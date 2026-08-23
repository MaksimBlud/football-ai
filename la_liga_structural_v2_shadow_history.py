"""Append-only live history for frozen La Liga Structural Edge V2.

Research-only.

Rules:
- reads the current Structural V2 shadow;
- attaches the real market snapshot timestamp;
- accepts only observations recorded BEFORE kickoff;
- exact repeated observations are ignored;
- existing history rows are never modified;
- no production artifact;
- no Supabase write.
"""

from __future__ import annotations

import argparse
import hashlib
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent

SHADOW_PATH = (
    ROOT
    / "experiments"
    / "la_liga_structural_v2_shadow.csv"
)

MARKET_PATH = (
    ROOT
    / "experiments"
    / "la_liga_market_shadow.csv"
)

HISTORY_PATH = (
    ROOT
    / "experiments"
    / "la_liga_structural_v2_shadow_history.csv"
)

PRODUCTION_ARTIFACTS = (
    "football_model_xgboost_elo.pkl",
    "football_model_no_odds.pkl",
    "1x2_calibrator.pkl",
    "home_goals_model_no_odds.pkl",
    "away_goals_model_no_odds.pkl",
    "over_2_5_calibrator.pkl",
    "btts_calibrator.pkl",
)

KEY_COLUMNS = [
    "league",
    "event_id",
    "commence_time_utc",
    "snapshot_time_utc",
    "home_team",
    "away_team",
    "structural_ready",
    "structural_score",
    "correction_enabled",
    "realized_correction_weight",
    "market_home_probability",
    "market_draw_probability",
    "market_away_probability",
    "shadow_home_probability",
    "shadow_draw_probability",
    "shadow_away_probability",
    "market_argmax",
    "shadow_argmax",
    "prediction_source",
]


def sha256(path: Path) -> str | None:
    if not path.exists():
        return None

    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def production_state() -> dict:
    return {
        name: sha256(
            ROOT / name
        )
        for name in PRODUCTION_ARTIFACTS
    }


def stable_value(value) -> str:
    if pd.isna(value):
        return "<NA>"

    if isinstance(
        value,
        (float, np.floating),
    ):
        return format(
            float(value),
            ".15g",
        )

    return str(value)


def observation_key(
    row: pd.Series,
) -> str:
    payload = "\x1f".join(
        stable_value(
            row.get(column)
        )
        for column in KEY_COLUMNS
    )

    return hashlib.sha256(
        payload.encode(
            "utf-8"
        )
    ).hexdigest()


def prepare_observations(
    shadow: pd.DataFrame,
    market: pd.DataFrame,
    *,
    recorded_at_utc: datetime,
) -> pd.DataFrame:
    required_shadow = {
        "league",
        "event_id",
        "commence_time_utc",
        "home_team",
        "away_team",
        "structural_ready",
        "structural_score",
        "correction_enabled",
        "realized_correction_weight",
        "market_home_probability",
        "market_draw_probability",
        "market_away_probability",
        "shadow_home_probability",
        "shadow_draw_probability",
        "shadow_away_probability",
        "market_argmax",
        "shadow_argmax",
        "prediction_source",
        "research_only",
    }

    required_market = {
        "league",
        "event_id",
        "snapshot_time_utc",
        "generated_at_utc",
        "market_shadow_status",
    }

    missing_shadow = (
        required_shadow
        - set(shadow.columns)
    )

    missing_market = (
        required_market
        - set(market.columns)
    )

    if missing_shadow:
        raise ValueError(
            "Structural shadow missing: "
            + ", ".join(
                sorted(missing_shadow)
            )
        )

    if missing_market:
        raise ValueError(
            "Market shadow missing: "
            + ", ".join(
                sorted(missing_market)
            )
        )

    market_lookup = (
        market[
            list(
                required_market
            )
        ]
        .copy()
    )

    market_lookup = market_lookup[
        market_lookup[
            "market_shadow_status"
        ]
        == "OK"
    ].copy()

    if market_lookup.duplicated(
        subset=[
            "league",
            "event_id",
        ]
    ).any():
        raise ValueError(
            "Latest market shadow has duplicate event_id"
        )

    merged = shadow.merge(
        market_lookup[
            [
                "league",
                "event_id",
                "snapshot_time_utc",
                "generated_at_utc",
            ]
        ],
        on=[
            "league",
            "event_id",
        ],
        how="left",
        validate="one_to_one",
    )

    merged[
        "commence_time_utc"
    ] = pd.to_datetime(
        merged[
            "commence_time_utc"
        ],
        utc=True,
        errors="raise",
    )

    merged[
        "snapshot_time_utc"
    ] = pd.to_datetime(
        merged[
            "snapshot_time_utc"
        ],
        utc=True,
        errors="raise",
    )

    merged[
        "market_generated_at_utc"
    ] = pd.to_datetime(
        merged[
            "generated_at_utc"
        ],
        utc=True,
        errors="raise",
    )

    recorded = pd.Timestamp(
        recorded_at_utc
    )

    if recorded.tzinfo is None:
        recorded = recorded.tz_localize(
            "UTC"
        )
    else:
        recorded = recorded.tz_convert(
            "UTC"
        )

    merged[
        "recorded_at_utc"
    ] = recorded

    # Market price itself must have existed pre-kickoff.
    valid_market_time = (
        merged[
            "snapshot_time_utc"
        ]
        < merged[
            "commence_time_utc"
        ]
    )

    # More importantly: this V2 observation must itself
    # actually have been recorded before kickoff.
    valid_record_time = (
        merged[
            "recorded_at_utc"
        ]
        < merged[
            "commence_time_utc"
        ]
    )

    merged[
        "pre_kickoff_valid"
    ] = (
        valid_market_time
        & valid_record_time
    )

    valid = merged[
        merged[
            "pre_kickoff_valid"
        ]
    ].copy()

    if not valid.empty:
        valid[
            "observation_key"
        ] = valid.apply(
            observation_key,
            axis=1,
        )

    # Original generated_at_utc is retained under
    # a clear market-specific name.
    valid = valid.drop(
        columns=[
            "generated_at_utc",
        ],
        errors="ignore",
    )

    return valid


def append_history(
    current: pd.DataFrame,
    path: Path,
) -> tuple[
    pd.DataFrame,
    int,
]:
    if path.exists():
        existing = pd.read_csv(
            path
        )
    else:
        existing = pd.DataFrame()

    if current.empty:
        return (
            existing,
            0,
        )

    if (
        not existing.empty
        and "observation_key"
        not in existing.columns
    ):
        raise ValueError(
            "Existing history lacks observation_key"
        )

    known = (
        set(
            existing[
                "observation_key"
            ].astype(str)
        )
        if not existing.empty
        else set()
    )

    additions = current[
        ~current[
            "observation_key"
        ]
        .astype(str)
        .isin(known)
    ].copy()

    if additions.empty:
        return (
            existing,
            0,
        )

    combined = pd.concat(
        [
            existing,
            additions,
        ],
        ignore_index=True,
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    combined.to_csv(
        path,
        index=False,
    )

    return (
        combined,
        len(additions),
    )


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--shadow",
        type=Path,
        default=SHADOW_PATH,
    )

    parser.add_argument(
        "--market",
        type=Path,
        default=MARKET_PATH,
    )

    parser.add_argument(
        "--history",
        type=Path,
        default=HISTORY_PATH,
    )

    args = parser.parse_args()

    before = production_state()

    shadow = pd.read_csv(
        args.shadow
    )

    market = pd.read_csv(
        args.market
    )

    now = datetime.now(
        timezone.utc
    )

    observations = (
        prepare_observations(
            shadow,
            market,
            recorded_at_utc=now,
        )
    )

    combined, appended = (
        append_history(
            observations,
            args.history,
        )
    )

    after = production_state()

    if before != after:
        raise RuntimeError(
            "Production artifact changed"
        )

    invalid_count = (
        len(shadow)
        - len(observations)
    )

    print("=" * 72)
    print("LA LIGA STRUCTURAL V2 SHADOW HISTORY")
    print("=" * 72)

    print(
        "current shadow rows:",
        len(shadow),
    )

    print(
        "valid pre-kickoff observations:",
        len(observations),
    )

    print(
        "rejected/non-pre-kickoff rows:",
        invalid_count,
    )

    print(
        "new observations appended:",
        appended,
    )

    print(
        "history rows:",
        len(combined),
    )

    if not combined.empty:
        print(
            "unique observations:",
            combined[
                "observation_key"
            ].nunique(),
        )

        print(
            "fixtures:",
            combined[
                "event_id"
            ].nunique(),
        )

    print(
        "production unchanged:",
        True,
    )

    print(
        "history:",
        args.history,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
