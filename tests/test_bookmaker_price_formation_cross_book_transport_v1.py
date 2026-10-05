from io import BytesIO

import pandas as pd

import bookmaker_price_formation_cross_book_transport_v1 as mod


def _payload(wh_valid_rows=8):
    rows = []
    mappings = {**mod.BOOKMAKERS, "AVG": mod.CONSENSUS}
    for index in range(10):
        row = {}
        for book, horizons in mappings.items():
            for columns in horizons.values():
                for column in columns:
                    row[column] = 2.0
            if book == "WH" and index >= wh_valid_rows:
                row[horizons["closing"][0]] = None
        rows.append(row)
    return pd.DataFrame(rows).to_csv(index=False).encode()


def test_outcome_free_coverage_selects_every_qualifying_third_book():
    payloads = {
        (league, season): _payload()
        for league in mod.LEAGUES
        for season in (mod.VALIDATION, mod.TEST)
    }
    audit, books, gate = mod._coverage_audit(payloads)
    assert gate is True
    assert books == ["BW", "IW", "VC"]
    assert audit["coverage"]["WH"]["BUNDESLIGA:2024-2025"]["coverage"] == 0.8
    assert audit["outcome_read_before_audit"] is False


def _split_report(vector=(0.01, -0.005, -0.005), common_high=-0.001):
    decomposition = {
        "specific_variance_share": 0.20,
        "variance_after_margin_fraction": 0.80,
        "mean_specific_move": dict(zip(("H", "D", "A"), vector)),
    }
    return {
        "common_information": {
            "log_loss": {"mean": -0.01, "ci95_high": common_high},
            "by_league_log_loss": {"BUNDESLIGA": -0.01, "LIGUE_1": -0.02},
        },
        "by_bookmaker": {"BW": {"decomposition": decomposition}},
    }


def test_transport_gate_passes_complete_contract():
    report = _split_report()
    gate = mod._formal_gate(report, report, ["BW"], True)
    assert gate["supported"] is True


def test_transport_gate_rejects_contradictory_third_book_behavior():
    validation = _split_report(vector=(0.01, -0.005, -0.005))
    test = _split_report(vector=(-0.01, 0.005, 0.005))
    gate = mod._formal_gate(validation, test, ["BW"], True)
    assert gate["supported"] is False
    assert gate["gates"]["additional_book_behavior_not_contradictory"] is False


def test_evaluate_fails_closed_before_outcomes_without_third_book(monkeypatch):
    payloads = {
        (league, season): _payload(wh_valid_rows=0)
        for league in mod.LEAGUES
        for season in (mod.VALIDATION, mod.TEST)
    }
    # Make every predeclared third book ineligible while anchors/AVG remain.
    for key, raw in list(payloads.items()):
        frame = pd.read_csv(BytesIO(raw))
        for book in mod.ADDITIONAL:
            for column in mod._all_columns(mod.BOOKMAKERS[book]):
                frame[column] = None
        payloads[key] = frame.to_csv(index=False).encode()

    monkeypatch.setattr(mod, "download_and_audit", lambda _books: (payloads, {}, []))
    monkeypatch.setattr(mod, "_build_rows", lambda *_args: (_ for _ in ()).throw(AssertionError("outcomes read")))
    result = mod.evaluate()
    assert result["decision"] == "BLOCKED_BY_SOURCE_GAP"
    assert result["source_audit"]["outcome_read_before_audit"] is False

