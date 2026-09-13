"""Small, dependency-free runtime deployment identity helper."""

from __future__ import annotations

import os


def deployment_git_sha() -> str:
    """Return the immutable source identity exposed by the deployed runtime."""
    value = os.getenv("DEPLOYMENT_GIT_SHA") or os.getenv("VERCEL_GIT_COMMIT_SHA") or "unknown"
    return value.strip() or "unknown"
