"""Private immutable registry helpers for the Total Goals artifact bundle.

The registry transports already-existing production artifacts; it does not train,
promote, or execute them. Network operations require an explicitly supplied
privileged Supabase client. Bundle identity is delegated to the frozen
``total_goals_inference_contract``.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
from typing import Any, Mapping

from total_goals_inference_contract import (
    BUNDLE_VERSION,
    CONTRACT_VERSION,
    TOTAL_GOALS_ARTIFACTS,
    TotalGoalsContractError,
    bundle_sha256_from_hashes,
    inspect_artifact_bundle,
    validate_component_hashes,
)


REGISTRY_VERSION = "model-artifact-registry.v1"
ARTIFACT_FAMILY = "total_goals"
STORAGE_BUCKET = "model-artifacts"
REGISTRY_TABLE = "model_artifact_bundles"
MANIFEST_FILENAME = "manifest.json"


class ArtifactRegistryError(RuntimeError):
    """Raised when registry state is incomplete, mutable, or inconsistent."""


def _canonical_json_bytes(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def build_registry_manifest(root: str | Path, *, source_note: str | None = None) -> dict[str, Any]:
    """Build a deterministic manifest from the real four-file local bundle."""

    report = inspect_artifact_bundle(root)
    bundle_sha = str(report["bundle_sha256"])
    component_hashes = validate_component_hashes(report["artifacts"])
    prefix = f"total-goals/{bundle_sha}"

    return {
        "registry_version": REGISTRY_VERSION,
        "artifact_family": ARTIFACT_FAMILY,
        "inference_contract_version": CONTRACT_VERSION,
        "bundle_version": BUNDLE_VERSION,
        "bundle_sha256": bundle_sha,
        "component_hashes": component_hashes,
        "storage_bucket": STORAGE_BUCKET,
        "storage_prefix": prefix,
        "objects": {
            name: f"{prefix}/{name}"
            for name in TOTAL_GOALS_ARTIFACTS
        },
        "manifest_object": f"{prefix}/{MANIFEST_FILENAME}",
        "feature_names": list(report["feature_names"]),
        "feature_count": int(report["feature_count"]),
        "source_note": (source_note.strip() if source_note and source_note.strip() else None),
    }


def normalize_expected_bundle_sha256(value: str) -> str:
    """Normalize and validate an operator-supplied expected bundle identity."""

    digest = str(value).strip().lower()
    if len(digest) != 64:
        raise ArtifactRegistryError("expected bundle SHA must be a 64-character SHA-256")
    try:
        int(digest, 16)
    except ValueError as error:
        raise ArtifactRegistryError("expected bundle SHA must be hexadecimal") from error
    return digest


def validate_expected_bundle_sha256(
    manifest: Mapping[str, Any],
    expected_bundle_sha256: str,
) -> str:
    """Fail before network access when local files are not the expected bundle."""

    expected = normalize_expected_bundle_sha256(expected_bundle_sha256)
    actual = str(manifest.get("bundle_sha256") or "").strip().lower()
    if actual != expected:
        raise ArtifactRegistryError(
            "local Total Goals bundle does not match expected SHA: "
            f"expected={expected}, actual={actual or 'missing'}"
        )
    return expected


def registry_row(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Return the append-only metadata row written after Storage verification."""

    _validate_manifest_identity(manifest)
    return {
        "bundle_sha256": manifest["bundle_sha256"],
        "bundle_version": manifest["bundle_version"],
        "artifact_family": manifest["artifact_family"],
        "storage_bucket": manifest["storage_bucket"],
        "storage_prefix": manifest["storage_prefix"],
        "component_hashes": manifest["component_hashes"],
        "manifest": dict(manifest),
        "source_note": manifest.get("source_note"),
    }


def _validate_manifest_identity(manifest: Mapping[str, Any]) -> None:
    if manifest.get("registry_version") != REGISTRY_VERSION:
        raise ArtifactRegistryError("unsupported registry version")
    if manifest.get("artifact_family") != ARTIFACT_FAMILY:
        raise ArtifactRegistryError("unexpected artifact family")
    if manifest.get("inference_contract_version") != CONTRACT_VERSION:
        raise ArtifactRegistryError("unexpected inference contract version")
    if manifest.get("bundle_version") != BUNDLE_VERSION:
        raise ArtifactRegistryError("unexpected bundle version")
    if manifest.get("storage_bucket") != STORAGE_BUCKET:
        raise ArtifactRegistryError("unexpected Storage bucket")

    try:
        hashes = validate_component_hashes(manifest.get("component_hashes") or {})
    except TotalGoalsContractError as error:
        raise ArtifactRegistryError(str(error)) from error

    computed = bundle_sha256_from_hashes(hashes)
    if manifest.get("bundle_sha256") != computed:
        raise ArtifactRegistryError("manifest bundle SHA does not match component hashes")

    expected_prefix = f"total-goals/{computed}"
    if manifest.get("storage_prefix") != expected_prefix:
        raise ArtifactRegistryError("manifest storage prefix is not content-addressed")

    expected_objects = {name: f"{expected_prefix}/{name}" for name in TOTAL_GOALS_ARTIFACTS}
    if manifest.get("objects") != expected_objects:
        raise ArtifactRegistryError("manifest object map does not match the frozen bundle")
    if manifest.get("manifest_object") != f"{expected_prefix}/{MANIFEST_FILENAME}":
        raise ArtifactRegistryError("manifest object path is invalid")


def _query_registered_row(client: Any, bundle_sha: str) -> dict[str, Any] | None:
    response = (
        client.table(REGISTRY_TABLE)
        .select("*")
        .eq("bundle_sha256", bundle_sha)
        .limit(1)
        .execute()
    )
    rows = getattr(response, "data", None) or []
    if len(rows) > 1:
        raise ArtifactRegistryError("registry returned duplicate primary-key rows")
    return dict(rows[0]) if rows else None


def _validate_registered_row(row: Mapping[str, Any], manifest: Mapping[str, Any]) -> None:
    expected = registry_row(manifest)
    for key in (
        "bundle_sha256",
        "bundle_version",
        "artifact_family",
        "storage_bucket",
        "storage_prefix",
        "component_hashes",
        "manifest",
        "source_note",
    ):
        if row.get(key) != expected.get(key):
            raise ArtifactRegistryError(f"registered metadata differs for {key}")


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def verify_remote_bundle(client: Any, manifest: Mapping[str, Any]) -> None:
    """Download and hash every private object; never trust object names alone."""

    _validate_manifest_identity(manifest)
    bucket = client.storage.from_(STORAGE_BUCKET)
    hashes = validate_component_hashes(manifest["component_hashes"])

    for name in TOTAL_GOALS_ARTIFACTS:
        payload = bucket.download(manifest["objects"][name])
        if not isinstance(payload, (bytes, bytearray)):
            raise ArtifactRegistryError(f"Storage download for {name} did not return bytes")
        if _sha256_bytes(bytes(payload)) != hashes[name]:
            raise ArtifactRegistryError(f"remote artifact SHA mismatch: {name}")

    remote_manifest = bucket.download(manifest["manifest_object"])
    if not isinstance(remote_manifest, (bytes, bytearray)):
        raise ArtifactRegistryError("remote manifest download did not return bytes")
    if bytes(remote_manifest) != _canonical_json_bytes(manifest):
        raise ArtifactRegistryError("remote manifest bytes differ from canonical manifest")


def register_bundle(
    client: Any,
    root: str | Path,
    *,
    source_note: str | None = None,
    expected_bundle_sha256: str | None = None,
) -> dict[str, Any]:
    """Upload once with no overwrite, verify bytes, then append metadata.

    When ``expected_bundle_sha256`` is supplied it is checked against freshly
    hashed local files before the first database or Storage request. Existing
    matching registry rows are treated idempotently only after all remote bytes
    re-verify. Unregistered objects under the deterministic prefix are a
    fail-closed partial-state blocker; this function never deletes them.
    """

    root_path = Path(root)
    manifest = build_registry_manifest(root_path, source_note=source_note)
    if expected_bundle_sha256 is not None:
        validate_expected_bundle_sha256(manifest, expected_bundle_sha256)
    bundle_sha = manifest["bundle_sha256"]

    existing = _query_registered_row(client, bundle_sha)
    if existing is not None:
        _validate_registered_row(existing, manifest)
        verify_remote_bundle(client, manifest)
        return {"status": "ALREADY_REGISTERED", "manifest": manifest}

    bucket = client.storage.from_(STORAGE_BUCKET)
    existing_objects = bucket.list(manifest["storage_prefix"], {"limit": 100, "offset": 0})
    if existing_objects:
        names = sorted(str(item.get("name")) for item in existing_objects if isinstance(item, dict))
        raise ArtifactRegistryError(
            "unregistered objects already exist under immutable prefix; "
            f"manual reconciliation required: {names}"
        )

    for name in TOTAL_GOALS_ARTIFACTS:
        with (root_path / name).open("rb") as handle:
            bucket.upload(
                path=manifest["objects"][name],
                file=handle,
                file_options={
                    "cache-control": "31536000",
                    "content-type": "application/octet-stream",
                    "upsert": "false",
                },
            )

    bucket.upload(
        path=manifest["manifest_object"],
        file=io.BytesIO(_canonical_json_bytes(manifest)),
        file_options={
            "cache-control": "31536000",
            "content-type": "application/json",
            "upsert": "false",
        },
    )

    verify_remote_bundle(client, manifest)

    row = registry_row(manifest)
    try:
        client.table(REGISTRY_TABLE).insert(row).execute()
    except Exception as error:
        raced = _query_registered_row(client, bundle_sha)
        if raced is None:
            raise ArtifactRegistryError(
                "Storage objects verified but metadata insert failed; immutable prefix must be reconciled"
            ) from error
        _validate_registered_row(raced, manifest)
        verify_remote_bundle(client, manifest)
        return {"status": "ALREADY_REGISTERED", "manifest": manifest}

    stored = _query_registered_row(client, bundle_sha)
    if stored is None:
        raise ArtifactRegistryError("metadata insert returned but registry row is not readable")
    _validate_registered_row(stored, manifest)
    return {"status": "REGISTERED", "manifest": manifest}


def materialize_registered_bundle(
    client: Any,
    bundle_sha256: str,
    destination: str | Path,
) -> dict[str, Any]:
    """Download a registered bundle to an empty destination and verify all hashes."""

    digest = bundle_sha256.strip().lower()
    if len(digest) != 64:
        raise ArtifactRegistryError("bundle SHA must be a 64-character SHA-256")
    try:
        int(digest, 16)
    except ValueError as error:
        raise ArtifactRegistryError("bundle SHA must be hexadecimal") from error

    row = _query_registered_row(client, digest)
    if row is None:
        raise ArtifactRegistryError("bundle is not registered")
    manifest = row.get("manifest")
    if not isinstance(manifest, dict):
        raise ArtifactRegistryError("registry manifest is missing or invalid")
    _validate_registered_row(row, manifest)
    verify_remote_bundle(client, manifest)

    destination_path = Path(destination)
    destination_path.mkdir(parents=True, exist_ok=True)
    collisions = [name for name in (*TOTAL_GOALS_ARTIFACTS, MANIFEST_FILENAME) if (destination_path / name).exists()]
    if collisions:
        raise ArtifactRegistryError(f"destination is not empty for bundle files: {collisions}")

    bucket = client.storage.from_(STORAGE_BUCKET)
    for name in TOTAL_GOALS_ARTIFACTS:
        payload = bytes(bucket.download(manifest["objects"][name]))
        if _sha256_bytes(payload) != manifest["component_hashes"][name]:
            raise ArtifactRegistryError(f"downloaded artifact SHA mismatch: {name}")
        temporary = destination_path / f".{name}.partial"
        temporary.write_bytes(payload)
        temporary.replace(destination_path / name)

    (destination_path / MANIFEST_FILENAME).write_bytes(_canonical_json_bytes(manifest))
    local = inspect_artifact_bundle(destination_path)
    if local["bundle_sha256"] != digest:
        raise ArtifactRegistryError("materialized bundle identity does not match registry key")
    return {"status": "MATERIALIZED", "manifest": manifest, "destination": str(destination_path)}


def create_privileged_supabase_client() -> Any:
    """Create a server-side client only from an explicitly privileged key."""

    url = (os.getenv("SUPABASE_URL") or "").strip()
    secret = (
        os.getenv("SUPABASE_SECRET_KEY")
        or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        or ""
    ).strip()
    if not url:
        raise ArtifactRegistryError("SUPABASE_URL is required for registry network access")
    if not secret:
        raise ArtifactRegistryError(
            "SUPABASE_SECRET_KEY or SUPABASE_SERVICE_ROLE_KEY is required; SUPABASE_KEY is not accepted"
        )

    from supabase import create_client

    return create_client(url, secret)
