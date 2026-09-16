from epl_market_state_repricing_v14 import EXPERIMENT_ID,MOVEMENT_QUANTILE,C,FEATURES
def test_frozen_cross_league_contract():
 assert EXPERIMENT_ID=='EPL_MARKET_STATE_REPRICING_V14';assert MOVEMENT_QUANTILE==.75;assert C==.1
 assert set(FEATURES)=={'FULL_PROBS','DRAW_LEVEL','ENTROPY','FAVORITE_STRENGTH','TOP_TWO_GAP'}
def test_features_are_standard_market_only():
 assert all('closing' not in c.lower() and 'target' not in c.lower() for cols in FEATURES.values() for c in cols)
