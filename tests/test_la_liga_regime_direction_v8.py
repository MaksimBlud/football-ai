import numpy as np
from la_liga_regime_direction_v8 import baseline, metrics

def test_constant_direction_baseline():
    y=np.array([0,1,1,0]); m=baseline(y,0.5); assert m['brier']==0.25; assert m['roc_auc']==0.5

def test_informative_direction_probabilities_improve_proper_scores():
    y=np.array([0,0,1,1]); b=baseline(y,0.5); c=metrics(y,np.array([0.1,0.2,0.8,0.9])); assert c['brier']<b['brier']; assert c['log_loss']<b['log_loss']
