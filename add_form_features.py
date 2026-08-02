import pandas as pd


INPUT = "data/features.csv"
OUTPUT = "data/features_form.csv"


def add_form_features(df):
    print("Подготавливаю данные для расчёта формы...")

    # Здесь не добавляем очки текущего матча,
    # потому что они становятся известны только после игры.
    return df.copy()


if __name__ == "__main__":

    print("Загружаю features.csv")

    df = pd.read_csv(INPUT)

    df = add_form_features(df)

    df.to_csv(
        OUTPUT,
        index=False
    )

    print("Готово:", OUTPUT)
