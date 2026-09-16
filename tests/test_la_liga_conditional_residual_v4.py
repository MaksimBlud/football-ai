import numpy as np
from la_liga_conditional_residual_v4 import _candidate, _entropy


def test_gate_fallback_is_exact_market_for_unacted_rows():
    market=np.array([[.5,.3,.2],[.2,.3,.5]])
    residual=np.array([[.2,0,-.2],[-.2,0,.2]])
    mask=np.array([True,False])
    out=_candidate(market,residual,mask)
    assert np.array_equal(out[1],market[1])
    assert not np.array_equal(out[0],market[0])
    assert np.allclose(out.sum(axis=1),1.0)


def test_entropy_is_lower_for_confident_market():
    p=np.array([[.8,.1,.1],[1/3,1/3,1/3]])
    e=_entropy(p)
    assert e[0] < e[1]
