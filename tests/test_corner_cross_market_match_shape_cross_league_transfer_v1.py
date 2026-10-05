import io
import zipfile

import numpy as np
import pandas as pd

import corner_cross_market_match_shape_cross_league_transfer_v1 as mod


def _contract_frame():
    rows = []
    fixture = 1
    for league, count in mod.EXPECTED_SOURCE_ROWS.items():
        for index in range(count):
            rows.append({
                "fixture_id": str(fixture),
                "cohort": sorted(mod.EXPECTED_COHORTS)[index % 4],
                "league": league,
                "match_date": "2026-08-01",
                "home_team": f"Home {fixture}",
                "away_team": f"Away {fixture}",
                "opening_lambda": 9.0 + index / 100,
                "closing_lambda": 9.2 + index / 100,
                "centre_delta": 0.2,
            })
            fixture += 1
    return pd.DataFrame(rows)


def _zip(frame):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr(mod.ARTIFACT_MEMBER, frame.to_csv(index=False))
    return stream.getvalue()


def test_contract_loads_without_target_columns():
    frame = mod._read_artifact(_zip(_contract_frame()), target=False)
    assert len(frame) == 74
    assert "centre_delta" not in frame
    assert frame.groupby("league").size().to_dict() == mod.EXPECTED_SOURCE_ROWS


def test_source_identity_fails_closed_on_missing_row():
    frame = _contract_frame().iloc[:-1]
    try:
        mod._read_artifact(_zip(frame), target=False)
    except RuntimeError as error:
        assert "source identity mismatch" in str(error)
    else:
        raise AssertionError("missing cross-league row was accepted")


def test_coverage_gate_blocks_before_target_read(monkeypatch):
    monkeypatch.setattr(mod, "_artifact_bytes", lambda: b"artifact")
    monkeypatch.setattr(mod, "_read_artifact", lambda payload, target: (_ for _ in ()).throw(AssertionError("target read")) if target else _contract_frame()[list(mod.CONTRACT_COLUMNS)])
    monkeypatch.setattr(mod, "_download_football_data", lambda: {})
    monkeypatch.setattr(mod, "_prepare_without_target", lambda contract, data: (pd.DataFrame(), {"passed": False, "movement_target_loaded": False}))
    result = mod.evaluate()
    assert result["decision"] == "BLOCKED_BY_EXISTING_SOURCE_GAP"
    assert result["coverage_audit"]["movement_target_loaded"] is False


def test_evaluate_requires_both_leagues_and_reports_no_bet(monkeypatch):
    contract = _contract_frame()[list(mod.CONTRACT_COLUMNS)]
    index = np.arange(len(contract))
    prepared = contract.copy()
    prepared["match_shape_gap"] = np.linspace(-2, 2, len(prepared))
    prepared["match_shape_expected_corners"] = prepared["opening_lambda"] + prepared["match_shape_gap"]
    targets = _contract_frame()[list(mod.TARGET_COLUMNS)].copy()
    targets["centre_delta"] = np.linspace(-1, 1, len(targets))
    targets["closing_lambda"] = contract["opening_lambda"].to_numpy() + targets["centre_delta"].to_numpy()
    monkeypatch.setattr(mod, "_artifact_bytes", lambda: b"artifact")
    monkeypatch.setattr(mod, "_download_football_data", lambda: {})
    monkeypatch.setattr(mod, "_prepare_without_target", lambda source, data: (prepared, {"passed": True, "movement_target_loaded": False}))
    monkeypatch.setattr(mod, "_read_artifact", lambda payload, target: targets if target else contract)
    monkeypatch.setattr(mod, "PERMUTATION_DRAWS", 100)
    result = mod.evaluate()
    assert result["decision"] == "SUPPORTED_FOR_FUTURE_CONFIRMATION"
    assert set(result["raw_continuous"]["by_league"]) == set(mod.LEAGUES)
    assert result["safety"]["no_bet"] is True
    assert "not untouched confirmation" in result["interpretation_guard"]
