from multi_market_card import build_multi_market_card, no_vig_pair


def _market(key, outcomes):
    return {"key": key, "outcomes": outcomes}


def test_no_vig_pair_sums_to_one():
    a, b = no_vig_pair(1.80, 2.10)
    assert abs(a + b - 1.0) < 1e-12
    assert a > b


def test_card_prefers_goal_total_2_5_and_balanced_corner_lines():
    event = {
        "home_team": "Home", "away_team": "Away",
        "bookmakers": [{"key": "book", "markets": [
            _market("alternate_spreads", [
                {"name": "Home", "point": -1.0, "price": 2.0}, {"name": "Away", "point": 1.0, "price": 1.9},
                {"name": "Home", "point": -1.5, "price": 2.5}, {"name": "Away", "point": 1.5, "price": 1.55},
            ]),
            _market("alternate_totals", [
                {"name": "Over", "point": 2.5, "price": 1.80}, {"name": "Under", "point": 2.5, "price": 2.10},
                {"name": "Over", "point": 3.5, "price": 2.80}, {"name": "Under", "point": 3.5, "price": 1.45},
            ]),
            _market("alternate_totals_corners", [
                {"name": "Over", "point": 9.5, "price": 1.90}, {"name": "Under", "point": 9.5, "price": 1.90},
                {"name": "Over", "point": 10.5, "price": 2.40}, {"name": "Under", "point": 10.5, "price": 1.55},
            ]),
            _market("alternate_team_totals_corners", [
                {"name": "Over", "description": "Home", "point": 5.5, "price": 1.95},
                {"name": "Under", "description": "Home", "point": 5.5, "price": 1.85},
                {"name": "Over", "description": "Away", "point": 4.5, "price": 2.00},
                {"name": "Under", "description": "Away", "point": 4.5, "price": 1.80},
            ]),
        ]}],
    }
    card = build_multi_market_card(event)
    assert card["handicap"]["home_handicap"] == -1.0
    assert card["total_goals"]["point"] == 2.5
    assert card["total_corners"]["point"] == 9.5
    assert card["team_corners"]["home"]["point"] == 5.5
    assert card["team_corners"]["away"]["point"] == 4.5


def test_missing_corner_coverage_is_null_not_invented():
    card = build_multi_market_card({"home_team": "Home", "away_team": "Away", "bookmakers": []})
    assert card["total_corners"] is None
    assert card["team_corners"] == {"home": None, "away": None}
