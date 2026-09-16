from serie_a_cross_book_direction_v17 import EXPERIMENT_ID,Q,C,FEATURES

def test_frozen_transfer_contract():
 assert EXPERIMENT_ID=='SERIE_A_CROSS_BOOK_DIRECTION_V17';assert Q==.75;assert C==.1
 assert FEATURES==['disagree_home','disagree_draw','disagree_away']

def test_no_closing_features():
 assert all('closing' not in c.lower() for c in FEATURES)
