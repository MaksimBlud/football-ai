"""Immutable guards for POINT_IN_TIME_CROSS_LEAGUE_REPLAY_V1."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

EXPECTED_TOTAL_EVENTS = 47
EXPECTED_COUNTS = {
    "BUNDESLIGA": 9,
    "EREDIVISIE": 9,
    "LA_LIGA": 10,
    "LIGUE_1": 9,
    "SERIE_A": 10,
}
EXPECTED_COHORT_INVENTORY_SHA256 = (
    "1580ec1d361f97fd08040d0ebdfb78e922a9100180fe587f91b124e265f0d808"
)
EXPECTED_MODEL_SHA256 = (
    "1e516fe91420fdc2d6479e9fb92b005c4a0c75c7f0f217493dd6b27fd64d99a5"
)
EXPECTED_FULL_REPLAY_CSV_SHA256 = (
    "9c19001961b997d9b653d30f5cb660efbc7aeeecfe4069f9ef1de5aa522aef1e"
)
EXPECTED_FULL_MANIFEST_SHA256 = (
    "3c878d70904c9811da69581d1caadf359405c28bf66dad6ecc30227dbc06defb"
)
EXPECTED_ACTIONS_ARTIFACT_DIGEST = (
    "sha256:9fb205e602b87c3adffd799de8d7b0ba99a0e9eddd568c8f3cd9fb476db03faa"
)
EXPECTED_PREDICTIONS_CANONICAL_SHA256 = (
    "4a28ac7d728d6b9c394af7ec1c1b96d3fc41bae1f17e18c14d7be09594209d94"
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_predictions_sha256(rows: list[dict]) -> str:
    canonical = "\n".join(
        json.dumps(row, sort_keys=True, separators=(",", ":"))
        for row in rows
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def validate_frozen_predictions(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload["experiment_id"] != "POINT_IN_TIME_CROSS_LEAGUE_REPLAY_V1":
        raise RuntimeError("frozen experiment id changed")
    if payload["evidence_class"] != "RETROSPECTIVE_POINT_IN_TIME_REPLAY":
        raise RuntimeError("frozen evidence class changed")
    if payload["prospective"] is not False:
        raise RuntimeError("replay must never be relabeled prospective")
    if payload["outcome_fields_read_before_freeze"] is not False:
        raise RuntimeError("freeze no-peek attestation changed")
    if payload["total_events"] != EXPECTED_TOTAL_EVENTS:
        raise RuntimeError("frozen event count changed")
    if payload["league_counts"] != EXPECTED_COUNTS:
        raise RuntimeError("frozen league counts changed")
    if payload["cohort_inventory_sha256"] != EXPECTED_COHORT_INVENTORY_SHA256:
        raise RuntimeError("frozen cohort inventory hash changed")
    if payload["model_artifact_sha256"] != EXPECTED_MODEL_SHA256:
        raise RuntimeError("frozen model hash changed")
    if payload["full_replay_csv_sha256"] != EXPECTED_FULL_REPLAY_CSV_SHA256:
        raise RuntimeError("frozen full replay CSV hash changed")
    if payload["full_manifest_sha256"] != EXPECTED_FULL_MANIFEST_SHA256:
        raise RuntimeError("frozen full manifest hash changed")
    if payload["actions_artifact_digest"] != EXPECTED_ACTIONS_ARTIFACT_DIGEST:
        raise RuntimeError("frozen Actions artifact digest changed")

    rows = payload["predictions"]
    if len(rows) != EXPECTED_TOTAL_EVENTS:
        raise RuntimeError("frozen prediction row count changed")
    identities = [(row["league"], row["event_id"]) for row in rows]
    if len(set(identities)) != EXPECTED_TOTAL_EVENTS:
        raise RuntimeError("duplicate frozen replay identity")
    for row in rows:
        probs = [
            float(row["model_home_prob"]),
            float(row["model_draw_prob"]),
            float(row["model_away_prob"]),
        ]
        if any(probability < 0 or probability > 1 for probability in probs):
            raise RuntimeError("invalid frozen model probability")
        if abs(sum(probs) - 1.0) > 1e-9:
            raise RuntimeError("frozen model probabilities do not sum to one")
        feature_hash = str(row["feature_sha256"])
        if len(feature_hash) != 64 or any(c not in "0123456789abcdef" for c in feature_hash):
            raise RuntimeError("invalid frozen feature hash")

    actual = canonical_predictions_sha256(rows)
    if actual != EXPECTED_PREDICTIONS_CANONICAL_SHA256:
        raise RuntimeError(
            "frozen AI probability vectors changed: "
            f"expected={EXPECTED_PREDICTIONS_CANONICAL_SHA256}, actual={actual}"
        )
    if payload["predictions_canonical_sha256"] != actual:
        raise RuntimeError("embedded prediction hash does not match rows")
    return payload


def validate_generated_artifacts(csv_path: Path, manifest_path: Path) -> dict:
    csv_hash = sha256_file(csv_path)
    manifest_hash = sha256_file(manifest_path)
    if csv_hash != EXPECTED_FULL_REPLAY_CSV_SHA256:
        raise RuntimeError(
            f"replayed CSV drifted: expected={EXPECTED_FULL_REPLAY_CSV_SHA256}, actual={csv_hash}"
        )
    if manifest_hash != EXPECTED_FULL_MANIFEST_SHA256:
        raise RuntimeError(
            f"replayed manifest drifted: expected={EXPECTED_FULL_MANIFEST_SHA256}, actual={manifest_hash}"
        )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest["cohort_inventory_sha256"] != EXPECTED_COHORT_INVENTORY_SHA256:
        raise RuntimeError("generated cohort inventory drifted")
    if manifest["model_artifact_sha256"] != EXPECTED_MODEL_SHA256:
        raise RuntimeError("generated model artifact drifted")
    if manifest["total_events"] != EXPECTED_TOTAL_EVENTS:
        raise RuntimeError("generated replay event count drifted")
    if manifest["league_counts"] != EXPECTED_COUNTS:
        raise RuntimeError("generated replay league counts drifted")
    if manifest["outcome_fields_read"] is not False:
        raise RuntimeError("generated no-peek attestation changed")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--predictions",
        default="experiments/point_in_time_cross_league_replay_v1_predictions.json",
    )
    parser.add_argument("--csv")
    parser.add_argument("--manifest")
    args = parser.parse_args()

    validate_frozen_predictions(Path(args.predictions))
    if bool(args.csv) != bool(args.manifest):
        raise SystemExit("--csv and --manifest must be supplied together")
    if args.csv:
        validate_generated_artifacts(Path(args.csv), Path(args.manifest))
    print("POINT_IN_TIME_CROSS_LEAGUE_REPLAY_V1 freeze guard: PASS")


if __name__ == "__main__":
    main()
