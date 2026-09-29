from __future__ import annotations

import pandas as pd

import v2b_full_calendar_load_feasibility_v1 as mod


def test_manifest_has_only_pre_target_window_dates():
    dates=[pd.Timestamp(x["date"]) for x in mod.NON_LEAGUE_FIXTURES]
    assert min(dates) >= pd.Timestamp("2026-09-08")
    assert max(dates) <= pd.Timestamp("2026-09-17")


def test_manifest_contains_expected_competitions():
    comps={x["competition"] for x in mod.NON_LEAGUE_FIXTURES}
    assert comps=={
        "UEFA_CHAMPIONS_LEAGUE",
        "UEFA_EUROPA_LEAGUE",
        "CARABAO_CUP",
        "COPPA_ITALIA",
    }


def test_full_calendar_snapshot_changes_rest_and_load():
    league_dates=[
        pd.Timestamp("2026-09-06"),
        pd.Timestamp("2026-09-12"),
    ]
    nonleague=[
        {
            "date":pd.Timestamp("2026-09-16"),
            "competition":"CARABAO_CUP",
            "fixture_label":"Example",
        }
    ]
    r=mod._snapshot(
        team="Example",
        target_kickoff_utc="2026-09-19T14:00:00+00:00",
        league_dates=league_dates,
        nonleague_events=nonleague,
    )
    assert r["league_previous_match_date"]=="2026-09-12"
    assert r["full_previous_match_date"]=="2026-09-16"
    assert r["league_rest_days"]==7
    assert r["full_rest_days"]==3
    assert r["league_matches_7d"]==1
    assert r["full_matches_7d"]==2
    assert r["nonleague_matches_7d"]==1
    assert r["load_changed_vs_league_only"] is True


def test_old_nonleague_event_outside_14d_is_ignored():
    r=mod._snapshot(
        team="Example",
        target_kickoff_utc="2026-09-20T14:00:00+00:00",
        league_dates=[pd.Timestamp("2026-09-13")],
        nonleague_events=[
            {
                "date":pd.Timestamp("2026-09-03"),
                "competition":"CUP",
                "fixture_label":"Old",
            }
        ],
    )
    assert r["nonleague_matches_14d"]==0
    assert r["full_rest_days"]==7
    assert r["load_changed_vs_league_only"] is False


def test_nonleague_manifest_is_target_team_oriented():
    mapping=mod._nonleague_by_team()
    assert "Arsenal" in mapping
    assert "Man City" in mapping
    assert "Fiorentina" in mapping
    assert any(e["competition"]=="UEFA_CHAMPIONS_LEAGUE" for e in mapping["Arsenal"])
    assert any(e["competition"]=="CARABAO_CUP" for e in mapping["Arsenal"])
