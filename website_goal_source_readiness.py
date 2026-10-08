"""Fail-closed source-readiness audit for website goal markets.

The audit deliberately inspects repository contracts and file availability only.
It never loads a model pickle, queries Supabase, calls an odds provider, trains a
model, or reads match outcomes.  O/U 2.5 and BTTS use separate market contracts
and receive separate results even though their model bundle is shared.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any


BLOCKED = "BLOCKED_BY_UNTOUCHED_DATA_OR_PROVENANCE"
ARTIFACTS = (
    "home_goals_model_no_odds.pkl",
    "away_goals_model_no_odds.pkl",
    "over_2_5_calibrator.pkl",
    "btts_calibrator.pkl",
)
CONTRACT_FILES = (
    "docs/total-goals-readiness-audit.md",
    "evaluate_goal_markets_thresholds.py",
    "calibrate_goal_markets.py",
    "total_goals_inference_contract.py",
    "save_odds_snapshot.py",
    "bootstrap_product_predictions_from_pair_ledger.py",
)
MARKETS: dict[str, dict[str, Any]] = {
    "OU25": {
        "family": "website_goal_total_oos_readiness_v1",
        "ready_decision": "GOAL_OU25_EVIDENCE_READY",
        "prediction_fields": ("over_2_5_probability", "under_2_5_probability"),
        "price_fields": ("over_2_5_odds", "under_2_5_odds"),
        "target": "FTHG + FTAG > 2.5",
    },
    "BTTS": {
        "family": "website_btts_oos_readiness_v1",
        "ready_decision": "BTTS_EVIDENCE_READY",
        "prediction_fields": ("btts_yes_probability", "btts_no_probability"),
        "price_fields": ("btts_yes_odds", "btts_no_odds"),
        "target": "FTHG > 0 and FTAG > 0",
    },
}


def _text(root: Path, relative: str) -> str:
    path = root / relative
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def evaluate_source_readiness(market: str, root: str | Path = ".") -> dict[str, Any]:
    """Return a deterministic, outcome-free readiness decision for one market."""

    key = market.strip().upper()
    if key not in MARKETS:
        raise ValueError(f"unsupported goal market: {market!r}")
    spec = MARKETS[key]
    repo = Path(root)

    texts = {path: _text(repo, path) for path in CONTRACT_FILES}
    missing_contract_files = sorted(path for path, value in texts.items() if not value)
    artifact_presence = {name: (repo / name).is_file() for name in ARTIFACTS}
    bundle_complete = all(artifact_presence.values())

    audit_doc = texts["docs/total-goals-readiness-audit.md"]
    calibrator = texts["calibrate_goal_markets.py"]
    inference = texts["total_goals_inference_contract.py"]
    odds_snapshot = texts["save_odds_snapshot.py"]
    bootstrap = texts["bootstrap_product_predictions_from_pair_ledger.py"]

    lineage_documented = all(
        token in audit_doc
        for token in (
            "four-artifact bundle",
            "2023/24",
            "2024/25",
            "2025/26",
            "not an untouched final generalization test",
        )
    ) and all(token in calibrator for token in ("CALIBRATION_SEASONS", "TEST_SEASONS"))
    timestamp_contract_present = all(
        token in inference
        for token in (
            "validate_prediction_window",
            "validate_history_cutoff",
            "TOTAL_GOALS_FEATURES",
            "TOTAL_GOALS_ARTIFACTS",
        )
    )

    # The tracked bootstrap is the current durable-row producer.  Null goal
    # fields prove that it does not create immutable goal forecasts.
    prediction_fields = tuple(spec["prediction_fields"])
    immutable_goal_forecasts_present = all(
        f'"{field}": None' not in bootstrap and f'"{field}": null' not in bootstrap
        for field in prediction_fields
    ) and all(field in bootstrap for field in prediction_fields)

    price_fields = tuple(spec["price_fields"])
    exact_market_prices_present = all(field in odds_snapshot for field in price_fields)
    h2h_only_contract = all(
        field in odds_snapshot for field in ("home_odds", "draw_odds", "away_odds")
    ) and not exact_market_prices_present

    missing: list[dict[str, str]] = []
    if missing_contract_files:
        missing.append({
            "code": "MISSING_REPOSITORY_CONTRACT_FILES",
            "detail": ", ".join(missing_contract_files),
        })
    if not lineage_documented:
        missing.append({
            "code": "CALIBRATOR_LINEAGE_NOT_PROVEN",
            "detail": "Training, method-selection, and refit scopes are not all documented.",
        })
    if not bundle_complete:
        absent = [name for name, present in artifact_presence.items() if not present]
        missing.append({
            "code": "PORTABLE_FOUR_ARTIFACT_BUNDLE_UNAVAILABLE",
            "detail": "Missing runtime artifacts: " + ", ".join(absent),
        })
    if not timestamp_contract_present:
        missing.append({
            "code": "POINT_IN_TIME_INFERENCE_CONTRACT_UNAVAILABLE",
            "detail": "Strict history < as_of < kickoff contract is not proven.",
        })
    if not immutable_goal_forecasts_present:
        missing.append({
            "code": "IMMUTABLE_PREMATCH_GOAL_FORECASTS_UNAVAILABLE",
            "detail": "Current durable bootstrap writes null goal probabilities; no independent pre-match forecast cohort is tracked.",
        })
    if not exact_market_prices_present:
        missing.append({
            "code": "EXACT_PAIRED_MARKET_PRICES_UNAVAILABLE",
            "detail": "Required timestamped price fields are absent: " + ", ".join(price_fields),
        })
    # No currently registered post-refit cohort can be called untouched.  The
    # reserved 2026/27 targets remain deliberately unread by this evaluator.
    missing.append({
        "code": "UNTOUCHED_POST_REFIT_TARGET_COHORT_UNAVAILABLE",
        "detail": "2023/24-2025/26 selected/refit the calibrator; reserved 2026/27 outcomes were not inspected.",
    })

    ready = not missing
    decision = str(spec["ready_decision"]) if ready else BLOCKED
    return {
        "experiment_id": f"{spec['family'].upper()}_SOURCE_AUDIT",
        "hypothesis_family": spec["family"],
        "market": key,
        "target_contract": spec["target"],
        "decision": decision,
        "no_bet": True,
        "evidence_ready": ready,
        "source_audit": {
            "contract_files": {path: bool(value) for path, value in texts.items()},
            "lineage_documented": lineage_documented,
            "artifact_presence_checked_without_loading": artifact_presence,
            "four_artifact_bundle_complete": bundle_complete,
            "point_in_time_inference_contract_present": timestamp_contract_present,
            "immutable_prematch_forecasts_present": immutable_goal_forecasts_present,
            "required_market_price_fields": list(price_fields),
            "exact_paired_market_prices_present": exact_market_prices_present,
            "current_odds_contract_is_h2h_only": h2h_only_contract,
            "previous_method_selection_scope": ["2023/2024", "2024/2025", "2025/2026"],
            "previous_scope_is_untouched_post_refit_evidence": False,
        },
        "missing_prerequisites": missing,
        "safety": {
            "match_outcomes_read": False,
            "reserved_2026_27_outcomes_read": False,
            "model_pickle_files_loaded": False,
            "model_training_or_promotion": False,
            "paid_api_calls": 0,
            "supabase_reads": 0,
            "supabase_writes": 0,
            "production_operations": 0,
            "automatic_deployment": False,
        },
        "interpretation_guard": (
            "Source readiness only. Existing calibrator-selection rows are opened and "
            "cannot confirm the refit calibrator. Do not inspect reserved 2026/27 outcomes, "
            "reconstruct forecasts with post-result features, deploy, or recommend a bet."
        ),
    }
