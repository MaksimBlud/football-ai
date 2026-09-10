from __future__ import annotations

import pandas as pd
import pytest

import la_liga_nested_development_v1 as protocol
import league_model_diagnostics
import league_model_sweep


def _minimal_history(*seasons: str) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "season": list(seasons),
            "result": ["H"] * len(seasons),
        }
    )


def test_protocol_reuses_only_preexisting_candidate_space() -> None:
    assert tuple(protocol.ALPHAS) == tuple(league_model_diagnostics.ALPHAS)
    assert set(league_model_sweep.FEATURE_SETS) == {
        "core",
        "core_elo",
        "full_no_odds",
    }
    assert set(league_model_sweep.MODEL_VARIANTS) == {
        "logistic_l2",
        "xgb_shallow",
        "xgb_base",
        "xgb_regularized",
    }
    assert len(league_model_sweep.FEATURE_SETS) * len(
        league_model_sweep.MODEL_VARIANTS
    ) == 12


def test_prepare_development_frame_explicitly_excludes_observed_holdout() -> None:
    frame = _minimal_history(
        "2020-2021",
        "2021-2022",
        "2022-2023",
        "2023-2024",
        "2024-2025",
        "2025-2026",
    )

    development, excluded = protocol.prepare_development_frame(frame)

    assert excluded == 1
    assert development["season"].max() == "2024-2025"
    assert "2025-2026" not in set(development["season"])
    assert development["target"].tolist() == [0, 0, 0, 0, 0]


def test_prepare_development_frame_rejects_post_boundary_season() -> None:
    frame = _minimal_history(
        "2020-2021",
        "2021-2022",
        "2022-2023",
        "2023-2024",
        "2024-2025",
        "2025-2026",
        "2026-2027",
    )

    with pytest.raises(ValueError, match="Future/post-boundary seasons"):
        protocol.prepare_development_frame(frame)


def test_nested_outer_splits_have_only_earlier_inner_seasons() -> None:
    assert protocol.inner_seasons_for_outer("2022-2023") == (
        "2020-2021",
        "2021-2022",
    )
    assert protocol.inner_seasons_for_outer("2023-2024") == (
        "2020-2021",
        "2021-2022",
        "2022-2023",
    )
    assert protocol.inner_seasons_for_outer("2024-2025") == (
        "2020-2021",
        "2021-2022",
        "2022-2023",
        "2023-2024",
    )


def test_development_gate_requires_aggregate_and_fold_robustness() -> None:
    outer_rows = [
        {
            "beats_market_accuracy": True,
            "beats_market_logloss": True,
            "beats_market_brier": True,
            "beats_market_all_three": True,
        },
        {
            "beats_market_accuracy": True,
            "beats_market_logloss": True,
            "beats_market_brier": True,
            "beats_market_all_three": True,
        },
        {
            "beats_market_accuracy": False,
            "beats_market_logloss": False,
            "beats_market_brier": False,
            "beats_market_all_three": False,
        },
    ]

    passed = protocol.development_gate(
        outer_rows,
        aggregate_market={
            "accuracy": 0.50,
            "logloss": 1.00,
            "brier": 0.60,
        },
        aggregate_hybrid={
            "accuracy": 0.51,
            "logloss": 0.99,
            "brier": 0.59,
        },
        final_selection_beats_market_all_three=True,
    )
    assert passed["passed"] is True

    failed = protocol.development_gate(
        outer_rows,
        aggregate_market={
            "accuracy": 0.50,
            "logloss": 1.00,
            "brier": 0.60,
        },
        aggregate_hybrid={
            "accuracy": 0.49,
            "logloss": 0.99,
            "brier": 0.59,
        },
        final_selection_beats_market_all_three=True,
    )
    assert failed["aggregate_beats_market_accuracy"] is False
    assert failed["passed"] is False


def test_output_surface_is_research_only() -> None:
    assert "experiments" in protocol.OUTPUT_DIR.parts
    assert "candidates" not in protocol.OUTPUT_DIR.parts
    assert protocol.OBSERVED_HOLDOUT_SEASON not in protocol.OOS_DEVELOPMENT_SEASONS
    assert all(
        season < protocol.OBSERVED_HOLDOUT_SEASON
        for season in protocol.OOS_DEVELOPMENT_SEASONS
    )
