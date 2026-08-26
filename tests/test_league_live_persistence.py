from __future__ import annotations

import pandas as pd
import pytest

import league_live_persistence as persistence
from league_runtime_config import (
    LA_LIGA_RUNTIME_CONFIG,
)


CONFIG = LA_LIGA_RUNTIME_CONFIG


def observation_frame():
    return pd.DataFrame(
        [
            {
                "league": CONFIG.identity.identifier,
                "event_id": "event-1",
                "snapshot_time_utc": "2026-08-26T10:00:00Z",
                "commence_time_utc": "2026-08-26T18:00:00Z",
                "market_argmax": "H",
                "shadow_argmax": "H",
                "pre_kickoff_valid": True,
                "research_only": True,
            }
        ]
    )


def result_frame():
    return pd.DataFrame(
        [
            {
                "league": CONFIG.identity.identifier,
                "season": "2026-2027",
                "match_date": "2026-08-26",
                "home_team": "Getafe",
                "away_team": "Sevilla",
                "home_goals": 2,
                "away_goals": 1,
                "result": "H",
            }
        ]
    )


def test_observation_key_is_deterministic_and_league_scoped():
    row = observation_frame().iloc[0].to_dict()

    first = persistence.observation_key(
        config=CONFIG,
        row=row,
    )

    second = persistence.observation_key(
        config=CONFIG,
        row=dict(row),
    )

    assert first == second

    assert first.startswith(
        CONFIG.identity.identifier + ":"
    )


def test_validate_observations_accepts_valid_row():
    result = persistence.validate_observations(
        observation_frame(),
        CONFIG,
    )

    assert len(result) == 1
    assert result["observation_key"].nunique() == 1


def test_validate_observations_rejects_post_kickoff():
    frame = observation_frame()

    frame.loc[
        0,
        "snapshot_time_utc",
    ] = "2026-08-26T19:00:00Z"

    with pytest.raises(
        ValueError,
        match="pre-kickoff",
    ):
        persistence.validate_observations(
            frame,
            CONFIG,
        )


def test_validate_observations_rejects_argmax_change():
    frame = observation_frame()
    frame.loc[0, "shadow_argmax"] = "A"

    with pytest.raises(
        ValueError,
        match="argmax",
    ):
        persistence.validate_observations(
            frame,
            CONFIG,
        )


def test_validate_observations_rejects_wrong_league():
    frame = observation_frame()
    frame.loc[0, "league"] = "EPL"

    with pytest.raises(
        ValueError,
        match="league mismatch",
    ):
        persistence.validate_observations(
            frame,
            CONFIG,
        )


def test_validate_results_accepts_finished_result():
    result = persistence.validate_results(
        result_frame(),
        CONFIG,
    )

    assert len(result) == 1
    assert result.iloc[0]["result"] == "H"


def test_validate_results_rejects_score_result_conflict():
    frame = result_frame()
    frame.loc[0, "result"] = "A"

    with pytest.raises(
        ValueError,
        match="disagrees",
    ):
        persistence.validate_results(
            frame,
            CONFIG,
        )


def test_validate_results_rejects_duplicate_fixture():
    frame = pd.concat(
        [
            result_frame(),
            result_frame(),
        ],
        ignore_index=True,
    )

    with pytest.raises(
        ValueError,
        match="Duplicate",
    ):
        persistence.validate_results(
            frame,
            CONFIG,
        )


def test_result_identity_is_league_scoped():
    assert persistence.result_identity_columns() == (
        "league",
        "season",
        "match_date",
        "home_team",
        "away_team",
    )


def test_immutable_payload_comparison_is_order_independent():
    assert persistence.immutable_payload_equal(
        {
            "a": 1,
            "b": 2,
        },
        {
            "b": 2,
            "a": 1,
        },
    )


def test_generic_module_does_not_import_la_liga_persistence():
    source = open(
        "league_live_persistence.py",
        encoding="utf-8",
    ).read()

    assert "la_liga_live_persistence" not in source

def test_same_event_and_snapshot_with_changed_prediction_state_is_new_observation():
    first = observation_frame()

    first[
        "home_team"
    ] = "Barcelona"

    first[
        "away_team"
    ] = "Valencia"

    first[
        "market_home_probability"
    ] = 0.60

    first[
        "market_draw_probability"
    ] = 0.24

    first[
        "market_away_probability"
    ] = 0.16

    first[
        "shadow_home_probability"
    ] = 0.62

    first[
        "shadow_draw_probability"
    ] = 0.23

    first[
        "shadow_away_probability"
    ] = 0.15

    first[
        "prediction_source"
    ] = "STRUCTURAL_EDGE_V2_SHADOW"

    second = first.copy()

    second[
        "shadow_home_probability"
    ] = 0.63

    second[
        "shadow_draw_probability"
    ] = 0.22

    first_valid = (
        persistence.validate_observations(
            first,
            CONFIG,
        )
    )

    second_valid = (
        persistence.validate_observations(
            second,
            CONFIG,
        )
    )

    assert (
        first_valid.iloc[0][
            "event_id"
        ]
        ==
        second_valid.iloc[0][
            "event_id"
        ]
    )

    assert (
        first_valid.iloc[0][
            "snapshot_time_utc"
        ]
        ==
        second_valid.iloc[0][
            "snapshot_time_utc"
        ]
    )

    assert (
        first_valid.iloc[0][
            "observation_key"
        ]
        !=
        second_valid.iloc[0][
            "observation_key"
        ]
    )


def test_exact_prediction_state_replay_keeps_same_observation_key():
    frame = observation_frame()

    frame[
        "home_team"
    ] = "Barcelona"

    frame[
        "away_team"
    ] = "Valencia"

    frame[
        "market_home_probability"
    ] = 0.60

    frame[
        "market_draw_probability"
    ] = 0.24

    frame[
        "market_away_probability"
    ] = 0.16

    frame[
        "shadow_home_probability"
    ] = 0.62

    frame[
        "shadow_draw_probability"
    ] = 0.23

    frame[
        "shadow_away_probability"
    ] = 0.15

    frame[
        "prediction_source"
    ] = "STRUCTURAL_EDGE_V2_SHADOW"

    first = (
        persistence.validate_observations(
            frame,
            CONFIG,
        )
    )

    second = (
        persistence.validate_observations(
            frame.copy(),
            CONFIG,
        )
    )

    assert (
        first.iloc[0][
            "observation_key"
        ]
        ==
        second.iloc[0][
            "observation_key"
        ]
    )
