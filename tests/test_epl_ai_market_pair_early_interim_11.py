import json
from pathlib import Path

import pandas as pd

from epl_ai_market_pair_early_interim_11 import (
    COMPLETED_CUTOFF_UTC,
    EXPECTED_PAIR_KEYS,
    EXPECTED_RESULTS_CSV_SHA256,
    EXPECTED_TOTAL,
    canonical_completed_pairs,
    evaluate,
    sha256_file,
)

RESULTS = Path("experiments/epl_ai_market_pair_v1_early_interim_11_results.csv")
REPORT = Path("experiments/epl_ai_market_pair_v1_early_interim_11_report.json")


def test_interim_rows_are_exact_prospective_completed_set():
    frame = pd.read_csv(RESULTS)
    assert len(frame) == EXPECTED_TOTAL == 11
    assert set(frame["pair_key"].astype(str)) == EXPECTED_PAIR_KEYS
    assert not frame["event_id"].duplicated().any()
    assert (pd.to_datetime(frame["kickoff_utc"], utc=True) < COMPLETED_CUTOFF_UTC).all()
    assert (
        pd.to_datetime(frame["market_snapshot_time_utc"], utc=True)
        < pd.to_datetime(frame["kickoff_utc"], utc=True)
    ).all()
    assert (
        pd.to_datetime(frame["model_generated_at_utc"], utc=True)
        < pd.to_datetime(frame["kickoff_utc"], utc=True)
    ).all()
    assert "b7a2cad26d908a943a27340b4b607068" not in set(frame["event_id"].astype(str))
    assert sha256_file(RESULTS) == EXPECTED_RESULTS_CSV_SHA256


def test_interim_reuses_preexisting_latest_snapshot_rule():
    frame = pd.read_csv(RESULTS)
    frame["experiment_id"] = "EPL_AI_MARKET_PAIR_V1"
    frame["league"] = "EPL"
    frame["provider_home_team"] = frame["home_team"]
    frame["provider_away_team"] = frame["away_team"]
    late = frame.loc[frame["event_id"] == "14f6639178a943ac614c7b872bf6e4d6"].iloc[0].copy()
    early = late.copy()
    early["pair_key"] = "synthetic-earlier-pair"
    early["market_snapshot_time_utc"] = "2026-09-04T04:41:30.626977Z"
    pair_ledger = pd.concat([frame, pd.DataFrame([early])], ignore_index=True)
    selected = canonical_completed_pairs(pair_ledger)
    row = selected.loc[selected["event_id"] == "14f6639178a943ac614c7b872bf6e4d6"].iloc[0]
    assert row["pair_key"] == late["pair_key"]


def test_report_recomputes_from_frozen_rows_and_preserves_honest_label():
    frame = pd.read_csv(RESULTS)
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    actual = evaluate(frame)

    assert report["evidence_status"] == "EARLY_EXPLORATORY_OUTCOME_READ"
    assert report["pair_predictions_were_prospectively_frozen_before_outcomes"] is True
    assert report["outcomes_were_exposed_before_this_interim_manifest_was_created"] is True
    assert report["original_primary_no_peek_gate_overridden_by_user_authorized_early_read"] is True
    assert report["future_primary_claim_status"] == "PRISTINE_PRIMARY_NO_PEEK_CLAIM_NO_LONGER_AVAILABLE"
    assert actual["descriptive_result"] == report["descriptive_result"]
    assert actual["bet_decision"] == "NO_BET"
    assert actual["model_correct_n"] == report["model_correct_n"] == 2
    assert actual["market_correct_n"] == report["market_correct_n"] == 4
    assert actual["top1_disagreement_n"] == report["top1_disagreement_n"] == 2
    assert actual["disagreement_model_correct_market_wrong"] == 0
    assert actual["disagreement_market_correct_model_wrong"] == 2

    numeric = (
        "model_brier", "market_brier", "delta_brier_model_minus_market",
        "model_log_loss", "market_log_loss", "delta_log_loss_model_minus_market",
        "model_accuracy", "market_accuracy", "draw_actual_rate",
        "model_mean_draw_probability", "market_mean_draw_probability",
    )
    for key in numeric:
        assert abs(float(actual[key]) - float(report[key])) < 1e-12
