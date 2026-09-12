from pathlib import Path


def test_web_app_exposes_read_only_production_readiness_view():
    source = Path("web_app.py").read_text(encoding="utf-8")

    assert "from product_production_readiness import PRODUCTION_READINESS_VERSION" in source
    assert '@app.get("/production-readiness-view")' in source
    assert 'return product_market_view()["production_readiness"]' in source
    assert '"production_readiness_version": PRODUCTION_READINESS_VERSION' in source


def test_production_readiness_contract_is_governance_only_and_outcome_blind():
    source = Path("product_production_readiness.py").read_text(encoding="utf-8")

    assert '"reads_research_outcomes": False' in source
    assert '"changes_market_readiness": False' in source
    assert '"changes_decision_tier": False' in source
    assert '"promotes_model": False' in source
    assert '"promotes_market": False' in source
    assert '"creates_bet_recommendation": False' in source

    lowered = source.lower()
    assert "league_finished_results" not in lowered
    assert "execute_sql" not in lowered
    assert ".insert(" not in lowered
    assert ".update(" not in lowered
    assert ".delete(" not in lowered
