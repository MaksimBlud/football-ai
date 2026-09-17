import math

import numpy as np
import pandas as pd
import pytest

import corners10_bet365_market_v1 as v1


def _row(league: str, season: str, y: int, i: int) -> dict:
    strong = 4.0 if y else -4.0
    row = {
        "league": league,
        "season": season,
        "opening_line": 9.5,
        "opening_over": 1.90,
        "opening_under": 1.90,
        "HC": 6 if y else 5,
        "AC": 4,
    }
    for j, feature in enumerate(v1.CORNER_STATE_FEATURES):
        row[feature] = strong + (j * 0.01) + ((i % 3) * 0.001)
    return row


def _sufficient_frame() -> pd.DataFrame:
    rows = []
    for league in v1.LEAGUES:
        for season in v1.TRAIN_SEASONS:
            for i in range(75):
                rows.append(_row(league, season, i % 2, i))
        for season in (v1.VALIDATION_SEASON, v1.OOT_SEASON):
            for i in range(100):
                rows.append(_row(league, season, i % 2, i))
    return pd.DataFrame(rows)


def test_half_line_contract_excludes_integer_and_quarter_lines():
    assert v1._is_half_line(9.5)
    assert v1._is_half_line(10.5)
    assert not v1._is_half_line(9.0)
    assert not v1._is_half_line(9.25)
    assert not v1._is_half_line(float("nan"))


def test_devig_opening_market_is_same_row_two_way_probability():
    assert math.isclose(v1._devig_over(1.90, 1.90), 0.5)
    p = v1._devig_over(2.00, 1.80)
    expected = (1 / 2.00) / ((1 / 2.00) + (1 / 1.80))
    assert math.isclose(p, expected)
    with pytest.raises(ValueError):
        v1._devig_over(1.0, 2.0)


def test_candidate_features_are_frozen_pre_match_only():
    assert v1.FEATURES[0:2] == ("market_logit", "opening_line")
    assert set(v1.FEATURES[2:]) == set(v1.CORNER_STATE_FEATURES)
    forbidden = {
        "HC", "AC", "total_corners", "y_over",
        "closing_line", "closing_over", "closing_under",
        "FTHG", "FTAG", "FTR",
    }
    assert not (set(v1.FEATURES) & forbidden)
    model = v1._model().named_steps["model"]
    assert model.C == 0.1
    assert model.max_iter == 2000


def test_prepare_rows_keeps_only_opening_half_lines_and_rejects_2026_27():
    rows = [
        _row("EPL", "2025-26", 1, 0),
        {**_row("EPL", "2025-26", 1, 1), "opening_line": 10.0},
        {**_row("EPL", "2025-26", 1, 2), "opening_line": 9.25},
    ]
    prepared = v1.prepare_rows(pd.DataFrame(rows))
    assert len(prepared) == 1
    assert prepared.iloc[0]["opening_line"] == 9.5
    assert prepared.iloc[0]["y_over"] == 1
    assert math.isclose(prepared.iloc[0]["p_market_over"], 0.5)

    bad = pd.DataFrame([_row("EPL", "2026-27", 1, 0)])
    with pytest.raises(ValueError, match="forbidden season"):
        v1.prepare_rows(bad)


def test_data_sufficiency_gate_fails_closed_before_model_metrics():
    frame = pd.DataFrame([_row("EPL", "2025-26", 1, 0)])
    report = v1.evaluate(frame)
    assert report["decision"] == "SKIP"
    assert report["league_reports"]["EPL"]["status"] == "DATA_INSUFFICIENT"
    assert "validation" not in report["league_reports"]["EPL"]


def test_strong_frozen_corner_state_can_pass_only_through_both_metrics():
    report = v1.evaluate(_sufficient_frame())
    assert report["decision"] == "PILOT"
    assert report["pass_count"] == 3
    assert report["pooled_oot"]["selected_beats_market_both"] is True
    for league in v1.LEAGUES:
        item = report["league_reports"][league]
        assert item["counts"] == {"train": 600, "validation": 100, "oot": 100}
        assert item["validation_admissible"] is True
        assert item["status"] == "PASS"
        assert item["validation"]["candidate"]["brier"] < item["validation"]["market"]["brier"]
        assert item["validation"]["candidate"]["log_loss"] < item["validation"]["market"]["log_loss"]
        assert item["oot"]["candidate"]["brier"] < item["oot"]["market"]["brier"]
        assert item["oot"]["candidate"]["log_loss"] < item["oot"]["market"]["log_loss"]
