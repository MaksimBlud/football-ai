from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

import pandas as pd

from goal_prediction import predict_goal_markets
from market_value import calculate_market_values
from predict_match import predict_match
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

    return df.head(50).to_dict(
        orient="records"
    )




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
