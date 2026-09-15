"""Replay the frozen Serie A MARKET_ANCHOR_1X2_V2 lambda=1 shadow on saved matches.

Research only. This is a post-outcome diagnostic replay, not prospective evidence.
The V2 residual was frozen only for Serie A, so the valid replay scope is the ten
Serie A fixtures inside POINT_IN_TIME_CROSS_LEAGUE_REPLAY_V1 (47 total events).
No parameter is selected from these outcomes. Production artifacts are never read,
written, trained, or promoted, and this script makes no Odds API or Supabase calls.
"""
from __future__ import annotations

import argparse
from collections import defaultdict, deque
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import types
from typing import Any

import numpy as np
import pandas as pd
import requests

EXPERIMENT_ID = "MARKET_ANCHOR_V2_SAVED_COHORT_REPLAY"
EVIDENCE_CLASS = "POST_OUTCOME_DIAGNOSTIC_REPLAY"
FROZEN_V2_COMMIT = "df19777087fb89af049eedce44ff93f0aa6e6360"
FROZEN_PARENT_REPLAY_COMMIT = "57cace46bcf61557837a8235f1239b06813f39eb"
FROZEN_PARENT_REPLAY_EVENTS = 47
PRIMARY_LEAGUE = "SERIE_A"
FEATURE_VARIANT = "ALL_FOOTBALL"
SHADOW_LAMBDA = 1.0
L2_PENALTY = 1.0
HISTORY_CUTOFF_DATE = pd.Timestamp("2026-09-11")
BASE_URL = "https://www.football-data.co.uk/mmz4281/{code}/I1.csv"
TRAIN_SEASONS = {
    "1617": "2016-2017",
    "1718": "2017-2018",
    "1819": "2018-2019",
    "1920": "2019-2020",
    "2021": "2020-2021",
    "2122": "2021-2022",
    "2223": "2022-2023",
    "2324": "2023-2024",
    "2425": "2024-2025",
    "2526": "2025-2026",
}
CURRENT_SEASON_CODE = "2627"
EXPECTED_FROZEN_GIT_BLOBS = {
    "historical_football_signal_lab.py": "401b3a0893371bfa4a488ec92a4a54af2678c8f7",
    "market_anchor_1x2_v1.py": "58c35bf3768f7bf2b951f19a37b9a5f46b6b9801",
    "market_anchor_1x2_v2_shadow.py": "b2770d726ffafe7a3cef706b57d3391063cbfe1b",
}
SOURCE_NAME = {
    "AC Milan": "Milan",
    "Atalanta BC": "Atalanta",
    "AS Roma": "Roma",
    "Inter Milan": "Inter",
}
RESULT_TO_INT = {"H": 0, "D": 1, "A": 2}

# Market probabilities are the exact 2026-09-11 saved MARKET_ONLY ledger rows used
# by the parent 47-event replay. Old-model probabilities come from the frozen
# POINT_IN_TIME_CROSS_LEAGUE_REPLAY_V1 manifest. Outcomes are now known and are
# used only for this explicitly post-outcome diagnostic.
TARGETS: tuple[dict[str, Any], ...] = (
    {
        "event_id": "a9656d25ca6b06be9e477a098333bd70", "home": "Venezia", "away": "Fiorentina", "result": "A",
        "market": [0.347195829018205, 0.281422174186932, 0.371381996794863],
        "old_model": [0.2372110003648549, 0.2243963446558066, 0.5383926549793384],
    },
    {
        "event_id": "3dba40cdf22e962c0f6f6c940ef01850", "home": "Genoa", "away": "Frosinone", "result": "D",
        "market": [0.445403244400048, 0.282980928929109, 0.271615826670843],
        "old_model": [0.3334816594874364, 0.2821909105124798, 0.3843274300000837],
    },
    {
        "event_id": "b412817739a87e18bf391bf6ccff6560", "home": "Lazio", "away": "AC Milan", "result": "D",
        "market": [0.281318981610276, 0.299624870383391, 0.419056148006334],
        "old_model": [0.2839135910246846, 0.2934240786261582, 0.4226623303491572],
    },
    {
        "event_id": "fd30ca2b96bfa088e51bffddeb3b6e56", "home": "Atalanta BC", "away": "Cagliari", "result": "A",
        "market": [0.599241512092612, 0.237932289673021, 0.162826198234367],
        "old_model": [0.5754179358482361, 0.2043052911758422, 0.2202767729759216],
    },
    {
        "event_id": "e66df35062d3cc1c59258406374c2e76", "home": "Lecce", "away": "Monza", "result": "H",
        "market": [0.358238198691022, 0.307047489045547, 0.334714312263432],
        "old_model": [0.3413350385825347, 0.3025469274087825, 0.3561180340086828],
    },
    {
        "event_id": "27eaaab4498bb2984321e5f81f0ff9fd", "home": "Napoli", "away": "Bologna", "result": "H",
        "market": [0.529471343018315, 0.267441816899981, 0.203086840081704],
        "old_model": [0.5386763375603061, 0.2388650548119859, 0.2224586076277079],
    },
    {
        "event_id": "0a91f850039ce571eb6e90b2eed15548", "home": "Sassuolo", "away": "Juventus", "result": "H",
        "market": [0.182743963070909, 0.242218002399942, 0.575038034529149],
        "old_model": [0.2073271932401416, 0.2628998536735729, 0.5297729530862854],
    },
    {
        "event_id": "17a081148b714450797ef8d6a29d16e6", "home": "Torino", "away": "AS Roma", "result": "A",
        "market": [0.162349921031296, 0.235421660599638, 0.602228418369067],
        "old_model": [0.1335925499675437, 0.2143672470559849, 0.6520402029764713],
    },
    {
        "event_id": "9da3aa4b46166eb4ccd1e600d67080a6", "home": "Como", "away": "Parma", "result": "H",
        "market": [0.774299209903783, 0.155769910752818, 0.0699308793433981],
        "old_model": [0.6703084111213684, 0.2181374281644821, 0.1115541607141494],
    },
    {
        "event_id": "7ea3ea9925ae0f1d149965fb9769c7dc", "home": "Inter Milan", "away": "Udinese", "result": "H",
        "market": [0.758308448454786, 0.157106223942894, 0.08458532760232],
        "old_model": [0.7089131474494934, 0.1738733053207397, 0.1172135472297668],
    },
)


def git_blob_sha1(path: Path) -> str:
    payload = path.read_bytes()
    return hashlib.sha1(f"blob {len(payload)}\0".encode("ascii") + payload).hexdigest()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load frozen module {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_frozen_modules(source_dir: Path):
    for filename, expected_blob in EXPECTED_FROZEN_GIT_BLOBS.items():
        path = source_dir / filename
        if not path.is_file():
            raise FileNotFoundError(path)
        actual = git_blob_sha1(path)
        if actual != expected_blob:
            raise RuntimeError(f"frozen source mismatch for {filename}: {actual} != {expected_blob}")

    lab = load_module("historical_football_signal_lab", source_dir / "historical_football_signal_lab.py")
    runner_stub = types.ModuleType("historical_football_signal_runner")
    runner_stub.LEAGUES = {}
    runner_stub.download = lambda *args, **kwargs: None
    sys.modules["historical_football_signal_runner"] = runner_stub
    v1 = load_module("market_anchor_1x2_v1", source_dir / "market_anchor_1x2_v1.py")
    v2 = load_module("market_anchor_1x2_v2_shadow", source_dir / "market_anchor_1x2_v2_shadow.py")

    if v2.PRIMARY_LEAGUE != PRIMARY_LEAGUE:
        raise RuntimeError("frozen V2 league changed")
    if v2.FEATURE_VARIANT != FEATURE_VARIANT:
        raise RuntimeError("frozen V2 feature variant changed")
    if float(v2.SHADOW_RESIDUAL_LAMBDA) != SHADOW_LAMBDA:
        raise RuntimeError("frozen V2 shadow lambda changed")
    if float(v1.L2_PENALTY) != L2_PENALTY:
        raise RuntimeError("frozen V2 L2 penalty changed")
    return lab, v1, v2


def download_csv(code: str) -> tuple[pd.DataFrame, str]:
    url = BASE_URL.format(code=code)
    response = requests.get(url, timeout=60, headers={"User-Agent": "football-ai-frozen-replay/1"})
    response.raise_for_status()
    if len(response.content) < 500:
        raise RuntimeError(f"suspiciously small Football-Data response for {code}")
    return pd.read_csv(pd.io.common.BytesIO(response.content)), sha256_bytes(response.content)


def build_training_frame(lab) -> tuple[pd.DataFrame, dict[str, str], dict[str, pd.DataFrame]]:
    raw_frames: list[pd.DataFrame] = []
    hashes: dict[str, str] = {}
    by_code: dict[str, pd.DataFrame] = {}
    for code, season in TRAIN_SEASONS.items():
        frame, digest = download_csv(code)
        by_code[code] = frame.copy()
        hashes[code] = digest
        frame = frame.copy()
        frame["_season"] = season
        raw_frames.append(frame)

    raw = pd.concat(raw_frames, ignore_index=True)
    features = lab.build_point_in_time_features(raw, PRIMARY_LEAGUE, "MULTI_SEASON")
    keys = raw[["Date", "HomeTeam", "AwayTeam", "_season"]].copy()
    keys["match_date"] = pd.to_datetime(keys["Date"], dayfirst=True, errors="coerce")
    keys = keys.rename(
        columns={"HomeTeam": "home_team", "AwayTeam": "away_team", "_season": "season"}
    )[["match_date", "home_team", "away_team", "season"]].drop_duplicates()
    features = features.drop(columns=["season"]).merge(
        keys,
        on=["match_date", "home_team", "away_team"],
        how="left",
        validate="one_to_one",
    )
    if features["season"].isna().any():
        raise RuntimeError("failed to restore frozen training season labels")
    return features, hashes, by_code


def build_target_features(lab, historical_by_code: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, str, dict[str, int]]:
    current, current_sha256 = download_csv(CURRENT_SEASON_CODE)
    frames = [historical_by_code[code].copy() for code in TRAIN_SEASONS]
    frames.append(current.copy())
    raw = pd.concat(frames, ignore_index=True)
    raw["match_date"] = pd.to_datetime(raw["Date"], dayfirst=True, errors="coerce")
    raw = raw.dropna(subset=["match_date", "HomeTeam", "AwayTeam", "FTR"])
    raw = raw.loc[raw["match_date"] < HISTORY_CUTOFF_DATE].sort_values("match_date", kind="stable")

    histories = defaultdict(lambda: deque(maxlen=30))
    for _, row in raw.iterrows():
        home, away = str(row.HomeTeam), str(row.AwayTeam)
        hg = float(row.FTHG)
        ag = float(row.FTAG)
        hp, ap = (3.0, 0.0) if hg > ag else ((0.0, 3.0) if hg < ag else (1.0, 1.0))
        vals = {}
        for name, (home_col, away_col) in lab.STAT_COLUMNS.items():
            vals[name] = (
                pd.to_numeric(row.get(home_col), errors="coerce"),
                pd.to_numeric(row.get(away_col), errors="coerce"),
            )
        histories[home].append(
            lab.TeamMatch(hp, hg, ag, vals["corners"][0], vals["corners"][1], vals["yellow"][0], vals["red"][0], True)
        )
        histories[away].append(
            lab.TeamMatch(ap, ag, hg, vals["corners"][1], vals["corners"][0], vals["yellow"][1], vals["red"][1], False)
        )

    records: list[dict[str, Any]] = []
    prior_counts: dict[str, int] = {}
    for target in TARGETS:
        home_source = SOURCE_NAME.get(target["home"], target["home"])
        away_source = SOURCE_NAME.get(target["away"], target["away"])
        if home_source not in histories or away_source not in histories:
            raise RuntimeError(f"missing frozen history for {target['home']} vs {target['away']}")
        record = {"event_id": target["event_id"]}
        record.update(lab._snapshot(histories[home_source], "home"))
        record.update(lab._snapshot(histories[away_source], "away"))
        records.append(record)
        prior_counts[target["event_id"]] = min(len(histories[home_source]), len(histories[away_source]))

    feature_frame = lab.add_difference_features(pd.DataFrame(records).set_index("event_id"))
    frozen_features = list(lab.FEATURE_SETS[FEATURE_VARIANT])
    return feature_frame[frozen_features], current_sha256, prior_counts


def validate_targets() -> None:
    if len(TARGETS) != 10:
        raise RuntimeError("frozen Serie A parent cohort must contain exactly 10 events")
    ids = [row["event_id"] for row in TARGETS]
    if len(ids) != len(set(ids)):
        raise RuntimeError("duplicate event_id in frozen replay cohort")
    for row in TARGETS:
        for field in ("market", "old_model"):
            p = np.asarray(row[field], dtype=float)
            if p.shape != (3,) or not np.isfinite(p).all() or (p <= 0).any():
                raise RuntimeError(f"invalid {field} probabilities for {row['event_id']}")
            if not np.isclose(p.sum(), 1.0, atol=1e-12):
                raise RuntimeError(f"{field} probabilities do not sum to one for {row['event_id']}")
        if row["result"] not in RESULT_TO_INT:
            raise RuntimeError(f"invalid outcome for {row['event_id']}")


def replay(source_dir: Path) -> dict[str, Any]:
    validate_targets()
    lab, v1, v2 = load_frozen_modules(source_dir)
    training, historical_hashes, historical_by_code = build_training_frame(lab)
    artifact = v2.fit_candidate_artifact(training)
    target_features, current_sha256, prior_counts = build_target_features(lab, historical_by_code)

    market = np.asarray([row["market"] for row in TARGETS], dtype=float)
    old_model = np.asarray([row["old_model"] for row in TARGETS], dtype=float)
    y = np.asarray([RESULT_TO_INT[row["result"]] for row in TARGETS], dtype=int)
    shadow = v2.predict_shadow_residual(market, target_features, artifact)
    active = v2.predict_candidate(market, target_features, artifact)
    if not np.allclose(active, market, atol=1e-15, rtol=0):
        raise RuntimeError("frozen active V2 must remain exact market fallback")

    market_score = v1.score_probabilities(y, market)
    old_score = v1.score_probabilities(y, old_model)
    shadow_score = v1.score_probabilities(y, shadow)
    predictions = []
    for idx, target in enumerate(TARGETS):
        predictions.append({
            "event_id": target["event_id"],
            "home_team": target["home"],
            "away_team": target["away"],
            "result": target["result"],
            "market": [float(x) for x in market[idx]],
            "old_model": [float(x) for x in old_model[idx]],
            "shadow_lambda_1": [float(x) for x in shadow[idx]],
            "feature_min_prior_matches": int(prior_counts[target["event_id"]]),
        })

    report = {
        "experiment_id": EXPERIMENT_ID,
        "evidence_class": EVIDENCE_CLASS,
        "research_only": True,
        "no_bet": True,
        "production_promotion": False,
        "frozen_v2_commit": FROZEN_V2_COMMIT,
        "parent_replay_commit": FROZEN_PARENT_REPLAY_COMMIT,
        "parent_replay_total_events": FROZEN_PARENT_REPLAY_EVENTS,
        "contract_scope": "SERIE_A_ONLY",
        "contract_scope_reason": "The frozen V2 residual primary cohort is Serie A; applying it to the other saved leagues would be off-contract.",
        "cohort_n": len(TARGETS),
        "history_cutoff_date": HISTORY_CUTOFF_DATE.strftime("%Y-%m-%d"),
        "outcomes_were_known_before_this_replay": True,
        "interpretation_limit": "Post-outcome diagnostic only; not untouched OOT or prospective evidence.",
        "parameter_selection_from_replay_outcomes": False,
        "feature_variant": FEATURE_VARIANT,
        "shadow_lambda": SHADOW_LAMBDA,
        "active_lambda": float(v2.ACTIVE_LAMBDA),
        "stability_gate_passed": bool(v2.STABILITY_GATE_PASSED),
        "l2_penalty": L2_PENALTY,
        "training_rows": int(artifact["training_rows"]),
        "training_fingerprint_sha256": artifact["training_fingerprint_sha256"],
        "candidate_artifact_sha256": artifact["artifact_sha256"],
        "frozen_source_git_blobs": EXPECTED_FROZEN_GIT_BLOBS,
        "football_data_sha256": {**historical_hashes, CURRENT_SEASON_CODE: current_sha256},
        "market": market_score,
        "old_model": old_score,
        "shadow_lambda_1": shadow_score,
        "shadow_delta_brier_vs_market": float(shadow_score["brier"] - market_score["brier"]),
        "shadow_delta_log_loss_vs_market": float(shadow_score["log_loss"] - market_score["log_loss"]),
        "shadow_delta_accuracy_vs_market": float(shadow_score["accuracy"] - market_score["accuracy"]),
        "shadow_dual_metric_better_than_market": bool(
            shadow_score["brier"] < market_score["brier"] and shadow_score["log_loss"] < market_score["log_loss"]
        ),
        "predictions": predictions,
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--frozen-source-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("artifacts/market_anchor_v2_saved_cohort_replay/report.json"))
    args = parser.parse_args()
    report = replay(args.frozen_source_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
