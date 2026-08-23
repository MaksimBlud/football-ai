"""Frozen La Liga Structural Edge V2 live shadow.

Research-only.

Inputs:
- historical normalized La Liga results;
- optional finished 2026-2027 results;
- latest La Liga market shadow.

For every upcoming fixture:
- reconstruct pre-match form / venue / Elo state;
- fit Structural Edge V2 normalization using historical trainable data only;
- apply the frozen V2 correction;
- preserve market argmax exactly;
- cold-start / insufficient-history teams remain MARKET ONLY.

No production artifact.
No model promotion.
No Supabase write.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

import league_structural_edge_v2 as v2
from add_la_liga_elo_features import (
    HOME_ADVANTAGE,
    INITIAL_ELO,
    K_FACTOR,
    actual_scores,
    expected_score,
)


ROOT = Path(__file__).resolve().parent

HISTORY_PATH = (
    ROOT
    / "data"
    / "la_liga_official_history_2016_2026_normalized.csv"
)

CURRENT_RESULTS_PATH = (
    ROOT
    / "data"
    / "la_liga_2026_2027_results.csv"
)

TRAINABLE_PATH = (
    ROOT
    / "data"
    / "la_liga_features_with_elo_trainable.csv"
)

MARKET_PATH = (
    ROOT
    / "experiments"
    / "la_liga_market_shadow.csv"
)

OUTPUT_PATH = (
    ROOT
    / "experiments"
    / "la_liga_structural_v2_shadow.csv"
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

MIN_PRIOR_MATCHES = 5
PREDICTION_SOURCE = "STRUCTURAL_EDGE_V2_SHADOW"


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


def normalize_finished_matches(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    result = frame.copy()

    required = {
        "match_date",
        "home_team",
        "away_team",
        "home_goals",
        "away_goals",
        "result",
    }

    missing = (
        required
        - set(result.columns)
    )

    if missing:
        raise ValueError(
            "Finished match input missing: "
            + ", ".join(
                sorted(missing)
            )
        )

    if (
        "match_time"
        not in result.columns
    ):
        result[
            "match_time"
        ] = "00:00"

    result["match_date"] = (
        pd.to_datetime(
            result["match_date"],
            errors="raise",
        )
    )

    result["home_goals"] = (
        pd.to_numeric(
            result["home_goals"],
            errors="raise",
        )
    )

    result["away_goals"] = (
        pd.to_numeric(
            result["away_goals"],
            errors="raise",
        )
    )

    result["result"] = (
        result["result"]
        .astype(str)
        .str.upper()
    )

    result = result[
        result["result"]
        .isin(
            ["H", "D", "A"]
        )
    ].copy()

    return (
        result
        .sort_values(
            [
                "match_date",
                "match_time",
                "home_team",
                "away_team",
            ]
        )
        .reset_index(drop=True)
    )


def load_finished_history(
    history_path: Path,
    current_results_path: Path,
) -> pd.DataFrame:
    historical = (
        normalize_finished_matches(
            pd.read_csv(
                history_path
            )
        )
    )

    frames = [
        historical
    ]

    if (
        current_results_path.exists()
        and current_results_path.stat().st_size
        > 0
    ):
        current = (
            normalize_finished_matches(
                pd.read_csv(
                    current_results_path
                )
            )
        )

        frames.append(
            current
        )

    combined = pd.concat(
        frames,
        ignore_index=True,
    )

    combined = (
        combined
        .drop_duplicates(
            subset=[
                "match_date",
                "home_team",
                "away_team",
            ],
            keep="last",
        )
        .sort_values(
            [
                "match_date",
                "match_time",
                "home_team",
                "away_team",
            ]
        )
        .reset_index(drop=True)
    )

    return combined


def points(
    result: str,
    *,
    home: bool,
) -> int:
    if result == "D":
        return 1

    if home:
        return (
            3
            if result == "H"
            else 0
        )

    return (
        3
        if result == "A"
        else 0
    )


def build_state(
    history: pd.DataFrame,
) -> dict:
    team_matches: dict[
        str,
        list[dict],
    ] = {}

    home_venue: dict[
        str,
        list[dict],
    ] = {}

    away_venue: dict[
        str,
        list[dict],
    ] = {}

    ratings: dict[
        str,
        float,
    ] = {}

    for _, row in (
        history.iterrows()
    ):
        home = str(
            row["home_team"]
        )

        away = str(
            row["away_team"]
        )

        result = str(
            row["result"]
        )

        home_goals = float(
            row["home_goals"]
        )

        away_goals = float(
            row["away_goals"]
        )

        home_record = {
            "points":
                points(
                    result,
                    home=True,
                ),
            "goals_scored":
                home_goals,
            "goals_conceded":
                away_goals,
            "win":
                1.0
                if result == "H"
                else 0.0,
        }

        away_record = {
            "points":
                points(
                    result,
                    home=False,
                ),
            "goals_scored":
                away_goals,
            "goals_conceded":
                home_goals,
            "win":
                1.0
                if result == "A"
                else 0.0,
        }

        team_matches.setdefault(
            home,
            [],
        ).append(
            home_record
        )

        team_matches.setdefault(
            away,
            [],
        ).append(
            away_record
        )

        home_venue.setdefault(
            home,
            [],
        ).append(
            home_record
        )

        away_venue.setdefault(
            away,
            [],
        ).append(
            away_record
        )

        home_rating = (
            ratings.get(
                home,
                INITIAL_ELO,
            )
        )

        away_rating = (
            ratings.get(
                away,
                INITIAL_ELO,
            )
        )

        expected_home = (
            expected_score(
                home_rating
                + HOME_ADVANTAGE,
                away_rating,
            )
        )

        expected_away = (
            1.0
            - expected_home
        )

        actual_home, actual_away = (
            actual_scores(
                result
            )
        )

        ratings[home] = (
            home_rating
            + K_FACTOR
            * (
                actual_home
                - expected_home
            )
        )

        ratings[away] = (
            away_rating
            + K_FACTOR
            * (
                actual_away
                - expected_away
            )
        )

    return {
        "team_matches":
            team_matches,
        "home_venue":
            home_venue,
        "away_venue":
            away_venue,
        "ratings":
            ratings,
    }


def mean(
    values,
) -> float:
    values = list(
        values
    )

    if not values:
        return 0.0

    return float(
        np.mean(values)
    )


def fixture_features(
    home: str,
    away: str,
    state: dict,
) -> dict:
    team_matches = (
        state["team_matches"]
    )

    home_history = (
        team_matches.get(
            home,
            [],
        )
    )

    away_history = (
        team_matches.get(
            away,
            [],
        )
    )

    home_last5 = (
        home_history[-5:]
    )

    away_last5 = (
        away_history[-5:]
    )

    home_venue = (
        state[
            "home_venue"
        ].get(
            home,
            [],
        )
    )

    away_venue = (
        state[
            "away_venue"
        ].get(
            away,
            [],
        )
    )

    home_last5_points = sum(
        item["points"]
        for item in home_last5
    )

    away_last5_points = sum(
        item["points"]
        for item in away_last5
    )

    home_venue_win_rate = (
        mean(
            item["win"]
            for item
            in home_venue
        )
    )

    away_venue_win_rate = (
        mean(
            item["win"]
            for item
            in away_venue
        )
    )

    home_elo = (
        state["ratings"].get(
            home,
            INITIAL_ELO,
        )
    )

    away_elo = (
        state["ratings"].get(
            away,
            INITIAL_ELO,
        )
    )

    structural_ready = (
        len(home_history)
        >= MIN_PRIOR_MATCHES
        and len(away_history)
        >= MIN_PRIOR_MATCHES
    )

    return {
        "home_prior_matches":
            len(home_history),

        "away_prior_matches":
            len(away_history),

        "structural_ready":
            structural_ready,

        "home_last5_points":
            home_last5_points,

        "away_last5_points":
            away_last5_points,

        "form_difference":
            (
                home_last5_points
                - away_last5_points
            ),

        "home_goals_scored_last5":
            mean(
                item[
                    "goals_scored"
                ]
                for item
                in home_last5
            ),

        "away_goals_scored_last5":
            mean(
                item[
                    "goals_scored"
                ]
                for item
                in away_last5
            ),

        "home_goals_conceded_last5":
            mean(
                item[
                    "goals_conceded"
                ]
                for item
                in home_last5
            ),

        "away_goals_conceded_last5":
            mean(
                item[
                    "goals_conceded"
                ]
                for item
                in away_last5
            ),

        "home_venue_win_rate":
            home_venue_win_rate,

        "away_venue_win_rate":
            away_venue_win_rate,

        "venue_win_rate_difference":
            (
                home_venue_win_rate
                - away_venue_win_rate
            ),

        "home_elo":
            home_elo,

        "away_elo":
            away_elo,

        "elo_difference":
            (
                home_elo
                - away_elo
            ),
    }


def build_shadow(
    market: pd.DataFrame,
    history: pd.DataFrame,
    training: pd.DataFrame,
) -> pd.DataFrame:
    required_market = {
        "league",
        "event_id",
        "commence_time_utc",
        "home_team",
        "away_team",
        "market_home_probability",
        "market_draw_probability",
        "market_away_probability",
        "market_argmax",
        "market_shadow_status",
    }

    missing = (
        required_market
        - set(market.columns)
    )

    if missing:
        raise ValueError(
            "Market shadow missing: "
            + ", ".join(
                sorted(missing)
            )
        )

    stats = v2.fit_stats(
        training
    )

    state = build_state(
        history
    )

    rows = []

    for _, row in (
        market.iterrows()
    ):
        if (
            str(
                row[
                    "market_shadow_status"
                ]
            )
            != "OK"
        ):
            continue

        home = str(
            row["home_team"]
        )

        away = str(
            row["away_team"]
        )

        features = (
            fixture_features(
                home,
                away,
                state,
            )
        )

        market_probability = (
            np.array(
                [[
                    float(
                        row[
                            "market_home_probability"
                        ]
                    ),
                    float(
                        row[
                            "market_draw_probability"
                        ]
                    ),
                    float(
                        row[
                            "market_away_probability"
                        ]
                    ),
                ]],
                dtype=float,
            )
        )

        market_probability = (
            market_probability
            / market_probability.sum(
                axis=1,
                keepdims=True,
            )
        )

        if (
            features[
                "structural_ready"
            ]
        ):
            feature_frame = (
                pd.DataFrame(
                    [features]
                )
            )

            score = float(
                v2.structural_score(
                    feature_frame,
                    stats,
                ).iloc[0]
            )

            corrected, enabled, weights = (
                v2.apply_correction(
                    market_probability,
                    np.array(
                        [score]
                    ),
                )
            )

            correction_enabled = bool(
                enabled[0]
            )

            realized_weight = float(
                weights[0]
            )

        else:
            score = float("nan")

            corrected = (
                market_probability.copy()
            )

            correction_enabled = False

            realized_weight = 0.0

        market_argmax = int(
            np.argmax(
                market_probability[0]
            )
        )

        shadow_argmax = int(
            np.argmax(
                corrected[0]
            )
        )

        if (
            market_argmax
            != shadow_argmax
        ):
            raise RuntimeError(
                "V2 shadow changed market argmax "
                f"for {home} - {away}"
            )

        labels = (
            "H",
            "D",
            "A",
        )

        rows.append({
            "league":
                row["league"],

            "event_id":
                row["event_id"],

            "commence_time_utc":
                row[
                    "commence_time_utc"
                ],

            "home_team":
                home,

            "away_team":
                away,

            "home_prior_matches":
                features[
                    "home_prior_matches"
                ],

            "away_prior_matches":
                features[
                    "away_prior_matches"
                ],

            "structural_ready":
                features[
                    "structural_ready"
                ],

            "structural_score":
                score,

            "correction_enabled":
                correction_enabled,

            "realized_correction_weight":
                realized_weight,

            "market_home_probability":
                market_probability[
                    0,
                    0,
                ],

            "market_draw_probability":
                market_probability[
                    0,
                    1,
                ],

            "market_away_probability":
                market_probability[
                    0,
                    2,
                ],

            "shadow_home_probability":
                corrected[
                    0,
                    0,
                ],

            "shadow_draw_probability":
                corrected[
                    0,
                    1,
                ],

            "shadow_away_probability":
                corrected[
                    0,
                    2,
                ],

            "market_argmax":
                labels[
                    market_argmax
                ],

            "shadow_argmax":
                labels[
                    shadow_argmax
                ],

            "prediction_source":
                PREDICTION_SOURCE,

            "research_only":
                True,
        })

    result = pd.DataFrame(
        rows
    )

    if not result.empty:
        result = (
            result
            .sort_values(
                [
                    "commence_time_utc",
                    "home_team",
                ]
            )
            .reset_index(drop=True)
        )

    return result


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--history",
        type=Path,
        default=HISTORY_PATH,
    )

    parser.add_argument(
        "--current-results",
        type=Path,
        default=CURRENT_RESULTS_PATH,
    )

    parser.add_argument(
        "--market",
        type=Path,
        default=MARKET_PATH,
    )

    parser.add_argument(
        "--training",
        type=Path,
        default=TRAINABLE_PATH,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_PATH,
    )

    args = parser.parse_args()

    before = production_state()

    history = load_finished_history(
        args.history,
        args.current_results,
    )

    market = pd.read_csv(
        args.market
    )

    training = pd.read_csv(
        args.training
    )

    shadow = build_shadow(
        market,
        history,
        training,
    )

    output = args.output.resolve()

    experiments = (
        ROOT
        / "experiments"
    ).resolve()

    if experiments not in (
        output.parents
    ):
        raise ValueError(
            "Shadow output must stay "
            "under experiments/"
        )

    args.output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    shadow.to_csv(
        args.output,
        index=False,
    )

    after = production_state()

    if before != after:
        raise RuntimeError(
            "Production artifact changed"
        )

    print("=" * 72)
    print("LA LIGA STRUCTURAL EDGE V2 SHADOW")
    print("=" * 72)

    print(
        "finished history rows:",
        len(history),
    )

    print(
        "shadow fixtures:",
        len(shadow),
    )

    if not shadow.empty:
        print(
            "structural ready:",
            int(
                shadow[
                    "structural_ready"
                ].sum()
            ),
        )

        print(
            "correction enabled:",
            int(
                shadow[
                    "correction_enabled"
                ].sum()
            ),
        )

        print(
            "argmax changes:",
            int(
                (
                    shadow[
                        "market_argmax"
                    ]
                    != shadow[
                        "shadow_argmax"
                    ]
                ).sum()
            ),
        )

        print()
        print(
            shadow[
                [
                    "home_team",
                    "away_team",
                    "structural_ready",
                    "structural_score",
                    "correction_enabled",
                    "market_argmax",
                    "shadow_argmax",
                    "market_home_probability",
                    "shadow_home_probability",
                    "market_draw_probability",
                    "shadow_draw_probability",
                    "market_away_probability",
                    "shadow_away_probability",
                ]
            ].to_string(
                index=False
            )
        )

    print()
    print(
        "prediction source:",
        PREDICTION_SOURCE,
    )

    print(
        "production unchanged:",
        True,
    )

    print(
        "output:",
        args.output,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
