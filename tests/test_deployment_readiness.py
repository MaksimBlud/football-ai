import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_product_snapshot_grants_are_explicit_and_append_only():
    sql = (
        ROOT
        / "supabase/migrations/20260912073000_product_prediction_snapshot_grants.sql"
    ).read_text(encoding="utf-8").lower()

    assert "grant select, insert" in sql
    assert "to service_role" in sql
    assert "revoke update, delete" in sql
    assert "from service_role" in sql
    assert "from anon, authenticated" in sql
    assert "product_prediction_snapshots_id_seq" in sql
    assert "grant usage, select" in sql


def test_product_web_entrypoint_remains_explicit():
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert 'entrypoint = "web_app:app"' in pyproject


def test_vercel_web_dependencies_are_minimal_and_model_free():
    with (ROOT / "pyproject.toml").open("rb") as handle:
        pyproject = tomllib.load(handle)

    dependencies = set(pyproject["project"]["dependencies"])
    assert dependencies == {"fastapi", "supabase", "python-dotenv"}

    forbidden = {
        "xgboost",
        "scikit-learn",
        "pandas",
        "numpy",
        "joblib",
    }
    assert dependencies.isdisjoint(forbidden)


def test_product_frontend_exposes_no_dead_refresh_write_action():
    html = (ROOT / "static/index_v2.html").read_text(encoding="utf-8")

    assert "/refresh-predictions" not in html
    assert 'id="refresh"' not in html
    assert "function refresh()" not in html
    assert "Обновить данные и прогнозы" not in html


def test_clean_web_deploy_has_only_public_supabase_defaults():
    config = (ROOT / "config.py").read_text(encoding="utf-8")

    assert "https://besxwboamipygwvrsblz.supabase.co" in config
    assert "sb_publishable_" in config
    assert 'SUPABASE_KEY = os.getenv("SUPABASE_KEY")' in config
    assert "sb_secret_" not in config
    assert "service_role API key" not in config
