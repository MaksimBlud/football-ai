from epl_cross_book_direction_v15 import EXPERIMENT_ID,Q,C,FEATURES

def test_fixed_research_contract():
    assert EXPERIMENT_ID == 'EPL_CROSS_BOOK_DIRECTION_V15'
    assert Q == .75
    assert C == .1
    assert set(('disagree_home','disagree_draw','disagree_away','favorite_gap')).issubset(FEATURES)

def test_feature_names_are_prematch_market_state():
    assert all('closing' not in name.lower() for name in FEATURES)
