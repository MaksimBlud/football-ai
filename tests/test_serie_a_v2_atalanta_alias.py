"""V2-only regression for verified historical Atalanta vs bookmaker Atalanta BC.

These are *synthetic pre-freeze* completed fixtures. No protected 2026/27
results are read and no model refit or weights are changed.
"""
from datetime import datetime, timezone

import pandas as pd
import pytest

from serie_a_v2_asof_feature_manifest import build_manifest
from serie_a_v2_frozen_shadow_preview import load_verified_original, shadow_preview

BASE = {"HC": 5, "AC": 4, "HY": 2, "AY": 1, "HR": 0, "AR": 0}
ASOF = datetime(2026, 10, 13, 15, 1, tzinfo=timezone.utc)


def history():
    games = [
        ("03/10/2025", "Atalanta", "Juventus", 2, 1, "H"),
        ("04/10/2025", "Inter", "Atalanta", 1, 1, "D"),
        ("05/10/2025", "Frosinone", "Torino", 0, 1, "A"),
        ("06/10/2025", "Lecce", "Frosinone", 1, 2, "A"),
        ("07/10/2025", "Milan", "Inter", 2, 1, "H"),
        ("08/10/2025", "Roma", "Milan", 0, 0, "D"),
    ]
    return pd.DataFrame([
        {**BASE, "Date": date, "HomeTeam": home, "AwayTeam": away,
         "FTHG": hg, "FTAG": ag, "FTR": result}
        for date, home, away, hg, ag, result in games
    ])


def fixture(event_id, home, away):
    return {
        "event_id": event_id, "league": "SERIE_A",
        "home_team": home, "away_team": away,
        "snapshot_time_utc": "2026-10-13T15:00:00Z",
        "commence_time_utc": "2026-10-19T17:00:00Z",
        "home_odds": 2.2, "draw_odds": 3.4, "away_odds": 3.1,
    }


@pytest.mark.parametrize("quote,atalanta_side", [
    (fixture("a", "Atalanta BC", "Frosinone"), "home"),
    (fixture("b", "AC Milan", "Atalanta BC"), "away"),
])
def test_v2_bookmaker_atalanta_identity_joins_verified_10_season_team_history(quote, atalanta_side):
    original = load_verified_original()
    row = build_manifest(history(), [quote])["feature_manifests"][0]
    assert list(row["features"]) == list(original["features"])
    assert row["event_id"] == quote["event_id"]
    assert row["home_team"] == quote["home_team"]
    assert row["away_team"] == quote["away_team"]
    assert row["observed_frozen_feature_count"] == 19
    assert row["median_imputed_frozen_feature_count"] == 0
    assert row["history_coverage"][atalanta_side]["historical_team"] == "Atalanta"
    assert row["history_coverage"][atalanta_side]["prior_matches_in_frozen_30_match_window"] == 2
    assert row["history_coverage"][atalanta_side]["prior_matches_at_fixture_venue_in_window"] == 1
    preview = shadow_preview([quote], [row], as_of_utc=ASOF)
    assert preview["scored"] == 1
    assert preview["blocked"]["ALL_FEATURES_MEDIAN_IMPUTED"] == 0
    assert preview["previews"][0]["median_imputed_frozen_feature_count"] == 0
    assert preview["previews"][0]["market_1x2"] == pytest.approx(
        preview["previews"][0]["active_market_fallback_1x2"]
    )
    assert preview["previews"][0]["model_candidate_sha256"] == original["artifact_sha256"]
    assert preview["previews"][0]["no_bet"] is True


def test_historical_and_bookmaker_atalanta_names_cannot_create_duplicate_games():
    data = history()
    dupe = data.iloc[[0]].copy()
    dupe.loc[dupe.index[0], "HomeTeam"] = "Atalanta BC"
    with pytest.raises(ValueError, match="historical fixture identity collision"):
        build_manifest(pd.concat([data, dupe], ignore_index=True), [
            fixture("a", "Atalanta BC", "Frosinone")
        ])
