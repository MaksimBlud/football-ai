from multi_market_odds import (
    EVENT_MARKETS,
    FEATURED_CARD_MARKETS,
    index_sport_events,
    merge_event_market_payloads,
    summarize_market_coverage,
)


def test_event_request_contains_only_corner_markets_consumed_by_card_v1():
    assert FEATURED_CARD_MARKETS == ("spreads", "totals")
    assert EVENT_MARKETS == (
        "alternate_totals_corners",
        "alternate_team_totals_corners",
    )
    assert len(EVENT_MARKETS) == 2
    assert "alternate_spreads" not in EVENT_MARKETS
    assert "alternate_totals" not in EVENT_MARKETS


def test_featured_and_event_markets_merge_by_bookmaker_without_duplication():
    featured = {
        "id": "e1", "home_team": "Home", "away_team": "Away",
        "bookmakers": [{"key": "book_a", "markets": [
            {"key": "spreads", "outcomes": []},
            {"key": "totals", "outcomes": []},
        ]}],
    }
    corners = {
        "id": "e1", "home_team": "Home", "away_team": "Away",
        "bookmakers": [{"key": "book_a", "markets": [
            {"key": "alternate_totals_corners", "outcomes": []},
            {"key": "alternate_team_totals_corners", "outcomes": []},
        ]}],
    }
    merged = merge_event_market_payloads(featured, corners)
    assert [m["key"] for m in merged["bookmakers"][0]["markets"]] == [
        "spreads", "totals", "alternate_totals_corners", "alternate_team_totals_corners"
    ]
    assert index_sport_events([featured])["e1"] is featured


def test_summarize_market_coverage_collects_points_and_books():
    event = {
        "bookmakers": [
            {"key": "book_a", "markets": [{"key": "alternate_totals_corners", "outcomes": [
                {"name": "Over", "point": 9.5, "price": 1.9},
                {"name": "Under", "point": 9.5, "price": 1.9},
            ]}]},
            {"key": "book_b", "markets": [{"key": "alternate_totals_corners", "outcomes": [
                {"name": "Over", "point": 10.5, "price": 2.0},
                {"name": "Under", "point": 10.5, "price": 1.8},
            ]}]},
        ]
    }
    result = summarize_market_coverage(event)
    assert result["alternate_totals_corners"]["bookmakers"] == 2
    assert result["alternate_totals_corners"]["points"] == [9.5, 10.5]
    assert result["alternate_totals_corners"]["outcomes"] == ["Over", "Under"]


def test_summarize_market_coverage_does_not_emit_prices():
    event = {"bookmakers": [{"key": "b", "markets": [{"key": "totals", "outcomes": [{"name": "Over", "point": 2.5, "price": 1.73}]}]}]}
    result = summarize_market_coverage(event)
    assert "price" not in str(result).lower()
    assert result["totals"]["points"] == [2.5]
