"""Tests for actual historical-source + stored-market, always research-only."""
from datetime import datetime, timezone

import pandas as pd
import pytest

from serie_a_v2_live_diagnostic_report import (
    PUBLIC_BASE, _source_codes, fetch_public_history, make_report,
)

NOW = datetime(2026,10,13,15,1,tzinfo=timezone.utc)


def history_fixture():
    rows = []
    for date, home, away, home_goals, away_goals, result in [
        ("10/10/2026","Inter Milan","Genoa",2,0,"H"),
        ("11/10/2026","Napoli","Lecce",1,1,"D"),
        ("13/10/2026","Inter Milan","Lecce",4,0,"H"),
    ]:
        rows.append({
            "Date":date, "HomeTeam":home, "AwayTeam":away,
            "FTHG":home_goals,"FTAG":away_goals,"FTR":result,
            "HC":5,"AC":4,"HY":2,"AY":1,"HR":0,"AR":0,
        })
    return pd.DataFrame(rows)


def quote():
    return {
        "league":"SERIE_A","event_id":"real-research-fixture-1",
        "home_team":"Inter Milan","away_team":"Napoli",
        "commence_time_utc":"2026-10-19T19:00:00Z",
        "snapshot_time_utc":"2026-10-13T14:00:00Z",
        "home_odds":1.8,"draw_odds":3.9,"away_odds":5.0,
    }


def source_audit(observed_at="2026-10-13T15:00:00Z"):
    return [{"season_code":"2627",
             "source_url":f"{PUBLIC_BASE}/2627/I1.csv",
             "source_observed_at_utc":observed_at,
             "csv_sha256":"f"*64,
             "completed_source_rows":3}]


def test_real_frozen_model_diagnostic_never_relabels_later_source_as_prospective():
    report = make_report([quote()], history_fixture(),source_audit(),as_of_utc=NOW)
    assert report["diagnostic_scored"]==1
    assert report["feature_count"]==19
    assert report["quotes_with_source_observed_after_quote"]==1
    assert report["paid_provider_requests"]==report["supabase_writes"]==0
    assert report["independently_attested_feature_availability_at_quote"] is False
    assert report["eligible_for_frozen_prospective_cohort"] is False
    assert report["eligible_for_product_publication"] is False
    assert report["no_bet"] is True
    assert report["protect_2026_27_prospective_outcomes"] is True
    assert report["2026_27_public_results_downloaded"] is False
    assert report["history_stale_without_2026_27_form"] is True
    row = report["diagnostic_previews"][0]
    assert row["market_1x2"]==pytest.approx(row["active_market_fallback_1x2"])
    assert row["model_candidate_sha256"]==report["frozen_candidate_sha256"]


def test_same_day_future_outcome_changes_never_affect_diagnostic():
    before=make_report([quote()],history_fixture(),source_audit(),as_of_utc=NOW)
    modified=history_fixture()
    modified.loc[2,"FTHG"]=8
    after=make_report([quote()],modified,source_audit(),as_of_utc=NOW)
    assert before["diagnostic_previews"]==after["diagnostic_previews"]


def test_missing_source_stats_fail_closed_and_do_not_impute_fake_history():
    with pytest.raises(ValueError,match="required football stats"):
        make_report([quote()],history_fixture().drop(columns=["HC"]),source_audit(),as_of_utc=NOW)


def test_public_free_history_never_downloads_protected_2026_27_outcomes():
    # The current-season CSV includes frozen-prospective outcomes and must
    # NOT be fetched, even if its rows might later be filtered in-memory.
    current = "2627"
    assert current not in _source_codes()
    assert len(_source_codes()) == 10
    csv_completed = history_fixture().to_csv(index=False).encode()
    calls = []
    class Response:
        status_code = 200
        content = csv_completed
    def fake_get(url, timeout):
        calls.append((url, timeout))
        assert url.startswith(PUBLIC_BASE + "/") and url.endswith("/I1.csv")
        assert f"/{current}/" not in url
        return Response()
    history, audit = fetch_public_history(get=fake_get)
    assert len(calls) == 10
    assert len(audit) == len(calls)
    assert len(history) == 3*len(calls)
    assert all(x["csv_sha256"] and x["source_observed_at_utc"] for x in audit)


def test_upstream_status_failure_is_not_filled_with_guessed_data():
    class BadResponse:
        status_code=503
        content=b""
    with pytest.raises(RuntimeError,match="unavailable"):
        fetch_public_history(get=lambda url,timeout: BadResponse())
