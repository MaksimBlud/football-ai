"""Fail-closed direct-call guards for the original frozen V2 research path.

The CLI/workflow gates are not sufficient: every public helper that reads source,
quotes, archives, or constructs V2 features must enforce the same rights and
private-artifact boundary before touching caller inputs or external resources.
"""
from __future__ import annotations


def _require_live_flag() -> None:
    from serie_a_v2_live_access_guard import require_v2_live_access
    require_v2_live_access()


def require_v2_inference_rights() -> dict:
    """Check only the provider's separate frozen-inference permission."""
    from market_anchor_v2_source_rights import require_personal_research_inference_scope
    return require_personal_research_inference_scope()


def require_v2_inference_access() -> dict:
    """Require owner live hold, provider-cleared frozen inference, and private storage."""
    _require_live_flag()
    rights = require_v2_inference_rights()
    from market_anchor_v2_artifact_privacy import require_private_repository_for_source_artifacts
    privacy = require_private_repository_for_source_artifacts()
    return {
        "access_scope": "FROZEN_V2_INFERENCE",
        "rights": rights,
        "artifact_privacy": privacy,
    }


def require_v2_source_capture_access() -> dict:
    """Require owner live hold, separately cleared source capture, and private storage."""
    _require_live_flag()
    rights = require_v2_source_capture_rights()
    from market_anchor_v2_artifact_privacy import require_private_repository_for_source_artifacts
    privacy = require_private_repository_for_source_artifacts()
    return {
        "access_scope": "SOURCE_CAPTURE_ONLY",
        "rights": rights,
        "artifact_privacy": privacy,
    }



def require_v2_source_capture_rights() -> dict:
    """Require the provider's separate source-capture grant, without conflating scopes.

    This local rights check intentionally does not perform the private-repository
    lookup. Forward capture must also pass the independent inference/private-storage
    guard before any archive or quote operation.
    """
    from market_anchor_v2_source_capture_rights import require_personal_research_source_capture_scope
    return require_personal_research_source_capture_scope()
