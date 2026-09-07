"""Deterministic audit for CORNER_COMBINED_DISCRIMINATOR_V4. Research only."""
from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd

EXPECTED_SEASONS = (
    "2019/2020","2020/2021","2021/2022","2022/2023",
    "2023/2024","2024/2025","2025/2026",
)
MIN_WEIGHTED_AUC = 0.52
MIN_POSITIVE_SEASONS = 5


def validate_reference(frame: pd.DataFrame) -> None:
    required={"season","matches","train_matches","intercept","b_corner","b_shots","b_sot","auc_9_5"}
    missing=required-set(frame.columns)
    if missing:
        raise ValueError(f"missing reference columns: {sorted(missing)}")
    seasons=tuple(frame["season"].astype(str))
    if seasons!=EXPECTED_SEASONS:
        raise ValueError(f"unexpected held-out seasons: {seasons}")
    if (frame["matches"]<=0).any() or (frame["train_matches"]<=0).any():
        raise ValueError("invalid train/test coverage")


def summarize(frame: pd.DataFrame) -> dict[str,float|int|str]:
    validate_reference(frame)
    w=frame["matches"].astype(float)
    weighted_auc=float((frame["auc_9_5"]*w).sum()/w.sum())
    wins=int((frame["auc_9_5"]>0.5).sum())
    status=("PORTABLE_COMBINED_DISCRIMINATOR"
            if weighted_auc>MIN_WEIGHTED_AUC and wins>=MIN_POSITIVE_SEASONS
            else "NOT_PORTABLE_COMBINED_DISCRIMINATOR")
    return {"research_block":"CORNER_COMBINED_DISCRIMINATOR_V4","status":status,
            "matches":int(w.sum()),"seasons":len(frame),"weighted_auc_9_5":weighted_auc,
            "seasons_above_0_5":wins}


def write_report(reference:Path,output_dir:Path)->Path:
    report=pd.DataFrame([summarize(pd.read_csv(reference))])
    output_dir.mkdir(parents=True,exist_ok=True)
    path=output_dir/"corner_combined_discriminator_v4_summary.csv"
    report.to_csv(path,index=False)
    return path


def main()->None:
    p=argparse.ArgumentParser(); p.add_argument("--reference",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,default=Path("artifacts/corner_combined_discriminator_v4"))
    a=p.parse_args(); out=write_report(a.reference,a.output_dir); print(pd.read_csv(out).to_string(index=False))

if __name__=="__main__": main()
