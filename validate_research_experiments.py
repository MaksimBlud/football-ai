"""Validate the frozen research experiment registry without side effects."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


REGISTRY_PATH = Path(__file__).resolve().parent / "research_experiments.json"
REQUIRED = {
    "experiment_id",
    "status",
    "research_only",
    "prediction_source",
    "prediction_mode",
    "eligible_leagues",
    "start_time_utc",
    "code_sha",
    "parameters",
    "evaluation_view",
    "readiness_threshold",
}


def validate_registry(payload: dict) -> list[dict]:
    if payload.get("schema_version") != 1:
        raise ValueError("Unsupported experiment registry schema")
    experiments = payload.get("experiments")
    if not isinstance(experiments, list) or not experiments:
        raise ValueError("Experiment registry must contain experiments")

    ids: set[str] = set()
    for item in experiments:
        missing = REQUIRED - set(item)
        if missing:
            raise ValueError("Experiment missing fields: " + ", ".join(sorted(missing)))
        experiment_id = str(item["experiment_id"]).strip()
        if not experiment_id or experiment_id in ids:
            raise ValueError("Experiment IDs must be non-empty and unique")
        ids.add(experiment_id)
        if item["status"] != "FROZEN":
            raise ValueError(f"Experiment {experiment_id} is not FROZEN")
        if item["research_only"] is not True:
            raise ValueError(f"Experiment {experiment_id} is not research-only")
        if item["readiness_threshold"] is not None:
            raise ValueError(f"Experiment {experiment_id} defines a readiness threshold")
        if not isinstance(item["eligible_leagues"], list) or not item["eligible_leagues"]:
            raise ValueError(f"Experiment {experiment_id} has no eligible leagues")
        if len(str(item["code_sha"])) != 40:
            raise ValueError(f"Experiment {experiment_id} has invalid code SHA")
        timestamp = datetime.fromisoformat(str(item["start_time_utc"]).replace("Z", "+00:00"))
        if timestamp.tzinfo is None:
            raise ValueError(f"Experiment {experiment_id} start time is not timezone-aware")
        if not isinstance(item["parameters"], dict):
            raise ValueError(f"Experiment {experiment_id} parameters must be an object")
    return experiments


def load_and_validate(path: Path = REGISTRY_PATH) -> list[dict]:
    return validate_registry(json.loads(path.read_text(encoding="utf-8")))


def main() -> None:
    experiments = load_and_validate()
    print(f"experiments: {len(experiments)}")
    for item in experiments:
        print(item["experiment_id"], item["status"], item["prediction_mode"])
    print("PASS: RESEARCH EXPERIMENT REGISTRY VALID")


if __name__ == "__main__":
    main()
