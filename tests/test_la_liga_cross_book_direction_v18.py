from la_liga_cross_book_direction_v18 import EXPERIMENT_ID,Q,C,FEATURES

def test_frozen_transfer_contract():
 assert EXPERIMENT_ID=='LA_LIGA_CROSS_BOOK_DIRECTION_V18';assert Q==.75;assert C==.1
 assert FEATURES==['disagree_home','disagree_draw','disagree_away']

def test_no_closing_features():
 assert all('closing' not in c.lower() for c in FEATURES)
