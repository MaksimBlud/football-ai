from datetime import (
    datetime,
    timezone,
)

import pandas as pd

import la_liga_structural_v2_shadow_history as history


def shadow_row():
    return pd.DataFrame([
        {
            "league": "LA_LIGA",
            "event_id": "event-1",
            "commence_time_utc":
                "2030-01-02T12:00:00+00:00",
            "home_team": "A",
            "away_team": "B",
            "structural_ready": True,
            "structural_score": 1.0,
            "correction_enabled": True,
            "realized_correction_weight": 1.0,
            "market_home_probability": 0.50,
            "market_draw_probability": 0.30,
            "market_away_probability": 0.20,
            "shadow_home_probability": 0.52,
            "shadow_draw_probability": 0.29,
            "shadow_away_probability": 0.19,
            "market_argmax": "H",
            "shadow_argmax": "H",
            "prediction_source":
                "STRUCTURAL_EDGE_V2_SHADOW",
            "research_only": True,
        }
    ])


def market_row():
    return pd.DataFrame([
        {
            "league": "LA_LIGA",
            "event_id": "event-1",
            "snapshot_time_utc":
                "2030-01-01T10:00:00+00:00",
            "generated_at_utc":
                "2030-01-01T10:01:00+00:00",
            "market_shadow_status": "OK",
        }
    ])


def test_pre_kickoff_observation_is_accepted():
    result = history.prepare_observations(
        shadow_row(),
        market_row(),
        recorded_at_utc=datetime(
            2030,
            1,
            1,
            11,
            tzinfo=timezone.utc,
        ),
    )

    assert len(result) == 1
    assert bool(
        result.iloc[0][
            "pre_kickoff_valid"
        ]
    )


def test_post_kickoff_observation_is_rejected():
    result = history.prepare_observations(
        shadow_row(),
        market_row(),
        recorded_at_utc=datetime(
            2030,
            1,
            2,
            13,
            tzinfo=timezone.utc,
        ),
    )

    assert result.empty


def test_observation_key_is_stable():
    result = history.prepare_observations(
        shadow_row(),
        market_row(),
        recorded_at_utc=datetime(
            2030,
            1,
            1,
            11,
            tzinfo=timezone.utc,
        ),
    )

    key1 = result.iloc[0][
        "observation_key"
    ]

    key2 = history.observation_key(
        result.iloc[0]
    )

    assert key1 == key2


def test_append_is_idempotent(tmp_path):
    result = history.prepare_observations(
        shadow_row(),
        market_row(),
        recorded_at_utc=datetime(
            2030,
            1,
            1,
            11,
            tzinfo=timezone.utc,
        ),
    )

    path = (
        tmp_path
        / "history.csv"
    )

    combined, appended = (
        history.append_history(
            result,
            path,
        )
    )

    assert len(combined) == 1
    assert appended == 1

    combined, appended = (
        history.append_history(
            result,
            path,
        )
    )

    assert len(combined) == 1
    assert appended == 0
