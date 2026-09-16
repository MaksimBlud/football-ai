import numpy as np
from la_liga_v7_incremental_robustness_v9 import losses, paired_bootstrap

def test_binary_losses_are_per_match():
    b,l=losses(np.array([0,1]),np.array([0.2,0.8])); assert np.allclose(b,[.04,.04]); assert np.all(l>0)

def test_paired_bootstrap_detects_uniform_form_improvement():
    y=np.array([0,1]*50); market=np.where(y==1,.6,.4); form=np.where(y==1,.8,.2); r=paired_bootstrap(y,form,market); assert r['delta_brier']<0; assert r['delta_log_loss']<0; assert r['prob_form_improves_both']==1.0
