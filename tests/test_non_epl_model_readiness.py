import json
from pathlib import Path

import non_epl_model_readiness as readiness


def _evidence(root: Path, league: str):
    c=readiness.LEAGUES[league]
    for key in ("data","pit","norm","oos","market"):
        for rel in c[key]:
            p=root/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_text("evidence\n")
    if c.get("builder"):
        (root/c["builder"]).write_text("# builder\n")


def test_matrix_covers_all_eight_and_selects_la_liga():
    matrix=readiness.build_matrix()
    assert {r["league"] for r in matrix["rows"]}=={
        "LA_LIGA","SERIE_A","BUNDESLIGA","LIGUE_1","EREDIVISIE","RPL","PRIMEIRA_LIGA","SUPER_LIG"
    }
    assert matrix["recommended_first_league"]=="LA_LIGA"
    assert matrix["prospective_outcomes_read"] is False
    assert matrix["paid_provider_requests"]==0
    assert all(r["statuses"]["PROSPECTIVE_READY"] is False for r in matrix["rows"])


def test_la_liga_foundation_ready_but_artifact_layers_fail_closed():
    row=readiness.audit_league("LA_LIGA")
    for key in ("DATA_READY","PIT_READY","NORMALIZATION_READY","OOS_READY","MARKET_READY"):
        assert row["statuses"][key] is True
    assert row["candidate_builder_ready"] is True
    for key in ("MODEL_READY","CALIBRATION_READY","PROVENANCE_READY","PROSPECTIVE_READY"):
        assert row["statuses"][key] is False


def test_rpl_market_does_not_override_missing_history():
    row=readiness.audit_league("RPL")
    assert row["historical_seasons"]==0
    assert row["statuses"]["DATA_READY"] is False
    assert row["statuses"]["PIT_READY"] is False
    assert row["statuses"]["OOS_READY"] is False
    assert row["statuses"]["MARKET_READY"] is True


def test_valid_candidate_manifest_opens_only_non_prospective_layers(tmp_path):
    _evidence(tmp_path,"LA_LIGA")
    p=tmp_path/"artifacts/candidates/la_liga/manifest.json"; p.parent.mkdir(parents=True)
    p.write_text(json.dumps({
        "league":"LA_LIGA","model_artifact_sha256":"a"*64,"calibrator_sha256":"b"*64,
        "code_commit_sha":"c"*40,"historical_cutoff":"2026-05-24","feature_schema_sha256":"d"*64,
        "oos_validation":{"status":"PASSED"},"calibration":{"status":"PASSED"}
    }))
    row=readiness.audit_league("LA_LIGA",tmp_path)
    for key in ("MODEL_READY","CALIBRATION_READY","PROVENANCE_READY"):
        assert row["statuses"][key] is True
    assert row["statuses"]["PROSPECTIVE_READY"] is False
