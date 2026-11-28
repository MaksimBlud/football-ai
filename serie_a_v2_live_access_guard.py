"""Shared fail-closed access gate for original MARKET_ANCHOR_1X2_V2 live reads.

This module does not enable access. The default is always denied; an owner-controlled
flag and a successful exact-repository privacy check are both required before
source or saved-quote access.
"""
from __future__ import annotations

import os
from typing import Any

import requests

REPOSITORY = "MaksimBlud/football-ai"
GITHUB_API = f"https://api.github.com/repos/{REPOSITORY}"


def require_v2_live_access() -> None:
    """Fail closed unless the owner explicitly clears the V2 source/quote hold."""
    allowed = os.environ.get("MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED", "false")
    if allowed.strip().lower() != "true":
        raise PermissionError(
            "original V2 source/quote access is held; "
            "MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED=true is required"
        )


def require_private_repository(*, token: str, get=requests.get) -> dict[str, Any]:
    """Require the exact GitHub repository to be private before any live V2 read."""
    require_v2_live_access()
    if not isinstance(token, str) or not token.strip():
        raise ValueError("GitHub Actions read token missing for private-repository verification")
    url = GITHUB_API
    response = get(url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }, timeout=30, allow_redirects=False)
    if getattr(response, "url", None) != url:
        raise ValueError("unexpected GitHub repository metadata response URL")
    status = getattr(response, "status_code", None)
    if status != 200:
        raise ValueError(f"GitHub repository metadata request returned HTTP {status}")
    data = response.json()
    if not isinstance(data, dict) or data.get("full_name") != REPOSITORY:
        raise ValueError("GitHub repository metadata identity mismatch")
    if data.get("private") is not True:
        raise PermissionError(
            "original V2 source/quote access requires the exact GitHub repository to be private"
        )
    return {"repository": REPOSITORY, "private": True}
