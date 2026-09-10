import numpy as np
import pandas as pd
import pytest

import train_la_liga_1x2_candidate as candidate


def test_temperature_probabilities_remain_normalized():
    raw=np.array([[.5,.3,.2],[.2,.25,.55]])
    calibrated=candidate.temperature(raw,1.25)
    assert np.allclose(calibrated.sum(axis=1),1.0)
    assert np.isfinite(calibrated).all()


def test_history_guard_rejects_2026_27_rows():
    frame=pd.DataFrame({
        "league":["LA_LIGA","LA_LIGA"],
        "season":[candidate.FINAL,"2026-2027"],
        "match_date":["2026-05-01","2026-08-01"],
        "result":["H","A"],
    })
    with pytest.raises(ValueError,match="prospective/current"):
        candidate.validate(frame)


def test_quality_gate_is_strict_against_market():
    raw={"accuracy":.54,"logloss":1.00,"brier":.60}
    calibrated={"accuracy":.56,"logloss":.95,"brier":.56}
    market={"accuracy":.55,"logloss":.96,"brier":.57}
    assert candidate.gate(raw,calibrated,market)["passed"] is True
    market["logloss"]=.94
    assert candidate.gate(raw,calibrated,market)["passed"] is False


def test_candidate_outputs_are_ignored_research_paths():
    assert "artifacts/candidates/la_liga" in str(candidate.OUT).replace("\\","/")
    assert "experiments/la_liga_candidate_artifact" in str(candidate.REPORT).replace("\\","/")
    assert candidate.FINAL=="2025-2026"
    assert "2026-2027" not in candidate.SELECTION
