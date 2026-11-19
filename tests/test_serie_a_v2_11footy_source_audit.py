import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "research" / "source_rights" / "11footy.json"
CANDIDATE_PATH = ROOT / "research" / "models" / "market_anchor_v2_serie_a_frozen_candidate.json"
AUDIT_PATH = ROOT / "research" / "SERIE_A_V2_11FOOTY_SOURCE_AUDIT_20261119.md"


def load_manifest():
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def test_11footy_remains_hold_for_rights_and_commercial_scope():
    manifest = load_manifest()
    rights = manifest["license_and_rights"]

    assert manifest["decision"] == "HOLD"
    assert rights["declared_license"] == "CC BY-NC 4.0"
    assert rights["noncommercial_use_only"] is True
    assert rights["commercial_use_authorized"] is False
    assert rights["upstream_rights_resolved"] is False
    assert rights["upstream_provider_names_disclosed"] is False
    assert rights["written_clearance_for_serie_a_report_or_feed_layers"] is False


def test_structural_mapping_covers_exact_frozen_19_feature_order():
    manifest = load_manifest()
    candidate = json.loads(CANDIDATE_PATH.read_text(encoding="utf-8"))
    frozen = manifest["original_v2"]
    mapping = manifest["feature_compatibility"]["feature_sources"]

    assert candidate["artifact_sha256"] == frozen["candidate_sha256"]
    assert candidate["features"] == frozen["features"]
    assert len(candidate["features"]) == 19
    assert list(mapping) == candidate["features"]
    assert len(mapping) == len(set(mapping))

    for feature, source in mapping.items():
        if feature.startswith(("diff_points_", "diff_goals_")):
            assert source["table"] == "matches"
            assert set(source["source_columns"]) >= {"home_goals", "away_goals"}
        else:
            assert source["table"] == "match_team_statistics"
            assert source["layer"] == "report"
            assert source["join"].startswith("match_team_statistics.match_id")

    assert sum(f.startswith("diff_points_") for f in mapping) == 3
    assert sum(f.startswith("diff_goals_") for f in mapping) == 6
    assert sum(f.startswith("diff_corners_") for f in mapping) == 6
    assert sum(f.startswith("diff_yellow_") for f in mapping) == 2
    assert sum(f.startswith("diff_red_") for f in mapping) == 2


def test_release_integrity_metadata_is_not_misrepresented_as_download_verification():
    manifest = load_manifest()
    integrity = manifest["source_integrity"]
    assets = manifest["release_assets"]

    assert integrity["sha256_manifest_present"] is True
    assert integrity["github_release_asset_digest_matches_manifest_for_serie_a_csv_zip"] is True
    assert integrity["github_release_asset_digest_matches_manifest_for_serie_a_db_xz"] is True
    assert integrity["signature_asset_present"] is True
    assert integrity["signature_verification_key_published_in_repository_tree"] is False
    assert integrity["downloaded_asset_bytes_verified"] is False
    assert integrity["project_private_archive_created"] is False
    assert integrity["source_before_quote_proven"] is False
    assert assets["italy.serie-a.csv.zip"]["github_asset_sha256"] == (
        assets["italy.serie-a.csv.zip"]["sha256sums_sha256"]
    )


def test_current_release_fails_the_frozen_24_hour_source_age_limit():
    manifest = load_manifest()
    freshness = manifest["freshness"]

    assert freshness["frozen_source_max_age_hours"] == 24
    assert freshness["release_age_hours_at_audit"] > 24
    assert freshness["passes_frozen_source_freshness_limit"] is False
    assert freshness["current_release_freshness_status"] == "STALE_OVER_24_HOURS"
    assert manifest["upstream_repository"]["documented_rebuild_cadence"] == (
        "after each round of matches"
    )


def test_original_candidate_and_safety_controls_are_unchanged():
    manifest = load_manifest()
    candidate = json.loads(CANDIDATE_PATH.read_text(encoding="utf-8"))
    original = manifest["original_v2"]
    actions = manifest["non_actions"]

    assert original["candidate_sha256"] == candidate["artifact_sha256"]
    assert original["training_fingerprint_sha256"] == (
        "f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098"
    )
    assert original["weight_matrix_shape"] == [20, 2]
    assert candidate["active_lambda"] == original["active_lambda"] == 0
    assert candidate["shadow_residual_lambda"] == original["shadow_residual_lambda"] == 1
    assert original["stability_gate_passed"] is False
    assert original["evaluation_gate"] == "CLOSED_0_OF_30"
    assert original["automatic_promotion"] is False

    assert actions["dataset_asset_downloads"] == 0
    assert actions["provider_api_requests"] == 0
    assert actions["supabase_reads"] == 0
    assert actions["supabase_writes"] == 0
    assert actions["supabase_ddl"] == 0
    assert actions["protected_2026_27_outcomes_read"] is False
    assert actions["feature_calculations"] == 0
    assert actions["inference_runs"] == 0
    assert actions["training_or_refit"] is False
    assert actions["production_pickle_changes"] is False
    assert actions["main_changes"] == 0
    assert actions["merges"] == 0
    assert actions["schedule_changes"] == 0
    assert actions["other_agent_settings_changes"] == 0


def test_audit_and_workflow_explicitly_describe_hold_without_live_access():
    document = AUDIT_PATH.read_text(encoding="utf-8")
    manifest = load_manifest()

    assert "HOLD" in document
    assert "CC BY-NC 4.0" in document
    assert "212.667 hours" in document
    assert "source-before-quote" in document
    assert "No dataset asset was downloaded" in document
    assert manifest["decision"] == "HOLD"
