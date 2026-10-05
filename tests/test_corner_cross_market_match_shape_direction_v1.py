import io
import zipfile

import numpy as np
import pandas as pd
import pytest

import corner_cross_market_match_shape_direction_v1 as mod


def _frame(rows=117):
    index = np.arange(rows)
    score = np.linspace(-1.0, 1.0, rows)
    return pd.DataFrame({
        "fixture_id": index,
        "cohort": [sorted(mod.EXPECTED_COHORTS)[i % 4] for i in index],
        "league": [sorted(mod.EXPECTED_LEAGUES)[i % 3] for i in index],
        "opening_lambda": 9.0 + (index % 7) * 0.1,
        "centre_delta": score + 0.01 * np.sin(index),
        "match_shape_gap": score,
    })


def _zip(frame):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr(mod.ARTIFACT_MEMBER, frame.to_csv(index=False))
    return stream.getvalue()


def test_load_rows_enforces_frozen_identity():
    assert len(mod._load_rows(_zip(_frame()))) == 117
    with pytest.raises(RuntimeError, match="117 unique fixtures"):
        mod._load_rows(_zip(_frame(116)))


def test_residual_signal_removes_opening_and_fixed_effects():
    assert mod._residual_spearman(_frame()) > 0.99


def test_binary_metrics_reports_majority_and_down_scarcity():
    frame = _frame()
    frame.loc[:99, "centre_delta"] = frame.loc[:99, "centre_delta"].abs() + 0.1
    frame.loc[100:, "centre_delta"] = -(frame.loc[100:, "centre_delta"].abs() + 0.1)
    result = mod._binary_metrics(frame)
    assert result["up_rows"] == 100
    assert result["down_rows"] == 17
    assert result["always_up_accuracy"] == pytest.approx(100 / 117)


def test_source_gap_fails_closed_without_proxy(monkeypatch):
    def fail():
        raise RuntimeError("gone")
    monkeypatch.setattr(mod, "_artifact_bytes", fail)
    result = mod.evaluate()
    assert result["decision"] == "BLOCKED_BY_EXISTING_SOURCE_GAP"
    assert result["rows"] == 0
    assert result["safety"]["new_prospective_rows_collected"] == 0


def test_evaluate_supports_only_future_confirmation(monkeypatch):
    monkeypatch.setattr(mod, "_artifact_bytes", lambda: b"unused")
    monkeypatch.setattr(mod, "_load_rows", lambda payload: _frame())
    monkeypatch.setattr(mod, "PERMUTATION_DRAWS", 100)
    result = mod.evaluate()
    assert result["decision"] == "SUPPORTED_FOR_FUTURE_CONFIRMATION"
    assert "untouched confirmation" in result["interpretation_guard"]
    assert result["safety"]["no_bet"] is True
