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


def test_paid_eredivisie_odds_is_manual_only_and_guarded():
    odds = _read("eredivisie-odds-snapshots.yml")
    assert "workflow_dispatch:" in odds
    assert "cron:" not in odds
    assert "push:" not in odds
    assert "python odds_api_budget_guard.py --max-cost 1" in odds


def test_eredivisie_results_are_provider_free_and_scheduled():
    results = _read("eredivisie-results.yml")
    assert "workflow_dispatch:" in results
    assert 'cron: "23 */12 * * *"' in results
    assert "THE_ODDS_API_KEY" not in results
    assert "odds_api_budget_guard.py" not in results
    assert 'source.provider == "FOOTBALL_DATA_CSV"' in results
    assert 'source.competition_code == "N1"' in results
    assert 'source.season_code == "2627"' in results

    # The downstream live cycle works from already persisted state and remains scheduled.
    assert 'cron: "58 */2 * * *"' in _read("eredivisie-live-cycle.yml")


def test_eredivisie_odds_does_not_collide_with_ligue1_live_cycle():
    ligue1_live = _read("ligue1-live-cycle.yml")
    assert 'cron: "33 */2 * * *"' in ligue1_live
    assert 'cron: "33 */2 * * *"' not in _read("eredivisie-odds-snapshots.yml")
