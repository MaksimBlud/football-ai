from serie_a_cross_book_direction_v17 import *
EXPERIMENT_ID='LA_LIGA_CROSS_BOOK_DIRECTION_V18'
def load(work):
 work.mkdir(parents=True,exist_ok=True);out=[]
 for code,s in SEASONS.items():
  p=work/f'{code}.csv'
  if not p.exists():
   r=requests.get(f'https://www.football-data.co.uk/mmz4281/{code}/SP1.csv',timeout=30);r.raise_for_status();p.write_bytes(r.content)
  x=pd.read_csv(p);x['season']=s;out.append(x)
 return pd.concat(out,ignore_index=True)
def evaluate(raw):
 r=__import__('serie_a_cross_book_direction_v17').evaluate(raw);r['experiment_id']=EXPERIMENT_ID;r['league']='LA_LIGA';r.pop('parameters_transferred_without_serie_a_tuning',None);r['parameters_transferred_without_la_liga_tuning']=True;r['source_signal']='EPL_V16_DISAGREEMENT_ONLY';return r
def main():
 p=argparse.ArgumentParser();p.add_argument('--work-dir',type=Path,default=Path('artifacts/la_liga_cross_book_direction_v18/work'));p.add_argument('--output',type=Path,default=Path('artifacts/la_liga_cross_book_direction_v18/report.json'));a=p.parse_args();r=evaluate(load(a.work_dir));a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps(r,indent=2,sort_keys=True))
if __name__=='__main__':main()
