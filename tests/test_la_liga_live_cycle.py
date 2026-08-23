from pathlib import Path

import la_liga_live_cycle as cycle


def test_step_shape():
    result = cycle.step(
        "PASS",
        "ok",
    )

    assert (
        result["status"]
        == "PASS"
    )

    assert (
        result["detail"]
        == "ok"
    )


def test_production_artifacts_are_explicit():
    assert (
        "football_model_xgboost_elo.pkl"
        in cycle.PRODUCTION_ARTIFACTS
    )


def test_runner_exposes_skip_collection():
    import inspect

    source = inspect.getsource(
        cycle.main
    )

    assert (
        "--skip-collection"
        in source
    )


def test_runner_contains_no_training_or_promotion():
    import inspect

    source = inspect.getsource(
        cycle
    )

    forbidden = [
        "train_model",
        "artifact_lifecycle.py promote",
        "git push",
        "git commit",
    ]

    for token in forbidden:
        assert (
            token
            not in source
        )


def test_summary_accepts_wait(capsys):
    result = {
        "status": "PASS",
        "steps": {
            "collection": {
                "status": "SKIP",
                "detail": "",
            },
            "results": {
                "status": "WAIT",
                "detail":
                    "WAITING_FOR_RESULTS_SOURCE",
            },
            "evaluation": {
                "status": "WAIT",
                "detail":
                    "NO_SETTLED_MATCHES",
            },
        },
        "metrics": {},
        "production_unchanged":
            True,
    }

    cycle.print_summary(
        result
    )

    captured = capsys.readouterr()

    assert (
        "WAITING_FOR_RESULTS_SOURCE"
        in captured.out
    )

    assert (
        "NO_SETTLED_MATCHES"
        in captured.out
    )


def test_expected_paths_are_research_paths():
    assert (
        "experiments"
        in cycle.STRUCTURAL_PATH.parts
    )

    assert (
        "experiments"
        in cycle.HISTORY_PATH.parts
    )

    assert (
        cycle.RESULTS_PATH.name
        == "la_liga_2026_2027_results.csv"
    )


def test_legacy_main_does_not_receive_parent_cli_args(
    monkeypatch,
):
    import sys

    received = []

    def legacy_main():
        received.extend(
            sys.argv[1:]
        )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "la_liga_live_cycle.py",
            "--skip-collection",
        ],
    )

    cycle.call_legacy_main(
        legacy_main
    )

    assert received == []

    assert sys.argv == [
        "la_liga_live_cycle.py",
        "--skip-collection",
    ]


def test_legacy_system_exit_becomes_runtime_error():
    import pytest

    def legacy_main():
        raise SystemExit(2)

    with pytest.raises(
        RuntimeError,
        match="legacy main exited",
    ):
        cycle.call_legacy_main(
            legacy_main
        )
