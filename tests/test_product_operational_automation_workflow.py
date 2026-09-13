from pathlib import Path


def test_product_operational_workflow_is_scheduled_and_manual():
    source = Path(
        ".github/workflows/product-operational-automation.yml"
    ).read_text(encoding="utf-8")

    assert "workflow_dispatch:" in source
    assert 'cron: "37 */2 * * *"' in source
    assert "group: product-operational-automation-v1" in source
    assert "cancel-in-progress: false" in source
    assert "contents: read" in source


def test_product_operational_workflow_uses_only_existing_private_supabase_contract():
    source = Path(
        ".github/workflows/product-operational-automation.yml"
    ).read_text(encoding="utf-8")

    assert "secrets.SUPABASE_URL" in source
    assert "secrets.SUPABASE_KEY" in source
    assert "THE_ODDS_API_KEY" not in source
    assert "API_FOOTBALL_KEY" not in source


def test_product_operational_workflow_cannot_run_provider_collection_or_model_work():
    source = Path(
        ".github/workflows/product-operational-automation.yml"
    ).read_text(encoding="utf-8")

    forbidden = (
        "epl_ai_market_pair_cycle.py",
        "predict_upcoming_round.py",
        "train_model",
        "collect_odds",
        "the-odds-api",
    )
    lowered = source.lower()
    for token in forbidden:
        assert token.lower() not in lowered

    assert "python run_product_operational_cycle.py" in source
    assert "--publish" in source


def test_runner_has_no_provider_or_model_execution_imports():
    source = Path("run_product_operational_cycle.py").read_text(encoding="utf-8")
    lowered = source.lower()

    assert "the_odds_api" not in lowered
    assert "requests.get" not in lowered
    assert "predict_upcoming_round" not in lowered
    assert "train_model" not in lowered
    assert "epl_ai_market_pair_cycle" not in lowered
    assert "league_finished_results" not in source
    assert "load_live_inputs" in source
