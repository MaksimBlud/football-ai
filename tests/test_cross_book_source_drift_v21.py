import numpy as np,pandas as pd
import cross_book_source_drift_v21 as v

def frame():
 rows=[]
 for s in ['2024-2025','2025-2026']:
  for i in range(8):
   rows.append({'season':s,'B365H':2+i*.01,'B365D':3.2,'B365A':3.8,'B365CH':1.95+i*.01,'B365CD':3.3,'B365CA':3.9,'PSH':2.02+i*.01,'PSD':3.18,'PSA':3.75,'PSCH':1.98+i*.01,'PSCD':3.25,'PSCA':3.85,'FTR':'H' if i%2 else 'A'})
 return pd.DataFrame(rows)

def test_outcomes_do_not_change_diagnostic():
 a=frame();b=a.copy();b['FTR']='D'
 assert v.summarize(a)==v.summarize(b)

def test_closing_changes_book_movement_not_standard_disagreement():
 a=frame();b=a.copy();b['B365CH']*=.8
 sa=v.summarize(a)[-1];sb=v.summarize(b)[-1]
 assert sa['cross_standard']==sb['cross_standard']
 assert not np.isclose(sa['b365']['movement_mean'],sb['b365']['movement_mean'])

def test_missing_pinnacle_closing_is_explicit_not_fatal():
 a=frame().drop(columns=['PSCH','PSCD','PSCA']);s=v.summarize(a)[-1]
 assert s['pinnacle']['paired_n']==0
 assert s['b365']['paired_n']>0
