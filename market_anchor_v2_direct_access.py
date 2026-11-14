"""Fail-closed direct-call guards for the original frozen V2 research path.

The CLI/workflow gates are not sufficient: every public helper that reads source,
quotes, archives, or constructs V2 features must enforce the same rights and
private-artifact boundary before touching caller inputs or external resources.
"""
from __future__ import annotations


def require_v2_inference_access() -> dict:
    """Require provider-cleared frozen inference and private artifact storage."""
    from market_anchor_v2_source_rights import require_personal_research_inference_scope
    rights = require_personal_research_inference_scope()
    from market_anchor_v2_artifact_privacy import require_private_repository_for_source_artifacts
    privacy = require_private_repository_for_source_artifacts()
    return {
        "access_scope": "FROZEN_V2_INFERENCE",
        "rights": rights,
        "artifact_privacy": privacy,
    }


def require_v2_source_capture_access() -> dict:
    """Require separately cleared source capture and private artifact storage."""
    from market_anchor_v2_source_capture_rights import require_personal_research_source_capture_scope
    rights = require_personal_research_source_capture_scope()
    from market_anchor_v2_artifact_privacy import require_private_repository_for_source_artifacts
    privacy = require_private_repository_for_source_artifacts()
    return {
        "access_scope": "SOURCE_CAPTURE_ONLY",
        "rights": rights,
        "artifact_privacy": privacy,
    }
