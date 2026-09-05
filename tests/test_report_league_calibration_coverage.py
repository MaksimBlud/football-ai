from types import SimpleNamespace

import pandas as pd

import report_league_calibration_coverage as coverage


def test_data_stage_is_descriptive_only():
    assert coverage.data_stage(ledger_rows=0, settled_fixtures=0) == "NO_PREDICTIONS"
    assert coverage.data_stage(ledger_rows=3, settled_fixtures=0) == "AWAITING_SETTLED_RESULTS"
    assert coverage.data_stage(ledger_rows=3, settled_fixtures=1) == "SETTLED_DATA_AVAILABLE"


def test_report_covers_all_operational_leagues_and_preserves_calibration_status():
    seen = []

    def evaluate(league):
        seen.append(league)
        report = SimpleNamespace(
            ledger_rows=2,
            result_rows=1,
            settled_rows=2,
            settled_fixtures=1,
        )
        latest = pd.DataFrame([{"event_id": f"{league}-1"}])
        return report, pd.DataFrame(), latest

    rows = coverage.build_coverage_report(evaluate=evaluate)

    expected = {
        "EPL", "LA_LIGA", "RPL", "SERIE_A",
        "BUNDESLIGA", "LIGUE_1", "EREDIVISIE",
        "TURKEY_SUPER_LIG", "PRIMEIRA_LIGA",
    }

    assert set(seen) == expected
    assert {row["league"] for row in rows} == expected

    by_league = {row["league"]: row for row in rows}
    assert by_league["LA_LIGA"]["calibration_status"] == "CALIBRATED"
    assert by_league["LA_LIGA"]["structural_alpha"] == 0.10
    assert by_league["LA_LIGA"]["edge_threshold"] == 0.75

    for league in expected - {"LA_LIGA"}:
        assert by_league[league]["calibration_status"] == "CALIBRATION_REQUIRED"
        assert by_league[league]["structural_alpha"] is None
        assert by_league[league]["edge_threshold"] is None

    assert all(row["data_stage"] == "SETTLED_DATA_AVAILABLE" for row in rows)


def test_report_does_not_invent_readiness_thresholds():
    source = open("report_league_calibration_coverage.py", encoding="utf-8").read()

    assert "READY" not in source
    assert "min_settled" not in source
    assert "persist" not in source.lower()
    assert "insert(" not in source
    assert "update(" not in source
