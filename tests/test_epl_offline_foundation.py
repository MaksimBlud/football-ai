from dataclasses import FrozenInstanceError

import pandas as pd
import pytest

from league_offline_features import (
    build_temporal_elo_features,
)

from league_offline_history import (
    load_configured_history,
    normalize_team,
    parse_football_data_date,
)

from league_runtime_config import (
    EPL_RUNTIME_CONFIG,
)


CONFIG = EPL_RUNTIME_CONFIG


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (
            "Manchester City",
            "Man City",
        ),
        (
            "Manchester United",
            "Man United",
        ),
        (
            "Newcastle United",
            "Newcastle",
        ),
        (
            "Tottenham Hotspur",
            "Tottenham",
        ),
        (
            "Brighton and Hove Albion",
            "Brighton",
        ),
        (
            "Brighton & Hove Albion",
            "Brighton",
        ),
        (
            "Nottingham Forest",
            "Nott'm Forest",
        ),
        (
            "Ipswich Town",
            "Ipswich",
        ),
        (
            "Leeds United",
            "Leeds",
        ),
        (
            "Hull City",
            "Hull",
        ),
        (
            "AFC Bournemouth",
            "Bournemouth",
        ),
    ],
)
def test_epl_aliases(
    source,
    expected,
):
    assert (
        normalize_team(
            source,
            CONFIG,
        )
        == expected
    )


def test_unknown_nonempty_team_is_not_guessed():
    assert (
        normalize_team(
            "Example FC",
            CONFIG,
        )
        == "Example FC"
    )


def test_empty_team_rejected():
    with pytest.raises(
        ValueError,
    ):
        normalize_team(
            "",
            CONFIG,
        )


def test_epl_runtime_contract():
    CONFIG.validate()

    assert (
        CONFIG.identity.identifier
        == "EPL"
    )

    assert (
        CONFIG.identity.timezone
        == "Europe/London"
    )

    assert (
        CONFIG.identity.odds_sport_key
        == "soccer_epl"
    )

    assert (
        CONFIG
        .historical_source
        .competition_code
        == "E0"
    )

    assert (
        CONFIG
        .finished_results_source
        .competition_code
        == "PL"
    )

    assert (
        CONFIG
        .structural_v2
        .calibration_status
        == "CALIBRATION_REQUIRED"
    )

    assert (
        CONFIG
        .structural_v2
        .structural_alpha
        is None
    )

    assert (
        CONFIG
        .structural_v2
        .edge_threshold
        is None
    )


def test_runtime_is_frozen():
    with pytest.raises(
        FrozenInstanceError,
    ):
        CONFIG.identity.identifier = (
            "OTHER"
        )


def test_explicit_date_parsing():
    series = pd.Series(
        [
            "13/08/2016",
            "13/08/16",
        ]
    )

    parsed = (
        parse_football_data_date(
            series
        )
    )

    assert (
        parsed.dt.strftime(
            "%Y-%m-%d"
        ).tolist()
        ==
        [
            "2016-08-13",
            "2016-08-13",
        ]
    )


def test_all_ten_real_seasons_normalize():
    frame = load_configured_history(
        config=CONFIG,
        raw_directory=(
            CONFIG.paths.historical_raw
            .parent
            / "raw"
        ),
        file_prefix="epl",
        require_complete=True,
    )

    assert len(frame) == 3800

    assert (
        frame[
            "season"
        ].nunique()
        == 10
    )

    counts = (
        frame
        .groupby(
            "season"
        )
        .size()
    )

    assert (
        counts
        == 380
    ).all()

    assert not frame.duplicated(
        subset=[
            "league",
            "season",
            "match_date",
            "home_team",
            "away_team",
        ]
    ).any()

    assert frame[
        "match_date"
    ].is_monotonic_increasing


def test_temporal_elo_is_pre_match():
    historical = pd.DataFrame(
        [
            {
                "league": "EPL",
                "season": "2026-2027",
                "match_date":
                    pd.Timestamp(
                        "2026-08-01"
                    ),
                "home_team": "Arsenal",
                "away_team": "Chelsea",
                "home_goals": 1,
                "away_goals": 0,
                "result": "H",
            },
            {
                "league": "EPL",
                "season": "2026-2027",
                "match_date":
                    pd.Timestamp(
                        "2026-08-08"
                    ),
                "home_team": "Chelsea",
                "away_team": "Arsenal",
                "home_goals": 0,
                "away_goals": 0,
                "result": "D",
            },
        ]
    )

    features = (
        build_temporal_elo_features(
            historical,
            CONFIG,
        )
    )

    assert (
        features.iloc[0][
            "home_prior_matches"
        ]
        == 0
    )

    assert (
        features.iloc[0][
            "away_prior_matches"
        ]
        == 0
    )

    assert (
        features.iloc[0][
            "home_elo"
        ]
        == CONFIG.elo.initial_rating
    )

    assert (
        features.iloc[1][
            "home_prior_matches"
        ]
        == 1
    )

    assert (
        features.iloc[1][
            "away_prior_matches"
        ]
        == 1
    )


def test_epl_paths_are_isolated_from_la_liga():
    for path in (
        CONFIG.paths.historical_normalized,
        CONFIG.paths.temporal_features,
        CONFIG.paths.trainable_features,
        CONFIG.paths.upcoming_fixtures,
        CONFIG.paths.market_shadow,
        CONFIG.paths.market_history,
        CONFIG.paths.structural_shadow,
        CONFIG.paths.structural_history,
        CONFIG.paths.current_results,
    ):
        assert "la_liga" not in str(
            path
        ).lower()


def test_structural_features_are_strictly_pre_match():
    historical = pd.DataFrame(
        [
            {
                "league": "EPL",
                "season": "2026-2027",
                "match_date":
                    pd.Timestamp(
                        "2026-08-01"
                    ),
                "home_team": "Arsenal",
                "away_team": "Chelsea",
                "home_goals": 5,
                "away_goals": 0,
                "result": "H",
            },
            {
                "league": "EPL",
                "season": "2026-2027",
                "match_date":
                    pd.Timestamp(
                        "2026-08-08"
                    ),
                "home_team": "Chelsea",
                "away_team": "Arsenal",
                "home_goals": 0,
                "away_goals": 1,
                "result": "A",
            },
        ]
    )

    features = build_temporal_elo_features(
        historical,
        CONFIG,
    )

    first = features.iloc[0]
    second = features.iloc[1]

    # First match cannot contain its own 5-0 result.
    assert (
        first[
            "home_goals_scored_last5"
        ]
        == 0.0
    )

    assert (
        first[
            "away_goals_conceded_last5"
        ]
        == 0.0
    )

    # Second match sees ONLY the previous match.
    assert (
        second[
            "home_goals_scored_last5"
        ]
        == 0.0
    )

    assert (
        second[
            "home_goals_conceded_last5"
        ]
        == 5.0
    )

    assert (
        second[
            "away_goals_scored_last5"
        ]
        == 5.0
    )

    assert (
        second[
            "away_goals_conceded_last5"
        ]
        == 0.0
    )


def test_form_difference_uses_previous_last_five_points():
    historical = pd.DataFrame(
        [
            {
                "league": "EPL",
                "season": "2026-2027",
                "match_date":
                    pd.Timestamp(
                        "2026-08-01"
                    ),
                "home_team": "Arsenal",
                "away_team": "Chelsea",
                "home_goals": 1,
                "away_goals": 0,
                "result": "H",
            },
            {
                "league": "EPL",
                "season": "2026-2027",
                "match_date":
                    pd.Timestamp(
                        "2026-08-08"
                    ),
                "home_team": "Chelsea",
                "away_team": "Arsenal",
                "home_goals": 0,
                "away_goals": 0,
                "result": "D",
            },
        ]
    )

    features = build_temporal_elo_features(
        historical,
        CONFIG,
    )

    second = features.iloc[1]

    # Chelsea had 0 points; Arsenal had 3.
    assert (
        second[
            "home_last5_points"
        ]
        == 0
    )

    assert (
        second[
            "away_last5_points"
        ]
        == 3
    )

    assert (
        second[
            "form_difference"
        ]
        == -3
    )


def test_venue_win_rate_difference_is_pre_match():
    historical = pd.DataFrame(
        [
            {
                "league": "EPL",
                "season": "2026-2027",
                "match_date":
                    pd.Timestamp(
                        "2026-08-01"
                    ),
                "home_team": "Arsenal",
                "away_team": "Chelsea",
                "home_goals": 1,
                "away_goals": 0,
                "result": "H",
            },
            {
                "league": "EPL",
                "season": "2026-2027",
                "match_date":
                    pd.Timestamp(
                        "2026-08-08"
                    ),
                "home_team": "Arsenal",
                "away_team": "Liverpool",
                "home_goals": 0,
                "away_goals": 1,
                "result": "A",
            },
            {
                "league": "EPL",
                "season": "2026-2027",
                "match_date":
                    pd.Timestamp(
                        "2026-08-15"
                    ),
                "home_team": "Arsenal",
                "away_team": "Chelsea",
                "home_goals": 0,
                "away_goals": 0,
                "result": "D",
            },
        ]
    )

    features = build_temporal_elo_features(
        historical,
        CONFIG,
    )

    third = features.iloc[2]

    # Arsenal prior HOME record = 1 win / 2.
    assert abs(
        third[
            "home_venue_win_rate"
        ]
        - 0.5
    ) < 1e-12

    # Chelsea prior AWAY record = 0 wins / 1.
    assert (
        third[
            "away_venue_win_rate"
        ]
        == 0.0
    )

    assert abs(
        third[
            "venue_win_rate_difference"
        ]
        - 0.5
    ) < 1e-12


def test_structural_elo_difference_includes_home_advantage():
    historical = pd.DataFrame(
        [
            {
                "league": "EPL",
                "season": "2026-2027",
                "match_date":
                    pd.Timestamp(
                        "2026-08-01"
                    ),
                "home_team": "Arsenal",
                "away_team": "Chelsea",
                "home_goals": 0,
                "away_goals": 0,
                "result": "D",
            },
        ]
    )

    features = build_temporal_elo_features(
        historical,
        CONFIG,
    )

    first = features.iloc[0]

    assert (
        first[
            "elo_diff"
        ]
        == 0.0
    )

    assert (
        first[
            "elo_difference"
        ]
        ==
        CONFIG.elo.home_advantage
    )
