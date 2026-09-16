"""V22: quantify 2025/26 cross-book common-support selection after V21.
Research-only. Bet365 STANDARD->explicit closing defines movement/direction; Pinnacle
STANDARD availability defines common support only. No outcomes, betting, promotion or live writes.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd
from bookmaker_reconstruction_devig_v1 import power
from cross_league_structural_break_v19 import LEAGUES,SEASONS,load
EXPERIMENT_ID='CROSS_BOOK_COMMON_SUPPORT_V22';Q=.75
B=['B365H','B365D','B365A'];C=['B365CH','B365CD','B365CA'];P=['PSH','PSD','PSA']
def prepare(raw):
 x=raw.dropna(subset=B+C).copy();a=power(1/x[B].to_numpy(float));c=power(1/x[C].to_numpy(float));
 x['move_home']=np.log(c[:,0]/c[:,1])-np.log(a[:,0]/a[:,1]);x['move_away']=np.log(c[:,2]/c[:,1])-np.log(a[:,2]/a[:,1]);x['movement']=np.sqrt(x.move_home**2+x.move_away**2);x['direction']=(x.move_home>0).astype(int);x['pinnacle_standard_available']=x[P].notna().all(axis=1) if all(k in x for k in P) else False;return x
def stats(z,thr):
 if not len(z):return {'n':0}
 m=z[z.movement>=thr]
 return {'n':int(len(z)),'material_n':int(len(m)),'material_rate':float(len(m)/len(z)),'movement_mean':float(z.movement.mean()),'movement_p75':float(z.movement.quantile(.75)),'direction_rate_all':float(z.direction.mean()),'direction_rate_material':float(m.direction.mean()) if len(m) else None}
def summarize(raw):
 x=prepare(raw);ss=[s for s in SEASONS.values() if len(x[x.season==s])];rows=[]
 for i,s in enumerate(ss):
  z=x[x.season==s];hist=x[x.season.isin(ss[:i])] if i else z;thr=float(np.quantile(hist.movement,Q));covered=z[z.pinnacle_standard_available];missing=z[~z.pinnacle_standard_available]
  full=stats(z,thr);cov=stats(covered,thr);mis=stats(missing,thr)
  rows.append({'season':s,'threshold_source':'prior_seasons' if i else 'same_season_descriptive_only','threshold':thr,'full':full,'covered':cov,'missing':mis,'coverage':float(len(covered)/len(z)),'covered_minus_full_material_rate':cov.get('material_rate',np.nan)-full['material_rate'] if len(covered) else None,'covered_minus_full_direction_material':cov.get('direction_rate_material')-full['direction_rate_material'] if len(covered) and cov.get('direction_rate_material') is not None and full['direction_rate_material'] is not None else None})
 return rows
def evaluate(work):
 leagues={k:summarize(load(v,work)) for k,v in LEAGUES.items()};latest={k:v[-1] for k,v in leagues.items()}
 return {'experiment_id':EXPERIMENT_ID,'research_only':True,'result':'DIAGNOSTIC_ONLY_NO_BET','production_promotion':False,'betting_enabled':False,'match_outcome_used':False,'standard_is_labeled_opening':False,'movement_quantile':Q,'support_definition':'Pinnacle STANDARD 1X2 present on Bet365 STANDARD+closing-valid row','leagues':leagues,'latest_2025_26':latest,'latest_all_coverage_below_60pct':all(r['coverage']<.6 for r in latest.values())}
def main():
 p=argparse.ArgumentParser();p.add_argument('--work-dir',type=Path,default=Path('artifacts/cross_book_common_support_v22/work'));p.add_argument('--output',type=Path,default=Path('artifacts/cross_book_common_support_v22/report.json'));a=p.parse_args();r=evaluate(a.work_dir);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps(r,indent=2,sort_keys=True))
if __name__=='__main__':main()
