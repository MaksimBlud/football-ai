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
from research_model_features import FEATURES


class DummyModel:
    feature_names_in_ = np.array(FEATURES)

    def predict_proba(self, frame):
        assert list(frame.columns) == FEATURES
        assert frame.iloc[0]["home_odds"] == 2.0
        assert frame.iloc[0]["draw_odds"] == 3.0
        assert frame.iloc[0]["away_odds"] == 4.0
        return np.array([[0.50, 0.25, 0.25]])


def _market_probs(home_odds=2.0, draw_odds=3.0, away_odds=4.0):
    implied = np.array([1 / home_odds, 1 / draw_odds, 1 / away_odds], dtype=float)
    return implied / implied.sum()


def _ledger(snapshot="2026-09-04T16:00:00Z", kickoff="2026-09-06T15:30:00Z"):
    p = _market_probs()
    common = {
        "league": "EPL",
        "event_id": "evt-1",
        "home_team": "Manchester United",
        "away_team": "Arsenal",
        "kickoff_utc": kickoff,
        "market_home_prob": p[0],
        "market_draw_prob": p[1],
        "market_away_prob": p[2],
        "prediction_mode": "MARKET_ONLY",
    }
    return pd.DataFrame([
        {
            **common,
            "prediction_key": "old",
            "prediction_time_utc": "2026-09-04T15:00:00Z",
            "snapshot_time_utc": "2026-09-04T15:00:00Z",
        },
        {
            **common,
            "prediction_key": "latest",
            "prediction_time_utc": snapshot,
            "snapshot_time_utc": snapshot,
        },
    ])


def _odds(snapshot="2026-09-04T16:00:00Z", kickoff="2026-09-06T15:30:00Z"):
    rows = []
    for when in ("2026-09-04T15:00:00Z", snapshot):
        rows.append({
            "league": "EPL",
            "event_id": "evt-1",
            "snapshot_time_utc": when,
            "commence_time_utc": kickoff,
            "home_team": "Manchester United",
            "away_team": "Arsenal",
            "home_odds": 2.0,
            "draw_odds": 3.0,
            "away_odds": 4.0,
        })
    return pd.DataFrame(rows)


def _row(date, time, home, away, result="H"):
    return {
        "match_date": date,
        "match_time": time,
        "home_team": home,
        "away_team": away,
        "home_goals": 2,
        "away_goals": 1,
        "result": result,
        "home_shots": 10,
        "away_shots": 8,
        "home_shots_target": 5,
        "away_shots_target": 3,
    }


def _history():
    return pd.DataFrame([
        _row("2026-08-30", "15:00", "Man United", "Everton"),
        _row("2026-08-31", "16:30", "Arsenal", "Chelsea"),
        # Missing time only one local day before cutoff: fail closed and exclude.
        _row("2026-09-03", None, "Chelsea", "Everton"),
        # 12:30 BST + 4h buffer = 15:30 BST = 14:30Z; safe at 16:00Z cutoff.
        _row("2026-09-04", "12:30", "Man United", "Chelsea"),
        # 15:00 BST + 4h buffer = 19:00 BST = 18:00Z; not safe at cutoff.
        _row("2026-09-04", "15:00", "Arsenal", "Everton"),
    ])


def _bundle():
    return ModelBundle(model=DummyModel(), model_sha256="a" * 64)


def test_history_asof_uses_london_time_and_four_hour_buffer():
    asof = history_as_of_market_snapshot(_history(), "2026-09-04T16:00:00Z")
    identities = set(zip(asof["match_date"].dt.strftime("%Y-%m-%d"), asof["match_time"]))
    assert ("2026-09-04", "12:30") in identities
    assert ("2026-09-04", "15:00") not in identities
    assert not ((asof["match_date"].dt.strftime("%Y-%m-%d") == "2026-09-03") & asof["match_time"].isna()).any()


def test_canonical_market_candidate_uses_latest_observed_exact_snapshot():
    candidates = canonical_market_candidates(_ledger(), _odds(), now_utc="2026-09-04T17:00:00Z")
    assert len(candidates) == 1
    assert candidates.iloc[0]["prediction_key"] == "latest"
    assert candidates.iloc[0]["snapshot_time_utc"] == pd.Timestamp("2026-09-04T16:00:00Z")


def test_canonical_market_candidate_rejects_probability_price_mismatch():
    ledger = _ledger()
    ledger.loc[ledger["prediction_key"] == "latest", "market_home_prob"] += 0.05
    with pytest.raises(RuntimeError, match="do not reproduce"):
        canonical_market_candidates(ledger, _odds(), now_utc="2026-09-04T17:00:00Z")


def test_build_pair_normalizes_team_uses_exact_odds_and_asof_history():
    candidates = canonical_market_candidates(_ledger(), _odds(), now_utc="2026-09-04T17:00:00Z")
    pairs, excluded = build_pair_rows(
        candidates,
        _history(),
        _bundle(),
        generated_at_utc="2026-09-04T17:00:00Z",
        code_commit_sha="abc123",
    )
    assert excluded == []
    assert len(pairs) == 1
    row = pairs.iloc[0]
    assert row["model_home_team"] == "Man United"
    assert row["model_away_team"] == "Arsenal"
    assert row["market_home_odds"] == 2.0
    assert row["history_cutoff_utc"] == "2026-09-04T16:00:00+00:00"
    assert row["history_max_match_date"] == "2026-09-04"
    assert row["history_rows"] == 3
    assert np.isclose(row["model_home_prob"] + row["model_draw_prob"] + row["model_away_prob"], 1.0)


def test_pair_key_is_stable_for_same_snapshot_and_model():
    candidates = canonical_market_candidates(_ledger(), _odds(), now_utc="2026-09-04T17:00:00Z")
    first, _ = build_pair_rows(candidates, _history(), _bundle(), generated_at_utc="2026-09-04T17:00:00Z", code_commit_sha="abc")
    second, _ = build_pair_rows(candidates, _history(), _bundle(), generated_at_utc="2026-09-04T18:00:00Z", code_commit_sha="def")
    assert first.iloc[0]["pair_key"] == second.iloc[0]["pair_key"]


def test_post_kickoff_generation_is_excluded():
    candidates = canonical_market_candidates(_ledger(), _odds(), now_utc="2026-09-04T17:00:00Z")
    pairs, excluded = build_pair_rows(
        candidates, _history(), _bundle(),
        generated_at_utc="2026-09-06T16:00:00Z",
        code_commit_sha="abc123",
    )
    assert pairs.empty
    assert excluded == [{"event_id": "evt-1", "reason": "MODEL_NOT_GENERATED_PRE_KICKOFF"}]
