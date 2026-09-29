from __future__ import annotations

from datetime import date

import v2b_travel_coordinate_feasibility_v1 as mod


def _coord_claim(lat, lon, rank="normal"):
    return {
        "rank": rank,
        "mainsnak": {
            "datavalue": {
                "value": {"latitude": lat, "longitude": lon}
            }
        },
    }


def _item_claim(qid, rank="normal", qualifiers=None):
    row = {
        "rank": rank,
        "mainsnak": {"datavalue": {"value": {"id": qid}}},
    }
    if qualifiers is not None:
        row["qualifiers"] = qualifiers
    return row


def _time_snak(value):
    return {"datavalue": {"value": {"time": value}}}


def test_wikipedia_titles_are_identity_only():
    assert mod._wikipedia_title("Man City") == "Manchester City"
    assert mod._wikipedia_title("Chelsea") == "Chelsea F.C."
    assert mod._wikipedia_title("Liverpool") == "Liverpool F.C."
    assert mod._wikipedia_title("Ath Bilbao") == "Athletic Bilbao"
    assert mod._wikipedia_title("Milan") == "AC Milan"
    assert mod._wikipedia_title("Vallecano") == "Rayo Vallecano"


def test_coordinate_prefers_preferred_claim():
    entity = {"claims": {"P625": [
        _coord_claim(1, 2, "normal"),
        _coord_claim(3, 4, "preferred"),
    ]}}
    assert mod._claim_coordinate(entity) == (3.0, 4.0)


def test_home_venue_end_date_filters_old_ground():
    old = _item_claim(
        "QOLD",
        qualifiers={"P582": [_time_snak("+2020-01-01T00:00:00Z")]},
    )
    current = _item_claim("QNEW")
    assert mod._claim_active_at(old, target=date(2026, 9, 20)) is False
    assert mod._claim_active_at(current, target=date(2026, 9, 20)) is True


def test_resolve_coordinate_uses_stadium_before_club_fallback():
    club = {
        "qid": "QCLUB",
        "search_label": "Example FC",
        "entity": {"claims": {
            "P115": [_item_claim("QVENUE", "preferred")],
            "P625": [_coord_claim(10, 20)],
        }},
    }
    venue = {
        "QVENUE": {
            "labels": {"en": {"value": "Example Stadium"}},
            "claims": {"P625": [_coord_claim(30, 40)]},
        }
    }
    out = mod._resolve_coordinate(club=club, venue_entities=venue)
    assert out["coordinate_status"] == "STADIUM_COORDINATE"
    assert out["venue_qid"] == "QVENUE"
    assert out["latitude"] == 30.0
    assert out["longitude"] == 40.0


def test_resolve_coordinate_marks_direct_club_point_as_fallback():
    club = {
        "qid": "QCLUB",
        "search_label": "Example FC",
        "entity": {"claims": {"P625": [_coord_claim(10, 20)]}},
    }
    out = mod._resolve_coordinate(club=club, venue_entities={})
    assert out["coordinate_status"] == "CLUB_COORDINATE_FALLBACK"
    assert out["latitude"] == 10.0


def test_multiple_active_stadiums_fail_ambiguous():
    club = {
        "qid": "QCLUB",
        "search_label": "Example FC",
        "entity": {"claims": {"P115": [
            _item_claim("Q1"),
            _item_claim("Q2"),
        ]}},
    }
    venues = {
        "Q1": {"claims": {"P625": [_coord_claim(1, 2)]}},
        "Q2": {"claims": {"P625": [_coord_claim(3, 4)]}},
    }
    out = mod._resolve_coordinate(club=club, venue_entities=venues)
    assert out["coordinate_status"] == "AMBIGUOUS_ACTIVE_HOME_VENUES"
    assert out["latitude"] is None


def test_candidate_must_be_footballish():
    results = [
        {"id": "QCITY", "label": "Como", "description": "city in Italy"},
        {
            "id": "QCLUB",
            "label": "Como 1907",
            "description": "Italian association football club",
        },
    ]
    entities = {
        "QCITY": {"claims": {"P625": [_coord_claim(1, 2)]}},
        "QCLUB": {"claims": {"P115": [_item_claim("QVENUE")]}},
    }
    chosen = mod._choose_club_candidate(
        "Como 1907 football club",
        results,
        entities,
    )
    assert chosen is not None
    assert chosen["qid"] == "QCLUB"


def test_source_backed_home_venue_override_wins_ambiguity():
    club = {
        "qid": "QCLUB",
        "search_label": "SC Freiburg",
        "entity": {"claims": {"P115": [
            _item_claim("QOLD"),
            _item_claim("QNEW"),
        ]}},
    }
    venues = {
        "QOLD": {
            "labels": {"en": {"value": "Old Ground"}},
            "claims": {"P625": [_coord_claim(1, 2)]},
        },
        "QNEW": {
            "labels": {"en": {"value": "Europa-Park-Stadion"}},
            "claims": {"P625": [_coord_claim(3, 4)]},
        },
    }
    out = mod._resolve_coordinate(
        club=club,
        venue_entities=venues,
        forced_venue_qid="QNEW",
    )
    assert out["coordinate_status"] == "STADIUM_COORDINATE"
    assert out["venue_qid"] == "QNEW"
    assert out["venue_selection"] == "EXPLICIT_SOURCE_BACKED_OVERRIDE"
