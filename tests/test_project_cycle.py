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
