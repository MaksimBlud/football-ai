from pathlib import Path

import project_cycle


def test_protected_artifacts_are_explicit():
    assert (
        "football_model_xgboost_elo.pkl"
        in project_cycle.PRODUCTION_ARTIFACTS
    )

    assert (
        "football_model_no_odds.pkl"
        in project_cycle.PRODUCTION_ARTIFACTS
    )


def test_live_snapshot_is_not_normal_step():
    commands = [
        command
        for _, command
        in project_cycle.LA_LIGA_STEPS
    ]

    flattened = [
        token
        for command in commands
        for token in command
    ]

    assert (
        "save_la_liga_odds_snapshot.py"
        not in flattened
    )


def test_no_training_commands_present():
    source = Path(
        "project_cycle.py"
    ).read_text(
        encoding="utf-8"
    )

    forbidden = [
        "train_model_xgboost_elo.py",
        "--production",
        "promote",
    ]

    for token in forbidden:
        assert token not in source


def test_la_liga_pipeline_order():
    labels = [
        label
        for label, _
        in project_cycle.LA_LIGA_STEPS
    ]

    assert labels == [
        "fixture export",
        "market shadow",
        "movement classifier",
        "transition tracker",
        "temporal behavior",
    ]


def test_runner_does_not_stage_or_commit():
    source = Path(
        "project_cycle.py"
    ).read_text(
        encoding="utf-8"
    )

    forbidden = [
        '"git", "add"',
        '"git", "commit"',
        '"git", "push"',
    ]

    for token in forbidden:
        assert token not in source


def test_hash_function(tmp_path):
    path = tmp_path / "sample.bin"

    path.write_bytes(
        b"football-ai"
    )

    first = project_cycle.sha256(
        path
    )

    second = project_cycle.sha256(
        path
    )

    assert first == second
    assert len(first) == 64


def test_v1_readiness_release_gate(
    monkeypatch,
):
    monkeypatch.setattr(
        project_cycle,
        "production_hashes",
        lambda: {
            name: "hash"
            for name
            in project_cycle.PRODUCTION_ARTIFACTS
        },
    )

    monkeypatch.setattr(
        project_cycle,
        "database_state",
        lambda: {
            "rows": 100,
            "league_counts": {
                "EPL": 50,
                "LA_LIGA": 50,
            },
            "la_liga_rows": 50,
            "la_liga_snapshot_times": 4,
            "la_liga_fixtures": 13,
            "duplicate_snapshot_rows": 0,
        },
    )

    monkeypatch.setattr(
        project_cycle,
        "csv_health",
        lambda: {
            "history":
                __import__("pandas").DataFrame(
                    [{"x": 1}]
                ),

            "transitions":
                __import__("pandas").DataFrame(
                    [{"x": 1}]
                ),
        },
    )

    monkeypatch.setattr(
        project_cycle,
        "_la_liga_collection_status",
        lambda: (
            True,
            "READY",
        ),
    )

    monkeypatch.setattr(
        project_cycle,
        "_la_liga_prediction_status",
        lambda: (
            True,
            "READY",
        ),
    )

    monkeypatch.setattr(
        project_cycle,
        "_file_present",
        lambda path: True,
    )

    result = (
        project_cycle.v1_readiness()
    )

    assert result["percent"] == 100
    assert result["blockers"] == []


def test_current_release_gate_has_explicit_blockers():
    result = (
        project_cycle.v1_readiness()
    )

    assert (
        "la_liga_automated_collection"
        in result["checks"]
    )

    assert (
        "la_liga_prediction_runtime"
        in result["checks"]
    )

    assert (
        "release_audit_script"
        in result["checks"]
    )


def test_release_audit_mode_is_registered():
    source = Path(
        "project_cycle.py"
    ).read_text(
        encoding="utf-8"
    )

    assert (
        '"release-audit"'
        in source
    )

    assert (
        '"release_audit.py"'
        in source
    )


def test_la_liga_collection_mode_registered():
    source = Path(
        "project_cycle.py"
    ).read_text(
        encoding="utf-8"
    )

    assert (
        '"la-liga-collect"'
        in source
    )

    assert (
        '"la_liga_collection_runner.py"'
        in source
    )
