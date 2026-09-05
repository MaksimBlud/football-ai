from pathlib import Path

from multi_market_migration_contract import EXPECTED, audit_migrations


def _write(root: Path, name: str, sql: str) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / name).write_text(sql, encoding="utf-8")


def test_repository_multi_market_migrations_pass_static_contract():
    result = audit_migrations()
    assert result["static_contract_ready"] is True
    assert result["blockers"] == []
    assert result["expected_order"] == list(EXPECTED)
    assert result["deployment_path_status"] == "EXTERNAL_ADMIN_PATH_REQUIRED"
    assert result["applies_migrations"] is False


def test_destructive_sql_fails_closed(tmp_path):
    _write(tmp_path, EXPECTED[0], "create table if not exists public.league_multi_market_snapshots (snapshot_key text primary key); drop table x;")
    _write(tmp_path, EXPECTED[1], "create table if not exists public.league_multi_market_settlements (snapshot_key text references public.league_multi_market_snapshots(snapshot_key));")
    _write(tmp_path, EXPECTED[2], "create table if not exists public.league_corner_results (corner_result_key text primary key);")
    result = audit_migrations(tmp_path)
    assert result["static_contract_ready"] is False
    assert any(item.startswith(f"DESTRUCTIVE_SQL:{EXPECTED[0]}:DROP") for item in result["blockers"])


def test_missing_dependency_or_file_fails_closed(tmp_path):
    _write(tmp_path, EXPECTED[0], "create table if not exists public.league_multi_market_snapshots (snapshot_key text primary key);")
    _write(tmp_path, EXPECTED[1], "create table if not exists public.league_multi_market_settlements (snapshot_key text);")
    result = audit_migrations(tmp_path)
    assert result["static_contract_ready"] is False
    assert "SETTLEMENT_SNAPSHOT_FK_MISSING" in result["blockers"]
    assert f"MISSING:{EXPECTED[2]}" in result["blockers"]
