"""Fail-closed contract for controlled Total Goals inference.

This module is intentionally dependency-light and performs no model inference,
network access, database writes, training, or artifact promotion.  It freezes the
input feature order recovered from the production goal-model training lineage,
requires explicit causal timestamps, and computes the identity of the complete
four-artifact inference bundle.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Iterable, Mapping


CONTRACT_VERSION = "total-goals-inference-contract.v1"
BUNDLE_VERSION = "goal-artifact-bundle.v1"

# Exact order used by train_goal_models_no_odds.py when the production lineage
# was introduced.  Do not add odds or silently reorder these features.
TOTAL_GOALS_FEATURES = (
    "home_last5_points",
    "away_last5_points",
    "form_difference",
    "home_goals_scored_last5",
    "home_goals_conceded_last5",
    "away_goals_scored_last5",
    "away_goals_conceded_last5",
    "home_shots_last5",
    "away_shots_last5",
    "home_shots_target_last5",
    "away_shots_target_last5",
    "home_elo",
    "away_elo",
    "elo_difference",
    "home_venue_win_rate",
    "away_venue_win_rate",
    "home_venue_goals_scored",
    "away_venue_goals_scored",
)

TOTAL_GOALS_ARTIFACTS = (
    "home_goals_model_no_odds.pkl",
    "away_goals_model_no_odds.pkl",
    "over_2_5_calibrator.pkl",
    "btts_calibrator.pkl",
)

# Historical source of the feature/training lineage.  This is provenance only;
# it is not permission to retrain or promote artifacts automatically.
RECOVERED_TRAINING_COMMIT = "bab8522d379131f30fdc4bbea9b03879e5c11f0f"


class TotalGoalsContractError(ValueError):
    """Raised when controlled inference would violate the frozen contract."""


def _utc_datetime(value: str | datetime, *, field: str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        text = value.strip()
        if not text:
            raise TotalGoalsContractError(f"{field} must not be empty")
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError as error:
            raise TotalGoalsContractError(f"{field} is not a valid ISO-8601 timestamp") from error
    else:
        raise TotalGoalsContractError(f"{field} must be an ISO-8601 string or datetime")

    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise TotalGoalsContractError(f"{field} must be timezone-aware UTC")
    if parsed.utcoffset() != timedelta(0):
        raise TotalGoalsContractError(f"{field} must use UTC offset +00:00/Z")
    return parsed.astimezone(UTC)


def validate_prediction_window(
    *,
    as_of_utc: str | datetime,
    commence_times_utc: Iterable[str | datetime],
) -> datetime:
    """Require every target fixture to be strictly future relative to ``as_of``."""

    as_of = _utc_datetime(as_of_utc, field="as_of_utc")
    targets = list(commence_times_utc)
    if not targets:
        raise TotalGoalsContractError("at least one target fixture is required")

    for index, raw_kickoff in enumerate(targets):
        kickoff = _utc_datetime(raw_kickoff, field=f"commence_times_utc[{index}]")
        if kickoff <= as_of:
            raise TotalGoalsContractError(
                "target fixture must be strictly after as_of_utc: "
                f"index={index}, kickoff={kickoff.isoformat()}, as_of={as_of.isoformat()}"
            )
    return as_of


def validate_history_cutoff(
    *,
    as_of_utc: str | datetime,
    observation_times_utc: Iterable[str | datetime],
) -> datetime:
    """Require all source observations to predate the inference snapshot."""

    as_of = _utc_datetime(as_of_utc, field="as_of_utc")
    for index, raw_observed in enumerate(observation_times_utc):
        observed = _utc_datetime(raw_observed, field=f"observation_times_utc[{index}]")
        if observed >= as_of:
            raise TotalGoalsContractError(
                "history observation must be strictly before as_of_utc: "
                f"index={index}, observed={observed.isoformat()}, as_of={as_of.isoformat()}"
            )
    return as_of


def validate_feature_order(feature_names: Iterable[str]) -> tuple[str, ...]:
    """Reject any schema drift from the trained no-odds goal-model feature order."""

    names = tuple(feature_names)
    if names != TOTAL_GOALS_FEATURES:
        raise TotalGoalsContractError(
            "Total Goals feature schema/order does not match the recovered training contract"
        )
    return names


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_component_hashes(component_hashes: Mapping[str, str]) -> dict[str, str]:
    """Return normalized hashes only when the complete four-artifact set is present."""

    if set(component_hashes) != set(TOTAL_GOALS_ARTIFACTS):
        missing = sorted(set(TOTAL_GOALS_ARTIFACTS) - set(component_hashes))
        extra = sorted(set(component_hashes) - set(TOTAL_GOALS_ARTIFACTS))
        raise TotalGoalsContractError(
            f"incomplete/unknown Total Goals artifact bundle; missing={missing}, extra={extra}"
        )

    normalized: dict[str, str] = {}
    for name in TOTAL_GOALS_ARTIFACTS:
        digest = str(component_hashes[name]).strip().lower()
        if len(digest) != 64:
            raise TotalGoalsContractError(f"invalid SHA-256 for {name}")
        try:
            int(digest, 16)
        except ValueError as error:
            raise TotalGoalsContractError(f"invalid SHA-256 for {name}") from error
        normalized[name] = digest
    return normalized


def build_bundle_payload(component_hashes: Mapping[str, str]) -> bytes:
    hashes = validate_component_hashes(component_hashes)
    lines = [BUNDLE_VERSION]
    lines.extend(f"{name}:{hashes[name]}" for name in TOTAL_GOALS_ARTIFACTS)
    return ("\n".join(lines) + "\n").encode("utf-8")


def bundle_sha256_from_hashes(component_hashes: Mapping[str, str]) -> str:
    return hashlib.sha256(build_bundle_payload(component_hashes)).hexdigest()


def inspect_artifact_bundle(root: str | Path) -> dict[str, object]:
    """Hash the real bundle without loading, modifying, or repackaging any artifact."""

    root_path = Path(root)
    missing = [name for name in TOTAL_GOALS_ARTIFACTS if not (root_path / name).is_file()]
    if missing:
        raise TotalGoalsContractError(
            "Total Goals inference bundle is unavailable: " + ", ".join(missing)
        )

    component_hashes = {
        name: sha256_file(root_path / name)
        for name in TOTAL_GOALS_ARTIFACTS
    }
    return {
        "contract_version": CONTRACT_VERSION,
        "bundle_version": BUNDLE_VERSION,
        "artifacts": component_hashes,
        "bundle_sha256": bundle_sha256_from_hashes(component_hashes),
        "feature_names": list(TOTAL_GOALS_FEATURES),
        "feature_count": len(TOTAL_GOALS_FEATURES),
    }
