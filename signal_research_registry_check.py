"""Validate the signal research registry without running or scoring experiments."""
from __future__ import annotations

import json
from pathlib import Path

REGISTRY = Path("research/signal_research_registry_v1.json")
CLOSED_PREFIX = "CLOSED_"
ACTIVE_PREFIX = "ACTIVE_"
OPERATIONALLY_CLOSED_PROSPECTIVE = {
    "PROSPECTIVE_MARKET_PATH_V1",
    "PROSPECTIVE_AVAILABILITY_SIGNAL_LAB",
    "LA_LIGA_MARKET_HOME_60_70_V1",
}


def validate_registry(root: Path = Path(".")) -> list[str]:
    payload = json.loads((root / REGISTRY).read_text())
    errors: list[str] = []
    blocks = payload.get("blocks") or []
    ids = [str(block.get("id", "")).strip() for block in blocks]
    if not ids or any(not value for value in ids):
        errors.append("every registry block must have a non-empty id")
    if len(ids) != len(set(ids)):
        errors.append("registry block ids must be unique")

    for block in blocks:
        block_id = str(block.get("id", ""))
        status = str(block.get("status", ""))
        family = str(block.get("hypothesis_family", "")).strip()
        sample = str(block.get("sample_family", "")).strip()
        decision = str(block.get("decision", "")).strip()
        if not family or not sample or not decision:
            errors.append(f"{block_id}: hypothesis_family, sample_family and decision are required")
        if status.startswith(CLOSED_PREFIX):
            if block.get("retune_on_seen_sample") is not False:
                errors.append(f"{block_id}: closed block must set retune_on_seen_sample=false")
            document = block.get("closure_document")
            if not document or not (root / str(document)).is_file():
                errors.append(f"{block_id}: closure_document must exist")
        elif status.startswith(ACTIVE_PREFIX):
            if block.get("frozen_protocol") is not True:
                errors.append(f"{block_id}: active block must set frozen_protocol=true")
            if block.get("outcome_scoring_before_readiness") is not False:
                errors.append(f"{block_id}: early outcome scoring must be false")
            document = block.get("status_document")
            if not document or not (root / str(document)).is_file():
                errors.append(f"{block_id}: status_document must exist")
        else:
            errors.append(f"{block_id}: unsupported registry status {status!r}")

        if block_id in OPERATIONALLY_CLOSED_PROSPECTIVE:
            if block.get("operational_implementation") != "CLOSED":
                errors.append(f"{block_id}: operational implementation must be CLOSED")
            if block.get("scheduled_outcome_scoring") is not False:
                errors.append(f"{block_id}: scheduled outcome scoring must be false")
            if block.get("evaluation_requires_explicit_manual_dispatch") is not True:
                errors.append(f"{block_id}: evaluation must require explicit manual dispatch")
            closure = block.get("operational_closure_document")
            if not closure or not (root / str(closure)).is_file():
                errors.append(f"{block_id}: operational_closure_document must exist")

        if block_id == "PROSPECTIVE_AVAILABILITY_SIGNAL_LAB":
            if block.get("activation_monitor_read_only") is not True:
                errors.append(f"{block_id}: activation monitor must be read-only")
            if block.get("automatic_external_gate_bypass") is not False:
                errors.append(f"{block_id}: automatic external gate bypass must be false")

    governance = payload.get("governance") or {}
    required_true = (
        "closed_hypotheses_must_not_be_retuned_on_seen_sample",
        "active_prospective_blocks_must_preserve_frozen_protocol",
        "new_retrospective_feature_family_requires_independent_information_justification",
        "production_promotion_requires_separate_explicit_decision",
        "research_runs_must_not_modify_production_artifacts",
        "negative_results_are_first_class_results",
        "prospective_outcome_evaluation_requires_explicit_action",
    )
    for key in required_true:
        if governance.get(key) is not True:
            errors.append(f"governance.{key} must be true")
    return errors


def main() -> None:
    errors = validate_registry()
    if errors:
        raise SystemExit("SIGNAL_RESEARCH_REGISTRY_INVALID\n" + "\n".join(f"- {error}" for error in errors))
    payload = json.loads(REGISTRY.read_text())
    blocks = payload["blocks"]
    closed = sum(str(block["status"]).startswith(CLOSED_PREFIX) for block in blocks)
    active = sum(str(block["status"]).startswith(ACTIVE_PREFIX) for block in blocks)
    print(f"PASS SIGNAL_RESEARCH_REGISTRY_V1 blocks={len(blocks)} closed={closed} active={active}")


if __name__ == "__main__":
    main()
