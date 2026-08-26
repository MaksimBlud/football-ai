from dataclasses import replace
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import pytest

from league_fixture_export import (
    prepare_upcoming_fixtures,
)
from league_market_shadow import (
    normalized_market_probabilities,
    prepare_snapshots,
    probability_argmax,
)
from league_runtime_config import (
    LA_LIGA_RUNTIME_CONFIG,
)


def normalize_identity(
    value,
):
    return str(
        value
    )


def fixture_rows():
    return pd.DataFrame(
        [
            {
                "league": "LA_LIGA",
                "event_id": "event-1",
                "snapshot_time_utc":
                    "2026-08-25T10:00:00Z",
                "commence_time_utc":
                    "2026-08-26T20:00:00Z",
                "home_team":
                    "Barcelona",
                "away_team":
                    "Valencia",
            },
            {
                "league": "LA_LIGA",
                "event_id": "event-1",
                "snapshot_time_utc":
                    "2026-08-25T12:00:00Z",
                "commence_time_utc":
                    "2026-08-26T20:00:00Z",
                "home_team":
                    "Barcelona",
                "away_team":
                    "Valencia",
            },
        ]
    )


def market_rows():
    return pd.DataFrame(
        [
            {
                "league":
                    "LA_LIGA",
                "event_id":
                    "event-1",
                "snapshot_time_utc":
                    "2026-08-25T10:00:00Z",
                "commence_time_utc":
                    "2026-08-26T20:00:00Z",
                "home_team":
                    "Barcelona",
                "away_team":
                    "Valencia",
                "home_odds":
                    1.80,
                "draw_odds":
                    3.80,
                "away_odds":
                    4.50,
            },
        ]
    )


def test_la_liga_runtime_config_is_frozen_and_valid():
    config = (
        LA_LIGA_RUNTIME_CONFIG
    )

    config.validate()

    assert (
        config.identity.identifier
        == "LA_LIGA"
    )

    assert (
        config.identity.timezone
        == "Europe/Madrid"
    )

    assert (
        config.identity.odds_sport_key
        == "soccer_spain_la_liga"
    )

    assert (
        config.elo.initial_rating
        == 1500.0
    )

    assert (
        config.elo.k_factor
        == 20.0
    )

    assert (
        config.elo.home_advantage
        == 65.0
    )

    assert (
        config.structural_v2.structural_alpha
        == 0.10
    )

    assert (
        config.structural_v2.edge_threshold
        == 0.75
    )

    assert (
        config.structural_v2.min_prior_matches
        == 5
    )


def test_structural_calibration_cannot_attach_to_other_league():
    config = (
        LA_LIGA_RUNTIME_CONFIG
    )

    bad_structural = replace(
        config.structural_v2,
        league_id="TEST_OTHER",
    )

    bad_config = replace(
        config,
        structural_v2=bad_structural,
    )

    with pytest.raises(
        ValueError,
        match="calibration league mismatch",
    ):
        bad_config.validate()


def test_fixture_projection_keeps_latest_future_snapshot():
    result = (
        prepare_upcoming_fixtures(
            fixture_rows(),
            LA_LIGA_RUNTIME_CONFIG,
            normalize_team=(
                normalize_identity
            ),
            now=datetime(
                2026,
                8,
                25,
                9,
                0,
                tzinfo=timezone.utc,
            ),
        )
    )

    assert len(result) == 1

    row = result.iloc[0]

    assert (
        row["league"]
        == "LA_LIGA"
    )

    assert (
        row["event_id"]
        == "event-1"
    )

    assert (
        row["home_team_model"]
        == "Barcelona"
    )

    assert (
        row["away_team_model"]
        == "Valencia"
    )


def test_fixture_projection_rejects_cross_league_input():
    frame = fixture_rows()

    frame.loc[
        1,
        "league",
    ] = "TEST_OTHER"

    with pytest.raises(
        ValueError,
        match="Mixed/non-target",
    ):
        prepare_upcoming_fixtures(
            frame,
            LA_LIGA_RUNTIME_CONFIG,
            normalize_team=(
                normalize_identity
            ),
            now=datetime(
                2026,
                8,
                25,
                9,
                0,
                tzinfo=timezone.utc,
            ),
        )


def test_market_probabilities_are_normalized():
    probability = (
        normalized_market_probabilities(
            1.80,
            3.80,
            4.50,
        )
    )

    assert all(
        np.isfinite(
            probability
        )
    )

    assert all(
        value > 0
        for value in probability
    )

    assert sum(
        probability
    ) == pytest.approx(
        1.0,
        abs=1e-12,
    )

    assert (
        probability_argmax(
            *probability
        )
        == "H"
    )


def test_market_snapshot_contract_is_pre_kickoff():
    frame = market_rows()

    frame.loc[
        len(frame)
    ] = {
        **frame.iloc[
            0
        ].to_dict(),
        "snapshot_time_utc":
            "2026-08-26T21:00:00Z",
    }

    result = (
        prepare_snapshots(
            frame,
            LA_LIGA_RUNTIME_CONFIG,
        )
    )

    assert len(result) == 1

    assert (
        result[
            "snapshot_time_utc"
        ]
        <
        result[
            "commence_time_utc"
        ]
    ).all()


def test_market_snapshot_rejects_other_league():
    frame = market_rows()

    frame.loc[
        0,
        "league",
    ] = "TEST_OTHER"

    with pytest.raises(
        ValueError,
        match="Mixed/non-target",
    ):
        prepare_snapshots(
            frame,
            LA_LIGA_RUNTIME_CONFIG,
        )


def test_runtime_alias_contract_preserves_current_rayo_mapping():
    assert (
        LA_LIGA_RUNTIME_CONFIG
        .aliases[
            "Rayo Vallecano"
        ]
        == "Vallecano"
    )


def test_structural_ready_respects_league_minimum_history():
    from league_structural_v2_shadow import (
        structural_ready,
    )

    assert structural_ready(
        home_prior_matches=5,
        away_prior_matches=5,
        config=LA_LIGA_RUNTIME_CONFIG,
    )

    assert not structural_ready(
        home_prior_matches=4,
        away_prior_matches=5,
        config=LA_LIGA_RUNTIME_CONFIG,
    )


def test_observation_history_rejects_post_kickoff_and_cross_league():
    from league_structural_v2_history import (
        prepare_observations,
    )

    base = {
        "league":
            "LA_LIGA",
        "event_id":
            "event-1",
        "commence_time_utc":
            "2026-08-26T20:00:00Z",
        "snapshot_time_utc":
            "2026-08-26T19:00:00Z",
        "home_team":
            "Barcelona",
        "away_team":
            "Valencia",
        "market_home_probability":
            0.60,
        "market_draw_probability":
            0.24,
        "market_away_probability":
            0.16,
        "shadow_home_probability":
            0.62,
        "shadow_draw_probability":
            0.23,
        "shadow_away_probability":
            0.15,
        "market_argmax":
            "H",
        "shadow_argmax":
            "H",
        "prediction_source":
            "STRUCTURAL_EDGE_V2_SHADOW",
    }

    valid = pd.DataFrame(
        [base]
    )

    result = (
        prepare_observations(
            valid,
            LA_LIGA_RUNTIME_CONFIG,
        )
    )

    assert len(result) == 1

    assert (
        result[
            "observation_key"
        ]
        .nunique()
        == 1
    )

    invalid = valid.copy()

    invalid.loc[
        0,
        "snapshot_time_utc",
    ] = "2026-08-26T21:00:00Z"

    with pytest.raises(
        ValueError,
        match="before kickoff",
    ):
        prepare_observations(
            invalid,
            LA_LIGA_RUNTIME_CONFIG,
        )

    wrong = valid.copy()

    wrong.loc[
        0,
        "league",
    ] = "TEST_OTHER"

    with pytest.raises(
        ValueError,
        match="league mismatch",
    ):
        prepare_observations(
            wrong,
            LA_LIGA_RUNTIME_CONFIG,
        )


def test_observation_append_exact_replay_is_idempotent():
    from league_structural_v2_history import (
        append_only,
        prepare_observations,
    )

    frame = pd.DataFrame(
        [
            {
                "league":
                    "LA_LIGA",
                "event_id":
                    "event-1",
                "commence_time_utc":
                    "2026-08-26T20:00:00Z",
                "snapshot_time_utc":
                    "2026-08-26T19:00:00Z",
                "home_team":
                    "Barcelona",
                "away_team":
                    "Valencia",
                "market_home_probability":
                    0.60,
                "market_draw_probability":
                    0.24,
                "market_away_probability":
                    0.16,
                "shadow_home_probability":
                    0.62,
                "shadow_draw_probability":
                    0.23,
                "shadow_away_probability":
                    0.15,
                "market_argmax":
                    "H",
                "shadow_argmax":
                    "H",
                "prediction_source":
                    "STRUCTURAL_EDGE_V2_SHADOW",
            }
        ]
    )

    prepared = (
        prepare_observations(
            frame,
            LA_LIGA_RUNTIME_CONFIG,
        )
    )

    combined, inserted = (
        append_only(
            prepared,
            frame,
            LA_LIGA_RUNTIME_CONFIG,
        )
    )

    assert inserted == 0
    assert len(combined) == 1


def test_generic_evaluator_rejects_cross_league_results():
    from evaluate_league_structural_v2_live import (
        evaluate,
    )

    history = pd.DataFrame(
        [
            {
                "league":
                    "LA_LIGA",
                "event_id":
                    "event-1",
                "snapshot_time_utc":
                    "2026-08-26T19:00:00Z",
                "commence_time_utc":
                    "2026-08-26T20:00:00Z",
                "home_team":
                    "Barcelona",
                "away_team":
                    "Valencia",
                "market_home_probability":
                    0.60,
                "market_draw_probability":
                    0.24,
                "market_away_probability":
                    0.16,
                "shadow_home_probability":
                    0.62,
                "shadow_draw_probability":
                    0.23,
                "shadow_away_probability":
                    0.15,
                "correction_enabled":
                    True,
            }
        ]
    )

    results = pd.DataFrame(
        [
            {
                "league":
                    "TEST_OTHER",
                "home_team":
                    "Barcelona",
                "away_team":
                    "Valencia",
                "result":
                    "H",
            }
        ]
    )

    with pytest.raises(
        ValueError,
        match="league mismatch",
    ):
        evaluate(
            history,
            results,
            LA_LIGA_RUNTIME_CONFIG,
        )
