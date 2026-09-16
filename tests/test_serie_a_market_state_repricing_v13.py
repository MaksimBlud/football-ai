from serie_a_market_state_repricing_v13 import EXPERIMENT_ID,MOVEMENT_QUANTILE,C,FEATURES

def test_replication_contract_is_frozen_from_la_liga():
 assert EXPERIMENT_ID=='SERIE_A_MARKET_STATE_REPRICING_V13';assert MOVEMENT_QUANTILE==.75;assert C==.1
 assert set(FEATURES)=={'FULL_PROBS','DRAW_LEVEL','ENTROPY','FAVORITE_STRENGTH','TOP_TWO_GAP'}
def test_features_are_preclose_only():
 assert all('closing' not in c.lower() and 'target' not in c.lower() for cols in FEATURES.values() for c in cols)
