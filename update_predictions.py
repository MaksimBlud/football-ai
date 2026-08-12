import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd


UPCOMING_FILE = Path(
    "data/upcoming_matches.csv"
)

PREDICTIONS_FILE = Path(
    "data/upcoming_round_predictions.csv"
)


def run_script(script, *extra_args):
    print()
    print("=" * 70)
    print("Запускаю:", script)
    print("=" * 70)

    result = subprocess.run(
        [
            sys.executable,
            script,
            *extra_args,
        ],
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"{script} завершился с ошибкой "
            f"(код {result.returncode})"
        )


parser = argparse.ArgumentParser(
    description="Обновление Football AI."
)

parser.add_argument(
    "--apply-results",
    action="store_true",
    help=(
        "Записать новые завершённые матчи "
        "в Supabase."
    ),
)

args = parser.parse_args()

print()
print("=" * 70)
print("FOOTBALL AI — ОБНОВЛЕНИЕ ПРОГНОЗОВ")
print("=" * 70)

# 1. Проверяем завершённые матчи.
#
# По умолчанию update_finished_matches.py работает
# только в DRY-RUN. Запись выполняется исключительно
# при явном --apply-results.

if args.apply_results:
    run_script(
        "update_finished_matches.py",
        "--apply",
    )
else:
    run_script(
        "update_finished_matches.py"
    )



# 2. Обновляем официальный календарь.
run_script(
    "download_upcoming_matches.py"
)


# 3. Проверяем календарь.
if not UPCOMING_FILE.exists():
    raise FileNotFoundError(
        f"Не создан файл: {UPCOMING_FILE}"
    )

upcoming = pd.read_csv(
    UPCOMING_FILE
)

if upcoming.empty:
    raise RuntimeError(
        "Календарь не содержит будущих матчей."
    )

required_upcoming_columns = {
    "match_date",
    "match_time",
    "home_team",
    "away_team",
    "home_team_model",
    "away_team_model",
}

missing = (
    required_upcoming_columns
    - set(upcoming.columns)
)

if missing:
    raise RuntimeError(
        "В календаре отсутствуют колонки: "
        + ", ".join(sorted(missing))
    )


# 4. Пересчитываем ближайший тур.
run_script(
    "predict_upcoming_round.py"
)


# 5. Проверяем прогнозы.
if not PREDICTIONS_FILE.exists():
    raise FileNotFoundError(
        f"Не создан файл: {PREDICTIONS_FILE}"
    )

predictions = pd.read_csv(
    PREDICTIONS_FILE
)

if predictions.empty:
    raise RuntimeError(
        "Файл прогнозов тура пуст."
    )


# 6. Считаем итоговую статистику.
strength_counts = (
    predictions["prediction_strength"]
    .value_counts()
    .to_dict()
)

strong = int(
    strength_counts.get(
        "STRONG",
        0,
    )
)

medium = int(
    strength_counts.get(
        "MEDIUM",
        0,
    )
)

weak = int(
    strength_counts.get(
        "WEAK",
        0,
    )
)

agreement = int(
    predictions[
        "model_agreement"
    ].sum()
)

over_60 = int(
    (
        predictions[
            "over_2_5_probability"
        ] >= 0.60
    ).sum()
)


print()
print("=" * 70)
print("ОБНОВЛЕНИЕ ЗАВЕРШЕНО")
print("=" * 70)

print(
    "Будущих матчей:",
    len(upcoming),
)

print(
    "Матчей в ближайшем туре:",
    len(predictions),
)

print()
print("Сила прогнозов:")
print("  STRONG:", strong)
print("  MEDIUM:", medium)
print("  WEAK:", weak)

print()
print(
    "Модели согласны:",
    f"{agreement}/{len(predictions)}",
)

print(
    "ТБ 2.5 >= 60%:",
    over_60,
)

print()
print(
    "Последнее обновление:",
    datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    ),
)

print()
print(
    "Календарь:",
    UPCOMING_FILE,
)

print(
    "Прогнозы:",
    PREDICTIONS_FILE,
)

print()
print("Football AI готов.")
