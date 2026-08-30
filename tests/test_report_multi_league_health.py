import report_multi_league_health as health


def test_health_report_merges_coverage_and_audit_by_league():
    coverage_rows = [
        {
            "league": "EPL",
            "ledger_rows": 10,
            "finished_result_rows": 2,
            "settled_fixtures": 2,
            "latest_pre_kickoff_fixtures": 2,
            "data_stage": "SETTLED_DATA_AVAILABLE",
        },
        {
            "league": "RPL",
            "ledger_rows": 4,
            "finished_result_rows": 1,
            "settled_fixtures": 1,
            "latest_pre_kickoff_fixtures": 1,
            "data_stage": "SETTLED_DATA_AVAILABLE",
        },
    ]
    audit_rows = [
        {
            "league": "EPL",
            "duplicate_prediction_rows": 0,
            "duplicate_result_identities": 0,
            "missing_event_ids": 0,
            "unlinked_finished_results": 1,
            "critical_failures": 0,
        },
        {
            "league": "RPL",
            "duplicate_prediction_rows": 2,
            "duplicate_result_identities": 0,
            "missing_event_ids": 0,
            "unlinked_finished_results": 0,
            "critical_failures": 2,
        },
    ]

    rows = health.build_health_report(
        build_coverage=lambda: coverage_rows,
        build_audit=lambda: audit_rows,
    )

    by_league = {row["league"]: row for row in rows}
    assert by_league["EPL"]["ledger_rows"] == 10
    assert by_league["EPL"]["unlinked_finished_results"] == 1
    assert by_league["EPL"]["critical_failures"] == 0
    assert by_league["RPL"]["critical_failures"] == 2


def test_health_report_fails_closed_on_league_set_mismatch():
    try:
        health.build_health_report(
            build_coverage=lambda: [{"league": "EPL"}],
            build_audit=lambda: [{"league": "RPL"}],
        )
    except ValueError as exc:
        assert "league mismatch" in str(exc)
    else:
        raise AssertionError("Expected health report to fail on mismatched league sets")


def test_health_report_is_read_only_and_threshold_free():
    source = open("report_multi_league_health.py", encoding="utf-8").read()
    forbidden = [
        ".insert(", ".upsert(", ".update(", ".delete(",
        "joblib.load", "football_model_xgboost_elo", "train_model",
        "min_settled", "readiness_threshold",
    ]
    for token in forbidden:
        assert token not in source
