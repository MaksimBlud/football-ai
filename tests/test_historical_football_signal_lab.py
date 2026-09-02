import pandas as pd
from historical_football_signal_lab import build_point_in_time_features, add_difference_features, walk_forward_ablation

def _row(date,h,a,hg,ag,hc,ac,hy=1,ay=1,hr=0,ar=0):
    return {"Date":date,"HomeTeam":h,"AwayTeam":a,"FTHG":hg,"FTAG":ag,"FTR":"H" if hg>ag else "A" if hg<ag else "D","HC":hc,"AC":ac,"HY":hy,"AY":ay,"HR":hr,"AR":ar,"B365H":2.0,"B365D":3.5,"B365A":4.0}

def test_features_are_strictly_pre_match():
    df=pd.DataFrame([_row("01/08/2020","A","B",5,0,10,1),_row("08/08/2020","B","A",1,1,2,8)])
    out=build_point_in_time_features(df,"EPL","2020-2021")
    assert out.iloc[0].home_prior_matches==0
    assert pd.isna(out.iloc[0].home_goals_for_5)
    assert out.iloc[1].away_prior_matches==1
    assert out.iloc[1].away_goals_for_5==5
    assert out.iloc[1].away_corners_for_5==10

def test_home_away_orientation_is_correct():
    df=pd.DataFrame([_row("01/08/2020","A","B",2,1,7,3),_row("08/08/2020","B","C",0,3,4,9),_row("15/08/2020","C","A",1,1,5,6)])
    out=build_point_in_time_features(df,"EPL","2020-2021")
    assert out.iloc[2].away_goals_for_5==2
    assert out.iloc[2].away_goals_against_5==1
    assert out.iloc[2].away_corners_for_5==7

def test_market_probabilities_are_devigged():
    out=build_point_in_time_features(pd.DataFrame([_row("01/08/2020","A","B",1,0,4,2)]),"EPL","2020-2021")
    assert abs(out.iloc[0][["market_home","market_draw","market_away"]].sum()-1)<1e-9

def test_difference_features_exist():
    df=pd.DataFrame([_row("01/08/2020","A","B",1,0,4,2),_row("08/08/2020","A","B",0,1,2,4)])
    out=add_difference_features(build_point_in_time_features(df,"EPL","2020-2021"))
    assert "diff_points_5" in out.columns
