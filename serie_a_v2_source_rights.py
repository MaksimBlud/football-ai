"""Fail-closed rights gate for original MARKET_ANCHOR_1X2_V2 source use.

This gate is deliberately separate from the frozen model and protocol. It
requires documented permission for both automated source archiving and AI
feature inference before any live V2 source/forward entry point can proceed.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_POLICY_PATH = (
    Path(__file__).resolve().parent
    / "research"
    / "market_anchor_1x2_v2_source_rights.json"
)
POLICY_SCHEMA = "MARKET_ANCHOR_1X2_V2_SOURCE_RIGHTS_V1"
BLOCKED_CODE = "SOURCE_RIGHTS_BLOCKED_NO_NETWORK_NO_INFERENCE"
REQUIRED_PURPOSES = frozenset({
    "AI_FEATURE_INFERENCE",
    "AUTOMATED_SOURCE_ARCHIVE",
})
REQUIRED_SOURCE_SCOPES = frozenset({
    "HISTORICAL_SEASON_CSVS",
    "CURRENT_SEASON_LAGGED_FEATURE_CSV",
})


def require_original_v2_source_rights(
    policy_path: Path = DEFAULT_POLICY_PATH,
) -> dict[str, Any]:
    """Require explicit, scoped permission; otherwise fail before external I/O."""
    try:
        policy = json.loads(Path(policy_path).read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        raise RuntimeError(BLOCKED_CODE) from None

    if not isinstance(policy, dict):
        raise RuntimeError(BLOCKED_CODE)
    purposes = policy.get("authorized_purposes")
    source_scopes = policy.get("authorized_source_scopes")
    reference = policy.get("authorization_reference")
    if (
        policy.get("schema_version") != POLICY_SCHEMA
        or policy.get("provider") != "FOOTBALL_DATA_CSV"
        or policy.get("experiment_scope") != "MARKET_ANCHOR_1X2_V2"
        or policy.get("rights_status") != "GRANTED"
        or policy.get("ai_feature_inference_permitted") is not True
        or policy.get("automated_source_archiving_permitted") is not True
        or not isinstance(purposes, list)
        or not all(isinstance(item, str) for item in purposes)
        or not REQUIRED_PURPOSES.issubset(set(purposes))
        or not isinstance(source_scopes, list)
        or not all(isinstance(item, str) for item in source_scopes)
        or not REQUIRED_SOURCE_SCOPES.issubset(set(source_scopes))
        or policy.get("ai_model_training_permitted") is not False
        or policy.get("commercial_use_permitted") is not False
        or policy.get("product_publication_permitted") is not False
        or not isinstance(reference, str)
        or not reference.strip()
        or policy.get("provider_policy_url") != "https://football-data.co.uk/contact.php"
    ):
        raise RuntimeError(BLOCKED_CODE)
    return policy
