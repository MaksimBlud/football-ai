import numpy as np
import pandas as pd
import pytest

import cross_market_lead_lag_regime_audit_v1 as audit


def _cell_rows(season: str, league: str, value: float, n: int = 50):
    rows = []
    for index in range(n):
        sign = 1.0 if index % 2 == 0 else -1.0
        lead = np.array([0.02 * sign, -0.01 * sign, -0.01 * sign])
        move = lead * (value / 0.0006 if value != 0 else 0.0)
        rows.append(
            {
                "league": league,
                "season": season,
                "alignment_dot": float(np.dot(lead, move)),
                "positive_alignment": bool(np.dot(lead, move) > 0),
                "gap_open_tv": 0.02,
                "gap_reduction_tv": -0.01,
                "open_to_close_move_tv": 0.02,
                "lead_home": lead[0],
                "lead_draw": lead[1],
                "lead_away": lead[2],
                "move_home": move[0],
                "move_draw": move[1],
                "move_away": move[2],
            }
        )
    return rows


def test_scope_is_exact_five_leagues_seven_seasons():
    assert audit.LEAGUES == (
        "EPL",
        "LA_LIGA",
        "SERIE_A",
        "BUNDESLIGA",
        "LIGUE_1",
    )
    assert audit.SEASONS == (
        "2019-2020",
        "2020-2021",
        "2021-2022",
        "2022-2023",
        "2023-2024",
        "2024-2025",
        "2025-2026",
    )
    assert "2026-2027" not in audit.SEASONS


def test_audit_inherits_exact_statistical_seed_and_draws():
    assert audit.PERMUTATION_DRAWS == 10000
    assert audit.BOOTSTRAP_DRAWS == 10000
    assert audit.RANDOM_SEED == 20261004


def test_season_report_requires_all_five_leagues():
    rows = []
    for league in audit.LEAGUES[:-1]:
        rows.extend(
            _cell_rows(
                "2025-2026",
                league,
                0.0001,
                n=10,
            )
        )

    with pytest.raises(RuntimeError, match="missing LIGUE_1"):
        audit._season_report(
            pd.DataFrame(rows),
            "2025-2026",
        )


def test_season_permutation_detects_perfect_match_specific_alignment():
    rows = []
    for league in audit.LEAGUES:
        rows.extend(
            _cell_rows(
                "2025-2026",
                league,
                0.0006,
                n=40,
            )
        )

    report = audit._season_permutation(pd.DataFrame(rows))
    assert report["observed_mean_alignment_dot"] > 0.0
    assert report["one_sided_p"] < 0.01


def test_season_bootstrap_positive_sample_has_positive_ci():
    rows = []
    for league in audit.LEAGUES:
        for _ in range(40):
            rows.append(
                {
                    "league": league,
                    "alignment_dot": 0.001,
                }
            )

    report = audit._season_bootstrap(pd.DataFrame(rows))
    assert report["ci95_low"] > 0.0


def test_target_minus_prior_reports_all_five_leagues():
    rows = []
    for season in audit.SEASONS:
        for league in audit.LEAGUES:
            value = 0.002 if season == audit.TARGET_SEASON else 0.001
            for _ in range(10):
                rows.append(
                    {
                        "league": league,
                        "season": season,
                        "alignment_dot": value,
                    }
                )

    report = audit._target_minus_prior_bootstrap(
        pd.DataFrame(rows)
    )

    assert report["observed_target_minus_prior"] == pytest.approx(0.001)
    assert report["positive_within_league_differences"] == 5
    assert set(report["by_league"]) == set(audit.LEAGUES)
    assert report["bootstrap_ci95_low"] > 0.0


def test_diagnostic_is_explicitly_posthoc_not_confirmatory():
    # Guard the semantic boundary independently of runtime data.
    assert audit.EXPERIMENT_ID == "CROSS_MARKET_LEAD_LAG_REGIME_AUDIT_V1"
    assert audit.TARGET_SEASON == "2025-2026"
    assert audit.PRIOR_SEASONS == audit.SEASONS[:-1]
