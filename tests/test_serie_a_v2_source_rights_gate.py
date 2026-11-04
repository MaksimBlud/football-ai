from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from serie_a_v2_source_rights import (
    BLOCKED_CODE,
    POLICY_SCHEMA,
    require_original_v2_source_rights,
)

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "research" / "market_anchor_1x2_v2_source_rights.json"
LIVE_ENTRYPOINTS = (
    "serie_a_v2_current_form_source_capture.py",
    "serie_a_v2_current_form_forward_capture.py",
    "serie_a_v2_live_diagnostic_report.py",
    "serie_a_v2_forward_capture.py",
)
LIVE_WORKFLOWS = {
    ".github/workflows/serie-a-v2-current-form-source-capture.yml": "50 5 * * *",
    ".github/workflows/serie-a-v2-free-real-quote-diagnostic.yml": "13 6 * * *",
    ".github/workflows/serie-a-v2-current-form-forward-preview.yml": "18 8 * * *",
    ".github/workflows/serie-a-v2-forward-preview.yml": "8 8 * * *",
}


def _authorized_policy() -> dict:
    return {
        "schema_version": POLICY_SCHEMA,
        "experiment_scope": "MARKET_ANCHOR_1X2_V2",
        "provider": "FOOTBALL_DATA_CSV",
        "provider_policy_url": "https://football-data.co.uk/contact.php",
        "rights_status": "GRANTED",
        "ai_feature_inference_permitted": True,
        "automated_source_archiving_permitted": True,
        "authorized_purposes": [
            "AI_FEATURE_INFERENCE",
            "AUTOMATED_SOURCE_ARCHIVE",
        ],
        "authorized_source_scopes": [
            "HISTORICAL_SEASON_CSVS",
            "CURRENT_SEASON_LAGGED_FEATURE_CSV",
        ],
        "authorization_reference": "provider-written-authorization-reference",
    }


def test_checked_in_policy_is_not_granted_and_live_use_fails_closed():
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    assert policy["rights_status"] == "NOT_GRANTED"
    assert policy["ai_feature_inference_permitted"] is False
    assert policy["automated_source_archiving_permitted"] is False
    assert policy["authorization_reference"] is None
    with pytest.raises(RuntimeError, match=BLOCKED_CODE):
        require_original_v2_source_rights()


def test_explicit_scoped_authorization_is_required(tmp_path):
    policy = _authorized_policy()
    path = tmp_path / "rights.json"
    path.write_text(json.dumps(policy), encoding="utf-8")
    assert require_original_v2_source_rights(path) == policy

    for mutation in (
        {"rights_status": "NOT_GRANTED"},
        {"ai_feature_inference_permitted": False},
        {"automated_source_archiving_permitted": False},
        {"authorized_purposes": ["AI_FEATURE_INFERENCE"]},
        {"authorized_source_scopes": ["HISTORICAL_SEASON_CSVS"]},
        {"authorization_reference": None},
    ):
        denied = {**policy, **mutation}
        path.write_text(json.dumps(denied), encoding="utf-8")
        with pytest.raises(RuntimeError, match=BLOCKED_CODE):
            require_original_v2_source_rights(path)


def test_missing_or_malformed_policy_fails_closed(tmp_path):
    with pytest.raises(RuntimeError, match=BLOCKED_CODE):
        require_original_v2_source_rights(tmp_path / "missing.json")
    malformed = tmp_path / "malformed.json"
    malformed.write_text("{", encoding="utf-8")
    with pytest.raises(RuntimeError, match=BLOCKED_CODE):
        require_original_v2_source_rights(malformed)


def test_every_live_v2_entrypoint_checks_rights_before_side_effects():
    for relative in LIVE_ENTRYPOINTS:
        source = (ROOT / relative).read_text(encoding="utf-8")
        tree = ast.parse(source)
        main = next(
            node for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == "main"
        )
        first = main.body[0]
        assert isinstance(first, ast.Expr), relative
        assert isinstance(first.value, ast.Call), relative
        assert isinstance(first.value.func, ast.Name), relative
        assert first.value.func.id == "require_original_v2_source_rights", relative
        assert not first.value.args and not first.value.keywords, relative
        assert "from serie_a_v2_source_rights import require_original_v2_source_rights" in source


def test_live_workflows_require_rights_and_keep_existing_cron_times():
    for relative, cron in LIVE_WORKFLOWS.items():
        source = (ROOT / relative).read_text(encoding="utf-8")
        assert "vars.MARKET_ANCHOR_V2_SOURCE_RIGHTS_STATUS == 'GRANTED'" in source
        assert "github.event_name != 'push'" in source
        assert f'cron: "{cron}"' in source
