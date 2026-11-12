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

def test_original_feature_builder_source_is_runtime_pinned_and_drift_fails_closed(tmp_path):
    from serie_a_v2_asof_feature_manifest import (
        FROZEN_FEATURE_BUILDER_GIT_BLOB_SHA,
        _verify_original_feature_builder,
    )

    assert _verify_original_feature_builder() == FROZEN_FEATURE_BUILDER_GIT_BLOB_SHA
    drifted = tmp_path / "historical_football_signal_lab.py"
    drifted.write_text("# changed feature definitions\n", encoding="utf-8")
    with pytest.raises(ValueError, match="feature builder source drift"):
        _verify_original_feature_builder(drifted)

def test_online_manifest_matches_original_builder_after_frozen_30_match_truncation():
    """Exercise the exact rolling-window and venue semantics beyond the short fixture."""
    from historical_football_signal_lab import (
        FEATURE_SETS,
        add_difference_features,
        build_point_in_time_features,
    )

    rows = []
    start = pd.Timestamp("2026-08-01")
    for i in range(36):
        day = (start + pd.Timedelta(days=i)).strftime("%d/%m/%Y")
        alpha_home = i % 2 == 0
        beta_home = i % 3 == 0
        alpha_hg, alpha_ag = ((i % 4) + 1, i % 2) if alpha_home else (i % 2, (i % 4) + 1)
        beta_hg, beta_ag = ((i % 3) + 1, i % 2) if beta_home else (i % 2, (i % 3) + 1)
        rows.extend([
            {
                "Date": day,
                "HomeTeam": "Alpha" if alpha_home else f"Alpha Opponent {i}",
                "AwayTeam": f"Alpha Opponent {i}" if alpha_home else "Alpha",
                "FTHG": alpha_hg,
                "FTAG": alpha_ag,
                "FTR": "H" if alpha_hg > alpha_ag else ("A" if alpha_hg < alpha_ag else "D"),
                "HC": 2 + (i % 7),
                "AC": 1 + (i % 5),
                "HY": i % 4,
                "AY": (i + 1) % 4,
                "HR": i % 2,
                "AR": (i + 1) % 2,
            },
            {
                "Date": day,
                "HomeTeam": "Beta" if beta_home else f"Beta Opponent {i}",
                "AwayTeam": f"Beta Opponent {i}" if beta_home else "Beta",
                "FTHG": beta_hg,
                "FTAG": beta_ag,
                "FTR": "H" if beta_hg > beta_ag else ("A" if beta_hg < beta_ag else "D"),
                "HC": 1 + (i % 6),
                "AC": 2 + (i % 4),
                "HY": (i + 2) % 5,
                "AY": i % 5,
                "HR": (i + 1) % 2,
                "AR": i % 2,
            },
        ])

    prior = pd.DataFrame(rows)
    target = pd.DataFrame([{
        "Date": "13/10/2026",
        "HomeTeam": "Alpha",
        "AwayTeam": "Beta",
        "FTHG": 0,
        "FTAG": 0,
        "FTR": "D",
        "HC": 0,
        "AC": 0,
        "HY": 0,
        "AY": 0,
        "HR": 0,
        "AR": 0,
    }])
    original_rows = build_point_in_time_features(
        pd.concat([prior, target], ignore_index=True),
        "SERIE_A",
        "SYNTHETIC_30_MATCH_PARITY_ONLY",
    )
    original = add_difference_features(original_rows).iloc[-1]
    manifest_row = build_manifest(prior, [QUOTE])["feature_manifests"][0]
    manifest = manifest_row["features"]

    assert manifest_row["history_coverage"]["home"]["prior_matches_in_frozen_30_match_window"] == 30
    assert manifest_row["history_coverage"]["away"]["prior_matches_in_frozen_30_match_window"] == 30
    assert list(manifest) == list(FEATURE_SETS["ALL_FOOTBALL"])
    for feature in FEATURE_SETS["ALL_FOOTBALL"]:
        expected = original[feature]
        actual = manifest[feature]
        if pd.isna(expected):
            assert actual is None
        else:
            assert actual == pytest.approx(float(expected), abs=1e-12)



# The following tests use synthetic 5Dollar-shaped fixtures only. They never
# create an account, call an endpoint, read target outcomes, or authorize a
# real source archive. The checked-in rights manifest remains HOLD.

def _synthetic_5dollar_rights():
    return {
        "approval_status": "APPROVED",
        "provider_model_use_permitted": True,
        "provider_cache_permitted": True,
        "provider_private_retention_permitted": True,
        "upstream_rights_confirmed": True,
        "free_serie_a_required_fields_confirmed": True,
        "field_semantics_confirmed": True,
        "private_archive_verified": True,
        "raw_redistribution_permitted": False,
        "test_fixture_only": True,
    }


def _synthetic_5dollar_fixture(index, kickoff_utc=None, home="Juventus", away="Inter Milan"):
    from datetime import datetime, timedelta, timezone

    kickoff = kickoff_utc or (
        datetime(2026, 8, 1, 18, 0, tzinfo=timezone.utc) + timedelta(days=index)
    )
    return {
        "id": 1000 + index,
        "league": {"id": 3405541143, "name": "Italy Serie A"},
        "league_season_id": "season-2026-27",
        "kickoff_utc": kickoff.isoformat(),
        "status": "finished",
        "status_reason": None,
        "status_code": "full",
        "teams": {"home": {"name": home}, "away": {"name": away}},
        "goals": {"home": 2 if index % 2 == 0 else 0, "away": 0 if index % 2 == 0 else 1},
        "corners": {"home": 5 + index % 3, "away": 3 + index % 2},
        "cards": {
            "home": {"yellow": 1 + index % 2, "red": 0},
            "away": {"yellow": 2 + index % 2, "red": 0},
        },
    }


def _synthetic_5dollar_bundle(tmp_path, fixtures=None, quote=None):
    import hashlib
    import json

    fixtures = fixtures if fixtures is not None else [
        _synthetic_5dollar_fixture(i) for i in range(30)
    ]
    fixtures = list(fixtures)
    fixtures.append({
        "id": 9999,
        "league": {"id": 3405541143, "name": "Italy Serie A"},
        "league_season_id": "season-2026-27",
        "kickoff_utc": "2026-11-13T17:00:00+00:00",
        "status": "scheduled",
        "status_reason": None,
        "status_code": None,
        "teams": {"home": {"name": "Juventus"}, "away": {"name": "Inter Milan"}},
    })
    payload = {
        "success": 1,
        "data": fixtures,
        "pagination": {"page": 1, "per_page": 100, "count": len(fixtures), "has_more": False},
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    (tmp_path / "page-1.json").write_bytes(raw)
    default_quote = {
        "event_id": "odds-target-2026-11-13",
        "league": "SERIE_A",
        "home_team": "Juventus",
        "away_team": "Inter",
        "commence_time_utc": "2026-11-13T20:00:00+00:00",
        "snapshot_time_utc": "2026-11-12T08:05:00+00:00",
    }
    quote = dict(quote or default_quote)
    page = {
        "page_number": 1,
        "file": "page-1.json",
        "request_url": "https://api.5dollarfootballapi.com/v1/leagues/3405541143/fixtures?season=2026&page=1&per_page=100",
        "http_status": 200,
        "request_started_at_utc": "2026-11-12T07:59:59+00:00",
        "response_received_at_utc": "2026-11-12T08:00:00+00:00",
        "response_sha256": hashlib.sha256(raw).hexdigest(),
        "response_bytes": len(raw),
    }
    capture = {
        "schema_version": "5DOLLAR_PRIVATE_CAPTURE_BUNDLE_V1",
        "league_id": 3405541143,
        "league_season_id": "season-2026-27",
        "season": "2026-2027",
        "season_api_parameter": "2026",
        "api_plan": "free",
        "storage_class": "private_local",
        "capture_run_id": "43180000000",
        "capture_commit_sha": "a" * 40,
        "request_started_at_utc": "2026-11-12T07:59:59+00:00",
        "response_received_at_utc": "2026-11-12T08:00:00+00:00",
        "captured_at_utc": "2026-11-12T08:00:00+00:00",
        "page_count": 1,
        "pages": [page],
        "feature_source_gate": {
            "type": "CURRENT_FORM_FEATURE_INPUT_ONLY",
            "primary_league": "SERIE_A",
            "season": "2026-2027",
            "minimum_completed_primary_events": 30,
            "observed_completed_primary_events": 30,
            "checked_at_utc": "2026-11-12T07:59:58+00:00",
            "metadata_fields_read": ["match_date", "home_team", "away_team"],
            "score_or_result_fields_selected_for_gate": False,
            "passed": True,
        },
        "feature_policy": {
            "use_current_season_matches_only_as_lagged_features": True,
            "same_calendar_day_matches_excluded": True,
            "future_or_unplayed_fixtures_used": False,
            "model_weights_or_feature_definitions_changed": False,
            "model_refit": False,
            "model_selection": False,
        },
        "target_outcome_evaluation_gate": {
            "minimum_completed_eligible_prospective_forecasts": 30,
            "outcomes_read_for_evaluation": False,
            "outcome_gate_open": False,
        },
        "target_outcomes_read": False,
        "target_outcomes_scored": False,
        "paid_provider_calls": 0,
        "supabase_writes": 0,
    }
    return capture, [quote], _synthetic_5dollar_rights()


def test_5dollar_offline_adapter_maps_exact_original_19_features_and_verifies_sha(tmp_path):
    from serie_a_v2_5dollar_source_adapter import build_manifest_from_private_archive
    from serie_a_v2_frozen_shadow_preview import FROZEN_SHA

    capture, quotes, rights = _synthetic_5dollar_bundle(tmp_path)
    report = build_manifest_from_private_archive(tmp_path, capture, quotes, rights)

    assert report["candidate_sha256"] == FROZEN_SHA
    assert report["feature_count"] == 19
    row = report["feature_manifests"][0]
    assert len(row["features"]) == 19
    # Original V2 uses the frozen five-match mean, not a five-match sum.
    assert row["features"]["diff_points_5"] == pytest.approx(-0.6)
    assert row["history_coverage"]["home"]["prior_matches_in_frozen_30_match_window"] == 30
    assert row["history_coverage"]["away"]["prior_matches_in_frozen_30_match_window"] == 30
    assert row["history_coverage"]["home"]["last_historical_match_date"] == "2026-08-30"
    assert row["history_coverage"]["away"]["last_historical_match_date"] == "2026-08-30"
    assert report["source_before_quote_order_validated"] is True
    assert report["source_before_quote_verified"] is False
    assert report["source_capture_attestation_required"] is True
    assert report["source_capture"]["source_finished_fixture_count"] == 30
    assert report["source_capture"]["source_skipped_non_finished_fixture_count"] == 1
    assert report["source_capture"]["upstream_source_observation_timestamp_available"] is False
    assert report["target_outcomes_read"] is False
    assert report["model_inference_performed"] is False
    assert report["eligible_for_frozen_prospective_cohort"] is False
    assert report["eligible_for_product_publication"] is False
    assert report["scored"] is False
    assert report["source_capture"]["raw_payload_emitted"] is False


def test_5dollar_adapter_preserves_original_same_utc_day_exclusion(tmp_path):
    from datetime import datetime, timezone
    from serie_a_v2_5dollar_source_adapter import build_manifest_from_private_archive

    capture, quotes, rights = _synthetic_5dollar_bundle(tmp_path)
    baseline = build_manifest_from_private_archive(tmp_path, capture, quotes, rights)
    same_day = _synthetic_5dollar_fixture(
        99,
        kickoff_utc=datetime(2026, 11, 12, 7, 0, tzinfo=timezone.utc),
    )
    fixtures = [_synthetic_5dollar_fixture(i) for i in range(30)] + [same_day]
    capture2, quotes2, rights2 = _synthetic_5dollar_bundle(
        tmp_path,
        fixtures=fixtures,
    )
    changed = build_manifest_from_private_archive(tmp_path, capture2, quotes2, rights2)
    assert changed["feature_manifests"][0]["features"] == baseline["feature_manifests"][0]["features"]


def test_5dollar_adapter_rejects_source_received_after_quote(tmp_path):
    import pytest
    from serie_a_v2_5dollar_source_adapter import build_manifest_from_private_archive

    capture, quotes, rights = _synthetic_5dollar_bundle(tmp_path)
    capture["request_started_at_utc"] = "2026-11-12T08:05:01+00:00"
    capture["response_received_at_utc"] = "2026-11-12T08:06:00+00:00"
    capture["captured_at_utc"] = capture["response_received_at_utc"]
    capture["pages"][0]["request_started_at_utc"] = capture["request_started_at_utc"]
    capture["pages"][0]["response_received_at_utc"] = capture["response_received_at_utc"]
    with pytest.raises(ValueError, match="strictly before every quote"):
        build_manifest_from_private_archive(tmp_path, capture, quotes, rights)


def test_5dollar_adapter_rejects_raw_sha_mismatch(tmp_path):
    import pytest
    from serie_a_v2_5dollar_source_adapter import build_manifest_from_private_archive

    capture, quotes, rights = _synthetic_5dollar_bundle(tmp_path)
    capture["pages"][0]["response_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        build_manifest_from_private_archive(tmp_path, capture, quotes, rights)


def test_5dollar_adapter_rejects_target_fixture_identity_even_when_provider_id_differs(tmp_path):
    from datetime import datetime, timezone
    import pytest
    from serie_a_v2_5dollar_source_adapter import build_manifest_from_private_archive

    quote = {
        "event_id": "odds-provider-id",
        "league": "SERIE_A",
        "home_team": "Juventus",
        "away_team": "Inter",
        "commence_time_utc": "2026-11-12T12:00:00+00:00",
        "snapshot_time_utc": "2026-11-12T08:05:00+00:00",
    }
    fixtures = [_synthetic_5dollar_fixture(i) for i in range(30)]
    fixtures.append(_synthetic_5dollar_fixture(
        30,
        kickoff_utc=datetime(2026, 11, 12, 7, 0, tzinfo=timezone.utc),
    ))
    capture, quotes, rights = _synthetic_5dollar_bundle(tmp_path, fixtures, quote)
    with pytest.raises(ValueError, match="target fixture identity"):
        build_manifest_from_private_archive(tmp_path, capture, quotes, rights)


def test_5dollar_adapter_rejects_missing_stats_not_zero_fills(tmp_path):
    import pytest
    from serie_a_v2_5dollar_source_adapter import build_manifest_from_private_archive

    fixtures = [_synthetic_5dollar_fixture(i) for i in range(30)]
    fixtures[0]["corners"]["home"] = None
    capture, quotes, rights = _synthetic_5dollar_bundle(tmp_path, fixtures)
    with pytest.raises(ValueError, match="non-negative integer"):
        build_manifest_from_private_archive(tmp_path, capture, quotes, rights)


def test_5dollar_adapter_rejects_mixed_league_season_and_non_free_plan(tmp_path):
    import pytest
    from serie_a_v2_5dollar_source_adapter import build_manifest_from_private_archive

    fixtures = [_synthetic_5dollar_fixture(i) for i in range(30)]
    fixtures[0]["league_season_id"] = "other-season"
    capture, quotes, rights = _synthetic_5dollar_bundle(tmp_path, fixtures)
    with pytest.raises(ValueError, match="league_season_id"):
        build_manifest_from_private_archive(tmp_path, capture, quotes, rights)

    capture, quotes, rights = _synthetic_5dollar_bundle(tmp_path)
    capture["api_plan"] = "community"
    community_report = build_manifest_from_private_archive(tmp_path, capture, quotes, rights)
    assert community_report["source_capture"]["api_plan"] == "community"

    capture, quotes, rights = _synthetic_5dollar_bundle(tmp_path)
    capture["api_plan"] = "pro"
    with pytest.raises(PermissionError, match="only an approved"):
        build_manifest_from_private_archive(tmp_path, capture, quotes, rights)


def test_5dollar_adapter_default_rights_manifest_is_hold(tmp_path):
    import json
    import pytest
    from serie_a_v2_5dollar_source_adapter import (
        DEFAULT_RIGHTS_MANIFEST,
        build_manifest_from_private_archive,
    )

    capture, quotes, _ = _synthetic_5dollar_bundle(tmp_path)
    rights = json.loads(DEFAULT_RIGHTS_MANIFEST.read_text(encoding="utf-8"))
    with pytest.raises(PermissionError, match="manifest is HOLD"):
        build_manifest_from_private_archive(tmp_path, capture, quotes, rights)


def test_5dollar_adapter_rejects_public_archive_path(tmp_path):
    import pytest
    from serie_a_v2_5dollar_source_adapter import (
        REPO_ROOT,
        build_manifest_from_private_archive,
    )

    capture, quotes, rights = _synthetic_5dollar_bundle(tmp_path)
    with pytest.raises(ValueError, match="outside the public repository"):
        build_manifest_from_private_archive(REPO_ROOT, capture, quotes, rights)


def test_5dollar_adapter_rejects_target_outcome_fields_and_naive_timestamps(tmp_path):
    import pytest
    from serie_a_v2_5dollar_source_adapter import build_manifest_from_private_archive

    capture, quotes, rights = _synthetic_5dollar_bundle(tmp_path)
    quotes[0]["result"] = "H"
    with pytest.raises(ValueError, match="target outcome fields"):
        build_manifest_from_private_archive(tmp_path, capture, quotes, rights)

    capture, quotes, rights = _synthetic_5dollar_bundle(tmp_path)
    capture["request_started_at_utc"] = "2026-11-12T07:59:59"
    with pytest.raises(ValueError, match="explicit UTC offset"):
        build_manifest_from_private_archive(tmp_path, capture, quotes, rights)


def test_5dollar_adapter_has_no_network_or_supabase_client():
    import ast
    from pathlib import Path
    import serie_a_v2_5dollar_source_adapter as adapter

    source = Path(adapter.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0] + "." + node.module.split(".")[1] if node.module.startswith("urllib.") else node.module.split(".")[0])
    assert not ({"requests", "httpx", "supabase", "aiohttp"} & imported)
    assert "urllib.request" not in imported
    assert "requests.get(" not in source
    assert "create_client(" not in source


def test_5dollar_adapter_validates_all_pages_and_pagination_completeness(tmp_path):
    import hashlib
    import json
    from serie_a_v2_5dollar_source_adapter import build_manifest_from_private_archive

    capture, quotes, rights = _synthetic_5dollar_bundle(tmp_path)
    all_fixtures = json.loads((tmp_path / "page-1.json").read_text())["data"]
    pages = [all_fixtures[:15], all_fixtures[15:]]
    page_records = []
    for number, fixtures in enumerate(pages, start=1):
        payload = {
            "success": 1,
            "data": fixtures,
            "pagination": {
                "page": number,
                "per_page": 100,
                "count": len(fixtures),
                "has_more": number < len(pages),
            },
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        filename = f"page-{number}.json"
        (tmp_path / filename).write_bytes(raw)
        received = (
            "2026-11-12T08:00:00+00:00"
            if number == 1 else "2026-11-12T08:00:01+00:00"
        )
        started = (
            "2026-11-12T07:59:59+00:00"
            if number == 1 else "2026-11-12T08:00:00+00:00"
        )
        page_records.append({
            "page_number": number,
            "file": filename,
            "request_url": (
                "https://api.5dollarfootballapi.com/v1/leagues/3405541143/fixtures"
                f"?season=2026&page={number}&per_page=100"
            ),
            "http_status": 200,
            "request_started_at_utc": started,
            "response_received_at_utc": received,
            "response_sha256": hashlib.sha256(raw).hexdigest(),
            "response_bytes": len(raw),
        })
    capture["page_count"] = 2
    capture["pages"] = page_records
    capture["response_received_at_utc"] = "2026-11-12T08:00:01+00:00"
    capture["captured_at_utc"] = capture["response_received_at_utc"]
    report = build_manifest_from_private_archive(tmp_path, capture, quotes, rights)
    assert report["source_capture"]["page_count"] == 2
    assert report["source_capture"]["source_finished_fixture_count"] == 30

    first_payload = json.loads((tmp_path / "page-1.json").read_text())
    first_payload["pagination"]["has_more"] = False
    bad_raw = json.dumps(first_payload, sort_keys=True, separators=(",", ":")).encode()
    (tmp_path / "page-1.json").write_bytes(bad_raw)
    capture["pages"][0]["response_sha256"] = hashlib.sha256(bad_raw).hexdigest()
    capture["pages"][0]["response_bytes"] = len(bad_raw)
    with pytest.raises(ValueError, match="incomplete or page order"):
        build_manifest_from_private_archive(tmp_path, capture, quotes, rights)


def test_5dollar_adapter_rejects_request_url_with_credentials(tmp_path):
    import pytest
    from serie_a_v2_5dollar_source_adapter import build_manifest_from_private_archive

    capture, quotes, rights = _synthetic_5dollar_bundle(tmp_path)
    capture["pages"][0]["request_url"] += "&token=not-a-real-token"
    with pytest.raises(ValueError, match="credentials must not be embedded"):
        build_manifest_from_private_archive(tmp_path, capture, quotes, rights)


def test_5dollar_adapter_rejects_unconfirmed_finished_status(tmp_path):
    import pytest
    from serie_a_v2_5dollar_source_adapter import build_manifest_from_private_archive

    fixtures = [_synthetic_5dollar_fixture(i) for i in range(30)]
    fixtures[0]["status_code"] = "unknown"
    capture, quotes, rights = _synthetic_5dollar_bundle(tmp_path, fixtures)
    with pytest.raises(ValueError, match="full-time confirmation"):
        build_manifest_from_private_archive(tmp_path, capture, quotes, rights)


def test_5dollar_adapter_requires_30_event_metadata_gate_before_reading_pages(tmp_path):
    import pytest
    from serie_a_v2_5dollar_source_adapter import build_manifest_from_private_archive

    capture, quotes, rights = _synthetic_5dollar_bundle(tmp_path)
    capture.pop("feature_source_gate")
    capture["pages"][0]["file"] = "missing-before-gate.json"
    with pytest.raises(PermissionError, match="feature-source gate"):
        build_manifest_from_private_archive(tmp_path, capture, quotes, rights)

    capture, quotes, rights = _synthetic_5dollar_bundle(tmp_path)
    capture["feature_source_gate"]["observed_completed_primary_events"] = 29
    capture["pages"][0]["file"] = "missing-before-gate.json"
    with pytest.raises(PermissionError, match="fewer than 30"):
        build_manifest_from_private_archive(tmp_path, capture, quotes, rights)


def test_5dollar_adapter_requires_metadata_only_gate_before_request_and_closed_target_gate(tmp_path):
    import pytest
    from serie_a_v2_5dollar_source_adapter import build_manifest_from_private_archive

    capture, quotes, rights = _synthetic_5dollar_bundle(tmp_path)
    capture["feature_source_gate"]["checked_at_utc"] = capture["request_started_at_utc"]
    with pytest.raises(ValueError, match="strictly before the first source request"):
        build_manifest_from_private_archive(tmp_path, capture, quotes, rights)

    capture, quotes, rights = _synthetic_5dollar_bundle(tmp_path)
    capture["feature_source_gate"]["score_or_result_fields_selected_for_gate"] = True
    with pytest.raises(PermissionError, match="feature-source gate"):
        build_manifest_from_private_archive(tmp_path, capture, quotes, rights)

    capture, quotes, rights = _synthetic_5dollar_bundle(tmp_path)
    capture["target_outcome_evaluation_gate"]["outcome_gate_open"] = True
    with pytest.raises(PermissionError, match="target-outcome gate"):
        build_manifest_from_private_archive(tmp_path, capture, quotes, rights)


def test_5dollar_adapter_rejects_unapproved_quote_metadata_fields(tmp_path):
    import pytest
    from serie_a_v2_5dollar_source_adapter import build_manifest_from_private_archive

    capture, quotes, rights = _synthetic_5dollar_bundle(tmp_path)
    quotes[0]["full_time_score"] = "2-0"
    with pytest.raises(ValueError, match="unapproved fields"):
        build_manifest_from_private_archive(tmp_path, capture, quotes, rights)


def test_5dollar_adapter_rejects_page_timestamps_outside_capture_window(tmp_path):
    import pytest
    from serie_a_v2_5dollar_source_adapter import build_manifest_from_private_archive

    capture, quotes, rights = _synthetic_5dollar_bundle(tmp_path)
    capture["pages"][0]["request_started_at_utc"] = "2026-11-12T07:59:58+00:00"
    with pytest.raises(ValueError, match="outside the capture window"):
        build_manifest_from_private_archive(tmp_path, capture, quotes, rights)
