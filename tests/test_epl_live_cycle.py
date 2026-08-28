from dataclasses import replace

import pandas as pd
import pytest

import epl_live_cycle as cycle

from league_runtime_config import (
    EPL_RUNTIME_CONFIG,
)


def test_runtime_gate_accepts_current_market_only_epl():
    cycle.assert_market_only_runtime()


def test_runtime_gate_rejects_calibrated_structural(monkeypatch):
    config = replace(
        EPL_RUNTIME_CONFIG,
        structural_v2=replace(
            EPL_RUNTIME_CONFIG.structural_v2,
            calibration_status="CALIBRATED",
            structural_alpha=0.10,
            edge_threshold=0.75,
        ),
    )

    monkeypatch.setattr(
        cycle,
        "EPL_RUNTIME_CONFIG",
        config,
    )

    with pytest.raises(
        RuntimeError
    ):
        cycle.assert_market_only_runtime()


def test_validate_current_market_shadow():
    frame = pd.DataFrame(
        [
            {
                "league": "EPL",
                "event_id": "e1",
                "snapshot_time_utc":
                    "2030-01-01T10:00:00Z",
                "commence_time_utc":
                    "2030-01-01T15:00:00Z",
                "market_shadow_status":
                    "OK",
                "market_only":
                    True,
                "market_home_probability":
                    0.50,
                "market_draw_probability":
                    0.30,
                "market_away_probability":
                    0.20,
            }
        ]
    )

    result = (
        cycle
        .validate_current_market_shadow(
            frame
        )
    )

    assert len(result) == 1


def test_validate_current_market_shadow_rejects_postkickoff():
    frame = pd.DataFrame(
        [
            {
                "league": "EPL",
                "event_id": "e1",
                "snapshot_time_utc":
                    "2030-01-01T16:00:00Z",
                "commence_time_utc":
                    "2030-01-01T15:00:00Z",
                "market_shadow_status":
                    "OK",
                "market_only":
                    True,
                "market_home_probability":
                    0.50,
                "market_draw_probability":
                    0.30,
                "market_away_probability":
                    0.20,
            }
        ]
    )

    with pytest.raises(
        RuntimeError
    ):
        cycle.validate_current_market_shadow(
            frame
        )


def test_cycle_source_has_no_structural_or_model_runtime_import():
    source = open(
        "epl_live_cycle.py",
        encoding="utf-8",
    ).read()

    assert (
        "import league_structural_v2_shadow"
        not in source
    )

    assert (
        "football_model_xgboost_elo"
        not in source
    )

    assert (
        "persist_results("
        not in source
    )


def test_durable_boundary_uses_reloaded_market_shadow():
    """Durable persistence must consume the serialized market shadow."""

    source = open(
        "epl_live_cycle.py",
        encoding="utf-8",
    ).read()

    compact = "".join(
        source.split()
    )

    assert (
        "observation_mirror.load_market_shadow()"
        in compact
    )

    assert (
        "build_market_only_observations(persisted_shadow)"
        in compact
    )


def test_csv_probability_roundtrip_may_change_exact_float(tmp_path):
    """Document why durable identity must use one canonical boundary."""

    original = pd.DataFrame(
        [
            {
                "market_home_probability":
                    0.19625158816618252,
                "market_draw_probability":
                    0.23638865494927816,
                "market_away_probability":
                    0.5673597568845393,
            }
        ]
    )

    path = tmp_path / "shadow.csv"

    original.to_csv(
        path,
        index=False,
    )

    reloaded = pd.read_csv(
        path
    )

    # Both representations describe the same probability state.
    assert (
        abs(
            float(
                original.iloc[0][
                    "market_home_probability"
                ]
            )
            -
            float(
                reloaded.iloc[0][
                    "market_home_probability"
                ]
            )
        )
        < 1e-15
    )

    assert (
        abs(
            float(
                original.iloc[0][
                    "market_draw_probability"
                ]
            )
            -
            float(
                reloaded.iloc[0][
                    "market_draw_probability"
                ]
            )
        )
        < 1e-15
    )
