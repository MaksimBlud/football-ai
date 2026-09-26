from research_agent_safety import (
    merge_results,
    validate_changed_paths,
    validate_commands,
    validate_mode,
)


def test_v1_only_allows_historical_read_only_mode():
    assert validate_mode("historical_read_only").ok
    assert not validate_mode("live_write").ok


def test_promotion_command_is_blocked():
    result = validate_commands(["python artifact_lifecycle.py promote --candidate x.pkl"])
    assert not result.ok
    assert any("promote" in error for error in result.errors)


def test_production_artifact_change_is_blocked():
    result = validate_changed_paths(["football_model_xgboost_elo.pkl"])
    assert not result.ok


def test_runtime_mutation_is_blocked():
    result = validate_changed_paths(["turkey_super_lig_runtime_config.py"])
    assert not result.ok


def test_safe_research_paths_pass():
    result = validate_changed_paths([
        "research/new_signal_v1.json",
        "tests/test_new_signal_v1.py",
        "docs/NEW_SIGNAL_V1.md",
    ])
    assert result.ok


def test_merge_results_collects_failures():
    result = merge_results(validate_mode("live_write"), validate_commands(["echo ok"]))
    assert not result.ok
