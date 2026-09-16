import numpy as np,pandas as pd
from la_liga_market_state_decomposition_v11 import add_market_geometry,FEATURE_VARIANTS

def test_market_geometry_is_preclose_probability_only():
 f=pd.DataFrame({'standard_home_prob':[.6,.3],'standard_draw_prob':[.25,.3],'standard_away_prob':[.15,.4]});o=add_market_geometry(f)
 assert np.allclose(o.favorite_prob,[.6,.4]);assert np.allclose(o.top_two_gap,[.35,.1]);assert (o.market_entropy>0).all()

def test_variants_never_use_closing_or_outcome_fields():
 forbidden=('closing','target','result','goal','ftr')
 for cols in FEATURE_VARIANTS.values():
  assert all(not any(x in c.lower() for x in forbidden) for c in cols)
