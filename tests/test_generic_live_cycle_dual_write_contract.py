from pathlib import Path


CYCLES = (
    "bundesliga_live_cycle.py",
    "serie_a_live_cycle.py",
    "ligue1_live_cycle.py",
    "eredivisie_live_cycle.py",
    "rpl_live_cycle.py",
)


def test_clean_parity_generic_cycles_use_one_guarded_dual_write():
    for filename in CYCLES:
        source = Path(filename).read_text(encoding="utf-8")
        compact = "".join(source.split())
        assert "importleague_dual_write_guardasdual_write_guard" in compact, filename
        assert "dual_write_guard.execute_dual_write(" in compact, filename
        assert "persistence.persist_observations(" not in compact, filename
        assert "prediction_ledger.persist_current_predictions(" not in compact, filename


def test_generic_cycles_preserve_market_only_and_finished_result_guards():
    for filename in CYCLES:
        source = Path(filename).read_text(encoding="utf-8")
        assert "CALIBRATION_REQUIRED" in source, filename
        assert "Structural V2" in source, filename
        assert "results_before" in source or "res0" in source, filename
        assert "results_after" in source or "res1" in source, filename
        assert "persist_results(" not in source, filename
        assert "football_model_xgboost_elo" not in source, filename
