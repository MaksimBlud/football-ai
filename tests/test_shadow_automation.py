import hashlib
import sys
from pathlib import Path
from subprocess import CompletedProcess

import shadow_automation


PRODUCTION_ARTIFACTS = (
    "football_model_xgboost_elo.pkl",
    "football_model_no_odds.pkl",
    "1x2_calibrator.pkl",
    "home_goals_model_no_odds.pkl",
    "away_goals_model_no_odds.pkl",
    "over_2_5_calibrator.pkl",
    "btts_calibrator.pkl",
)


def digest(path):
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def test_scheduler_uses_single_success_gated_shadow_wrapper():
    scheduler = (
        Path(__file__).parents[1]
        / "scheduled_odds_snapshot.py"
    ).read_text()

    assert (
        scheduler.count(
            "run_with_shadow("
        )
        == 1
    )

    assert (
        '["save_odds_snapshot.py"]'
        in scheduler
    )

    assert (
        "generate_upcoming_challenger_shadow.py"
        not in scheduler
    )


def test_shadow_runs_after_success_with_current_interpreter():
    commands = []

    def runner(command, **kwargs):
        commands.append(
            (
                command,
                kwargs,
            )
        )

        return CompletedProcess(
            command,
            0,
        )

    result = (
        shadow_automation.run_with_shadow(
            [
                "save_odds_snapshot.py"
            ],
            runner=runner,
        )
    )

    assert result == 0

    assert commands == [
        (
            [
                sys.executable,
                "save_odds_snapshot.py",
            ],
            {
                "check": False,
            },
        ),
        (
            [
                sys.executable,
                "generate_upcoming_challenger_shadow.py",
            ],
            {
                "check": False,
            },
        ),
    ]


def test_shadow_does_not_run_after_upstream_failure(
    capsys,
):
    commands = []

    def runner(command, **kwargs):
        commands.append(
            command
        )

        return CompletedProcess(
            command,
            17,
        )

    result = (
        shadow_automation.run_with_shadow(
            [
                "save_odds_snapshot.py"
            ],
            runner=runner,
        )
    )

    assert result == 17

    assert commands == [
        [
            sys.executable,
            "save_odds_snapshot.py",
        ]
    ]

    assert (
        "shadow generation skipped"
        in capsys.readouterr().out
    )


def test_shadow_failure_warns_but_preserves_upstream_success(
    capsys,
):
    returncodes = iter(
        (
            0,
            9,
        )
    )

    def runner(command, **kwargs):
        return CompletedProcess(
            command,
            next(returncodes),
        )

    result = (
        shadow_automation.run_with_shadow(
            [
                "save_odds_snapshot.py"
            ],
            runner=runner,
        )
    )

    assert result == 0

    output = (
        capsys.readouterr().out
    )

    assert (
        "WARNING"
        in output
    )

    assert (
        "shadow generation failed"
        in output
    )

    assert (
        "exit code 9"
        in output
    )


def test_wrapper_does_not_write_production_artifacts(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(
        tmp_path
    )

    artifacts = {}

    for name in PRODUCTION_ARTIFACTS:
        path = Path(
            name
        )

        path.write_bytes(
            f"unchanged:{name}".encode()
        )

        artifacts[
            name
        ] = digest(
            path
        )

    def runner(
        command,
        **kwargs,
    ):
        if (
            command[-1]
            == shadow_automation.SHADOW_SCRIPT
        ):
            output = Path(
                "experiments/"
                "upcoming_challenger_shadow.csv"
            )

            output.parent.mkdir()

            output.write_text(
                "shadow_only\ntrue\n"
            )

        return CompletedProcess(
            command,
            0,
        )

    assert (
        shadow_automation.run_with_shadow(
            [
                "save_odds_snapshot.py"
            ],
            runner=runner,
        )
        == 0
    )

    assert {
        name: digest(
            Path(
                name
            )
        )
        for name
        in PRODUCTION_ARTIFACTS
    } == artifacts

    assert sorted(
        path.name
        for path
        in Path(".").glob(
            "*.pkl"
        )
    ) == sorted(
        PRODUCTION_ARTIFACTS
    )
