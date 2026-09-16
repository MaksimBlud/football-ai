from cross_league_regime_calibration_v20 import EXPERIMENT_ID,RECENT_SEASONS,Q,C,FEATURES

def test_frozen_contract():
 assert EXPERIMENT_ID=='CROSS_LEAGUE_REGIME_CALIBRATION_V20'
 assert RECENT_SEASONS==2;assert Q==.75;assert C==.1
 assert FEATURES==['disagree_home','disagree_draw','disagree_away']

def test_no_target_feature_leakage():
 assert all('close' not in f.lower() and 'movement' not in f.lower() and 'direction' not in f.lower() for f in FEATURES)
