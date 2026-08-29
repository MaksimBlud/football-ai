import pandas as pd

import build_league_calibration_dataset as calibration


def ledger_frame():
    return pd.DataFrame(
        [
            {
                "league": "EPL",
                "event_id": "event-1",
                "home_team": "Alpha",
                "away_team": "Beta",
                "kickoff_utc": "2026-08-01T14:00:00Z",
                "snapshot_time_utc": "2026-08-01T10:00:00Z",
                "market_home_prob": 0.60,
                "market_draw_prob": 0.25,
                "market_away_prob": 0.15,
                "market_pick": "H",
                "prediction_mode": "MARKET_ONLY",
                "structural_applied": False,
            },
            {
                "league": "EPL",
                "event_id": "event-1",
                "home_team": "Alpha",
                "away_team": "Beta",
                "kickoff_utc": "2026-08-01T14:00:00Z",
                "snapshot_time_utc": "2026-08-01T13:00:00Z",
                "market_home_prob": 0.70,
                "market_draw_prob": 0.20,
                "market_away_prob": 0.10,
                "market_pick": "H",
                "prediction_mode": "MARKET_ONLY",
                "structural_applied": False,
            },
            {
                "league": "EPL",
                "event_id": "event-2",
                "home_team": "Gamma",
                "away_team": "Delta",
                "kickoff_utc": "2026-08-02T14:00:00Z",
                "snapshot_time_utc": "2026-08-02T12:00:00Z",
                "market_home_prob": 0.20,
                "market_draw_prob": 0.30,
                "market_away_prob": 0.50,
                "market_pick": "A",
                "prediction_mode": "MARKET_ONLY",
                "structural_applied": False,
            },
        ]
    )


def result_frame():
    return pd.DataFrame(
        [
            {
                "league": "EPL",
                "match_date": "2026-08-01",
                "home_team": "Alpha",
                "away_team": "Beta",
                "result": "H",
            },
            {
                "league": "EPL",
                "match_date": "2026-08-02",
                "home_team": "Gamma",
                "away_team": "Delta",
                "result": "H",
            },
        ]
    )


def test_builds_all_and_latest_views():
    report, all_rows, latest = calibration.build_calibration_frames(
        "EPL", ledger_frame(), result_frame()
    )
    assert report.settled_rows == 3
    assert report.settled_fixtures == 2
    assert report.all_snapshot_rows == 3
    assert report.latest_rows == 2
    assert report.latest_fixtures == 2
    assert report.structural_applied_rows == 0
    assert set(all_rows["evaluation_view"]) == {calibration.ALL_SNAPSHOTS}
    assert set(latest["evaluation_view"]) == {calibration.LATEST_PRE_KICKOFF}


def test_latest_view_selects_latest_snapshot():
    _, _, latest = calibration.build_calibration_frames(
        "EPL", ledger_frame(), result_frame()
    )
    first = latest.loc[latest["event_id"] == "event-1"].iloc[0]
    assert first["snapshot_time_utc"] == pd.Timestamp("2026-08-01T13:00:00Z")
    assert first["hours_to_kickoff"] == 1.0


def test_actual_result_is_one_hot_encoded():
    _, all_rows, _ = calibration.build_calibration_frames(
        "EPL", ledger_frame(), result_frame()
    )
    actual = all_rows[["actual_home", "actual_draw", "actual_away"]]
    assert (actual.sum(axis=1) == 1).all()
    assert (all_rows.loc[all_rows["event_id"] == "event-1", "actual_home"] == 1).all()
    assert (all_rows.loc[all_rows["event_id"] == "event-2", "actual_home"] == 1).all()


def test_hours_to_kickoff_is_derived_from_timestamps():
    _, all_rows, _ = calibration.build_calibration_frames(
        "EPL", ledger_frame(), result_frame()
    )
    first = all_rows.loc[
        all_rows["snapshot_time_utc"] == pd.Timestamp("2026-08-01T10:00:00Z")
    ].iloc[0]
    assert first["hours_to_kickoff"] == 4.0


def test_empty_results_produce_empty_frames():
    report, all_rows, latest = calibration.build_calibration_frames(
        "EPL", ledger_frame(), pd.DataFrame()
    )
    assert report.settled_rows == 0
    assert report.latest_rows == 0
    assert all_rows.empty
    assert latest.empty
    for column in calibration.DERIVED_COLUMNS:
        assert column in all_rows.columns
        assert column in latest.columns


def test_builder_does_not_turn_on_structural():
    _, all_rows, latest = calibration.build_calibration_frames(
        "EPL", ledger_frame(), result_frame()
    )
    assert not all_rows["structural_applied"].any()
    assert not latest["structural_applied"].any()


def test_export_is_explicit_and_deterministic(tmp_path):
    _, all_rows, latest = calibration.build_calibration_frames(
        "EPL", ledger_frame(), result_frame()
    )
    all_path, latest_path = calibration.export_frames(
        all_snapshots=all_rows,
        latest=latest,
        output_dir=tmp_path,
        league="EPL",
    )
    assert all_path.name == "epl_calibration_all_snapshots.csv"
    assert latest_path.name == "epl_calibration_latest_pre_kickoff.csv"
    assert len(pd.read_csv(all_path)) == 3
    assert len(pd.read_csv(latest_path)) == 2
