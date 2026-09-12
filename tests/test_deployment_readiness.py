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


def test_product_frontend_is_read_only():
    html = (ROOT / "static/index_v2.html").read_text(encoding="utf-8")

    assert "/refresh-predictions" not in html
    assert 'id="refresh"' not in html
    assert "function refresh()" not in html
    assert "Обновить данные и прогнозы" not in html


def test_product_web_entrypoint_remains_explicit():
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert 'entrypoint = "web_app:app"' in pyproject
