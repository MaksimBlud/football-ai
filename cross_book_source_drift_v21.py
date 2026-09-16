"""V21: distinguish market-dynamics drift from historical source/field drift.
Research-only descriptive audit. Uses Bet365/Pinnacle STANDARD prices and explicit
closing prices where available. No match outcomes, betting, promotion, paid API or live writes.
STANDARD prices are deliberately not labelled opening prices.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd
from bookmaker_reconstruction_devig_v1 import power
from cross_league_structural_break_v19 import LEAGUES,SEASONS,load
EXPERIMENT_ID='CROSS_BOOK_SOURCE_DRIFT_V21'
BOOKS={
 'B365':(('B365H','B365D','B365A'),('B365CH','B365CD','B365CA')),
 'PINNACLE':(('PSH','PSD','PSA'),('PSCH','PSCD','PSCA')),
}
def fair(x,cols): return power(1/x[list(cols)].to_numpy(float))
def book_stats(raw,std,close):
 present=[c for c in (*std,*close) if c in raw.columns]
 if len(present)<6:return {'columns_present':present,'paired_n':0,'coverage':0.0}
 x=raw.dropna(subset=[*std,*close]).copy()
 if not len(x):return {'columns_present':present,'paired_n':0,'coverage':0.0}
 a=fair(x,std);b=fair(x,close);mh=np.log(b[:,0]/b[:,1])-np.log(a[:,0]/a[:,1]);ma=np.log(b[:,2]/b[:,1])-np.log(a[:,2]/a[:,1]);mag=np.sqrt(mh**2+ma**2)
 return {'columns_present':present,'paired_n':int(len(x)),'coverage':float(len(x)/len(raw)),'movement_mean':float(mag.mean()),'movement_p50':float(np.quantile(mag,.5)),'movement_p75':float(np.quantile(mag,.75)),'home_vs_draw_positive_rate':float((mh>0).mean())}
def cross_stats(raw):
 cols=['B365H','B365D','B365A','PSH','PSD','PSA'];present=[c for c in cols if c in raw.columns]
 if len(present)<6:return {'columns_present':present,'paired_n':0,'coverage':0.0}
 x=raw.dropna(subset=cols);a=fair(x,cols[:3]);b=fair(x,cols[3:]);d=b-a
 return {'columns_present':present,'paired_n':int(len(x)),'coverage':float(len(x)/len(raw)),'disagreement_norm_mean':float(np.linalg.norm(d,axis=1).mean()),'disagreement_norm_p75':float(np.quantile(np.linalg.norm(d,axis=1),.75)),'home_disagreement_mean':float(d[:,0].mean())}
def summarize(raw):
 rows=[]
 for s in SEASONS.values():
  z=raw[raw.season==s]
  if not len(z):continue
  row={'season':s,'rows':int(len(z)),'cross_standard':cross_stats(z)}
  for book,(std,close) in BOOKS.items():row[book.lower()]=book_stats(z,std,close)
  rows.append(row)
 return rows
def evaluate(work):
 leagues={}
 for league,code in LEAGUES.items():
  rows=summarize(load(code,work));latest=rows[-1];prior=rows[-2] if len(rows)>1 else None
  leagues[league]={'seasons':rows,'latest':latest,'prior':prior,'latest_pinnacle_closing_available':bool(latest['pinnacle']['paired_n']),'latest_b365_closing_available':bool(latest['b365']['paired_n'])}
 return {'experiment_id':EXPERIMENT_ID,'research_only':True,'result':'DIAGNOSTIC_ONLY_NO_BET','production_promotion':False,'betting_enabled':False,'match_outcome_used':False,'standard_is_labeled_opening':False,'purpose':'Separate bookmaker-specific STANDARD-to-closing dynamics from cross-book STANDARD/source coverage drift.','leagues':leagues}
def main():
 p=argparse.ArgumentParser();p.add_argument('--work-dir',type=Path,default=Path('artifacts/cross_book_source_drift_v21/work'));p.add_argument('--output',type=Path,default=Path('artifacts/cross_book_source_drift_v21/report.json'));a=p.parse_args();r=evaluate(a.work_dir);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps(r,indent=2,sort_keys=True))
if __name__=='__main__':main()
