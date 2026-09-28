from __future__ import annotations

import pandas as pd

import v2b_true_xg_replay_feasibility_v1 as mod


def test_identity_normalization_and_aliases():
    titles=["Manchester City","Manchester United","Nottingham Forest","Paris Saint Germain"]
    assert mod.resolve_team_title(league="EPL",target_team="Man City",source_titles=titles)=="Manchester City"
    assert mod.resolve_team_title(league="EPL",target_team="Man Utd",source_titles=titles)=="Manchester United"
    assert mod.resolve_team_title(league="EPL",target_team="Nottm Forest",source_titles=titles)=="Nottingham Forest"
    assert mod.resolve_team_title(league="LIGUE_1",target_team="PSG",source_titles=titles)=="Paris Saint Germain"


def test_prepare_histories_keeps_valid_true_xg_rows():
    payload={
        "teams":{
            "1":{
                "title":"Team A",
                "history":[
                    {"date":"2026-09-01 12:00:00","h_a":"h","xG":"1.2","xGA":"0.8","npxG":"1.1","npxGA":"0.7"},
                    {"date":"2026-09-08 12:00:00","h_a":"a","xG":"2.0","xGA":"1.0","npxG":"1.8","npxGA":"0.9"},
                ],
            }
        }
    }
    histories,titles=mod.prepare_team_histories([(2026,payload)])
    assert titles==["Team A"]
    assert len(histories["Team A"])==2
    assert histories["Team A"]["xg"].tolist()==[1.2,2.0]


def test_snapshot_uses_only_matches_strictly_before_target():
    history=pd.DataFrame({
        "match_date":pd.to_datetime([
            "2026-08-01","2026-08-08","2026-08-15","2026-08-22","2026-08-29","2026-09-19 12:00:00"
        ]),
        "xg":[1,2,3,4,5,99],
        "xga":[1,1,1,1,1,99],
        "npxg":[1,2,3,4,5,99],
        "npxga":[1,1,1,1,1,99],
    })
    snapshot=mod._prior_xg_snapshot(history,target_kickoff_utc="2026-09-19T12:00:00+00:00")
    assert snapshot["prior_valid_xg_matches"]==5
    assert snapshot["xg5_feasible"] is True
    assert snapshot["xg_last5"]==3.0


def test_snapshot_fails_closed_below_five_prior():
    history=pd.DataFrame({
        "match_date":pd.to_datetime(["2026-08-01","2026-08-08","2026-08-15","2026-08-22"]),
        "xg":[1,1,1,1],
        "xga":[1,1,1,1],
        "npxg":[1,1,1,1],
        "npxga":[1,1,1,1],
    })
    snapshot=mod._prior_xg_snapshot(history,target_kickoff_utc="2026-09-19T12:00:00+00:00")
    assert snapshot["prior_valid_xg_matches"]==4
    assert snapshot["xg5_feasible"] is False
    assert snapshot["xg_last5"] is None
