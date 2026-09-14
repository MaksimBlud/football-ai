import json
from pathlib import Path

import pytest

from total_goals_artifact_registry import (
    ARTIFACT_FAMILY,
    MANIFEST_FILENAME,
    REGISTRY_TABLE,
    STORAGE_BUCKET,
    ArtifactRegistryError,
    build_registry_manifest,
    create_privileged_supabase_client,
    materialize_registered_bundle,
    register_bundle,
)
from total_goals_inference_contract import TOTAL_GOALS_ARTIFACTS


class FakeResponse:
    def __init__(self, data):
        self.data = data


class FakeTable:
    def __init__(self, rows):
        self.rows = rows
        self.mode = "select"
        self.pending = None
        self.key = None
        self.value = None

    def select(self, _columns):
        self.mode = "select"
        return self

    def eq(self, key, value):
        self.key = key
        self.value = value
        return self

    def limit(self, _limit):
        return self

    def insert(self, row):
        self.mode = "insert"
        self.pending = dict(row)
        return self

    def execute(self):
        if self.mode == "insert":
            bundle_sha = self.pending["bundle_sha256"]
            if any(row["bundle_sha256"] == bundle_sha for row in self.rows):
                raise RuntimeError("duplicate")
            self.rows.append(dict(self.pending))
            return FakeResponse([dict(self.pending)])

        rows = self.rows
        if self.key is not None:
            rows = [row for row in rows if row.get(self.key) == self.value]
        return FakeResponse([dict(row) for row in rows])


class FakeBucket:
    def __init__(self):
        self.objects = {}
        self.upload_options = []

    def list(self, prefix, _options):
        start = prefix.rstrip("/") + "/"
        return [
            {"name": path[len(start):]}
            for path in sorted(self.objects)
            if path.startswith(start) and "/" not in path[len(start):]
        ]

    def upload(self, *, path, file, file_options):
        if path in self.objects:
            raise RuntimeError("duplicate object")
        payload = file.read() if hasattr(file, "read") else bytes(file)
        self.objects[path] = bytes(payload)
        self.upload_options.append((path, dict(file_options)))
        return {"path": path}

    def download(self, path):
        if path not in self.objects:
            raise RuntimeError(f"missing: {path}")
        return self.objects[path]


class FakeStorage:
    def __init__(self, bucket):
        self.bucket = bucket
        self.requested = []

    def from_(self, bucket_name):
        self.requested.append(bucket_name)
        assert bucket_name == STORAGE_BUCKET
        return self.bucket


class FakeClient:
    def __init__(self):
        self.rows = []
        self.bucket = FakeBucket()
        self.storage = FakeStorage(self.bucket)

    def table(self, table_name):
        assert table_name == REGISTRY_TABLE
        return FakeTable(self.rows)


def write_bundle(root: Path):
    for index, name in enumerate(TOTAL_GOALS_ARTIFACTS):
        (root / name).write_bytes(f"production-artifact-{index}".encode("utf-8"))


def test_manifest_is_content_addressed_and_covers_all_four_artifacts(tmp_path):
    write_bundle(tmp_path)
    manifest = build_registry_manifest(tmp_path, source_note="existing production bundle")

    assert manifest["artifact_family"] == ARTIFACT_FAMILY
    assert len(manifest["bundle_sha256"]) == 64
    assert manifest["storage_bucket"] == STORAGE_BUCKET
    assert manifest["storage_prefix"] == f"total-goals/{manifest['bundle_sha256']}"
    assert set(manifest["component_hashes"]) == set(TOTAL_GOALS_ARTIFACTS)
    assert set(manifest["objects"]) == set(TOTAL_GOALS_ARTIFACTS)
    assert manifest["manifest_object"].endswith("/manifest.json")
    assert manifest["source_note"] == "existing production bundle"


def test_registration_uploads_once_without_upsert_then_is_idempotent(tmp_path):
    write_bundle(tmp_path)
    client = FakeClient()

    first = register_bundle(client, tmp_path, source_note="manual provenance")
    assert first["status"] == "REGISTERED"
    assert len(client.rows) == 1
    assert len(client.bucket.objects) == len(TOTAL_GOALS_ARTIFACTS) + 1
    assert all(options["upsert"] == "false" for _, options in client.bucket.upload_options)

    upload_count = len(client.bucket.upload_options)
    second = register_bundle(client, tmp_path, source_note="manual provenance")
    assert second["status"] == "ALREADY_REGISTERED"
    assert len(client.bucket.upload_options) == upload_count
    assert len(client.rows) == 1


def test_existing_registry_row_is_not_trusted_when_remote_bytes_are_corrupted(tmp_path):
    write_bundle(tmp_path)
    client = FakeClient()
    result = register_bundle(client, tmp_path)
    manifest = result["manifest"]
    first_name = TOTAL_GOALS_ARTIFACTS[0]
    client.bucket.objects[manifest["objects"][first_name]] = b"corrupted"

    with pytest.raises(ArtifactRegistryError, match="remote artifact SHA mismatch"):
        register_bundle(client, tmp_path)


def test_unregistered_partial_prefix_fails_closed_without_overwrite(tmp_path):
    write_bundle(tmp_path)
    client = FakeClient()
    manifest = build_registry_manifest(tmp_path)
    orphan_path = manifest["objects"][TOTAL_GOALS_ARTIFACTS[0]]
    client.bucket.objects[orphan_path] = b"orphan"

    with pytest.raises(ArtifactRegistryError, match="manual reconciliation required"):
        register_bundle(client, tmp_path)

    assert client.bucket.objects == {orphan_path: b"orphan"}
    assert client.rows == []


def test_materialization_verifies_and_never_promotes_into_production_paths(tmp_path):
    source = tmp_path / "source"
    destination = tmp_path / "materialized"
    source.mkdir()
    write_bundle(source)
    client = FakeClient()
    registered = register_bundle(client, source)

    result = materialize_registered_bundle(
        client,
        registered["manifest"]["bundle_sha256"],
        destination,
    )
    assert result["status"] == "MATERIALIZED"
    assert (destination / MANIFEST_FILENAME).is_file()
    for name in TOTAL_GOALS_ARTIFACTS:
        assert (destination / name).read_bytes() == (source / name).read_bytes()


def test_materialization_refuses_destination_collision(tmp_path):
    source = tmp_path / "source"
    destination = tmp_path / "materialized"
    source.mkdir()
    destination.mkdir()
    write_bundle(source)
    client = FakeClient()
    registered = register_bundle(client, source)
    (destination / TOTAL_GOALS_ARTIFACTS[0]).write_bytes(b"do-not-overwrite")

    with pytest.raises(ArtifactRegistryError, match="destination is not empty"):
        materialize_registered_bundle(
            client,
            registered["manifest"]["bundle_sha256"],
            destination,
        )

    assert (destination / TOTAL_GOALS_ARTIFACTS[0]).read_bytes() == b"do-not-overwrite"


def test_privileged_client_rejects_ambiguous_supabase_key(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "publishable-or-unknown")
    monkeypatch.delenv("SUPABASE_SECRET_KEY", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)

    with pytest.raises(ArtifactRegistryError, match="SUPABASE_SECRET_KEY or SUPABASE_SERVICE_ROLE_KEY"):
        create_privileged_supabase_client()


def test_remote_manifest_is_canonical_json(tmp_path):
    write_bundle(tmp_path)
    client = FakeClient()
    result = register_bundle(client, tmp_path)
    manifest = result["manifest"]
    raw = client.bucket.objects[manifest["manifest_object"]]
    assert raw.endswith(b"\n")
    assert json.loads(raw.decode("utf-8")) == manifest
