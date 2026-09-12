"""Web/data adapter for the Football AI product market contract.

The functions in this module keep fixture/odds assembly out of the browser and
remain independently testable without calling Supabase or model code.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from product_markets import build_product_market_view, fixture_key


def build_odds_by_fixture(
    odds_rows: Iterable[Mapping[str, Any]],
) -> dict[tuple[str, str, str, str], dict[str, Any]]:
    """Index already-matched 1X2 prices by the scheduled product fixture key."""
    result: dict[tuple[str, str, str, str], dict[str, Any]] = {}

    for row in odds_rows:
        key = fixture_key(row)
        result[key] = {
            "home_odds": row.get("home_odds"),
            "draw_odds": row.get("draw_odds"),
            "away_odds": row.get("away_odds"),
        }

    return result


def assemble_product_market_view(
    predictions: Iterable[Mapping[str, Any]],
    odds_rows: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Assemble one server-owned payload for both product UI screens."""
    return build_product_market_view(
        list(predictions),
        odds_by_fixture=build_odds_by_fixture(odds_rows),
    )
