from pathlib import Path


def test_rpl_live_cycle_uses_serialized_shadow_before_durable_persistence():
    source = Path("rpl_live_cycle.py").read_text(encoding="utf-8")
    run_cycle = source[source.index("def run_cycle") :]
    compact = "".join(run_cycle.split())

    serialized = compact.index("observation_mirror.load_market_shadow()")
    build = compact.index("observation_mirror.build_market_only_observations(persisted_shadow)")
    persist = compact.index("persistence.persist_observations(")
    ledger = compact.index("prediction_ledger.persist_current_predictions()")

    assert serialized < build < persist < ledger


def test_rpl_live_cycle_never_modifies_finished_results():
    source = Path("rpl_live_cycle.py").read_text(encoding="utf-8")
    assert "persist_results(" not in source
    assert "update_rpl_results" not in source
