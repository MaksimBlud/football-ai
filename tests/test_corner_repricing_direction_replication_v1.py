import numpy as np
import pandas as pd

import corner_repricing_direction_replication_v1 as m


def _row(fid, league, opening_lambda, movement, sign=1):
    delta = abs(movement) * (1 if sign >= 0 else -1)
    return {
        "fixture_id": str(fid),
        "league": league,
        "opening_lambda": float(opening_lambda),
        "closing_lambda": float(opening_lambda + delta),
        "centre_delta": float(delta),
        "movement_magnitude": float(abs(delta)),
    }


def test_frozen_contract_constants():
    assert m.EXPERIMENT_ID == "CORNER_REPRICING_DIRECTION_REPLICATION_V1"
    assert m.FIXTURES_PER_LEAGUE == 10
    assert m.MAX_PROVIDER_REQUESTS == 60
    assert m.MOVEMENT_QUANTILE == 0.75
    assert m.LOGISTIC_C == 0.1
    assert m.MIN_TOTAL_ROWS == 30
    assert m.MIN_HIGH_RISK_NONZERO == 8
    assert m.DIRECTION_MIN_POSITIVE_SHARE == 0.70
    assert m.DIRECTION_MAX_PVALUE == 0.10


def test_selection_excludes_all_v1_ids_and_is_deterministic():
    data = []
    for idx in range(15):
        data.append(
            {
                "id": str(100 + idx),
                "status": "finished",
                "kickoff_utc": f"2026-09-{15-idx:02d}T12:00:00Z",
                "teams": {
                    "home": {"name": f"H{idx}"},
                    "away": {"name": f"A{idx}"},
                },
            }
        )
    payload = {"success": 1, "data": data}
    excluded = {"100", "101", "102"}
    selected = m.select_unseen_fixtures(payload, "EPL", excluded)
    assert len(selected) == 10
    assert not ({r["fixture_id"] for r in selected} & excluded)
    assert selected[0]["fixture_id"] == "103"


def test_sample_gate_fails_closed():
    v1_rows = []
    for league in m.LEAGUES:
        for idx in range(11):
            v1_rows.append(_row(f"old-{league}-{idx}", league, 9 + idx / 10, 0.1))
    fresh = pd.DataFrame(
        [_row(f"new-{idx}", "EPL", 9 + idx / 10, 0.2) for idx in range(20)]
    )
    _, report = m.evaluate_fresh(pd.DataFrame(v1_rows), fresh)
    assert report["verdict"] == "SAMPLE_TOO_SMALL"


def test_frozen_predictor_uses_negative_fair_centre_relationship():
    rows = []
    for league in m.LEAGUES:
        for idx in range(11):
            opening = 8.0 + idx * 0.4
            movement = 1.0 if idx < 3 else 0.1
            rows.append(_row(f"{league}-{idx}", league, opening, movement))
    model, threshold, prevalence = m.fit_frozen_v1_predictor(pd.DataFrame(rows))
    coef = float(model.named_steps["logit"].coef_[0][0])
    assert coef < 0
    assert threshold > 0
    assert 0 < prevalence < 1


def test_direction_gate_can_confirm_on_fresh_unseen_rows():
    v1_rows = []
    for league in m.LEAGUES:
        for idx in range(11):
            opening = 8.0 + idx * 0.4
            movement = 1.2 if idx < 3 else 0.05
            v1_rows.append(_row(f"old-{league}-{idx}", league, opening, movement))

    fresh_rows = []
    for league_num, league in enumerate(m.LEAGUES):
        for idx in range(8):
            opening = 8.0 + idx * 0.5
            # lowest opening centres are highest predicted risk; make top two
            # per league large positive moves so pooled high-risk direction is 10/10.
            if idx < 2:
                movement, sign = 1.3, 1
            else:
                movement, sign = 0.05, -1 if idx % 2 else 1
            fresh_rows.append(
                _row(f"new-{league_num}-{idx}", league, opening, movement, sign)
            )

    detail, report = m.evaluate_fresh(
        pd.DataFrame(v1_rows),
        pd.DataFrame(fresh_rows),
    )
    assert len(detail) == 40
    assert report["sample_gate_pass"] is True
    assert report["direction"]["high_risk_nonzero"] == 10
    assert report["direction"]["positive_moves"] == 10
    assert report["direction"]["confirmed"] is True
    assert report["verdict"] == "REPRICING_AND_DIRECTION_REPLICATED"


def test_direction_gate_requires_minimum_nonzero_high_risk_rows():
    v1_rows = []
    for league in m.LEAGUES:
        for idx in range(11):
            opening = 8.0 + idx * 0.4
            movement = 1.2 if idx < 3 else 0.05
            v1_rows.append(_row(f"old-{league}-{idx}", league, opening, movement))

    fresh_rows = []
    for league_num, league in enumerate(m.LEAGUES):
        for idx in range(8):
            opening = 8.0 + idx * 0.5
            row = _row(f"new-{league_num}-{idx}", league, opening, 0.05, 1)
            if idx < 2 and league_num >= 2:
                row["centre_delta"] = 0.0
                row["closing_lambda"] = row["opening_lambda"]
                row["movement_magnitude"] = 0.0
            fresh_rows.append(row)

    _, report = m.evaluate_fresh(pd.DataFrame(v1_rows), pd.DataFrame(fresh_rows))
    assert report["direction"]["high_risk_nonzero"] < m.MIN_HIGH_RISK_NONZERO
    assert report["direction"]["confirmed"] is False
