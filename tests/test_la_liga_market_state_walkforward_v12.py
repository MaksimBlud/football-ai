from la_liga_market_state_walkforward_v12 import EXPERIMENT_ID,FOCUS

def test_v12_contract_is_fixed_and_interpretable():
 assert EXPERIMENT_ID=='LA_LIGA_MARKET_STATE_WALKFORWARD_V12'
 assert 'DRAW_LEVEL' in FOCUS and 'ENTROPY' in FOCUS and 'FULL_PROBS' in FOCUS
 assert len(FOCUS)==len(set(FOCUS))
