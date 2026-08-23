"""AI + market diagnostics for league model research.

Current implementation: LA_LIGA.

Rules:
- model/feature winner comes from the completed sweep;
- hybrid alpha is selected ONLY on selection seasons;
- final 2025-2026 holdout remains locked until alpha is chosen;
- market odds are never AI features;
- no .pkl is created;
- no production artifact is modified or promoted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, log_loss

import league_model_sweep as sweep


ROOT = Path(__file__).resolve().parent

OUTPUT_DIR = (
    ROOT
    / "experiments"
    / "league_model_diagnostics"
)

SWEEP_REPORTS = {
    "LA_LIGA": (
        ROOT
        / "experiments"
        / "league_model_sweep"
        / "la_liga_report.json"
    ),
}

PRODUCTION_ARTIFACTS = (
    "football_model_xgboost_elo.pkl",
    "football_model_no_odds.pkl",
    "1x2_calibrator.pkl",
    "home_goals_model_no_odds.pkl",
    "away_goals_model_no_odds.pkl",
    "over_2_5_calibrator.pkl",
    "btts_calibrator.pkl",
)

# AI contribution to market consensus.
# alpha=0 is the pure market benchmark and is NOT a candidate.
ALPHAS = (
    0.05,
    0.10,
    0.15,
    0.20,
    0.25,
    0.30,
    0.35,
    0.40,
    0.45,
    0.50,
)


def sha256(path: Path) -> str | None:
    if not path.exists():
        return None

    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def production_state() -> dict:
    return {
        name: sha256(ROOT / name)
        for name in PRODUCTION_ARTIFACTS
    }


def multiclass_brier(
    y_true: np.ndarray,
    probability: np.ndarray,
) -> float:
    one_hot = np.eye(3)[y_true]

    return float(
        np.mean(
            np.sum(
                (probability - one_hot) ** 2,
                axis=1,
            )
        )
    )


def calculate_metrics(
    y_true: np.ndarray,
    probability: np.ndarray,
) -> dict:
    predicted = np.argmax(
        probability,
        axis=1,
    )

    return {
        "accuracy": float(
            accuracy_score(
                y_true,
                predicted,
            )
        ),
        "logloss": float(
            log_loss(
                y_true,
                probability,
                labels=[0, 1, 2],
            )
        ),
        "brier": multiclass_brier(
            y_true,
            probability,
        ),
    }


def hybrid_probability(
    market: np.ndarray,
    ai: np.ndarray,
    alpha: float,
) -> np.ndarray:
    result = (
        (1.0 - alpha) * market
        + alpha * ai
    )

    result = (
        result
        / result.sum(
            axis=1,
            keepdims=True,
        )
    )

    return result


def load_sweep_winner(
    league: str,
) -> tuple[str, str]:
    path = SWEEP_REPORTS[league]

    if not path.exists():
        raise FileNotFoundError(
            f"Sweep report missing: {path}"
        )

    report = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    return (
        str(
            report["winner"][
                "feature_set"
            ]
        ),
        str(
            report["winner"]["model"]
        ),
    )


def generate_oos_predictions(
    frame: pd.DataFrame,
    *,
    feature_set_name: str,
    model_name: str,
    seasons: tuple[str, ...],
) -> pd.DataFrame:
    features = (
        sweep.FEATURE_SETS[
            feature_set_name
        ]
    )

    outputs = []

    for season in seasons:
        train = frame[
            frame["season"]
            .astype(str)
            < season
        ].copy()

        test = frame[
            frame["season"]
            .astype(str)
            == season
        ].copy()

        required = (
            features
            + [
                "target",
                "home_odds",
                "draw_odds",
                "away_odds",
            ]
        )

        train = train.dropna(
            subset=required
        )

        test = test.dropna(
            subset=required
        )

        if train.empty or test.empty:
            continue

        model = sweep.make_model(
            model_name
        )

        model.fit(
            train[features],
            train["target"].astype(int),
        )

        ai = model.predict_proba(
            test[features]
        )

        market = (
            sweep.market_probabilities(
                test
            )
        )

        output = test[
            [
                "season",
                "match_date",
                "home_team",
                "away_team",
                "result",
                "target",
                "home_odds",
                "draw_odds",
                "away_odds",
            ]
        ].copy()

        output[
            "ai_home_probability"
        ] = ai[:, 0]

        output[
            "ai_draw_probability"
        ] = ai[:, 1]

        output[
            "ai_away_probability"
        ] = ai[:, 2]

        output[
            "market_home_probability"
        ] = market[:, 0]

        output[
            "market_draw_probability"
        ] = market[:, 1]

        output[
            "market_away_probability"
        ] = market[:, 2]

        outputs.append(output)

    if not outputs:
        raise RuntimeError(
            "No OOS predictions generated"
        )

    return pd.concat(
        outputs,
        ignore_index=True,
    )


def probability_arrays(
    frame: pd.DataFrame,
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
]:
    y = (
        frame["target"]
        .astype(int)
        .to_numpy()
    )

    ai = frame[
        [
            "ai_home_probability",
            "ai_draw_probability",
            "ai_away_probability",
        ]
    ].to_numpy()

    market = frame[
        [
            "market_home_probability",
            "market_draw_probability",
            "market_away_probability",
        ]
    ].to_numpy()

    return y, ai, market


def alpha_search(
    selection: pd.DataFrame,
) -> pd.DataFrame:
    y, ai, market = (
        probability_arrays(
            selection
        )
    )

    market_metrics = (
        calculate_metrics(
            y,
            market,
        )
    )

    rows = []

    for alpha in ALPHAS:
        hybrid = hybrid_probability(
            market,
            ai,
            alpha,
        )

        metric = (
            calculate_metrics(
                y,
                hybrid,
            )
        )

        rows.append({
            "alpha":
                alpha,

            **metric,

            "market_accuracy":
                market_metrics["accuracy"],

            "market_logloss":
                market_metrics["logloss"],

            "market_brier":
                market_metrics["brier"],

            "accuracy_gap":
                metric["accuracy"]
                - market_metrics["accuracy"],

            "logloss_gap":
                metric["logloss"]
                - market_metrics["logloss"],

            "brier_gap":
                metric["brier"]
                - market_metrics["brier"],

            "beats_market_accuracy":
                metric["accuracy"]
                > market_metrics["accuracy"],

            "beats_market_logloss":
                metric["logloss"]
                < market_metrics["logloss"],

            "beats_market_brier":
                metric["brier"]
                < market_metrics["brier"],
        })

    result = pd.DataFrame(rows)

    # Select on probability quality first.
    result = (
        result
        .sort_values(
            [
                "logloss",
                "brier",
                "accuracy",
            ],
            ascending=[
                True,
                True,
                False,
            ],
        )
        .reset_index(drop=True)
    )

    result.insert(
        0,
        "rank",
        np.arange(
            1,
            len(result) + 1,
        ),
    )

    return result


def segment_report(
    frame: pd.DataFrame,
    *,
    alpha: float,
) -> pd.DataFrame:
    y, ai, market = (
        probability_arrays(
            frame
        )
    )

    hybrid = hybrid_probability(
        market,
        ai,
        alpha,
    )

    ai_pred = np.argmax(
        ai,
        axis=1,
    )

    market_pred = np.argmax(
        market,
        axis=1,
    )

    hybrid_pred = np.argmax(
        hybrid,
        axis=1,
    )

    work = frame.copy()

    work["ai_prediction"] = (
        ai_pred
    )

    work["market_prediction"] = (
        market_pred
    )

    work["hybrid_prediction"] = (
        hybrid_pred
    )

    work["ai_confidence"] = (
        ai.max(axis=1)
    )

    work["market_confidence"] = (
        market.max(axis=1)
    )

    work["disagree"] = (
        ai_pred != market_pred
    )

    rows = []

    def add_segment(
        segment_type: str,
        segment: str,
        mask,
    ):
        subset = work[mask]

        if subset.empty:
            return

        index = subset.index.to_numpy()

        actual = (
            subset["target"]
            .astype(int)
            .to_numpy()
        )

        ai_probability = ai[index]
        market_probability = (
            market[index]
        )
        hybrid_probability_ = (
            hybrid[index]
        )

        ai_metric = calculate_metrics(
            actual,
            ai_probability,
        )

        market_metric = (
            calculate_metrics(
                actual,
                market_probability,
            )
        )

        hybrid_metric = (
            calculate_metrics(
                actual,
                hybrid_probability_,
            )
        )

        rows.append({
            "segment_type":
                segment_type,

            "segment":
                segment,

            "rows":
                len(subset),

            "ai_accuracy":
                ai_metric["accuracy"],

            "market_accuracy":
                market_metric["accuracy"],

            "hybrid_accuracy":
                hybrid_metric["accuracy"],

            "ai_logloss":
                ai_metric["logloss"],

            "market_logloss":
                market_metric["logloss"],

            "hybrid_logloss":
                hybrid_metric["logloss"],
        })

    for result in (
        "H",
        "D",
        "A",
    ):
        add_segment(
            "actual_result",
            result,
            work["result"] == result,
        )

    add_segment(
        "agreement",
        "AI_MARKET_AGREE",
        ~work["disagree"],
    )

    add_segment(
        "agreement",
        "AI_MARKET_DISAGREE",
        work["disagree"],
    )

    confidence_bucket = pd.cut(
        work["market_confidence"],
        bins=[
            0.0,
            0.45,
            0.55,
            0.65,
            1.0,
        ],
        labels=[
            "<0.45",
            "0.45-0.55",
            "0.55-0.65",
            ">=0.65",
        ],
        include_lowest=True,
    )

    for bucket in (
        confidence_bucket
        .dropna()
        .unique()
    ):
        add_segment(
            "market_confidence",
            str(bucket),
            confidence_bucket
            == bucket,
        )

    return pd.DataFrame(rows)


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--league",
        choices=sorted(
            sweep.INPUTS
        ),
        required=True,
    )

    args = parser.parse_args()

    league = args.league

    before = production_state()

    feature_set_name, model_name = (
        load_sweep_winner(
            league
        )
    )

    frame = pd.read_csv(
        sweep.INPUTS[league]
    )

    frame = frame.copy()

    frame["target"] = (
        frame["result"]
        .map(
            sweep.TARGET_MAP
        )
    )

    print("=" * 72)
    print("AI + MARKET HYBRID DIAGNOSTICS")
    print("=" * 72)

    print(
        "league:",
        league,
    )

    print(
        "sweep winner feature set:",
        feature_set_name,
    )

    print(
        "sweep winner model:",
        model_name,
    )

    print(
        "selection seasons:",
        sweep.SELECTION_TEST_SEASONS,
    )

    print(
        "locked holdout:",
        sweep.FINAL_HOLDOUT_SEASON,
    )

    selection = (
        generate_oos_predictions(
            frame,
            feature_set_name=(
                feature_set_name
            ),
            model_name=model_name,
            seasons=(
                sweep.SELECTION_TEST_SEASONS
            ),
        )
    )

    alpha_table = alpha_search(
        selection
    )

    selected_alpha = float(
        alpha_table.iloc[0][
            "alpha"
        ]
    )

    print()
    print("=" * 72)
    print("ALPHA SELECTION")
    print("=" * 72)

    print(
        alpha_table.to_string(
            index=False
        )
    )

    print()
    print(
        "selected alpha:",
        selected_alpha,
    )

    selection_segments = (
        segment_report(
            selection,
            alpha=selected_alpha,
        )
    )

    # Only now touch the locked holdout.
    holdout = (
        generate_oos_predictions(
            frame,
            feature_set_name=(
                feature_set_name
            ),
            model_name=model_name,
            seasons=(
                sweep.FINAL_HOLDOUT_SEASON,
            ),
        )
    )

    y, ai, market = (
        probability_arrays(
            holdout
        )
    )

    hybrid = hybrid_probability(
        market,
        ai,
        selected_alpha,
    )

    ai_metric = calculate_metrics(
        y,
        ai,
    )

    market_metric = (
        calculate_metrics(
            y,
            market,
        )
    )

    hybrid_metric = (
        calculate_metrics(
            y,
            hybrid,
        )
    )

    holdout_segments = (
        segment_report(
            holdout,
            alpha=selected_alpha,
        )
    )

    final_gate = all([
        hybrid_metric["accuracy"]
        > market_metric["accuracy"],

        hybrid_metric["logloss"]
        < market_metric["logloss"],

        hybrid_metric["brier"]
        < market_metric["brier"],
    ])

    after = production_state()

    production_unchanged = (
        before == after
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    alpha_path = (
        OUTPUT_DIR
        / f"{league.lower()}_alpha_selection.csv"
    )

    selection_segment_path = (
        OUTPUT_DIR
        / f"{league.lower()}_selection_segments.csv"
    )

    holdout_segment_path = (
        OUTPUT_DIR
        / f"{league.lower()}_holdout_segments.csv"
    )

    report_path = (
        OUTPUT_DIR
        / f"{league.lower()}_report.json"
    )

    alpha_table.to_csv(
        alpha_path,
        index=False,
    )

    selection_segments.to_csv(
        selection_segment_path,
        index=False,
    )

    holdout_segments.to_csv(
        holdout_segment_path,
        index=False,
    )

    report = {
        "league":
            league,

        "feature_set":
            feature_set_name,

        "model":
            model_name,

        "selection_seasons":
            list(
                sweep.SELECTION_TEST_SEASONS
            ),

        "locked_holdout":
            sweep.FINAL_HOLDOUT_SEASON,

        "selected_alpha":
            selected_alpha,

        "selection_best": (
            alpha_table.iloc[0]
            .to_dict()
        ),

        "holdout": {
            "ai":
                ai_metric,

            "market":
                market_metric,

            "hybrid":
                hybrid_metric,
        },

        "hybrid_beats_market_holdout":
            final_gate,

        "production_unchanged":
            production_unchanged,

        "candidate_model_saved":
            False,

        "promotion_performed":
            False,
    }

    report_path.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    print()
    print("=" * 72)
    print("LOCKED HOLDOUT RESULT")
    print("=" * 72)

    print(
        "AI:",
        ai_metric,
    )

    print(
        "Market:",
        market_metric,
    )

    print(
        "Hybrid:",
        hybrid_metric,
    )

    print()
    print(
        "Hybrid beats market:",
        final_gate,
    )

    print(
        "production unchanged:",
        production_unchanged,
    )

    print(
        "candidate saved:",
        False,
    )

    print(
        "promotion:",
        False,
    )

    print()
    print(
        "alpha table:",
        alpha_path,
    )

    print(
        "selection segments:",
        selection_segment_path,
    )

    print(
        "holdout segments:",
        holdout_segment_path,
    )

    print(
        "report:",
        report_path,
    )

    if not production_unchanged:
        print(
            "FAIL: production safety violation"
        )
        return 2

    if final_gate:
        print()
        print(
            "PASS: hybrid established "
            "incremental OOS value over market."
        )
    else:
        print()
        print(
            "REJECTED: hybrid did not beat "
            "market on all locked-holdout metrics."
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
