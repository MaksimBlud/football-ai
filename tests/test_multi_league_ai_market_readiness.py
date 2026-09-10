import pandas as pd
import pytest

from multi_league_ai_market_readiness import (
    assert_no_false_ai_promotion,
    build_readiness_report,
    validate_pair_provenance,
)


def _operational():
    return pd.DataFrame(
        [
            {
                "league": "EPL",
                "event_id": "epl-1",
                "prediction_mode": "MARKET_ONLY",
                "structural_status": "CALIBRATION_REQUIRED",
                "structural_applied": False,
            },
            {
                "league": "LA_LIGA",
                "event_id": "laliga-1",
                "prediction_mode": "MARKET_ONLY",
                "structural_status": "CALIBRATION_REQUIRED",
                "structural_applied": False,
            },
            {
                "league": "SERIE_A",
                "event_id": "seriea-1",
                "prediction_mode": "MARKET_ONLY",
                "structural_status": "CALIBRATION_REQUIRED",
                "structural_applied": False,
            },
        ]
    )


def _pairs():
    return pd.DataFrame(
        [
            {
                "pair_key": "pair-1",
                "experiment_id": "EPL_AI_MARKET_PAIR_V1",
                "league": "EPL",
                "event_id": "epl-1",
                "kickoff_utc": "2026-09-12T14:00:00Z",
                "market_snapshot_time_utc": "2026-09-11T12:00:00Z",
                "model_generated_at_utc": "2026-09-11T12:05:00Z",
                "history_cutoff_utc": "2026-09-11T12:00:00Z",
                "model_home_prob": 0.50,
                "model_draw_prob": 0.25,
                "model_away_prob": 0.25,
                "model_artifact_sha256": "a" * 64,
                "code_commit_sha": "b" * 40,
            }
        ]
    )


def test_readiness_keeps_operational_volume_separate_from_ai_evidence():
    report = build_readiness_report(_operational(), _pairs()).set_index("league")

    assert report.loc["EPL", "operational_events"] == 1
    assert report.loc["EPL", "valid_paired_ai_events"] == 1
    assert report.loc["EPL", "evidence_status"] == "EXISTING_EPL_PAIRED_AI_EVIDENCE"

    for league in ("LA_LIGA", "SERIE_A"):
        assert report.loc[league, "operational_events"] == 1
        assert report.loc[league, "market_only_events"] == 1
        assert report.loc[league, "calibration_required_events"] == 1
        assert report.loc[league, "valid_paired_ai_events"] == 0
        assert report.loc[league, "evidence_status"] == "MARKET_ONLY_NO_PAIRED_AI_PROVENANCE"

    assert not report["eligible_for_new_multileague_primary"].any()
    assert_no_false_ai_promotion(report.reset_index())


def test_invalid_pair_provenance_does_not_count_as_ai_evidence():
    pairs = _pairs()
    pairs.loc[0, "model_generated_at_utc"] = "2026-09-12T15:00:00Z"

    assert not validate_pair_provenance(pairs).iloc[0]
    report = build_readiness_report(_operational(), pairs).set_index("league")
    assert report.loc["EPL", "paired_ai_events"] == 1
    assert report.loc["EPL", "valid_paired_ai_events"] == 0
    assert report.loc["EPL", "evidence_status"] == "MARKET_ONLY_NO_PAIRED_AI_PROVENANCE"


def test_missing_provenance_column_fails_closed():
    with pytest.raises(ValueError, match="AI-market pair ledger missing columns"):
        build_readiness_report(_operational(), _pairs().drop(columns=["model_artifact_sha256"]))


def test_report_cannot_activate_new_primary_cohort():
    report = build_readiness_report(_operational(), _pairs())
    report.loc[report["league"] == "LA_LIGA", "eligible_for_new_multileague_primary"] = True
    with pytest.raises(RuntimeError, match="must not activate"):
        assert_no_false_ai_promotion(report)
