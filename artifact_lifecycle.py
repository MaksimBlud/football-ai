"""Safe creation, verification, and explicit promotion of model artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import joblib


NO_ODDS_FEATURES = [
    "home_last5_points", "away_last5_points", "form_difference",
    "home_goals_scored_last5", "home_goals_conceded_last5",
    "away_goals_scored_last5", "away_goals_conceded_last5",
    "home_shots_last5", "away_shots_last5", "home_shots_target_last5",
    "away_shots_target_last5", "home_elo", "away_elo", "elo_difference",
    "home_venue_win_rate", "away_venue_win_rate",
    "home_venue_goals_scored", "away_venue_goals_scored",
]

ARTIFACT_SPECS = {
    "football_model_xgboost_elo.pkl": {
        "type": "xgboost_1x2_classifier",
        "features": ["home_odds", "draw_odds", "away_odds", *NO_ODDS_FEATURES],
    },
    "football_model_no_odds.pkl": {
        "type": "xgboost_1x2_classifier_no_odds", "features": NO_ODDS_FEATURES,
    },
    "1x2_calibrator.pkl": {
        "type": "1x2_probability_calibrator",
        "features": ["home_probability", "draw_probability", "away_probability"],
    },
    "home_goals_model_no_odds.pkl": {
        "type": "xgboost_home_goals_regressor_no_odds", "features": NO_ODDS_FEATURES,
    },
    "away_goals_model_no_odds.pkl": {
        "type": "xgboost_away_goals_regressor_no_odds", "features": NO_ODDS_FEATURES,
    },
    "over_2_5_calibrator.pkl": {
        "type": "over_2_5_probability_calibrator", "features": ["over_probability"],
    },
    "btts_calibrator.pkl": {
        "type": "btts_probability_calibrator", "features": ["btts_probability"],
    },
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def save_candidate(
    artifact: Any,
    production_filename: str,
    producer: str,
    input_paths: list[str | Path],
    artifact_type: str,
    feature_names: list[str],
    parameters: dict[str, Any] | None = None,
    candidate_dir: str | Path = "artifacts/candidates",
) -> tuple[Path, Path]:
    """Serialize an artifact and an integrity manifest outside production paths."""
    if production_filename not in ARTIFACT_SPECS:
        raise ValueError(f"Destination is not allow-listed: {production_filename}")
    directory = Path(candidate_dir)
    directory.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S_%fZ")
    artifact_path = directory / f"{Path(production_filename).stem}_{timestamp}.pkl"
    joblib.dump(artifact, artifact_path)

    inputs = []
    for raw_path in input_paths:
        path = Path(raw_path)
        inputs.append({"path": str(path), "sha256": sha256_file(path)})
    manifest = {
        "manifest_version": 1,
        "production_filename": production_filename,
        "artifact_filename": artifact_path.name,
        "sha256": sha256_file(artifact_path),
        "producer": producer,
        "created_at_utc": datetime.now(UTC).isoformat(),
        "input_data": inputs,
        "artifact_type": artifact_type,
        "feature_schema": {"names": feature_names, "count": len(feature_names)},
        "parameters": parameters or {},
    }
    manifest_path = artifact_path.with_suffix(".pkl.json")
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return artifact_path, manifest_path


def validate_candidate(candidate: Path, manifest_path: Path, destination: str) -> dict:
    if destination not in ARTIFACT_SPECS:
        raise ValueError(f"Destination is not allow-listed: {destination}")
    manifest = json.loads(manifest_path.read_text())
    spec = ARTIFACT_SPECS[destination]
    required = {
        "manifest_version", "production_filename", "artifact_filename", "sha256",
        "producer", "created_at_utc", "input_data", "artifact_type",
        "feature_schema", "parameters",
    }
    missing = required - manifest.keys()
    if missing:
        raise ValueError(f"Manifest fields missing: {sorted(missing)}")
    if manifest["production_filename"] != destination:
        raise ValueError("Manifest destination does not match requested destination")
    if manifest["artifact_filename"] != candidate.name:
        raise ValueError("Manifest artifact filename does not match candidate")
    if manifest["sha256"] != sha256_file(candidate):
        raise ValueError("Candidate SHA256 does not match manifest")
    if not manifest["producer"] or not manifest["created_at_utc"]:
        raise ValueError("Producer and UTC timestamp are required")
    for input_item in manifest["input_data"]:
        input_hash = input_item.get("sha256", "")
        if not input_item.get("path") or len(input_hash) != 64:
            raise ValueError("Input-data metadata is invalid")
        try:
            int(input_hash, 16)
        except ValueError as error:
            raise ValueError("Input-data SHA256 is invalid") from error
    if manifest["artifact_type"] != spec["type"]:
        raise ValueError("Artifact type does not match allow-listed destination")
    schema = manifest["feature_schema"]
    if schema.get("count") != len(schema.get("names", [])):
        raise ValueError("Feature schema count is invalid")
    if schema.get("names") != spec["features"]:
        raise ValueError("Feature schema does not match allow-listed destination")
    return manifest


def promote_candidate(
    candidate: Path,
    manifest_path: Path,
    destination: str,
    root: Path = Path("."),
    dry_run: bool = False,
) -> Path:
    validate_candidate(candidate, manifest_path, destination)
    destination_path = root / destination
    if dry_run:
        return destination_path
    if destination_path.exists():
        backup_dir = root / "artifacts/production_backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S_%fZ")
        shutil.copy2(destination_path, backup_dir / f"{destination}.{timestamp}.bak")
    temporary = destination_path.with_suffix(destination_path.suffix + ".promoting")
    shutil.copy2(candidate, temporary)
    temporary.replace(destination_path)
    return destination_path


def verify_production(root: Path = Path(".")) -> list[dict[str, Any]]:
    reports = []
    for filename, spec in ARTIFACT_SPECS.items():
        path = root / filename
        present = path.is_file()
        reports.append({
            "filename": filename,
            "status": "PRESENT" if present else "MISSING",
            "sha256": sha256_file(path) if present else None,
            "artifact_type": spec["type"],
            "feature_schema": {
                "count": len(spec["features"]),
                "names": spec["features"],
            },
        })
    return reports


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    verify_parser = subparsers.add_parser("verify", help="Verify required production files")
    verify_parser.add_argument("--root", type=Path, default=Path("."))
    promote_parser = subparsers.add_parser("promote", help="Explicitly promote a candidate")
    promote_parser.add_argument("candidate", type=Path)
    promote_parser.add_argument("--manifest", type=Path)
    promote_parser.add_argument("--destination", required=True, choices=sorted(ARTIFACT_SPECS))
    promote_parser.add_argument("--root", type=Path, default=Path("."))
    promote_parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.command == "verify":
        reports = verify_production(args.root)
        for report in reports:
            schema = report["feature_schema"]
            digest = report["sha256"] or "-"
            print(
                f"{report['filename']} | {report['status']} | SHA256={digest} | "
                f"type={report['artifact_type']} | features={schema['count']} | "
                f"feature_names={','.join(schema['names'])}"
            )
        return 1 if any(report["status"] == "MISSING" for report in reports) else 0
    manifest = args.manifest or args.candidate.with_suffix(".pkl.json")
    path = promote_candidate(args.candidate, manifest, args.destination, args.root, args.dry_run)
    print(f"{'DRY RUN: would promote to' if args.dry_run else 'Promoted to'} {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
