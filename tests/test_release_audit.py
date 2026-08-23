from pathlib import Path

import release_audit


def test_release_audit_has_no_external_write_commands():
    source = Path(
        "release_audit.py"
    ).read_text(
        encoding="utf-8"
    )

    forbidden = [
        "train_model_xgboost_elo.py",
        '"git", "add"',
        '"git", "commit"',
        '"git", "push"',
        "--production",
    ]

    for token in forbidden:
        assert token not in source


def test_known_blockers_are_explicit(
    monkeypatch,
):
    monkeypatch.setattr(
        release_audit.project_cycle,
        "_la_liga_collection_status",
        lambda: (
            False,
            "MANUAL_ONLY",
        ),
    )

    monkeypatch.setattr(
        release_audit.project_cycle,
        "_la_liga_prediction_status",
        lambda: (
            False,
            "NOT_READY",
        ),
    )

    checks = (
        release_audit
        .known_release_blockers()
    )

    names = {
        check.name
        for check in checks
        if not check.passed
    }

    assert names == {
        "la_liga_automated_collection",
        "la_liga_prediction_runtime",
    }


def test_report_restricted_to_experiments(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        release_audit,
        "ROOT",
        tmp_path,
    )

    (
        tmp_path
        / "experiments"
    ).mkdir()

    audit = {
        "audit_passed": True,
    }

    try:
        release_audit.write_report(
            audit,
            Path("outside.json"),
        )

    except ValueError:
        pass

    else:
        raise AssertionError(
            "outside report should fail"
        )


def test_audit_can_pass_with_known_v1_blockers(
    monkeypatch,
):
    monkeypatch.setattr(
        release_audit,
        "production_artifact_checks",
        lambda: [],
    )

    monkeypatch.setattr(
        release_audit,
        "database_checks",
        lambda: [],
    )

    monkeypatch.setattr(
        release_audit,
        "research_history_checks",
        lambda: [],
    )

    monkeypatch.setattr(
        release_audit,
        "runtime_checks",
        lambda: [],
    )

    monkeypatch.setattr(
        release_audit,
        "working_tree_warnings",
        lambda: [],
    )

    monkeypatch.setattr(
        release_audit,
        "known_release_blockers",
        lambda: [
            release_audit.AuditCheck(
                name="future_blocker",
                passed=False,
                detail="not ready",
                severity="V1_BLOCKER",
            )
        ],
    )

    result = (
        release_audit.build_audit()
    )

    assert (
        result["audit_passed"]
        is True
    )

    assert (
        result["release_ready"]
        is False
    )
