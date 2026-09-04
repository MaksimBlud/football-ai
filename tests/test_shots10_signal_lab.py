import pandas as pd

from shots10_signal_lab import SHOTS_FEATURES, build_shots10_features, paired_incremental, run_shots10_lab


def _raw():
    return pd.DataFrame([
        {"Date":"01/08/2023","HomeTeam":"A","AwayTeam":"B","FTR":"H","_season":"2023/24","HS":10,"AS":8,"HST":4,"AST":3,"B365H":2.0,"B365D":3.2,"B365A":4.0},
        {"Date":"05/08/2023","HomeTeam":"C","AwayTeam":"A","FTR":"D","_season":"2023/24","HS":7,"AS":12,"HST":2,"AST":5,"B365H":2.4,"B365D":3.1,"B365A":3.0},
        {"Date":"10/08/2023","HomeTeam":"A","AwayTeam":"D","FTR":"A","_season":"2023/24","HS":14,"AS":9,"HST":6,"AST":4,"B365H":2.1,"B365D":3.3,"B365A":3.7},
    ])


def test_current_match_shots_are_not_in_its_snapshot():
    f=build_shots10_features(_raw(),"EPL")
    assert pd.isna(f.iloc[0].home_shots_for_10)
    assert f.iloc[1].away_team=="A"
    assert f.iloc[1].away_shots_for_10==10
    assert f.iloc[1].away_shots_against_10==8
    assert f.iloc[2].home_shots_for_10==11
    assert f.iloc[2].home_sot_for_10==4.5


def test_future_rows_do_not_change_prior_shot_features():
    base=build_shots10_features(_raw().iloc[:2].copy(),"EPL")
    extended=build_shots10_features(_raw(),"EPL").iloc[:2].reset_index(drop=True)
    pd.testing.assert_frame_equal(base.reset_index(drop=True),extended)


def test_feature_family_is_frozen():
    assert SHOTS_FEATURES==["diff_shots_for_10","diff_shots_against_10","diff_sot_for_10","diff_sot_against_10"]


def test_walk_forward_paired_market_comparison():
    rows=[]
    for s in range(5):
        season=f"20{20+s}/{str(21+s).zfill(2)}"
        for i in range(30):
            rows.append({
                "league":"EPL","season":season,"match_date":pd.Timestamp(2020+s,8,1)+pd.Timedelta(days=i),
                "home_team":f"T{i%6}","away_team":f"T{(i+1)%6}","result":["H","D","A"][i%3],
                "market_home":0.45,"market_draw":0.28,"market_away":0.27,
                "diff_shots_for_10":float((i%7)-3),"diff_shots_against_10":float(((i+2)%7)-3),
                "diff_sot_for_10":float((i%5)-2),"diff_sot_against_10":float(((i+1)%5)-2),
            })
    results=run_shots10_lab(pd.DataFrame(rows),min_train_seasons=3)
    assert set(results.feature_set)=={"MARKET_RAW","SHOTS10_ONLY","MARKET_MODEL","MARKET_SHOTS10"}
    paired=paired_incremental(results)
    assert len(paired)==2
