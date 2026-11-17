from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from pathlib import Path

import pandas as pd
import pytest

from historical_football_signal_lab import (
    FEATURE_SETS,
    add_difference_features,
    build_point_in_time_features,
)
from serie_a_v2_footiqo_manual_intake import (
    EXPECTED_CANDIDATE_SHA256,
    MIN_CURRENT_SEASON_FIXTURE_IDENTITIES,
    REPOSITORY_ROOT,
    _normalise_source,
    build_manifest_from_capture,
    capture_manual_export,
    load_frozen_contract,
    load_manual_rights,
)

NOW = datetime(2026, 11, 10, 10, 0, tzinfo=timezone.utc)
QUOTE = {
    "event_id": "footiqo-test-event",
    "league": "SERIE_A",
    "home_team": "Alpha",
    "away_team": "Beta",
    "commence_time_utc": "2026-11-10T15:00:00Z",
    "snapshot_time_utc": "2026-11-10T11:00:00Z",
}


def gate_csv(rows: int = 30) -> bytes:
    data = [
        {
            "match_date": f"2026-10-{i + 1:02d}",
            "home_team": f"Gate Home {i}",
            "away_team": f"Gate Away {i}",
        }
        for i in range(rows)
    ]
    return pd.DataFrame(data, columns=["match_date", "home_team", "away_team"]).to_csv(
        index=False
    ).encode()


def source_csv() -> bytes:
    rows = [
        ("01/11/2026", "Alpha", "Gamma", 2, 0, "H", 5, 2, 1, 0),
        ("02/11/2026", "Beta", "Delta", 0, 1, "A", 2, 4, 0, 1),
        ("03/11/2026", "Gamma", "Alpha", 1, 1, "D", 3, 3, 2, 2),
        ("04/11/2026", "Delta", "Beta", 0, 2, "A", 1, 5, 1, 0),
        ("05/11/2026", "Alpha", "Delta", 3, 1, "H", 6, 2, 0, 1),
        ("06/11/2026", "Beta", "Gamma", 2, 2, "D", 4, 4, 2, 1),
    ]
    columns = [
        "Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR",
        "HCFT", "ACFT", "HYCFT", "AYCFT",
    ]
    return pd.DataFrame(rows, columns=columns).to_csv(index=False).encode()


def capture(tmp_path: Path, *, gate: bytes | None = None, source: bytes | None = None):
    source_path = tmp_path / "footiqo-manual.csv"
    gate_path = tmp_path / "metadata-only-gate.csv"
    source_path.write_bytes(source if source is not None else source_csv())
    gate_path.write_bytes(gate if gate is not None else gate_csv())
    archive = capture_manual_export(
        source_csv=source_path,
        gate_metadata_csv=gate_path,
        private_store_dir=tmp_path / "private",
        manual_export_confirmed=True,
        noncommercial_research_confirmed=True,
        private_storage_confirmed=True,
        now=NOW,
    )
    return archive


def test_exact_frozen_v2_and_footiqo_manual_rights_are_pinned():
    contract = load_frozen_contract()
    rights = load_manual_rights()
    assert contract["candidate"]["artifact_sha256"] == EXPECTED_CANDIDATE_SHA256
    assert contract["features"] == FEATURE_SETS["ALL_FOOTBALL"]
    assert len(contract["features"]) == 19
    assert contract["candidate"]["active_lambda"] == 0.0
    assert contract["candidate"]["shadow_residual_lambda"] == 1.0
    assert contract["candidate"]["stability_gate_passed"] is False
    assert rights["manifest"]["decision"] == "HOLD"
    assert rights["manifest"]["rights"]["dataset_policy_permits_manual_exports"] is True
    assert rights["manifest"]["rights"]["explicit_commercial_product_use_permission"] is False


def test_metadata_only_gate_requires_30_unique_current_season_fixture_identities_before_source_read(tmp_path):
    gate_path = tmp_path / "gate.csv"
    gate_path.write_bytes(gate_csv(MIN_CURRENT_SEASON_FIXTURE_IDENTITIES - 1))
    missing_source = tmp_path / "source-does-not-exist.csv"

    with pytest.raises(ValueError, match="feature-input gate closed"):
        capture_manual_export(
            source_csv=missing_source,
            gate_metadata_csv=gate_path,
            private_store_dir=tmp_path / "private",
            manual_export_confirmed=True,
            noncommercial_research_confirmed=True,
            private_storage_confirmed=True,
            now=NOW,
        )


def test_gate_rejects_any_score_or_result_column_before_opening_source(tmp_path):
    gate = pd.read_csv(pd.io.common.BytesIO(gate_csv()))
    gate["result"] = "H"
    gate_path = tmp_path / "gate-with-outcome.csv"
    gate.to_csv(gate_path, index=False)
    missing_source = tmp_path / "source-does-not-exist.csv"

    with pytest.raises(ValueError, match="exactly match_date,home_team,away_team"):
        capture_manual_export(
            source_csv=missing_source,
            gate_metadata_csv=gate_path,
            private_store_dir=tmp_path / "private",
            manual_export_confirmed=True,
            noncommercial_research_confirmed=True,
            private_storage_confirmed=True,
            now=NOW,
        )



def test_metadata_gate_rejects_pre_2026_27_fixtures_before_opening_source(tmp_path):
    gate = pd.read_csv(pd.io.common.BytesIO(gate_csv()))
    gate["match_date"] = "2026-06-30"
    gate_path = tmp_path / "preseason-gate.csv"
    gate.to_csv(gate_path, index=False)
    missing_source = tmp_path / "source-does-not-exist.csv"

    with pytest.raises(ValueError, match="before current 2026/27 season start"):
        capture_manual_export(
            source_csv=missing_source,
            gate_metadata_csv=gate_path,
            private_store_dir=tmp_path / "private",
            manual_export_confirmed=True,
            noncommercial_research_confirmed=True,
            private_storage_confirmed=True,
            now=NOW,
        )


@pytest.mark.parametrize("bad_date", ["2026-10-01T12:00:00Z", "2026-10-01suffix", "2026-1-1"])
def test_metadata_gate_rejects_noncanonical_or_timestamp_dates_before_opening_source(tmp_path, bad_date):
    gate = pd.read_csv(pd.io.common.BytesIO(gate_csv()))
    gate.loc[0, "match_date"] = bad_date
    gate_path = tmp_path / "noncanonical-gate.csv"
    gate.to_csv(gate_path, index=False)
    missing_source = tmp_path / "source-does-not-exist.csv"

    with pytest.raises(ValueError, match="canonical YYYY-MM-DD"):
        capture_manual_export(
            source_csv=missing_source,
            gate_metadata_csv=gate_path,
            private_store_dir=tmp_path / "private",
            manual_export_confirmed=True,
            noncommercial_research_confirmed=True,
            private_storage_confirmed=True,
            now=NOW,
        )

def test_manual_noncommercial_private_confirmations_are_mandatory(tmp_path):
    source_path = tmp_path / "source.csv"
    gate_path = tmp_path / "gate.csv"
    with pytest.raises(ValueError, match="confirmations are required"):
        capture_manual_export(
            source_csv=source_path,
            gate_metadata_csv=gate_path,
            private_store_dir=tmp_path / "private",
            manual_export_confirmed=False,
            noncommercial_research_confirmed=True,
            private_storage_confirmed=True,
            now=NOW,
        )


def test_capture_archives_exact_raw_and_gate_bytes_outside_repository_with_sha(tmp_path):
    source = source_csv()
    gate = gate_csv()
    archive = capture(tmp_path, gate=gate, source=source)
    manifest = __import__("json").loads((archive / "manifest.json").read_text())

    assert archive.is_dir()
    assert (archive / "raw_source.csv").read_bytes() == source
    assert (archive / "gate_metadata.csv").read_bytes() == gate
    assert manifest["raw_source_sha256"] == hashlib.sha256(source).hexdigest()
    assert manifest["gate_metadata_sha256"] == hashlib.sha256(gate).hexdigest()
    assert manifest["gate_summary"]["canonical_unique_current_season_fixture_identities"] == 30
    assert manifest["gate_summary"]["current_season_start"] == "2026-07-01"
    assert manifest["gate_summary"]["completion_status_independently_verified"] is False
    assert manifest["gate_summary"]["primary_competition_independently_verified"] is False
    assert manifest["gate_summary"]["evaluation_outcome_gate_satisfied"] is False
    assert manifest["source_summary"]["completed_prior_day_rows"] == 6
    assert manifest["manual_export"] is True
    assert manifest["automated_access"] is False
    assert manifest["eligible_for_product_publication"] is False
    assert REPOSITORY_ROOT.resolve() not in archive.resolve().parents


def test_gate_canonicalises_atalanta_alias_without_inflating_unique_event_count(tmp_path):
    base = pd.read_csv(pd.io.common.BytesIO(gate_csv()))
    duplicate = pd.DataFrame([{
        "match_date": "2026-10-01",
        "home_team": "Atalanta BC",
        "away_team": "Gate Away 0",
    }])
    base.loc[0, "home_team"] = "Atalanta"
    base.loc[0, "away_team"] = "Gate Away 0"
    combined = pd.concat([base, duplicate], ignore_index=True)
    archive = capture(tmp_path, gate=combined.to_csv(index=False).encode())
    manifest = __import__("json").loads((archive / "manifest.json").read_text())
    assert manifest["gate_summary"]["raw_metadata_rows"] == 31
    assert manifest["gate_summary"]["canonical_unique_current_season_fixture_identities"] == 30
    assert manifest["gate_summary"]["current_season_start"] == "2026-07-01"
    assert manifest["gate_summary"]["completion_status_independently_verified"] is False
    assert manifest["gate_summary"]["primary_competition_independently_verified"] is False
    assert manifest["gate_summary"]["evaluation_outcome_gate_satisfied"] is False


def test_feature_vector_preserves_original_19_order_and_leaves_two_red_features_missing(tmp_path):
    archive = capture(tmp_path)
    report = build_manifest_from_capture(archive, [QUOTE])
    row = report["feature_rows"][0]

    assert report["candidate_sha256"] == EXPECTED_CANDIDATE_SHA256
    assert report["feature_count"] == 19
    assert row["feature_order"] == FEATURE_SETS["ALL_FOOTBALL"]
    assert list(row["features"]) == FEATURE_SETS["ALL_FOOTBALL"]
    assert row["features"]["diff_red_5"] is None
    assert row["features"]["diff_red_10"] is None
    assert row["observed_frozen_feature_count"] <= 17
    assert row["median_imputed_frozen_feature_count"] >= 2
    assert row["source_archive_before_quote_verified"] is False
    assert row["project_possession_before_quote_verified"] is False
    assert row["local_archive_ordering_consistent"] is True
    assert row["timestamp_attestation_verified"] is False
    assert row["source_before_quote_verified"] is False
    assert row["upstream_observation_time_verified"] is False
    assert row["information_time_independently_attested"] is False
    assert report["metadata_gate_attestation_level"] == "operator_supplied_local_metadata_csv_not_supabase_authenticated"
    assert report["feature_input_gate_completion_status_independently_verified"] is False
    assert report["feature_input_gate_primary_competition_independently_verified"] is False
    assert report["evaluation_outcome_gate_opened"] is False
    assert row["feature_input_outcomes_used"] is True
    assert row["target_quote_outcomes_read"] is False
    assert row["probabilities_generated"] is False
    assert row["model_weights_applied"] is False
    assert report["active_lambda"] == 0.0
    assert report["shadow_residual_lambda"] == 1.0
    assert report["eligible_for_frozen_prospective_cohort"] is False
    assert report["eligible_for_product_publication"] is False


def test_unattested_mutable_manifest_never_claims_verified_source_before_quote(tmp_path):
    archive = capture(tmp_path)
    manifest_path = archive / "manifest.json"
    manifest = __import__("json").loads(manifest_path.read_text())
    # Local manifest timestamps can be edited; they are not a trusted timestamp authority.
    manifest["source_received_at_utc"] = "2026-11-10T10:01:00+00:00"
    manifest["archive_published_at_utc"] = "2026-11-10T10:02:00+00:00"
    manifest_path.write_text(__import__("json").dumps(manifest, sort_keys=True))

    report = build_manifest_from_capture(archive, [QUOTE])
    row = report["feature_rows"][0]
    assert row["local_archive_ordering_consistent"] is True
    assert row["timestamp_attestation_verified"] is False
    assert row["source_archive_before_quote_verified"] is False
    assert row["project_possession_before_quote_verified"] is False
    assert row["source_before_quote_verified"] is False
    assert row["eligible_for_frozen_prospective_cohort"] is False


def test_manifest_cannot_claim_external_timestamp_attestation(tmp_path):
    archive = capture(tmp_path)
    manifest_path = archive / "manifest.json"
    manifest = __import__("json").loads(manifest_path.read_text())
    manifest["timestamp_attestation_verified"] = True
    manifest_path.write_text(__import__("json").dumps(manifest, sort_keys=True))

    with pytest.raises(ValueError, match="unsafe rights/provenance classification"):
        build_manifest_from_capture(archive, [QUOTE])


def test_manual_features_match_original_builder_for_all_supported_fields(tmp_path):
    archive = capture(tmp_path)
    report = build_manifest_from_capture(archive, [QUOTE])
    actual = report["feature_rows"][0]["features"]
    raw = (archive / "raw_source.csv").read_bytes()
    normalised, _ = _normalise_source(raw, received_at=NOW)
    original_history = normalised.drop(columns=["_match_date"]).copy()
    target = pd.DataFrame([{
        "Date": "10/11/2026",
        "HomeTeam": "Alpha",
        "AwayTeam": "Beta",
        "FTHG": 0,
        "FTAG": 0,
        "FTR": "D",
        "HC": 0,
        "AC": 0,
        "HY": 0,
        "AY": 0,
        "HR": float("nan"),
        "AR": float("nan"),
    }])
    original = add_difference_features(build_point_in_time_features(
        pd.concat([original_history, target], ignore_index=True),
        "SERIE_A",
        "SYNTHETIC_FOOTIQO_PARITY_ONLY",
    )).iloc[-1]

    for feature in FEATURE_SETS["ALL_FOOTBALL"]:
        expected = original[feature]
        if pd.isna(expected):
            assert actual[feature] is None
        else:
            assert actual[feature] == pytest.approx(float(expected), abs=1e-12)


def test_same_day_source_rows_are_excluded_because_no_kickoff_clock_exists(tmp_path):
    source = pd.read_csv(pd.io.common.BytesIO(source_csv()))
    source.loc[len(source)] = [
        "10/11/2026", "Alpha", "Beta", 9, 0, "H", 10, 0, 0, 0
    ]
    archive = capture(tmp_path, source=source.to_csv(index=False).encode())
    manifest = __import__("json").loads((archive / "manifest.json").read_text())
    assert manifest["source_summary"]["same_day_rows_excluded_without_kickoff_clock"] == 1
    report = build_manifest_from_capture(archive, [QUOTE])
    assert report["feature_rows"][0]["features"]["diff_red_5"] is None


def test_source_archive_must_precede_quote_and_quote_must_precede_kickoff(tmp_path):
    archive = capture(tmp_path)
    same_time = {**QUOTE, "snapshot_time_utc": "2026-11-10T10:00:00Z"}
    with pytest.raises(ValueError, match="strictly before quote"):
        build_manifest_from_capture(archive, [same_time])

    after_kickoff = {**QUOTE, "snapshot_time_utc": "2026-11-10T16:00:00Z"}
    with pytest.raises(ValueError, match="at/after kickoff"):
        build_manifest_from_capture(archive, [after_kickoff])


def test_quote_input_rejects_protected_target_outcome_fields(tmp_path):
    archive = capture(tmp_path)
    contaminated = {**QUOTE, "home_goals": 2, "away_goals": 0}
    with pytest.raises(ValueError, match="protected outcome fields"):
        build_manifest_from_capture(archive, [contaminated])


def test_tampered_manual_source_bytes_fail_sha_before_feature_build(tmp_path):
    archive = capture(tmp_path)
    raw_path = archive / "raw_source.csv"
    raw_path.write_bytes(raw_path.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="source archive SHA256 mismatch"):
        build_manifest_from_capture(archive, [QUOTE])


def test_inconsistent_score_result_and_duplicate_fixture_fail_closed(tmp_path):
    bad = pd.read_csv(pd.io.common.BytesIO(source_csv()))
    bad.loc[0, "FTR"] = "A"
    with pytest.raises(ValueError, match="does not match goals"):
        _normalise_source(bad.to_csv(index=False).encode(), received_at=NOW)

    duplicate = pd.concat([
        pd.read_csv(pd.io.common.BytesIO(source_csv())),
        pd.read_csv(pd.io.common.BytesIO(source_csv())).iloc[[0]],
    ], ignore_index=True)
    with pytest.raises(ValueError, match="identity collision"):
        _normalise_source(duplicate.to_csv(index=False).encode(), received_at=NOW)


def test_manual_intake_has_no_network_or_database_client_imports():
    source = (REPOSITORY_ROOT / "serie_a_v2_footiqo_manual_intake.py").read_text()
    assert "import requests" not in source
    assert "from requests" not in source
    assert "import supabase" not in source
    assert "from supabase" not in source
    assert "create_client(" not in source
    assert "urllib" not in source
