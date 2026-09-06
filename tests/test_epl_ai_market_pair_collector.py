from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from epl_ai_market_pair_collector import (
    ModelBundle,
    build_pair_rows,
    canonical_market_candidates,
)


class DummyModel:
    feature_names_in_ = np.array(["home_last5_points", "away_last5_points", "elo_difference"])

    def predict_proba(self, frame):
        assert list(frame.columns) == list(self.feature_names_in_)
        return np.array([[0.50, 0.25, 0.25]])


def _market_probs(home_odds=2.0, draw_odds=3.0, away_odds=4.0):
    implied = np.array([1 / home_odds, 1 / draw_odds, 1 / away_odds], dtype=float)
    return implied / implied.sum()


def _ledger(snapshot="2026-09-06T08:00:00Z", kickoff="2026-09-06T15:30:00Z"):
    p = _market_probs()
    return pd.DataFrame(
        [
            {
                "prediction_key": "old",
                "league": "EPL",
                "event_id": "evt-1",
                "home_team": "Manchester United",
                "away_team": "Arsenal",
                "kickoff_utc": kickoff,
                "prediction_time_utc": "2026-09-06T07:01:00Z",
                "snapshot_time_utc": "2026-09-06T07:00:00Z",
                "market_home_prob": p[0],
                "market_draw_prob": p[1],
                "market_away_prob": p[2],
                "prediction_mode": "MARKET_ONLY",
            },
            {
                "prediction_key": "latest",
                "league": "EPL",
                "event_id": "evt-1",
                "home_team": "Manchester United",
                "away_team": "Arsenal",
                "kickoff_utc": kickoff,
                "prediction_time_utc": snapshot,
                "snapshot_time_utc": snapshot,
                "market_home_prob": p[0],
                "market_draw_prob": p[1],
                "market_away_prob": p[2],
                "prediction_mode": "MARKET_ONLY",
            },
        ]
    )


def _odds(snapshot="2026-09-06T08:00:00Z", kickoff="2026-09-06T15:30:00Z"):
    return pd.DataFrame(
        [
            {
                "league": "EPL",
                "event_id": "evt-1",
                "snapshot_time_utc": snapshot,
                "commence_time_utc": kickoff,
                "home_team": "Manchester United",
                "away_team": "Arsenal",
                "home_odds": 2.0,
                "draw_odds": 3.0,
                "away_odds": 4.0,
            },
            {
                "league": "EPL",
                "event_id": "evt-1",
                "snapshot_time_utc": "2026-09-06T07:00:00Z",
                "commence_time_utc": kickoff,
                "home_team": "Manchester United",
                "away_team": "Arsenal",
                "home_odds": 2.0,
                "draw_odds": 3.0,
                "away_odds": 4.0,
            },
        ]
    )


def _history(max_date="2026-09-05"):
    return pd.DataFrame(
        [
            {
                "match_date": "2026-09-04",
                "match_time": "15:00",
                "home_team": "Man United",
                "away_team": "Chelsea",
                "home_goals": 2,
                "away_goals": 1,
                "result": "H",
                "home_shots": 10,
                "away_shots": 8,
                "home_shots_target": 5,
                "away_shots_target": 3,
            },
            {
                "match_date": max_date,
                "match_time": "15:00",
                "home_team": "Arsenal",
                "away_team": "Chelsea",
                "home_goals": 1,
                "away_goals": 0,
                "result": "H",
                "home_shots": 12,
                "away_shots": 7,
                "home_shots_target": 6,
                "away_shots_target": 2,
            },
        ]
    )


def _bundle():
    return ModelBundle(
        model=DummyModel(),
        calibrator={"method": "RAW"},
        model_sha256="m" * 64,
        calibrator_sha256="c" * 64,
    )


def test_canonical_market_candidate_uses_latest_observed_exact_snapshot():
    candidates = canonical_market_candidates(
        _ledger(), _odds(), now_utc="2026-09-06T09:00:00Z"
    )
    assert len(candidates) == 1
    assert candidates.iloc[0]["prediction_key"] == "latest"
    assert candidates.iloc[0]["snapshot_time_utc"] == pd.Timestamp("2026-09-06T08:00:00Z")


def test_canonical_market_candidate_rejects_probability_price_mismatch():
    ledger = _ledger()
    ledger.loc[ledger["prediction_key"] == "latest", "market_home_prob"] += 0.05
    with pytest.raises(RuntimeError, match="do not reproduce"):
        canonical_market_candidates(ledger, _odds(), now_utc="2026-09-06T09:00:00Z")


def test_build_pair_normalizes_provider_team_and_is_future_only():
    candidates = canonical_market_candidates(
        _ledger(), _odds(), now_utc="2026-09-06T09:00:00Z"
    )
    pairs, excluded = build_pair_rows(
        candidates,
        _history(),
        _bundle(),
        generated_at_utc="2026-09-06T09:00:00Z",
        code_commit_sha="abc123",
    )
    assert excluded == []
    assert len(pairs) == 1
    row = pairs.iloc[0]
    assert row["model_home_team"] == "Man United"
    assert row["model_away_team"] == "Arsenal"
    assert row["history_max_match_date"] == "2026-09-05"
    assert row["model_generated_at_utc"] < row["kickoff_utc"]
    assert np.isclose(
        row["model_home_prob"] + row["model_draw_prob"] + row["model_away_prob"], 1.0
    )


def test_build_pair_fails_closed_when_history_reaches_market_snapshot_date():
    candidates = canonical_market_candidates(
        _ledger(), _odds(), now_utc="2026-09-06T09:00:00Z"
    )
    pairs, excluded = build_pair_rows(
        candidates,
        _history(max_date="2026-09-06"),
        _bundle(),
        generated_at_utc="2026-09-06T09:00:00Z",
        code_commit_sha="abc123",
    )
    assert pairs.empty
    assert excluded == [
        {"event_id": "evt-1", "reason": "HISTORY_NOT_STRICTLY_BEFORE_MARKET_DATE"}
    ]


def test_pair_key_is_stable_for_same_snapshot_and_artifacts():
    candidates = canonical_market_candidates(
        _ledger(), _odds(), now_utc="2026-09-06T09:00:00Z"
    )
    first, _ = build_pair_rows(
        candidates,
        _history(),
        _bundle(),
        generated_at_utc="2026-09-06T09:00:00Z",
        code_commit_sha="abc123",
    )
    second, _ = build_pair_rows(
        candidates,
        _history(),
        _bundle(),
        generated_at_utc="2026-09-06T09:05:00Z",
        code_commit_sha="def456",
    )
    assert first.iloc[0]["pair_key"] == second.iloc[0]["pair_key"]


def test_post_kickoff_generation_is_excluded():
    candidates = canonical_market_candidates(
        _ledger(), _odds(), now_utc="2026-09-06T09:00:00Z"
    )
    pairs, excluded = build_pair_rows(
        candidates,
        _history(),
        _bundle(),
        generated_at_utc="2026-09-06T16:00:00Z",
        code_commit_sha="abc123",
    )
    assert pairs.empty
    assert excluded == [{"event_id": "evt-1", "reason": "MODEL_NOT_PRE_KICKOFF"}]
