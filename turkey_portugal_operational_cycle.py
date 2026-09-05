"""Quota-safe MARKET_ONLY operational cycle for Turkey Super Lig / Primeira Liga."""
from __future__ import annotations
import argparse
from scheduled_turkey_portugal_odds import run as run_snapshot
from persist_turkey_portugal_prediction_ledger import fetch_recent_snapshots, persist_from_snapshots
from update_turkey_portugal_results import sync_results

LEAGUES=("TURKEY_SUPER_LIG","PRIMEIRA_LIGA")

def run_cycle(league: str):
    snapshot=run_snapshot(league)
    ledger={"inserted":0,"unchanged":0,"conflicts":0,"predictions":0}
    if snapshot.get("status") in {"COLLECTED","NOT_DUE"}:
        recent=fetch_recent_snapshots(league)
        if not recent.empty:
            ledger=persist_from_snapshots(league,recent)
    results=sync_results(league,write=True)
    out={"league":league,"snapshot":snapshot,"ledger":ledger,"results":results,"production_model_used":False,"structural_v2_used":False}
    print(out); return out

def main():
    p=argparse.ArgumentParser(); p.add_argument("league",choices=LEAGUES); a=p.parse_args(); run_cycle(a.league)
if __name__=="__main__": main()
