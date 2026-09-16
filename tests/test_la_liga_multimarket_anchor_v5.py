import numpy as np
from la_liga_multimarket_anchor_v5 import _binary_devig

def test_binary_devig_is_probability():
    p=_binary_devig(1.9,1.9)
    assert 0<p<1 and np.isclose(p,0.5)

def test_binary_devig_favors_shorter_price():
    assert _binary_devig(1.7,2.2)>0.5
