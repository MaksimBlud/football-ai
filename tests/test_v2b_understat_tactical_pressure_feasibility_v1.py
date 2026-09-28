from __future__ import annotations

import pandas as pd
import pytest

import v2b_understat_tactical_pressure_feasibility_v1 as mod


def test_ppda_dict_normalization():
    assert mod._ppda_ratio({"att": 120, "def": 20}) == pytest.approx(6.0)
    assert mod._ppda_ratio({"att": "90", "def": "15"}) == pytest.approx(6.0)
    assert mod._ppda_ratio({"att": 20, "def": 0}) is None


def test_ppda_numeric_normalization():
    assert mod._ppda_ratio(8.5) == pytest.approx(8.5)
    assert mod._ppda_ratio(-1) is None
    assert mod._ppda_ratio(None) is None


def _payload():
    history=[]
    for i in range(6):
        history.append({
            "date":f"2026-08-{i+1:02d} 15:00:00",
            "h_a":"h" if i%2==0 else "a",
            "deep":5+i,
            "deep_allowed":3+i,
            "ppda":{"att":100+i*5,"def":20},
            "ppda_allowed":{"att":120+i*5,"def":20},
        })
    return {
        "teams":{
            "1":{"title":"Team A","history":history},
            "2":{"title":"Team B","history":history},
        }
    }


def test_prepare_histories_detects_tactical_schema():
    histories,titles,cap=mod.prepare_tactical_histories([(2026,_payload())])
    assert titles==["Team A","Team B"]
    assert cap["valid_tactical_rows"]==12
    assert all(cap["required_fields_seen"].values())
    assert len(histories["Team A"])==6


def test_prior_snapshot_is_strictly_pre_kickoff():
    histories,_,_=mod.prepare_tactical_histories([(2026,_payload())])
    r=mod._prior_snapshot(
        histories["Team A"],
        target_kickoff_utc="2026-08-06T12:00:00+00:00",
    )
    assert r["prior_valid_tactical_matches"]==5
    assert r["tactical5_feasible"] is True


def test_missing_required_field_fails_feature_row():
    p=_payload()
    for match in p["teams"]["1"]["history"]:
        match.pop("deep_allowed")
    histories,_,cap=mod.prepare_tactical_histories([(2026,p)])
    assert cap["required_fields_seen"]["deep_allowed"] is False
    assert "Team A" not in histories
