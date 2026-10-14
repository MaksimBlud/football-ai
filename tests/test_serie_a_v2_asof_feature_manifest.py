"""Date-only Serie A V2 feature adapter: exact original features, fail-closed tests."""
from copy import deepcopy
from datetime import datetime, timezone

import pandas as pd
import pytest

from serie_a_v2_asof_feature_manifest import build_manifest
from serie_a_v2_frozen_shadow_preview import shadow_preview

QUOTE = {
    "event_id": "test-v2-a",
    "league": "SERIE_A",
    "home_team": "Alpha",
    "away_team": "Beta",
    "commence_time_utc": "2026-10-19T19:00:00+00:00",
    "snapshot_time_utc": "2026-10-13T15:00:00+00:00",
    "home_odds": 2.1, "draw_odds": 3.4, "away_odds": 4.0,
}


def history():
    base = {"HC": 4, "AC": 2, "HY": 1, "AY": 2, "HR": 0, "AR": 0}
    return pd.DataFrame([
        {**base, "Date": "10/10/2026", "HomeTeam": "Alpha", "AwayTeam": "Gamma",
         "FTHG": 2, "FTAG": 0, "FTR": "H"},
        {**base, "Date": "11/10/2026", "HomeTeam": "Beta", "AwayTeam": "Delta",
         "FTHG": 0, "FTAG": 1, "FTR": "A"},
        {**base, "Date": "12/10/2026", "HomeTeam": "Alpha", "AwayTeam": "Delta",
         "FTHG": 1, "FTAG": 1, "FTR": "D"},
        {**base, "Date": "13/10/2026", "HomeTeam": "Beta", "AwayTeam": "Gamma",
         "FTHG": 5, "FTAG": 0, "FTR": "H"},
        {**base, "Date": "15/10/2026", "HomeTeam": "Beta", "AwayTeam": "Delta",
         "FTHG": 8, "FTAG": 0, "FTR": "H"},
    ])


def test_exact_frozen_19_features_and_no_same_day_outcome_leakage():
    report = build_manifest(history(), [QUOTE])
    assert report["feature_count"] == 19
    assert report["independently_attested_information_time"] is False
    assert report["eligible_for_frozen_prospective_cohort"] is False
    assert report["paid_provider_requests"] == report["database_writes"] == 0
    row = report["feature_manifests"][0]
    assert len(row["features"]) == 19
    assert row["feature_history_cutoff_utc"] == "2026-10-13T00:00:00+00:00"
    assert row["features"]["diff_points_5"] == pytest.approx(2.0)
    assert row["features"]["diff_goals_for_5"] == pytest.approx(1.5)
    assert row["features"]["diff_points_venue5"] is None  # real missing venue history, not zero
    observation = shadow_preview([QUOTE], report["feature_manifests"],
                                 as_of_utc=datetime(2026,10,13,15,1,tzinfo=timezone.utc))
    assert observation["scored"] == 1
    assert observation["eligible_for_product_publication"] is False


def test_additional_results_on_or_after_quote_day_never_change_features():
    older = history()
    before = build_manifest(older, [QUOTE])["feature_manifests"][0]["features"]
    newer = deepcopy(older)
    newer.loc[3, "FTHG"] = 9
    newer.loc[4, "FTHG"] = 10
    assert build_manifest(newer, [QUOTE])["feature_manifests"][0]["features"] == before


def test_old_or_incompatible_quotes_fail_closed():
    bad = {**QUOTE, "snapshot_time_utc": "2026-10-20T00:00:00Z"}
    with pytest.raises(ValueError, match="at/after kickoff"):
        build_manifest(history(), [bad])
    with pytest.raises(ValueError, match="Serie A"):
        build_manifest(history(), [{**QUOTE, "league": "EPL"}])
    with pytest.raises(ValueError, match="conflicting"):
        build_manifest(history(), [QUOTE, {**QUOTE, "away_team": "Gamma"}])


def test_bad_history_cannot_be_silently_imputed_or_deduplicated():
    no_corners = history().drop(columns=["HC"])
    with pytest.raises(ValueError, match="required football stats"):
        build_manifest(no_corners, [QUOTE])
    missing_corners = history()
    missing_corners.loc[0, "HC"] = None
    with pytest.raises(ValueError, match="missing history stat"):
        build_manifest(missing_corners, [QUOTE])
    duplicated = pd.concat([history(), history().iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="collision"):
        build_manifest(duplicated, [QUOTE])


def test_latest_saved_quote_is_used_without_duplicate_feature_identity():
    earlier = {**QUOTE, "snapshot_time_utc": "2026-10-13T10:00:00Z"}
    report = build_manifest(history(), [QUOTE, earlier])
    assert len(report["feature_manifests"]) == 1



def test_v2_history_coverage_explicitly_reports_frozen_median_imputation():
    row = build_manifest(history(), [QUOTE])["feature_manifests"][0]
    assert row["observed_frozen_feature_count"] == 14
    assert row["median_imputed_frozen_feature_count"] == 5
    assert row["history_coverage"]["home"]["historical_team"] == "Alpha"
    assert row["history_coverage"]["home"]["prior_matches_in_frozen_30_match_window"] == 2
    assert row["history_coverage"]["home"]["prior_matches_at_fixture_venue_in_window"] == 2
    assert row["history_coverage"]["home"]["last_historical_match_date"] == "2026-10-12"
    assert row["history_coverage"]["away"]["prior_matches_in_frozen_30_match_window"] == 1
    assert row["history_coverage"]["away"]["prior_matches_at_fixture_venue_in_window"] == 0
    assert row["history_coverage"]["away"]["last_historical_match_date"] == "2026-10-11"


def test_never_invent_observed_history_for_unseen_clubs():
    fixture = {**QUOTE, "event_id": "new-teams", "home_team": "Never Played Home",
               "away_team": "Never Played Away"}
    row = build_manifest(history(), [fixture])["feature_manifests"][0]
    assert row["observed_frozen_feature_count"] == 0
    assert row["median_imputed_frozen_feature_count"] == 19
    assert all(value is None for value in row["features"].values())
    assert row["history_coverage"]["home"]["prior_matches_in_frozen_30_match_window"] == 0
    assert row["history_coverage"]["away"]["last_historical_match_date"] is None

def test_online_manifest_matches_original_frozen_feature_builder_on_same_history():
    """Guard exact 19-feature calculation parity; no model values or outcomes are tuned."""
    from historical_football_signal_lab import (
        FEATURE_SETS,
        add_difference_features,
        build_point_in_time_features,
    )

    prior = history().iloc[:3].copy()
    target = pd.DataFrame([{
        "Date": "13/10/2026",
        "HomeTeam": "Alpha",
        "AwayTeam": "Beta",
        "FTHG": 1,
        "FTAG": 0,
        "FTR": "H",
        "HC": 5,
        "AC": 3,
        "HY": 2,
        "AY": 1,
        "HR": 0,
        "AR": 0,
    }])
    original_rows = build_point_in_time_features(
        pd.concat([prior, target], ignore_index=True),
        "SERIE_A",
        "SYNTHETIC_PARITY_ONLY",
    )
    original = add_difference_features(original_rows).iloc[-1]
    manifest = build_manifest(prior, [QUOTE])["feature_manifests"][0]["features"]

    assert list(manifest) == list(FEATURE_SETS["ALL_FOOTBALL"])
    for feature in FEATURE_SETS["ALL_FOOTBALL"]:
        expected = original[feature]
        actual = manifest[feature]
        if pd.isna(expected):
            assert actual is None
        else:
            assert actual == pytest.approx(float(expected), abs=1e-12)

