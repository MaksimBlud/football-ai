from pathlib import Path


WORKFLOWS = (
    "eredivisie-odds-snapshots.yml",
    "eredivisie-live-cycle.yml",
    "eredivisie-results.yml",
)


def _read(name: str) -> str:
    return (Path(__file__).parents[1] / ".github" / "workflows" / name).read_text()


def test_operational_workflows_enforce_market_only_safety():
    for name in WORKFLOWS:
        source = _read(name)
        assert 'CALIBRATION_REQUIRED' in source
        assert 'structural_alpha is None' in source
        assert 'edge_threshold is None' in source
        assert 'Eredivisie remains MARKET_ONLY' in source


def test_operational_workflows_do_not_load_or_train_production_models():
    forbidden = (
        "football_model_xgboost_elo.pkl",
        "joblib.load",
        "train_model",
        "--production",
    )
    for name in WORKFLOWS:
        source = _read(name)
        for token in forbidden:
            assert token not in source


def test_workflow_schedules_are_non_overlapping():
    assert 'cron: "33 */2 * * *"' in _read("eredivisie-odds-snapshots.yml")
    assert 'cron: "58 */2 * * *"' in _read("eredivisie-live-cycle.yml")
    assert 'cron: "23 */12 * * *"' in _read("eredivisie-results.yml")
