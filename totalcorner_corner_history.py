"""Research-only TotalCorner corner-history client and parser.

No network request is made unless a TotalCorner token is explicitly supplied.
The module is intended for a small source-qualification pilot before any
historical bookmaker-corners experiment is frozen or evaluated.
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

BASE_URL = "https://api.totalcorner.com/v1"
TOKEN_ENV = "TOTALCORNER_TOKEN"


def _parse_ts(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")


def normalize_corner_history(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalize documented TotalCorner `corner_list` rows.

    Output contains only valid *pre-match* rows. Rows at/after kickoff are
    deliberately excluded so later in-play corner state cannot leak into a
    future market experiment.
    """
    if payload.get("success") != 1:
        error = payload.get("error") or {}
        raise ValueError(f"TotalCorner API failure: {error}")

    data = payload.get("data")
    if not isinstance(data, list) or len(data) != 1 or not isinstance(data[0], dict):
        raise ValueError("expected exactly one match object in payload.data")

    match = data[0]
    match_id = str(match.get("id") or "").strip()
    home = str(match.get("h") or "").strip()
    away = str(match.get("a") or "").strip()
    league = str(match.get("l") or "").strip()
    kickoff_raw = str(match.get("start") or "").strip()
    if not all((match_id, home, away, kickoff_raw)):
        raise ValueError("match identity is incomplete")
    kickoff = _parse_ts(kickoff_raw)

    rows = match.get("corner_list")
    if rows is None:
        rows = match.get("cornerList")
    if rows is None:
        rows = []
    if not isinstance(rows, list):
        raise ValueError("corner_list must be a list")

    normalized: list[dict[str, Any]] = []
    for raw in rows:
        if not isinstance(raw, list) or len(raw) < 7:
            continue
        try:
            status = str(raw[0])
            line = float(str(raw[1]).replace(",", "."))
            over = float(raw[2])
            under = float(raw[3])
            observed_at = _parse_ts(str(raw[4]))
            home_corners = int(raw[5])
            away_corners = int(raw[6])
        except (TypeError, ValueError):
            continue
        if not (over > 1.0 and under > 1.0):
            continue
        if observed_at >= kickoff:
            continue
        normalized.append(
            {
                "match_id": match_id,
                "league": league,
                "home_team": home,
                "away_team": away,
                "kickoff": kickoff_raw,
                "observed_at": str(raw[4]),
                "status": status,
                "corner_line": line,
                "over_odds": over,
                "under_odds": under,
                "home_corners": home_corners,
                "away_corners": away_corners,
                "source": "TOTALCORNER",
            }
        )

    normalized.sort(key=lambda row: row["observed_at"])
    return normalized


def fetch_match_corner_history(match_id: str, token: str | None = None) -> dict[str, Any]:
    """Fetch one match through the official token-gated API only."""
    token = (token or os.getenv(TOKEN_ENV, "")).strip()
    if not token:
        raise RuntimeError(
            f"{TOKEN_ENV} is required; refusing to call TotalCorner without an explicitly supplied token"
        )
    match_id = str(match_id).strip()
    if not match_id.isdigit():
        raise ValueError("match_id must be numeric")
    response = requests.get(
        f"{BASE_URL}/match/odds/{match_id}",
        params={"token": token, "columns": "cornerList"},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("success") != 1:
        error = payload.get("error") or {}
        raise RuntimeError(f"TotalCorner API error: {error}")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--match-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    payload = fetch_match_corner_history(args.match_id)
    normalized = normalize_corner_history(payload)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(
            {"match_id": args.match_id, "pre_match_corner_history": normalized},
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    print(f"match_id={args.match_id} pre_match_snapshots={len(normalized)}")


if __name__ == "__main__":
    main()
