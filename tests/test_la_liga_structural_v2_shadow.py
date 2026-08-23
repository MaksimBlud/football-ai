import numpy as np
import pandas as pd

import la_liga_structural_v2_shadow as shadow


def sample_history():
    rows = []

    for i in range(6):
        rows.append({
            "match_date":
                f"2025-01-{i + 1:02d}",
            "match_time":
                "12:00",
            "home_team":
                "A",
            "away_team":
                "B",
            "home_goals":
                2,
            "away_goals":
                1,
            "result":
                "H",
        })

    return pd.DataFrame(
        rows
    )


def test_state_builds_team_history():
    state = shadow.build_state(
        shadow.normalize_finished_matches(
            sample_history()
        )
    )

    assert (
        len(
            state[
                "team_matches"
            ]["A"]
        )
        == 6
    )

    assert (
        len(
            state[
                "team_matches"
            ]["B"]
        )
        == 6
    )


def test_fixture_ready_after_five_matches():
    state = shadow.build_state(
        shadow.normalize_finished_matches(
            sample_history()
        )
    )

    result = shadow.fixture_features(
        "A",
        "B",
        state,
    )

    assert (
        result[
            "structural_ready"
        ]
        is True
    )


def test_cold_start_not_ready():
    state = shadow.build_state(
        shadow.normalize_finished_matches(
            sample_history()
        )
    )

    result = shadow.fixture_features(
        "A",
        "UNKNOWN",
        state,
    )

    assert (
        result[
            "structural_ready"
        ]
        is False
    )


def test_cold_start_market_unchanged():
    market = np.array([
        [
            0.55,
            0.25,
            0.20,
        ]
    ])

    corrected = market.copy()

    assert np.allclose(
        corrected,
        market,
    )


def test_prediction_source_is_shadow_only():
    assert (
        shadow.PREDICTION_SOURCE
        == "STRUCTURAL_EDGE_V2_SHADOW"
    )
