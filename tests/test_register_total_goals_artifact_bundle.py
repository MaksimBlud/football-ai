import sys
from pathlib import Path

import pytest

import register_total_goals_artifact_bundle as cli
from total_goals_artifact_registry import ArtifactRegistryError, build_registry_manifest
from total_goals_inference_contract import TOTAL_GOALS_ARTIFACTS


def write_bundle(root: Path):
    for index, name in enumerate(TOTAL_GOALS_ARTIFACTS):
        (root / name).write_bytes(f"production-artifact-{index}".encode("utf-8"))


def test_execute_requires_explicit_expected_bundle_sha_before_client_creation(tmp_path, monkeypatch):
    write_bundle(tmp_path)
    client_calls = []
    monkeypatch.setattr(cli, "create_privileged_supabase_client", lambda: client_calls.append(True))
    monkeypatch.setattr(
        sys,
        "argv",
        ["register_total_goals_artifact_bundle.py", "--root", str(tmp_path), "--execute"],
    )

    with pytest.raises(SystemExit) as error:
        cli.main()

    assert error.value.code == 2
    assert client_calls == []


def test_dry_run_can_assert_expected_bundle_without_network(tmp_path, monkeypatch, capsys):
    write_bundle(tmp_path)
    expected = build_registry_manifest(tmp_path)["bundle_sha256"]
    client_calls = []
    monkeypatch.setattr(cli, "create_privileged_supabase_client", lambda: client_calls.append(True))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "register_total_goals_artifact_bundle.py",
            "--root",
            str(tmp_path),
            "--expected-bundle-sha",
            expected,
        ],
    )

    assert cli.main() == 0
    assert client_calls == []
    output = capsys.readouterr().out
    assert '"status": "DRY_RUN"' in output
    assert expected in output


def test_dry_run_rejects_mismatched_expected_bundle_without_network(tmp_path, monkeypatch):
    write_bundle(tmp_path)
    client_calls = []
    monkeypatch.setattr(cli, "create_privileged_supabase_client", lambda: client_calls.append(True))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "register_total_goals_artifact_bundle.py",
            "--root",
            str(tmp_path),
            "--expected-bundle-sha",
            "0" * 64,
        ],
    )

    with pytest.raises(ArtifactRegistryError, match="does not match expected SHA"):
        cli.main()

    assert client_calls == []


def test_execute_forwards_expected_sha_to_registry(tmp_path, monkeypatch, capsys):
    write_bundle(tmp_path)
    expected = build_registry_manifest(tmp_path)["bundle_sha256"]
    sentinel_client = object()
    captured = {}

    monkeypatch.setattr(cli, "create_privileged_supabase_client", lambda: sentinel_client)

    def fake_register(client, root, *, source_note=None, expected_bundle_sha256=None):
        captured.update(
            client=client,
            root=root,
            source_note=source_note,
            expected_bundle_sha256=expected_bundle_sha256,
        )
        return {"status": "REGISTERED", "manifest": build_registry_manifest(root, source_note=source_note)}

    monkeypatch.setattr(cli, "register_bundle", fake_register)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "register_total_goals_artifact_bundle.py",
            "--root",
            str(tmp_path),
            "--source-note",
            "audited production bundle",
            "--expected-bundle-sha",
            expected,
            "--execute",
        ],
    )

    assert cli.main() == 0
    assert captured["client"] is sentinel_client
    assert captured["root"] == tmp_path
    assert captured["source_note"] == "audited production bundle"
    assert captured["expected_bundle_sha256"] == expected
    assert '"status": "REGISTERED"' in capsys.readouterr().out
