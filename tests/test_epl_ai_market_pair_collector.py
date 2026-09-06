from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from epl_ai_market_pair_collector import (
    ModelBundle,
    build_pair_rows,
    canonical_market_candidates,
    history_as_of_market_snapshot,
)


class DummyModel:
    feature_names_in_ = np.array([
        "home_odds", "draw_odds", "away_odds", "home_last5_points", "away_last5_points",
        "form_difference", "home_goals_scored_last5", "home_goals_conceded_last5",
        "away_goals_scored_last5", "away_goals_conceded_last5", "home_shots_last5",
        "away_shots_last5", "home_shots_target_last5", "away_shots_target_last5",
        "home_elo", "away_elo", "elo_difference", "home_venue_win_rate",
        "away_venue_win_rate", "home_venue_goals_scored", "away_venue_goals_scored",
    ])

    def predict_proba(self, frame):
        assert list(frame.columns) == list(self.feature_names_in_)
        return np.array([[0.50, 0.25, 0.25]])


def _market_probs(home_odds=2.0, draw_odds=3.0, away_odds=4.0):
    implied = np.array([1 / home_odds, 1 / draw_odds, 1 / away_odds], dtype=float)
    return implied / implied.sum()


def _ledger(snapshot="2026-09-04T16:00:00Z", kickoff="2026-09-06T15:30:00Z"):
    p = _market_probs()
    return pd.DataFrame([
        {
            "prediction_key": "old", "league": "EPL", "event_id": "evt-1",
            "home_team": "Manchester United", "away_team": "Arsenal", "kickoff_utc": kickoff,
            "prediction_time_utc": "2026-09-04T15:01:00Z", "snapshot_time_utc": "2026-09-04T15:00:00Z",
            "market_home_prob": p[0], "market_draw_prob": p[1], "market_away_prob": p[2],
            "prediction_mode": "MARKET_ONLY",
        },
        {
            "prediction_key": "latest", "league": "EPL", "event_id": "evt-1",
            "home_team": "Manchester United", "away_team": "Arsenal", "kickoff_utc": kickoff,
            "prediction_time_utc": "2026-09-04T16:01:00Z", "snapshot_time_utc": snapshot,
            "market_home_prob": p[0], "market_draw_prob": p[1], "market_away_prob": p[2],
            "prediction_mode": "MARKET_ONLY",
        },
    ])


def _odds():
    return pd.DataFrame([
        {"league": "EPL", "event_id": "evt-1", "snapshot_time_utc": "2026-09-04T15:00:00Z",
         "commence_time_utc": "2026-09-06T15:30:00Z", "home_team": "Manchester United",
         "away_team": "Arsenal", "home_odds": 2.0, "draw_odds": 3.0, "away_odds": 4.0},
        {"league": "EPL", "event_id": "evt-1", "snapshot_time_utc": "2026-09-04T16:00:00Z",
         "commence_time_utc": "2026-09-06T15:30:00Z", "home_team": "Manchester United",
         "away_team": "Arsenal", "home_odds": 2.0, "draw_odds": 3.0, "away_odds": 4.0},
    ])


def _history():
    rows = []
    for i, day in enumerate(range(20, 31)):
        home, away = ("Man United", "Arsenal") if i % 2 == 0 else ("Arsenal", "Man United")
        rows.append({
            "match_date": f"2026-08-{day:02d}", "match_time": "15:00", "home_team": home,
            "away_team": away, "home_goals": 2, "away_goals": 1, "result": "H",
            "home_shots": 12, "away_shots": 8, "home_shots_target": 5, "away_shots_target": 3,
        })
    rows.extend([
        {"match_date": "2026-09-03", "match_time": None, "home_team": "Arsenal", "away_team": "Man United",
         "home_goals": 1, "away_goals": 1, "result": "D", "home_shots": 10, "away_shots": 10,
         "home_shots_target": 4, "away_shots_target": 4},
        {"match_date": "2026-09-04", "match_time": "15:00", "home_team": "Arsenal", "away_team": "Man United",
         "home_goals": 1, "away_goals": 0, "result": "H", "home_shots": 9, "away_shots": 7,
         "home_shots_target": 4, "away_shots_target": 2},
    ])
    return pd.DataFrame(rows)


def _bundle():
    return ModelBundle(model=DummyModel(), model_sha256="a" * 64)


def test_history_asof_excludes_results_not_safely_available():
    asof = history_as_of_market_snapshot(_history(), "2026-09-04T16:00:00Z")
    identities = set(zip(asof["match_date"].dt.strftime("%Y-%m-%d"), asof["match_time"]))
    assert ("2026-09-04", "15:00") not in identities
    assert not ((asof["match_date"].dt.strftime("%Y-%m-%d") == "2026-09-03") & asof["match_time"].isna()).any()


def test_canonical_market_candidate_uses_latest_observed_exact_snapshot():
    candidates = canonical_market_candidates(_ledger(), _odds(), now_utc="2026-09-04T17:00:00Z")
    assert len(candidates) == 1
    assert candidates.iloc[0]["prediction_key"] == "latest"
    assert candidates.iloc[0]["snapshot_time_utc"] == pd.Timestamp("2026-09-04T16:00:00Z")


def test_canonical_market_candidate_rejects_invalid_latest_without_fallback():
    ledger = _ledger()
    ledger.loc[ledger["prediction_key"] == "latest", "market_home_prob"] += 0.05
    with pytest.raises(RuntimeError, match="Canonical latest ledger row has invalid market probabilities"):
        canonical_market_candidates(ledger, _odds(), now_utc="2026-09-04T17:00:00Z")


def test_canonical_market_candidate_rejects_valid_but_price_mismatched_latest():
    ledger = _ledger()
    p = np.array([0.50, 0.30, 0.20])
    ledger.loc[ledger["prediction_key"] == "latest", ["market_home_prob", "market_draw_prob", "market_away_prob"]] = p
    with pytest.raises(RuntimeError, match="do not reproduce"):
        canonical_market_candidates(ledger, _odds(), now_utc="2026-09-04T17:00:00Z")


def test_build_pair_normalizes_team_uses_exact_odds_and_asof_history():
    candidates = canonical_market_candidates(_ledger(), _odds(), now_utc="2026-09-04T17:00:00Z")
    pairs, excluded = build_pair_rows(
        candidates, _history(), _bundle(), generated_at_utc="2026-09-04T17:00:00Z", code_commit_sha="abc123"
    )
    assert excluded == []
    assert len(pairs) == 1
    row = pairs[0]
    assert row["model_home_team"] == "Man United"
    assert row["model_away_team"] == "Arsenal"
    assert row["home_odds"] == 2.0 and row["draw_odds"] == 3.0 and row["away_odds"] == 4.0
    assert row["history_cutoff_utc"] == "2026-09-04T16:00:00+00:00"
    assert row["history_rows"] < len(_history())
    assert abs(row["model_home_prob"] + row["model_draw_prob"] + row["model_away_prob"] - 1.0) < 1e-9


def test_build_pair_excludes_unknown_team_at_decision_time():
    candidates = canonical_market_candidates(_ledger(), _odds(), now_utc="2026-09-04T17:00:00Z")
    candidates.loc[:, "home_team"] = "Hull City"
    candidates.loc[:, "home_team_raw"] = "Hull City"
    pairs, excluded = build_pair_rows(
        candidates, _history(), _bundle(), generated_at_utc="2026-09-04T17:00:00Z", code_commit_sha="abc123"
    )
    assert pairs == []
    assert len(excluded) == 1
    assert "Unknown normalized model teams" in excluded[0]["reason"]


def test_build_pair_rejects_generation_after_kickoff():
    candidates = canonical_market_candidates(_ledger(), _odds(), now_utc="2026-09-04T17:00:00Z")
    with pytest.raises(RuntimeError, match="before kickoff"):
        build_pair_rows(
            candidates, _history(), _bundle(), generated_at_utc="2026-09-06T16:00:00Z", code_commit_sha="abc123"
        )
