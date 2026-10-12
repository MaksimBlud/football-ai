"""Public static history fallback: reproducible, read-only product MVP contract."""
import json
import math
from pathlib import Path
import re
import shutil
import subprocess

from product_reliability import (
    MIN_CALENDAR_MONTHS_FOR_REVIEW,
    MIN_SETTLED_FIXTURES_FOR_REVIEW,
    wilson_interval,
)

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "static/public_history_snapshot.json"
HISTORY = ROOT / "static/history.html"
APP = ROOT / "web_app.py"
EXPECTED_SHA = "1e516fe91420fdc2d6479e9fb92b005c4a0c75c7f0f217493dd6b27fd64d99a5"


def test_dated_frozen_history_has_no_private_results_or_fake_profit():
    doc = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert doc["schema_version"] == "public-product-history.v1"
    assert doc["source_mode"] == "verified_static_snapshot"
    assert doc["league"] == "EPL" and doc["market"] == "1x2"
    assert doc["as_of_utc"] == "2026-10-12T03:01:11.309155+00:00"
    assert doc["events"] == {
        "prediction_registered": 40, "market_observed": 29, "settled": 29
    }
    assert doc["settled_unique_fixtures"] == 29
    assert doc["policy"]["minimum_settled_fixtures_for_review"] == MIN_SETTLED_FIXTURES_FOR_REVIEW == 100
    assert doc["policy"]["minimum_calendar_months_for_review"] == MIN_CALENDAR_MONTHS_FOR_REVIEW == 4
    assert doc["policy"]["reliability_verdict"] == "INCONCLUSIVE"
    assert doc["policy"]["betting_action"] == "NO_BET"
    assert doc["policy"]["roi"] is None
    assert doc["policy"]["clv"] is None
    assert doc["policy"]["staking"] is None
    assert doc["policy"]["automatic_model_promotion"] is False
    assert doc["policy"]["contains_raw_outcomes"] is False
    assert doc["verification"]["data_refresh"].startswith("manual_reviewed_snapshot")
    assert doc["verification"]["mismatched_recorded_scores"] == 0
    assert doc["verification"]["invalid_pre_match_probabilities"] == 0
    forbidden = (
        '"actual_outcome"', '"product_match_id"', '"event_id"', '"home_team"',
        '"away_team"', '"home_goals"', '"away_goals"', '"service_role"',
        '"source_prediction_snapshot_id"', '"payload"', '"raw_odds"',
        '"pnl"', '"bet_result"', '"individual_fixtures"',
    )
    public = SNAPSHOT.read_text(encoding="utf-8")
    for name in forbidden:
        assert name not in public


def test_snapshot_aggregates_reconcile_with_frozen_product_gate():
    doc = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    scopes = doc["model_scopes"]
    assert len(scopes) == 1
    s = scopes[0]
    assert s["league"] == "EPL"
    assert s["model_1x2_sha256"] == EXPECTED_SHA
    assert re.fullmatch("[0-9a-f]{64}", s["model_1x2_sha256"])
    assert s["settled_unique_fixtures"] == 29
    assert s["correct_picks"] == 10
    assert math.isclose(s["accuracy"], 10 / 29, rel_tol=1e-12)
    assert math.isclose(s["multiclass_brier"], 0.674421440939774, rel_tol=1e-12)
    assert math.isclose(s["log_loss"], 1.1083571968605447, rel_tol=1e-12)
    assert s["reviewable"] is False
    assert s["evidence_state"] == "ACCUMULATING_SAMPLE"
    assert s["reliability_status"] == "INCONCLUSIVE"
    assert s["accuracy_wilson_95"]["lower"] < s["accuracy"] < s["accuracy_wilson_95"]["upper"]
    bounds = wilson_interval(10, 29)
    assert math.isclose(s["accuracy_wilson_95"]["lower"], bounds[0], rel_tol=1e-10)
    assert math.isclose(s["accuracy_wilson_95"]["upper"], bounds[1], rel_tol=1e-10)
    assert s["first_kickoff_utc"] == "2026-09-12T14:00:00+00:00"
    assert s["last_kickoff_utc"] == "2026-10-11T15:30:00+00:00"
    assert doc["verification"]["unique_settled_match_ids"] == doc["settled_unique_fixtures"]
    assert doc["verification"]["unique_settled_prediction_ids"] == doc["settled_unique_fixtures"]
    assert sum(s["settled_unique_fixtures"] for s in scopes) == doc["settled_unique_fixtures"]


def test_http_public_aggregate_file_is_separate_from_private_lifecycle():
    server = APP.read_text(encoding="utf-8")
    assert '@app.get("/history")' in server
    assert '@app.get("/public-history-snapshot")' in server
    assert 'return FileResponse(\n        "static/public_history_snapshot.json",' in server
    assert 'media_type="application/json"' in server
    assert '"Cache-Control": "no-cache, max-age=0"' in server
    assert '@app.get("/product-history")' in server
    assert "return load_public_product_history(_private_lifecycle_client())" in server
    assert 'SUPABASE_KEY == SUPABASE_PUBLISHABLE_KEY' in server
    assert "status_code=503" in server
    assert "create_client(SUPABASE_URL, SUPABASE_KEY)" in server


def test_browser_only_uses_fallback_when_private_server_reports_503():
    html = HISTORY.read_text(encoding="utf-8")
    assert "fetch('/product-history',{cache:'no-store'})" in html
    assert "if(response.status!==503)throw new Error('history HTTP '+response.status);" in html
    assert "fetch('/public-history-snapshot',{cache:'no-store'})" in html
    assert "data.source_mode!=='verified_static_snapshot'" in html
    assert "data.verification?.mismatched_recorded_scores!==0" in html
    assert "data.verification?.unique_settled_match_ids!==data.settled_unique_fixtures" in html
    assert "data.model_scopes.reduce(" in html
    assert "Date.parse(data.as_of_utc)>Date.now()+60000" in html
    assert "СОХРАНЁННЫЙ СРЕЗ, НЕ LIVE" in html
    assert "не обновляются онлайн" in html
    assert "Точность 1X2 не доказывает преимущество над букмекером" in html
    assert "return data;" in html
    assert "Неподтверждённые показатели не отображаются" in html
    assert "document.createElement(" in html
    assert "innerHTML" not in html


def test_frontend_javascript_syntax_and_fetch_contract(tmp_path):
    if shutil.which("node") is None:
        return
    html = HISTORY.read_text(encoding="utf-8")
    src = re.search(r"<script>(.*?)</script>", html, re.S)
    assert src
    f = tmp_path / "history_fallback.js"
    f.write_text(src.group(1), encoding="utf-8")
    out = subprocess.run(["node", "--check", str(f)], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
