from epl_cross_book_direction_decomposition_v16 import EXPERIMENT_ID,FEATURE_VARIANTS,Q,C

def test_frozen_contract():
 assert EXPERIMENT_ID=='EPL_CROSS_BOOK_DIRECTION_DECOMPOSITION_V16';assert Q==.75;assert C==.1
 assert set(FEATURE_VARIANTS)=={'B365_ONLY','PINNACLE_ONLY','DISAGREEMENT_ONLY','DISAGREEMENT_MAGNITUDE','B365_PLUS_DISAGREEMENT','V15_FULL'}

def test_disagreement_is_isolated():
 assert FEATURE_VARIANTS['DISAGREEMENT_ONLY']==['disagree_home','disagree_draw','disagree_away']
 assert FEATURE_VARIANTS['DISAGREEMENT_MAGNITUDE']==['favorite_gap']

def test_no_closing_features():
 assert all('closing' not in c.lower() for cols in FEATURE_VARIANTS.values() for c in cols)
