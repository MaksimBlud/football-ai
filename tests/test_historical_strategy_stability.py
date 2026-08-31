import math

import pandas as pd

from historical_strategy_stability import add_confidence_bucket, segment_stability


def sample_frame():
    return pd.DataFrame([
        {"league":"EPL","season":"2023-2024","market_pick":"H","market_confidence":0.65,"selected_odds":1.50,"won":True,"profit":0.50},
        {"league":"EPL","season":"2023-2024","market_pick":"H","market_confidence":0.65,"selected_odds":1.50,"won":False,"profit":-1.00},
        {"league":"EPL","season":"2024-2025","market_pick":"H","market_confidence":0.65,"selected_odds":1.50,"won":True,"profit":0.50},
        {"league":"LA_LIGA","season":"2024-2025","market_pick":"A","market_confidence":0.45,"selected_odds":2.20,"won":True,"profit":1.20},
    ])


def test_add_confidence_bucket_labels_rows():
    prepared = add_confidence_bucket(sample_frame())
    assert list(prepared["confidence_bucket"].astype(str)) == ["60–70%", "60–70%", "60–70%", "40–50%"]


def test_segment_stability_reports_season_consistency_and_recent_roi():
    summary, by_season = segment_stability(sample_frame())
    epl = summary[(summary["league"] == "EPL") & (summary["market_pick"] == "H")].iloc[0]
    assert epl["matches"] == 3
    assert epl["seasons"] == 2
    assert epl["positive_seasons"] == 1
    assert math.isclose(epl["positive_season_share"], 0.5)
    assert math.isclose(epl["profit"], 0.0)
    assert math.isclose(epl["recent_5_season_roi"], 0.0)
    assert len(by_season[(by_season["league"] == "EPL") & (by_season["market_pick"] == "H")]) == 2


def test_missing_required_columns_are_rejected():
    frame = sample_frame().drop(columns=["profit"])
    try:
        add_confidence_bucket(frame)
    except ValueError as exc:
        assert "profit" in str(exc)
    else:
        raise AssertionError("expected ValueError")
