from cross_league_structural_break_v19 import EXPERIMENT_ID,Q,C,FEATURES,LEAGUES

def test_frozen_contract():
 assert EXPERIMENT_ID=='CROSS_LEAGUE_STRUCTURAL_BREAK_V19';assert Q==.75;assert C==.1
 assert FEATURES==['disagree_home','disagree_draw','disagree_away']
 assert LEAGUES=={'EPL':'E0','SERIE_A':'I1','LA_LIGA':'SP1'}

def test_predictors_are_standard_disagreement_only():
 assert all('closing' not in x.lower() for x in FEATURES)
