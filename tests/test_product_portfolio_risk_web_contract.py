from pathlib import Path


def test_web_app_exposes_read_only_portfolio_risk_view():
    source = Path("web_app.py").read_text(encoding="utf-8")

    assert 'from product_portfolio_risk import PORTFOLIO_RISK_SCHEMA_VERSION, build_portfolio_risk_view' in source
    assert '@app.get("/portfolio-risk-view")' in source
    assert "return build_portfolio_risk_view(product_market_view())" in source
    assert '"portfolio_risk_version": PORTFOLIO_RISK_SCHEMA_VERSION' in source


def test_portfolio_endpoint_does_not_define_write_or_staking_side_effects():
    source = Path("web_app.py").read_text(encoding="utf-8")
    module = Path("product_portfolio_risk.py").read_text(encoding="utf-8")

    assert "insert(" not in source.lower()
    assert "update(" not in source.lower()
    assert "delete(" not in source.lower()
    assert '"kelly_sizing_enabled": False' in module
    assert '"stake_sizing_policy_defined": False' in module
    assert '"bankroll_policy_defined": False' in module
