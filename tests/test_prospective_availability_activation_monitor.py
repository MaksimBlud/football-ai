from pathlib import Path

import prospective_availability_activation_monitor as monitor


def test_activation_monitor_never_enables_collection(monkeypatch, tmp_path):
    monkeypatch.setattr(monitor, "OUTPUT_DIR", tmp_path)
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "key")
    monkeypatch.setenv("API_FOOTBALL_KEY", "provider")
    monkeypatch.setattr(monitor, "_schema_state", lambda url, key: {
        table: {"ready": True, "status_code": 200} for table in monitor.TABLES
    })
    monkeypatch.setattr(monitor, "_provider_state", lambda key: {
        league: {"ready": True} for league, *_ in monitor.LEAGUES
    })
    payload = monitor.run()
    assert payload["status"] == "READY"
    assert payload["automatic_activation"] is False
    assert payload["automatic_collection_enablement"] is False
    assert (tmp_path / "activation_readiness.json").is_file()


def test_activation_monitor_reports_blocked_without_throwing(monkeypatch, tmp_path):
    monkeypatch.setattr(monitor, "OUTPUT_DIR", tmp_path)
    for name in ("SUPABASE_URL", "SUPABASE_KEY", "API_FOOTBALL_KEY"):
        monkeypatch.delenv(name, raising=False)
    payload = monitor.run()
    assert payload["status"] == "BLOCKED"
    assert payload["schema"] == {}
    assert payload["provider"] == {}


def test_activation_workflow_is_read_only_and_scheduled():
    text = Path(".github/workflows/prospective-availability-activation-monitor.yml").read_text()
    assert "schedule:" in text
    assert "permissions:\n  contents: read" in text
    assert "Run read-only activation monitor" in text
    assert "prospective_availability_activation_monitor.py" in text
    assert "PROSPECTIVE_AVAILABILITY_ENABLED" not in text
