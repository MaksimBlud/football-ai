import pandas as pd

from prospective_market_path_sample_growth import readiness_without_outcomes, settled_identity_sample


def _paths(n=100):
    rows=[]
    start=pd.Timestamp('2026-09-05T12:00:00Z')
    for i in range(n):
        rows.append({
            'league':'EPL',
            'event_id':f'e{i}',
            'kickoff_utc':start + pd.Timedelta(days=i),
            'home_team':f'H{i}',
            'away_team':f'A{i}',
        })
    return pd.DataFrame(rows)


def test_settled_identity_sample_uses_presence_only():
    paths=_paths(2)
    audit=pd.DataFrame([
        {'league':'EPL','event_id':'e0','status':'SETTLED_IDENTITY_PRESENT'},
        {'league':'EPL','event_id':'e1','status':'AWAITING_GRACE'},
    ])
    sample=settled_identity_sample(paths,audit)
    assert sample['event_id'].tolist()==['e0']
    assert 'actual_result' not in sample.columns
    assert 'result' not in sample.columns


def test_readiness_counts_match_frozen_threshold_shape_without_outcomes():
    paths=_paths(160)
    audit=pd.DataFrame([
        {'league':'EPL','event_id':event_id,'status':'SETTLED_IDENTITY_PRESENT'}
        for event_id in paths['event_id']
    ])
    sample=settled_identity_sample(paths,audit)
    readiness=readiness_without_outcomes(sample).set_index('league')
    epl=readiness.loc['EPL']
    assert int(epl['settled_fixtures'])==160
    assert int(epl['calendar_months']) >= 5
    assert int(epl['valid_test_blocks']) >= 2
    assert bool(epl['ready']) is True
    assert int(epl['min_fixtures_required'])==100
    assert int(epl['min_months_required'])==4
    assert int(epl['min_test_blocks_required'])==2


def test_empty_sample_is_not_ready_for_any_league():
    readiness=readiness_without_outcomes(pd.DataFrame()).set_index('league')
    assert readiness['ready'].eq(False).all()
    assert readiness['settled_fixtures'].eq(0).all()
