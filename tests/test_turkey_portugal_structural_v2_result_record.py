import json
from pathlib import Path

from primeira_liga_runtime_config import PRIMEIRA_LIGA_RUNTIME_CONFIG
from turkey_super_lig_runtime_config import TURKEY_SUPER_LIG_RUNTIME_CONFIG


ROOT = Path(__file__).resolve().parents[1]
RESULT_PATH = ROOT / "research" / "turkey_portugal_structural_v2_calibration_v1_result.json"


def test_result_record_preserves_research_only_runtime_contract():
    result = json.loads(RESULT_PATH.read_text(encoding="utf-8"))

    assert result["preregistration_id"] == "TURKEY_PORTUGAL_STRUCTURAL_V2_CALIBRATION_V1"
    assert result["status"] == "HISTORICAL_OOS_EVALUATED_RESEARCH_ONLY"
    assert result["research_only"] is True
    assert result["runtime_mutation"] is False
    assert result["automatic_promotion"] is False
    assert result["production_artifacts_unchanged"] is True
    assert result["odds_api_requests"] == 0
    assert result["supabase_operations"] == 0
    assert result["runtime_calibration_status_after_research"] == "CALIBRATION_REQUIRED"

    assert TURKEY_SUPER_LIG_RUNTIME_CONFIG.structural_v2.calibration_status == "CALIBRATION_REQUIRED"
    assert PRIMEIRA_LIGA_RUNTIME_CONFIG.structural_v2.calibration_status == "CALIBRATION_REQUIRED"


def test_result_record_matches_frozen_metric_decisions():
    result = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    turkey = result["leagues"]["TURKEY_SUPER_LIG"]
    portugal = result["leagues"]["PRIMEIRA_LIGA"]

    assert turkey["research_conclusion"] == "HISTORICAL_OOS_SIGNAL_OBSERVED"
    assert turkey["weighted_logloss_delta"] < 0.0
    assert turkey["weighted_brier_delta"] < 0.0
    assert turkey["argmax_changes"] == 0
    assert len(turkey["outer_fold_results"]) == 5
    assert sum(
        fold["logloss_delta"] < 0.0 and fold["brier_delta"] < 0.0
        for fold in turkey["outer_fold_results"]
    ) == 4

    assert portugal["research_conclusion"] == "CALIBRATION_NOT_SUPPORTED_OR_INCONSISTENT"
    assert portugal["weighted_logloss_delta"] < 0.0
    assert portugal["weighted_brier_delta"] > 0.0
    assert portugal["argmax_changes"] == 0
    assert len(portugal["outer_fold_results"]) == 5

    assert result["decision"]["portugal"] == "DO_NOT_CALIBRATE_FROM_THIS_V1_RESULT"
    assert result["decision"]["runtime"] == "KEEP_BOTH_LEAGUES_CALIBRATION_REQUIRED"
