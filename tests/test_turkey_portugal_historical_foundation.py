from datetime import date

import pandas as pd
import pytest

import audit_turkey_portugal_historical_foundation as audit
from primeira_liga_runtime_config import PRIMEIRA_LIGA_RUNTIME_CONFIG
from turkey_super_lig_runtime_config import TURKEY_SUPER_LIG_RUNTIME_CONFIG


def _season_frame(teams=("A", "B", "C", "D")):
    rows = []
    day = 1
    for home in teams:
        for away in teams:
            if home == away:
                continue
            rows.append(
                {
                    "Date": f"{day:02d}/01/2020",
                    "HomeTeam": home,
                    "AwayTeam": away,
                    "FTHG": 1,
                    "FTAG": 0,
                    "FTR": "H",
                }
            )
            day += 1
    return pd.DataFrame(rows)


def test_season_completion_gate_is_as_of_aware():
    assert audit.season_is_complete("2025-2026", date(2026, 9, 5)) is True
    assert audit.season_is_complete("2026-2027", date(2026, 9, 5)) is False
    assert audit.season_is_complete("2025-2026", date(2026, 6, 30)) is False
    assert audit.season_is_complete("2025-2026", date(2026, 7, 1)) is True


@pytest.mark.parametrize(
    "config,competition",
    [
        (TURKEY_SUPER_LIG_RUNTIME_CONFIG, "T1"),
        (PRIMEIRA_LIGA_RUNTIME_CONFIG, "P1"),
    ],
)
def test_audit_uses_completed_seasons_and_keeps_current_availability_only(
    monkeypatch,
    config,
    competition,
):
    frame = _season_frame()

    def fake_fetch(session, *, code, competition, attempts=4):
        return frame.copy(), f"https://example.test/{code}/{competition}.csv"

    monkeypatch.setattr(audit, "_fetch_csv", fake_fetch)
    result = audit.audit_league(
        config,
        as_of=date(2026, 9, 5),
        session=object(),
    )

    assert result["competition_code"] == competition
    assert result["configured_seasons"] == 11
    assert result["available_seasons"] == 11
    assert result["completed_seasons"] == 10
    assert result["completed_matches"] == 120
    assert result["temporal_feature_rows"] == 120
    assert result["trainable_rows"] > 0
    assert result["calibration_status"] == "CALIBRATION_REQUIRED"
    assert result["seasons"][-1]["season"] == "2026-2027"
    assert result["seasons"][-1]["normalized_rows"] == 0
    assert result["seasons"][-1]["complete_double_round_robin"] is None


def test_incomplete_completed_season_is_a_hard_failure(monkeypatch):
    complete = _season_frame()
    incomplete = complete.iloc[:-1].copy()

    def fake_fetch(session, *, code, competition, attempts=4):
        if code == "1617":
            return incomplete, "https://example.test/incomplete.csv"
        return complete.copy(), "https://example.test/complete.csv"

    monkeypatch.setattr(audit, "_fetch_csv", fake_fetch)

    with pytest.raises(ValueError, match="Incomplete season 2016-2017"):
        audit.audit_league(
            TURKEY_SUPER_LIG_RUNTIME_CONFIG,
            as_of=date(2026, 9, 5),
            session=object(),
        )


def test_alias_collision_is_rejected():
    frame = _season_frame(("A", "B", "C"))
    original = dict(TURKEY_SUPER_LIG_RUNTIME_CONFIG.aliases)
    try:
        TURKEY_SUPER_LIG_RUNTIME_CONFIG.aliases.update({"A": "X", "B": "X"})
        with pytest.raises(ValueError, match="collapse distinct teams"):
            audit._canonical_team_collision_check(
                frame,
                TURKEY_SUPER_LIG_RUNTIME_CONFIG,
            )
    finally:
        TURKEY_SUPER_LIG_RUNTIME_CONFIG.aliases.clear()
        TURKEY_SUPER_LIG_RUNTIME_CONFIG.aliases.update(original)
