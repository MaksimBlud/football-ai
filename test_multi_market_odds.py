from multi_market_odds import EVENT_MARKETS, summarize_market_coverage


def test_event_request_contains_only_markets_consumed_by_card_v1():
    assert EVENT_MARKETS == (
        "alternate_spreads",
        "alternate_totals",
        "alternate_totals_corners",
        "alternate_team_totals_corners",
    )
    assert len(EVENT_MARKETS) == 4
    assert "team_totals" not in EVENT_MARKETS
    assert "alternate_team_totals" not in EVENT_MARKETS
    assert "alternate_spreads_corners" not in EVENT_MARKETS


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
