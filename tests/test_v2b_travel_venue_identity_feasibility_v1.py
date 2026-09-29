from __future__ import annotations

import pandas as pd

import v2b_travel_venue_identity_feasibility_v1 as mod


def test_target_aliases_cover_known_provider_variants():
    assert mod._matches_target("Man City", "Manchester City")
    assert mod._matches_target("Man Utd", "Man United")
    assert mod._matches_target("Nottm Forest", "Nott'm Forest")
    assert mod._matches_target("Atletico Madrid", "Ath Madrid")
    assert mod._matches_target("Rayo Vallecano", "Vallecano")
    assert mod._matches_target("AC Milan", "Milan")
    assert mod._matches_target("TSG Hoffenheim", "Hoffenheim")
    assert mod._matches_target("PSG", "Paris Saint-Germain")


def test_parse_fixture_label():
    assert mod._parse_fixture_label("Porto vs Manchester City") == (
        "Porto",
        "Manchester City",
    )


def test_latest_prior_event_prefers_latest_date():
    events=[
        {
            "team":"Arsenal",
            "date":pd.Timestamp("2026-09-12"),
            "competition":"LEAGUE",
            "source":"FOOTBALL_DATA_CSV",
            "role":"HOME",
            "home_label":"Arsenal",
            "away_label":"Everton",
            "venue_label":"Arsenal",
            "opponent_label":"Everton",
        },
        {
            "team":"Arsenal",
            "date":pd.Timestamp("2026-09-15"),
            "competition":"CARABAO_CUP",
            "source":"FROZEN_OFFICIAL_NONLEAGUE_MANIFEST",
            "role":"AWAY",
            "home_label":"Ipswich Town",
            "away_label":"Arsenal",
            "venue_label":"Ipswich Town",
            "opponent_label":"Ipswich Town",
        },
    ]
    event=mod._latest_prior_event(
        team="Arsenal",
        target_kickoff_utc="2026-09-20T14:00:00+00:00",
        events=events,
    )
    assert event is not None
    assert event["date"]==pd.Timestamp("2026-09-15")
    assert event["role"]=="AWAY"
    assert event["venue_label"]=="Ipswich Town"


def test_league_events_resolve_home_and_away_roles():
    frame=pd.DataFrame([
        {"Date":"12/09/2026","HomeTeam":"Man City","AwayTeam":"Man United"},
    ])
    events,summary=mod._league_events(
        league="EPL",
        frame=frame,
        targets={"Man City","Man Utd"},
    )
    assert len(events)==2
    by_team={e["team"]:e for e in events}
    assert by_team["Man City"]["role"]=="HOME"
    assert by_team["Man Utd"]["role"]=="AWAY"
    assert summary["source_rows"]==1


def test_nonleague_manifest_role_resolution_for_known_target():
    events=mod._nonleague_events({"Arsenal"})
    arsenal=[e for e in events if e["team"]=="Arsenal"]
    assert any(e["competition"]=="UEFA_CHAMPIONS_LEAGUE" for e in arsenal)
    assert any(e["competition"]=="CARABAO_CUP" for e in arsenal)
    assert all(e["role"] in {"HOME","AWAY"} for e in arsenal)
