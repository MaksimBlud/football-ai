from types import SimpleNamespace

import pandas as pd
import pytest

from football_data_current_results import PublicResultsSourceUnavailable
import sync_la_liga_public_results as sync


def _provider(frame):
    return {
        "frame": frame,
        "source_url": "https://www.football-data.co.uk/mmz4281/2627/SP1.csv",
        "public_http_requests": 1,
        "source_rows": len(frame),
        "finished_rows": len(frame),
        "paid_provider_requests": 0,
    }


def _frame():
    return pd.DataFrame([
        {
            "season": "2026-2027",
            "league": "LA_LIGA",
            "match_date": "2026-09-04",
            "match_time": "21:00",
            "home_team": "Real Betis",
            "away_team": "Real Madrid",
            "home_goals": 1,
            "away_goals": 2,
            "result": "A",
            "source": "FOOTBALL_DATA_CSV",
            "source_competition": "SP1",
            "source_updated_at_utc": "2026-09-05T00:00:00+00:00",
        }
    ])


def test_transient_source_outage_is_explicit_and_never_writes(monkeypatch):
    def unavailable():
        raise PublicResultsSourceUnavailable(
            url="https://www.football-data.co.uk/mmz4281/2627/SP1.csv",
            status_code=503,
            attempts=3,
            detail="temporarily unavailable",
        )

    calls=[]
    monkeypatch.setattr(sync.legacy,"persist_results",lambda *_a,**_k: calls.append("legacy"))
    monkeypatch.setattr(sync.canonical_bridge,"persist_authoritative_results",lambda *_a,**_k: calls.append("canonical"))
    result=sync.sync_results(client=object(),fetch_fn=unavailable,write=True)
    assert result["status"]=="SOURCE_UNAVAILABLE"
    assert result["http_status"]==503
    assert result["public_http_requests"]==3
    assert result["writes_performed"] is False
    assert result["paid_provider_requests"]==0
    assert result["legacy_inserted"]==0
    assert result["canonical_inserted"]==0
    assert calls==[]


def test_success_persists_legacy_authority_before_canonical_bridge(monkeypatch):
    calls=[]
    frame=_frame()

    def persist_legacy(client,incoming):
        calls.append(("legacy",client))
        pd.testing.assert_frame_equal(incoming,frame)
        return {"input":1,"inserted":1,"unchanged":0}

    def bridge(client):
        calls.append(("canonical",client))
        return {"input":1,"inserted":1,"unchanged":0,"conflicts":0}

    client=object()
    monkeypatch.setattr(sync.legacy,"persist_results",persist_legacy)
    monkeypatch.setattr(sync.canonical_bridge,"persist_authoritative_results",bridge)
    result=sync.sync_results(client=client,fetch_fn=lambda:_provider(frame),write=True)
    assert [name for name,_ in calls]==["legacy","canonical"]
    assert result["status"]=="WRITTEN"
    assert result["legacy_inserted"]==1
    assert result["canonical_inserted"]==1
    assert result["canonical_conflicts"]==0
    assert result["writes_performed"] is True
    assert result["paid_provider_requests"]==0


def test_idempotent_success_reports_no_new_writes(monkeypatch):
    frame=_frame()
    monkeypatch.setattr(sync.legacy,"persist_results",lambda *_a,**_k:{"input":1,"inserted":0,"unchanged":1})
    monkeypatch.setattr(sync.canonical_bridge,"persist_authoritative_results",lambda *_a,**_k:{"input":1,"inserted":0,"unchanged":1,"conflicts":0})
    result=sync.sync_results(client=object(),fetch_fn=lambda:_provider(frame),write=True)
    assert result["status"]=="WRITTEN"
    assert result["legacy_unchanged"]==1
    assert result["canonical_unchanged"]==1
    assert result["writes_performed"] is False


def test_non_transient_fetch_failure_stays_hard_and_never_writes(monkeypatch):
    calls=[]
    monkeypatch.setattr(sync.legacy,"persist_results",lambda *_a,**_k:calls.append("legacy"))
    with pytest.raises(RuntimeError,match="schema drift"):
        sync.sync_results(
            client=object(),
            fetch_fn=lambda:(_ for _ in ()).throw(RuntimeError("schema drift")),
            write=True,
        )
    assert calls==[]


def test_persistence_failure_stays_hard_and_canonical_bridge_is_not_called(monkeypatch):
    calls=[]
    frame=_frame()
    def fail_legacy(*_a,**_k):
        calls.append("legacy")
        raise RuntimeError("immutable conflict")
    monkeypatch.setattr(sync.legacy,"persist_results",fail_legacy)
    monkeypatch.setattr(sync.canonical_bridge,"persist_authoritative_results",lambda *_a,**_k:calls.append("canonical"))
    with pytest.raises(RuntimeError,match="immutable conflict"):
        sync.sync_results(client=object(),fetch_fn=lambda:_provider(frame),write=True)
    assert calls==["legacy"]


def test_existing_la_liga_normalization_keeps_rayo_identity():
    raw=pd.DataFrame([
        {"Date":"31/08/2026","Time":"20:30","HomeTeam":"Barcelona","AwayTeam":"Vallecano","FTHG":5,"FTAG":2,"FTR":"H"}
    ])
    normalized=sync.updater.normalize_source(raw,updated_at_utc="2026-09-01T00:00:00+00:00")
    assert normalized.iloc[0]["away_team"]=="Rayo Vallecano"
