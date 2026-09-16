import pandas as pd
import cross_book_common_support_v22 as v

def frame():
 rows=[]
 for s in ['2024-2025','2025-2026']:
  for i in range(12):rows.append({'season':s,'B365H':2+i*.02,'B365D':3.2,'B365A':3.8,'B365CH':1.9+i*.02,'B365CD':3.3,'B365CA':3.9,'PSH':2.02 if i<6 else None,'PSD':3.18 if i<6 else None,'PSA':3.75 if i<6 else None,'FTR':'H'})
 return pd.DataFrame(rows)
def test_outcome_does_not_affect_support_audit():
 a=frame();b=a.copy();b['FTR']='A';assert v.summarize(a)==v.summarize(b)
def test_pinnacle_values_only_define_availability_not_movement():
 a=frame();b=a.copy();b.loc[b.PSH.notna(),['PSH','PSD','PSA']]=[9,9,9]
 assert v.summarize(a)==v.summarize(b)
def test_missing_pinnacle_splits_full_sample():
 r=v.summarize(frame())[-1];assert r['full']['n']==r['covered']['n']+r['missing']['n'];assert r['coverage']==.5
