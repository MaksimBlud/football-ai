from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

import pandas as pd

from database import supabase
from goal_prediction import predict_goal_markets
from market_value import calculate_market_values
from predict_match import predict_match
from predict_match_no_odds import predict_match_no_odds
from predict_market import predict_market
from team_names import normalize_team_name
from teams import get_team_names


app = FastAPI(
    title="Football AI API",
    description="API прогнозирования футбольных матчей",
    version="1.1.0",
)


class PredictionRequest(BaseModel):
    home_team: str = Field(min_length=1)
    away_team: str = Field(min_length=1)
    home_odds: float = Field(gt=1)
    draw_odds: float = Field(gt=1)
    away_odds: float = Field(gt=1)


class ValueOutcome(BaseModel):
    name: str
    model_probability: float
    bookmaker_probability: float
    edge: float
    expected_roi: float
    odds: float
    status: str


class PredictionResponse(BaseModel):
    home_team: str
    away_team: str
    prediction: str

    home_probability: float
    draw_probability: float
    away_probability: float

    home_last5_points: int
    away_last5_points: int

    home_elo: float
    away_elo: float

    bookmaker_margin: float
    value_outcomes: list[ValueOutcome]
    best_value: ValueOutcome


class MarketValueRequest(PredictionRequest):
    over_2_5_odds: float = Field(gt=1)
    under_2_5_odds: float = Field(gt=1)
    btts_yes_odds: float = Field(gt=1)
    btts_no_odds: float = Field(gt=1)


class MarketValueItem(BaseModel):
    name: str
    group: str
    model_probability: float
    bookmaker_probability_raw: float
    odds: float
    edge_raw: float
    expected_roi: float
    status: str


class MarketValueResponse(BaseModel):
    markets: list[MarketValueItem]
    value_bets: list[MarketValueItem]
    best_market: MarketValueItem | None


class ScoreProbability(BaseModel):
    home_goals: int
    away_goals: int
    probability: float


class GoalPredictionResponse(BaseModel):
    home_team: str
    away_team: str

    expected_home_goals: float
    expected_away_goals: float
    expected_total_goals: float

    home_win_probability: float
    draw_probability: float
    away_win_probability: float

    over_2_5_probability: float
    under_2_5_probability: float

    btts_yes_probability: float
    btts_no_probability: float

    top_scores: list[ScoreProbability]


@app.get("/")
def root():
    return FileResponse("static/index_v2.html")


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.get("/teams")
def teams():
    return get_team_names()


@app.get("/upcoming-matches")
def upcoming_matches():
    path = "data/upcoming_matches.csv"

    try:
        df = pd.read_csv(path)
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail="Файл ближайших матчей не найден.",
        ) from error

    df = df.head(50).copy()

    odds_response = (
        supabase
        .table("odds_snapshots")
        .select(
            "snapshot_time_utc,"
            "home_team,"
            "away_team,"
            "home_odds,"
            "draw_odds,"
            "away_odds"
        )
        .order(
            "snapshot_time_utc",
            desc=True,
        )
        .limit(1000)
        .execute()
    )

    odds_df = pd.DataFrame(
        odds_response.data or []
    )

    df["home_odds"] = None
    df["draw_odds"] = None
    df["away_odds"] = None

    if not odds_df.empty:

        odds_df["snapshot_time_utc"] = pd.to_datetime(
            odds_df["snapshot_time_utc"],
            utc=True,
            errors="coerce",
        )

        odds_df = odds_df.sort_values(
            "snapshot_time_utc",
            ascending=False,
        )

        latest_odds = (
            odds_df
            .drop_duplicates(
                subset=[
                    "home_team",
                    "away_team",
                ],
                keep="first",
            )
        )

        odds_map = {
            (
                normalize_team_name(
                    row["home_team"]
                ),
                normalize_team_name(
                    row["away_team"]
                ),
            ): {
                "home_odds": row["home_odds"],
                "draw_odds": row["draw_odds"],
                "away_odds": row["away_odds"],
            }
            for _, row in latest_odds.iterrows()
        }

        for index, row in df.iterrows():

            key = (
                normalize_team_name(
                    row["home_team"]
                ),
                normalize_team_name(
                    row["away_team"]
                ),
            )

            odds = odds_map.get(key)

            if odds is None:
                continue

            df.at[index, "home_odds"] = odds["home_odds"]
            df.at[index, "draw_odds"] = odds["draw_odds"]
            df.at[index, "away_odds"] = odds["away_odds"]

    return df.to_dict(
        orient="records"
    )




@app.post("/predict-compare")
def create_compare_prediction(
    request: PredictionRequest,
):
    try:
        home_original = request.home_team.strip()
        away_original = request.away_team.strip()

        market = predict_market(
            home_team=home_original,
            away_team=away_original,
            home_odds=request.home_odds,
            draw_odds=request.draw_odds,
            away_odds=request.away_odds,
        )

        ai = predict_match_no_odds(
            home_team=normalize_team_name(
                home_original
            ),
            away_team=normalize_team_name(
                away_original
            ),
        )

        deltas = {
            "HOME": (
                ai["home_probability"]
                - market["home_probability"]
            ),
            "DRAW": (
                ai["draw_probability"]
                - market["draw_probability"]
            ),
            "AWAY": (
                ai["away_probability"]
                - market["away_probability"]
            ),
        }

        strongest_disagreement = max(
            deltas,
            key=lambda side: abs(
                deltas[side]
            ),
        )

        return {
            "home_team": home_original,
            "away_team": away_original,

            "market": market,

            "ai": ai,

            "agreement": (
                market["prediction"]
                == ai["prediction"]
            ),

            "market_prediction": (
                market["prediction"]
            ),

            "ai_prediction": (
                ai["prediction"]
            ),

            "delta": {
                "home": deltas["HOME"],
                "draw": deltas["DRAW"],
                "away": deltas["AWAY"],
            },

            "strongest_disagreement": {
                "outcome": strongest_disagreement,
                "delta": deltas[
                    strongest_disagreement
                ],
                "absolute_delta": abs(
                    deltas[
                        strongest_disagreement
                    ]
                ),
            },

            "note": (
                "AI-vs-market disagreement is an "
                "analytical signal, not validated betting value."
            ),
        }

    except (
        FileNotFoundError,
        ValueError,
        RuntimeError,
    ) as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error


@app.post("/predict-ai")
def create_ai_prediction(
    request: PredictionRequest,
):
    try:
        return predict_match_no_odds(
            home_team=normalize_team_name(
                request.home_team
            ),
            away_team=normalize_team_name(
                request.away_team
            ),
        )

    except (
        FileNotFoundError,
        ValueError,
        RuntimeError,
    ) as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error


@app.post("/predict-market")
def create_market_prediction(
    request: PredictionRequest,
):
    try:
        return predict_market(
            home_team=request.home_team.strip(),
            away_team=request.away_team.strip(),
            home_odds=request.home_odds,
            draw_odds=request.draw_odds,
            away_odds=request.away_odds,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error


@app.post(
    "/predict",
    response_model=PredictionResponse,
)
def create_prediction(request: PredictionRequest):
    try:
        return predict_match(
            home_team=request.home_team.strip(),
            away_team=request.away_team.strip(),
            home_odds=request.home_odds,
            draw_odds=request.draw_odds,
            away_odds=request.away_odds,
        )

    except (
        FileNotFoundError,
        ValueError,
        RuntimeError,
    ) as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error


@app.post(
    "/predict-goals",
    response_model=GoalPredictionResponse,
)
def create_goal_prediction(
    request: PredictionRequest,
):
    try:
        return predict_goal_markets(
            home_team=request.home_team.strip(),
            away_team=request.away_team.strip(),
            home_odds=request.home_odds,
            draw_odds=request.draw_odds,
            away_odds=request.away_odds,
        )

    except (
        FileNotFoundError,
        ValueError,
        RuntimeError,
    ) as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error


@app.post(
    "/market-value",
    response_model=MarketValueResponse,
)
def create_market_value(
    request: MarketValueRequest,
):
    try:
        match_prediction = predict_match(
            home_team=request.home_team.strip(),
            away_team=request.away_team.strip(),
            home_odds=request.home_odds,
            draw_odds=request.draw_odds,
            away_odds=request.away_odds,
        )

        goal_prediction = predict_goal_markets(
            home_team=request.home_team.strip(),
            away_team=request.away_team.strip(),
            home_odds=request.home_odds,
            draw_odds=request.draw_odds,
            away_odds=request.away_odds,
        )

        return calculate_market_values([
            {
                "name": f"Победа {request.home_team.strip()}",
                "group": "1X2",
                "model_probability": match_prediction["home_probability"],
                "odds": request.home_odds,
            },
            {
                "name": "Ничья",
                "group": "1X2",
                "model_probability": match_prediction["draw_probability"],
                "odds": request.draw_odds,
            },
            {
                "name": f"Победа {request.away_team.strip()}",
                "group": "1X2",
                "model_probability": match_prediction["away_probability"],
                "odds": request.away_odds,
            },
            {
                "name": "ТБ 2.5",
                "group": "TOTAL_2_5",
                "model_probability": goal_prediction["over_2_5_probability"],
                "odds": request.over_2_5_odds,
            },
            {
                "name": "ТМ 2.5",
                "group": "TOTAL_2_5",
                "model_probability": goal_prediction["under_2_5_probability"],
                "odds": request.under_2_5_odds,
            },
            {
                "name": "Обе забьют — Да",
                "group": "BTTS",
                "model_probability": goal_prediction["btts_yes_probability"],
                "odds": request.btts_yes_odds,
            },
            {
                "name": "Обе забьют — Нет",
                "group": "BTTS",
                "model_probability": goal_prediction["btts_no_probability"],
                "odds": request.btts_no_odds,
            },
        ])

    except (
        FileNotFoundError,
        ValueError,
        RuntimeError,
    ) as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error


@app.get("/upcoming-round-predictions")
def upcoming_round_predictions():
    path = "data/upcoming_round_predictions.csv"

    try:
        df = pd.read_csv(path)
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=(
                "Файл прогнозов тура не найден. "
                "Сначала запустите predict_upcoming_round.py."
            ),
        ) from error

    return df.to_dict(
        orient="records"
    )


@app.get("/match")
def match_page():
    return FileResponse("static/match.html")


@app.get("/upcoming-round-match/{match_id}")
def upcoming_round_match(match_id: int):
    path = "data/upcoming_round_predictions.csv"

    try:
        df = pd.read_csv(path)
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail="Файл прогнозов тура не найден.",
        ) from error

    if match_id < 0 or match_id >= len(df):
        raise HTTPException(
            status_code=404,
            detail="Матч не найден",
        )

    return df.iloc[match_id].to_dict()


@app.post("/refresh-predictions")
def refresh_predictions():
    import subprocess
    import sys

    try:
        result = subprocess.run(
            [
                sys.executable,
                "update_predictions.py",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired as error:
        raise HTTPException(
            status_code=504,
            detail="Обновление прогнозов превысило лимит времени.",
        ) from error

    if result.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail=(
                result.stderr
                or result.stdout
                or "Не удалось обновить прогнозы."
            ),
        )

    predictions_path = (
        "data/upcoming_round_predictions.csv"
    )

    try:
        df = pd.read_csv(
            predictions_path
        )
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=500,
            detail="Файл прогнозов после обновления не найден.",
        ) from error

    return {
        "status": "ok",
        "matches": len(df),
        "strong": int(
            (
                df["prediction_strength"]
                == "STRONG"
            ).sum()
        ),
        "medium": int(
            (
                df["prediction_strength"]
                == "MEDIUM"
            ).sum()
        ),
        "weak": int(
            (
                df["prediction_strength"]
                == "WEAK"
            ).sum()
        ),
        "model_agreement": int(
            df["model_agreement"].sum()
        ),
        "over_2_5_60": int(
            (
                df["over_2_5_probability"]
                >= 0.60
            ).sum()
        ),
    }
