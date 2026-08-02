
import pandas as pd
from database import supabase


def load_matches():
    print("Загружаю матчи из Supabase...")

    response = supabase.table("matches").select("*").execute()

    data = response.data

    if not data:
        raise Exception("Таблица matches пустая")

    df = pd.DataFrame(data)

    print(f"Матчей загружено: {len(df)}")

    return df


def build_features(df):
    print("Создаю признаки...")

    df = df.sort_values(["match_date", "match_time"]).reset_index(drop=True)

    features = pd.DataFrame()

    features["match_date"] = df["match_date"]
    features["match_time"] = df["match_time"]

    # команды
    features["home_team"] = df["home_team"]
    features["away_team"] = df["away_team"]

    # результат матча
    features["home_goals"] = df["home_goals"]
    features["away_goals"] = df["away_goals"]

    # тотал голов
    features["total_goals"] = (
        df["home_goals"] + df["away_goals"]
    )

    # исход
    features["result"] = df.apply(
        lambda x:
        "HOME" if x["home_goals"] > x["away_goals"]
        else "AWAY" if x["home_goals"] < x["away_goals"]
        else "DRAW",
        axis=1
    )

    return features


def save_features(df):
    print("Сохраняю features...")

    df.to_csv(
        "data/features.csv",
        index=False
    )

    print("Готово: data/features.csv")


if __name__ == "__main__":

    matches = load_matches()

    features = build_features(matches)

    save_features(features)