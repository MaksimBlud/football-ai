from research_agent_gemini import allowed_roots, parse_porcelain, validate_gemini_status


def test_issue_roots_are_isolated():
    assert allowed_roots(428) == (
        "research/agent_runs/issue_428/",
        "tests/agent_runs/issue_428/",
        "docs/agent_runs/issue_428/",
    )


def test_safe_issue_changes_pass():
    status = (
        "?? research/agent_runs/issue_428/preregistration.json\n"
        "?? tests/agent_runs/issue_428/test_contract.py\n"
        "?? docs/agent_runs/issue_428/REPORT.md\n"
    )
    result = validate_gemini_status(status, 428)
    assert result.ok


def test_root_source_change_is_blocked():
    result = validate_gemini_status(" M api.py\n", 428)
    assert not result.ok
    assert any("outside issue sandbox" in error for error in result.errors)


def test_production_artifact_change_is_blocked():
    result = validate_gemini_status(" M football_model_xgboost_elo.pkl\n", 428)
    assert not result.ok


def test_delete_or_rename_is_blocked():
    delete = validate_gemini_status(" D research/agent_runs/issue_428/old.py\n", 428)
    rename = validate_gemini_status("R  research/agent_runs/issue_428/a.py -> research/agent_runs/issue_428/b.py\n", 428)
    assert not delete.ok
    assert not rename.ok


def test_other_issue_directory_is_blocked():
    result = validate_gemini_status(
        "?? research/agent_runs/issue_429/preregistration.json\n",
        428,
    )
    assert not result.ok


def test_porcelain_parser_preserves_spaces_in_path():
    entries = parse_porcelain("?? docs/agent_runs/issue_428/report notes.md\n")
    assert entries[0].path == "docs/agent_runs/issue_428/report notes.md"
