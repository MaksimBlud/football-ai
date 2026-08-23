from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

import la_liga_collection_runner as runner


def test_default_interval():
    assert (
        runner.DEFAULT_MIN_INTERVAL_MINUTES
        == 120
    )


def test_due_without_previous_snapshot(
    monkeypatch,
):
    monkeypatch.setattr(
        runner,
        "minutes_since_latest",
        lambda **kwargs: None,
    )

    due, reason = (
        runner.collection_due(
            minimum_interval_minutes=120
        )
    )

    assert due is True
    assert (
        reason
        == "no_previous_la_liga_snapshot"
    )


def test_not_due_inside_interval(
    monkeypatch,
):
    monkeypatch.setattr(
        runner,
        "minutes_since_latest",
        lambda **kwargs: 90.0,
    )

    due, reason = (
        runner.collection_due(
            minimum_interval_minutes=120
        )
    )

    assert due is False
    assert "90.0" in reason


def test_due_after_interval(
    monkeypatch,
):
    monkeypatch.setattr(
        runner,
        "minutes_since_latest",
        lambda **kwargs: 150.0,
    )

    due, reason = (
        runner.collection_due(
            minimum_interval_minutes=120
        )
    )

    assert due is True
    assert "150.0" in reason


def test_minutes_since_latest(
    monkeypatch,
):
    latest = pd.Timestamp(
        "2030-01-01T10:00:00Z"
    )

    monkeypatch.setattr(
        runner,
        "latest_snapshot_time",
        lambda: latest,
    )

    elapsed = (
        runner.minutes_since_latest(
            now=datetime(
                2030,
                1,
                1,
                12,
                30,
                tzinfo=timezone.utc,
            )
        )
    )

    assert elapsed == 150.0


def test_downstream_has_no_training():
    flattened = [
        token
        for _, command
        in runner.DOWNSTREAM_STEPS
        for token in command
    ]

    assert (
        "train_model_xgboost_elo.py"
        not in flattened
    )

    assert (
        "save_la_liga_odds_snapshot.py"
        not in flattened
    )


def test_runner_source_has_no_git_mutation():
    source = Path(
        "la_liga_collection_runner.py"
    ).read_text(
        encoding="utf-8"
    )

    forbidden = [
        '"git", "add"',
        '"git", "commit"',
        '"git", "push"',
        "--production",
    ]

    for token in forbidden:
        assert token not in source
