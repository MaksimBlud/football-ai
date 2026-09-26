import math

import numpy as np
import pandas as pd
import pytest

import corner_repricing_timing_policy_v1 as timing


LEAGUES = ("EPL", "LA_LIGA", "SERIE_A", "BUNDESLIGA", "LIGUE_1")


class FakeModel:
    def predict_proba(self, frame):
        x = frame["opening_lambda"].to_numpy(float)
        # Lower FAIR_CENTRE => higher risk, matching the frozen predictor sign.
        p = np.clip((11.0 - x) / 4.0, 0.01, 0.99)
        return np.column_stack([1.0 - p, p])


def _cohort(rows_per_league: list[int]) -> pd.DataFrame:
    rows = []
    fixture = 1000
    for league, n in zip(LEAGUES, rows_per_league):
        for i in range(n):
            opening = 8.5 + i * 0.2
            wait_n = max(1, math.ceil(n * 0.25))
            if i < wait_n:
                delta = 0.6
            elif i == wait_n:
                delta = 0.5
            else:
                delta = 0.05
            rows.append(
                {
                    "fixture_id": str(fixture),
                    "league": league,
                    "opening_lambda": opening,
                    "centre_delta": delta,
                    "movement_magnitude": abs(delta),
                }
            )
            fixture += 1
    return pd.DataFrame(rows)


def test_frozen_expected_cohort_sizes():
    assert timing.EXPECTED_ROWS == {
        "FRESH_50": 50,
        "V1_46": 46,
        "V2B_43": 43,
    }
    assert timing.HIGH_RISK_FRACTION == 0.25


def test_apply_policy_uses_top_quarter_per_league_with_deterministic_count():
    frame = _cohort([10, 10, 10, 10, 10])
    out = timing.apply_timing_policy(
        frame,
        label="FRESH_50",
        model=FakeModel(),
        material_threshold=0.4,
    )

    assert int((out["timing_policy"] == timing.GROUP_WAIT).sum()) == 15
    for league in LEAGUES:
        g = out[out["league"] == league]
        assert int((g["timing_policy"] == timing.GROUP_WAIT).sum()) == 3
        wait_max = g.loc[g["timing_policy"] == timing.GROUP_WAIT, "opening_lambda"].max()
        stable_min = g.loc[g["timing_policy"] == timing.GROUP_STABLE, "opening_lambda"].min()
        assert wait_max < stable_min


def test_summary_marks_consistent_wait_policy_when_both_metrics_are_higher():
    frame = _cohort([10, 10, 10, 10, 10])
    out = timing.apply_timing_policy(
        frame,
        label="FRESH_50",
        model=FakeModel(),
        material_threshold=0.4,
    )
    report = timing.summarize_cohort(out)

    assert report["directionally_consistent_with_wait_policy"] is True
    assert report["wait_minus_stable_mean_movement_magnitude"] > 0
    assert report["wait_minus_stable_material_move_prevalence"] > 0
    assert report["wait_to_stable_material_move_risk_ratio"] > 1


def test_summary_fails_portability_direction_when_wait_group_is_worse():
    frame = _cohort([10, 10, 10, 10, 10])
    out = timing.apply_timing_policy(
        frame,
        label="FRESH_50",
        model=FakeModel(),
        material_threshold=0.4,
    )
    out.loc[out["timing_policy"] == timing.GROUP_WAIT, "movement_magnitude"] = 0.0
    out.loc[out["timing_policy"] == timing.GROUP_WAIT, "centre_delta"] = 0.0
    out.loc[out["timing_policy"] == timing.GROUP_WAIT, "material_move"] = 0
    report = timing.summarize_cohort(out)

    assert report["directionally_consistent_with_wait_policy"] is False
    assert report["wait_minus_stable_mean_movement_magnitude"] < 0
    assert report["wait_minus_stable_material_move_prevalence"] < 0


def test_validation_rejects_wrong_row_count_and_duplicate_fixture():
    frame = _cohort([10, 10, 10, 10, 10])
    with pytest.raises(ValueError, match="expected 46 rows"):
        timing.apply_timing_policy(
            frame,
            label="V1_46",
            model=FakeModel(),
            material_threshold=0.4,
        )

    dup = frame.copy()
    dup.loc[1, "fixture_id"] = dup.loc[0, "fixture_id"]
    with pytest.raises(ValueError, match="duplicate fixture IDs"):
        timing.apply_timing_policy(
            dup,
            label="FRESH_50",
            model=FakeModel(),
            material_threshold=0.4,
        )


def test_validation_rejects_inconsistent_movement_magnitude():
    frame = _cohort([10, 10, 10, 10, 10])
    frame.loc[0, "movement_magnitude"] = 999.0
    with pytest.raises(ValueError, match="movement_magnitude"):
        timing.apply_timing_policy(
            frame,
            label="FRESH_50",
            model=FakeModel(),
            material_threshold=0.4,
        )
