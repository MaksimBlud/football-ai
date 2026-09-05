from pathlib import Path

from multi_market_migration_contract import EXPECTED, audit_migrations


def _write(root: Path, name: str, sql: str) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / name).write_text(sql, encoding="utf-8")


def _policy_sql(table: str) -> str:
    return f"""
    alter table {table} enable row level security;
    create policy "reads" on {table} for select to service_role using (true);
    create policy "inserts" on {table} for insert to service_role with check (true);
    """


def _valid_set(root: Path) -> None:
    _write(
        root,
        EXPECTED[0],
        "create table if not exists public.league_multi_market_snapshots (snapshot_key text primary key);"
        + _policy_sql("public.league_multi_market_snapshots"),
    )
    _write(
        root,
        EXPECTED[1],
        "create table if not exists public.league_multi_market_settlements "
        "(snapshot_key text references public.league_multi_market_snapshots(snapshot_key));"
        + _policy_sql("public.league_multi_market_settlements"),
    )
    _write(
        root,
        EXPECTED[2],
        "create table if not exists public.league_corner_results (corner_result_key text primary key);"
        + _policy_sql("public.league_corner_results"),
    )


def test_repository_multi_market_migrations_pass_static_contract():
    result = audit_migrations()
    assert result["static_contract_ready"] is True
    assert result["blockers"] == []
    assert result["expected_order"] == list(EXPECTED)
    assert result["deployment_path_status"] == "EXTERNAL_ADMIN_PATH_REQUIRED"
    assert result["applies_migrations"] is False
    assert all(row["rls_and_append_only_policy_ready"] for row in result["files"])


def test_destructive_sql_fails_closed(tmp_path):
    _valid_set(tmp_path)
    first = tmp_path / EXPECTED[0]
    first.write_text(first.read_text(encoding="utf-8") + "\ndrop table x;\n", encoding="utf-8")
    result = audit_migrations(tmp_path)
    assert result["static_contract_ready"] is False
    assert any(item.startswith(f"DESTRUCTIVE_SQL:{EXPECTED[0]}:DROP") for item in result["blockers"])


def test_missing_dependency_or_file_fails_closed(tmp_path):
    _valid_set(tmp_path)
    (tmp_path / EXPECTED[2]).unlink()
    second = tmp_path / EXPECTED[1]
    second.write_text(
        "create table if not exists public.league_multi_market_settlements (snapshot_key text);"
        + _policy_sql("public.league_multi_market_settlements"),
        encoding="utf-8",
    )
    result = audit_migrations(tmp_path)
    assert result["static_contract_ready"] is False
    assert "SETTLEMENT_SNAPSHOT_FK_MISSING" in result["blockers"]
    assert f"MISSING:{EXPECTED[2]}" in result["blockers"]


def test_missing_rls_or_service_role_policy_fails_closed(tmp_path):
    _valid_set(tmp_path)
    table = "public.league_corner_results"
    _write(
        tmp_path,
        EXPECTED[2],
        "create table if not exists public.league_corner_results (corner_result_key text primary key);"
        f" alter table {table} enable row level security;"
        f" create policy \"reads\" on {table} for select to service_role using (true);",
    )
    result = audit_migrations(tmp_path)
    assert result["static_contract_ready"] is False
    assert f"SERVICE_ROLE_INSERT_POLICY_MISSING:{table}" in result["blockers"]


def test_update_delete_or_all_policy_is_forbidden(tmp_path):
    _valid_set(tmp_path)
    table = "public.league_multi_market_snapshots"
    first = tmp_path / EXPECTED[0]
    first.write_text(
        first.read_text(encoding="utf-8")
        + f"\ncreate policy \"too broad\" on {table} for update to service_role using (true);\n",
        encoding="utf-8",
    )
    result = audit_migrations(tmp_path)
    assert result["static_contract_ready"] is False
    assert any("POLICY_UPDATE" in blocker for blocker in result["blockers"])
