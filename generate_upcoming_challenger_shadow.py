"""
Generate research-only Challenger V0 predictions for upcoming matches.

This script:
- reads upcoming matches;
- reads already collected Supabase odds snapshots;
- uses only snapshots strictly before kickoff;
- produces MARKET / AI / Challenger V0 shadow diagnostics;
- writes only under experiments/;
- never modifies production model artifacts.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

from team_names import normalize_team_name
from fixture_identity import (
    load_legacy_epl_history,
    normalize_snapshot_rows,
    require_league,
)


UPCOMING_PATH = Path("data/upcoming_matches.csv")

DEFAULT_OUTPUT_PATH = Path(
    "experiments/upcoming_challenger_shadow.csv"
)

DEFAULT_HISTORY_PATH = Path(
    "experiments/upcoming_challenger_shadow_history.csv"
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

ODDS_COLUMNS = (
    "snapshot_time_utc",
    "commence_time_utc",
    "home_team",
    "away_team",
    "home_odds",
    "draw_odds",
    "away_odds",
)

OUTPUT_COLUMNS = (
    "league",
    "match_date",
    "match_time",
    "home_team",
    "away_team",
    "home_team_model",
    "away_team_model",
    "commence_time_utc",

    "shadow_status",

    "snapshot_time_utc",
    "hours_before_kickoff",

    "home_odds",
    "draw_odds",
    "away_odds",

    "market_home_probability",
    "market_draw_probability",
    "market_away_probability",
    "market_prediction",

    "ai_home_probability",
    "ai_draw_probability",
    "ai_away_probability",
    "ai_prediction",

    "delta_home",
    "delta_draw",
    "delta_away",

    "strongest_disagreement_outcome",
    "strongest_disagreement_delta",
    "strongest_disagreement_absolute_delta",

    "challenger_home_probability",
    "challenger_draw_probability",
    "challenger_away_probability",
    "challenger_prediction",
    "challenger_adjustment_weight",
    "challenger_probability_source",

    "shadow_only",
    "generated_at_utc",
)


def hash_production_artifacts(
    root: Path = Path("."),
) -> dict[str, str]:
    """Hash every recognized production artifact that exists."""

    hashes = {}

    for name in PRODUCTION_ARTIFACTS:
        path = root / name

        if path.is_file():
            hashes[name] = hashlib.sha256(
                path.read_bytes()
            ).hexdigest()

    return hashes


def prepare_upcoming_matches(
    upcoming: pd.DataFrame,
    limit: int = 50,
    now=None,
    *,
    legacy_epl: bool = True,
) -> pd.DataFrame:
    """Prepare future upcoming fixtures only."""

    upcoming = require_league(
        upcoming,
        legacy_epl=legacy_epl,
    )

    required = {
        "match_datetime_uk",
        "home_team",
        "away_team",
    }

    missing = required.difference(
        upcoming.columns
    )

    if missing:
        raise ValueError(
            "Upcoming matches missing columns: "
            f"{sorted(missing)}"
        )

    prepared = (
        upcoming
        .head(limit)
        .copy()
    )

    prepared["commence_time_utc"] = pd.to_datetime(
        prepared["match_datetime_uk"],
        utc=True,
        errors="coerce",
    )

    if now is None:
        now = pd.Timestamp.now(tz="UTC")
    else:
        now = pd.Timestamp(now)

        if now.tzinfo is None:
            now = now.tz_localize("UTC")
        else:
            now = now.tz_convert("UTC")

    prepared = prepared.loc[
        prepared["commence_time_utc"].notna()
        & (prepared["commence_time_utc"] > now)
    ].copy()

    prepared["home_team_model"] = (
        prepared["home_team"]
        .map(normalize_team_name)
    )

    prepared["away_team_model"] = (
        prepared["away_team"]
        .map(normalize_team_name)
    )

    return prepared


def prepare_odds_snapshots(
    snapshots: pd.DataFrame,
    *,
    legacy_epl: bool = True,
) -> pd.DataFrame:
    """Normalize snapshot keys and discard unusable rows."""

    if snapshots.empty:
        snapshots = snapshots.copy()

        if "league" not in snapshots.columns:
            snapshots["league"] = pd.Series(
                dtype="object"
            )

        return pd.DataFrame(
            columns=(
                "league",
                *ODDS_COLUMNS,
                "home_team_model",
                "away_team_model",
            )
        )

    snapshots = normalize_snapshot_rows(
        snapshots,
        legacy_epl=legacy_epl,
    )

    missing = set(
        ODDS_COLUMNS
    ).difference(
        snapshots.columns
    )

    if missing:
        raise ValueError(
            "Odds snapshots missing columns: "
            f"{sorted(missing)}"
        )

    prepared = snapshots.loc[
        :,
        (
            "league",
            *ODDS_COLUMNS,
        ),
    ].copy()

    for column in (
        "snapshot_time_utc",
        "commence_time_utc",
    ):
        prepared[column] = pd.to_datetime(
            prepared[column],
            utc=True,
            errors="coerce",
        )

    for column in (
        "home_odds",
        "draw_odds",
        "away_odds",
    ):
        prepared[column] = pd.to_numeric(
            prepared[column],
            errors="coerce",
        )

    prepared["home_team_model"] = (
        prepared["home_team"]
        .map(normalize_team_name)
    )

    prepared["away_team_model"] = (
        prepared["away_team"]
        .map(normalize_team_name)
    )

    odds = prepared[
        [
            "home_odds",
            "draw_odds",
            "away_odds",
        ]
    ]

    valid_odds = (
        np.isfinite(odds).all(axis=1)
        & (odds > 1.0).all(axis=1)
    )

    return prepared.loc[
        prepared["snapshot_time_utc"].notna()
        & prepared["commence_time_utc"].notna()
        & valid_odds
    ].copy()


def select_latest_pre_kickoff_odds(
    snapshots: pd.DataFrame,
    *,
    legacy_epl: bool = True,
) -> pd.DataFrame:
    """
    Select the latest snapshot strictly before each fixture kickoff.

    Snapshot at kickoff or after kickoff is never eligible.
    """

    prepared = prepare_odds_snapshots(
        snapshots,
        legacy_epl=legacy_epl,
    )

    eligible = (
        prepared.loc[
            prepared["snapshot_time_utc"]
            < prepared["commence_time_utc"]
        ]
        .sort_values(
            "snapshot_time_utc",
            ascending=False,
        )
    )

    return eligible.drop_duplicates(
        [
            "league",
            "home_team_model",
            "away_team_model",
            "commence_time_utc",
        ],
        keep="first",
    )


def match_odds_to_upcoming(
    upcoming: pd.DataFrame,
    snapshots: pd.DataFrame,
    *,
    legacy_epl: bool = True,
) -> pd.DataFrame:
    """
    Left join point-in-time odds.

    No upcoming fixture is allowed to disappear because odds
    are unavailable.
    """

    prepared = prepare_upcoming_matches(
        upcoming,
        legacy_epl=legacy_epl,
    )

    latest = select_latest_pre_kickoff_odds(
        snapshots,
        legacy_epl=legacy_epl,
    )

    keys = [
        "league",
        "home_team_model",
        "away_team_model",
        "commence_time_utc",
    ]

    odds_values = latest[
        keys
        + [
            "snapshot_time_utc",
            "home_odds",
            "draw_odds",
            "away_odds",
        ]
    ]

    return prepared.merge(
        odds_values,
        on=keys,
        how="left",
        validate="many_to_one",
    )


def build_shadow_result_row(
    match: pd.Series,
    predictor,
) -> dict:
    """Build one stable shadow output row."""

    kickoff = match[
        "commence_time_utc"
    ]

    snapshot = match.get(
        "snapshot_time_utc"
    )

    row = {
        column: None
        for column
        in OUTPUT_COLUMNS
    }

    for column in (
        "league",
        "match_date",
        "match_time",
        "home_team",
        "away_team",
        "home_team_model",
        "away_team_model",
    ):
        row[column] = match.get(
            column
        )

    row["commence_time_utc"] = (
        kickoff.isoformat()
        if pd.notna(kickoff)
        else None
    )

    row["shadow_status"] = (
        "NO_MARKET_ODDS"
    )

    row["shadow_only"] = True

    if pd.isna(snapshot):
        return row

    row.update({
        "snapshot_time_utc":
            snapshot.isoformat(),

        "hours_before_kickoff":
            (
                kickoff - snapshot
            ).total_seconds()
            / 3600,

        "home_odds":
            float(
                match["home_odds"]
            ),

        "draw_odds":
            float(
                match["draw_odds"]
            ),

        "away_odds":
            float(
                match["away_odds"]
            ),
    })

    result = predictor(
        home_team=match["home_team"],
        away_team=match["away_team"],
        home_odds=row["home_odds"],
        draw_odds=row["draw_odds"],
        away_odds=row["away_odds"],
    )

    for prefix in (
        "market",
        "ai",
    ):
        values = result[
            prefix
        ]

        for outcome in (
            "home",
            "draw",
            "away",
        ):
            row[
                f"{prefix}_"
                f"{outcome}_probability"
            ] = float(
                values[
                    f"{outcome}_probability"
                ]
            )

        row[
            f"{prefix}_prediction"
        ] = values[
            "prediction"
        ]

    for outcome in (
        "home",
        "draw",
        "away",
    ):
        row[
            f"delta_{outcome}"
        ] = float(
            result[
                "delta"
            ][outcome]
        )

        row[
            f"challenger_"
            f"{outcome}_probability"
        ] = float(
            result[
                "challenger"
            ][
                f"{outcome}_probability"
            ]
        )

    disagreement = result[
        "strongest_disagreement"
    ]

    row.update({
        "strongest_disagreement_outcome":
            disagreement["outcome"],

        "strongest_disagreement_delta":
            float(
                disagreement["delta"]
            ),

        "strongest_disagreement_absolute_delta":
            float(
                disagreement[
                    "absolute_delta"
                ]
            ),

        "challenger_prediction":
            result[
                "challenger"
            ][
                "prediction"
            ],

        "challenger_adjustment_weight":
            float(
                result[
                    "challenger"
                ][
                    "adjustment_weight"
                ]
            ),

        "challenger_probability_source":
            result[
                "challenger"
            ][
                "probability_source"
            ],

        "shadow_only":
            bool(
                result[
                    "shadow_only"
                ]
            ),

        "shadow_status":
            "OK",
    })

    return row


def build_shadow_results(
    upcoming: pd.DataFrame,
    snapshots: pd.DataFrame,
    predictor,
    generated_at_utc=None,
    *,
    legacy_epl: bool = True,
) -> pd.DataFrame:
    """Build shadow rows for every selected upcoming fixture."""

    matched = match_odds_to_upcoming(
        upcoming,
        snapshots,
        legacy_epl=legacy_epl,
    )

    if generated_at_utc is None:
        generated_at_utc = pd.Timestamp.now(tz="UTC")
    else:
        generated_at_utc = pd.Timestamp(generated_at_utc)

        if generated_at_utc.tzinfo is None:
            generated_at_utc = generated_at_utc.tz_localize("UTC")
        else:
            generated_at_utc = generated_at_utc.tz_convert("UTC")

    rows = []

    for _, match in matched.iterrows():
        row = build_shadow_result_row(
            match,
            predictor,
        )

        row["generated_at_utc"] = generated_at_utc.isoformat()
        rows.append(row)

    return pd.DataFrame(
        rows,
        columns=OUTPUT_COLUMNS,
    )


def write_shadow_results(
    results: pd.DataFrame,
    output_path: Path = DEFAULT_OUTPUT_PATH,
) -> None:
    """Write only beneath repository experiments/."""

    root = Path.cwd().resolve()

    destination = (
        (root / output_path).resolve()
        if not output_path.is_absolute()
        else output_path.resolve()
    )

    experiments = (
        root
        / "experiments"
    ).resolve()

    if (
        destination.parent
        != experiments
        and experiments
        not in destination.parents
    ):
        raise ValueError(
            "Shadow output must be written "
            "under experiments/"
        )

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    results.to_csv(
        destination,
        index=False,
    )


def append_shadow_history(
    results: pd.DataFrame,
    history_path: Path = DEFAULT_HISTORY_PATH,
) -> None:
    """Append shadow rows to an experiments-only history file."""

    root = Path.cwd().resolve()

    destination = (
        (root / history_path).resolve()
        if not history_path.is_absolute()
        else history_path.resolve()
    )

    experiments = (root / "experiments").resolve()

    if (
        destination.parent != experiments
        and experiments not in destination.parents
    ):
        raise ValueError(
            "Shadow history must be written under experiments/"
        )

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if destination.exists():
        existing = pd.read_csv(
            destination
        )

        existing = load_legacy_epl_history(
            existing
        )

        combined = pd.concat(
            [
                existing,
                results,
            ],
            ignore_index=True,
        )
    else:
        combined = results.copy()

    combined.to_csv(
        destination,
        index=False,
    )


def fetch_odds_snapshots() -> pd.DataFrame:
    """
    Read existing Supabase snapshots only.

    database import is intentionally isolated so unit tests do not
    require live credentials.
    """

    from database import supabase

    response = (
        supabase
        .table(
            "odds_snapshots"
        )
        .select(
            ",".join(
                (
                    "league",
                    "event_id",
                    *ODDS_COLUMNS,
                )
            )
        )
        .order(
            "snapshot_time_utc",
            desc=True,
        )
        .limit(
            1000
        )
        .execute()
    )

    return pd.DataFrame(
        response.data or [],
        columns=(
            "league",
            "event_id",
            *ODDS_COLUMNS,
        ),
    )


def main() -> None:
    before = hash_production_artifacts()

    try:
        from predict_challenger import (
            predict_challenger,
        )

        upcoming = pd.read_csv(
            UPCOMING_PATH
        )

        upcoming = normalize_upcoming_fixtures(
            upcoming,
            source_path=UPCOMING_PATH,
        )

        snapshots = (
            fetch_odds_snapshots()
        )

        results = build_shadow_results(
            upcoming,
            snapshots,
            predict_challenger,
            legacy_epl=False,
        )

        write_shadow_results(
            results
        )

        append_shadow_history(
            results
        )

        ok = int(
            (
                results[
                    "shadow_status"
                ]
                == "OK"
            ).sum()
        )

        total = len(
            results
        )

        no_odds = (
            total
            - ok
        )

        coverage = (
            100.0
            * ok
            / total
            if total
            else 0.0
        )

        print(
            f"total matches: {total}"
        )

        print(
            f"OK: {ok}"
        )

        print(
            "NO_MARKET_ODDS: "
            f"{no_odds}"
        )

        print(
            "coverage percentage: "
            f"{coverage:.1f}%"
        )

        print(
            "output:",
            DEFAULT_OUTPUT_PATH,
        )

        print(
            "history:",
            DEFAULT_HISTORY_PATH,
        )

    finally:
        after = (
            hash_production_artifacts()
        )

        if after != before:
            raise RuntimeError(
                "Production artifact hashes "
                "changed during shadow generation"
            )


if __name__ == "__main__":
    main()
