from pathlib import Path
from datetime import datetime
import csv
import json


ROOT = Path(__file__).resolve().parent
LOG_DIR = ROOT / "logs"
RESULTS_DIR = ROOT / "experiments"

RESULTS_DIR.mkdir(exist_ok=True)

HISTORY_FILE = LOG_DIR / "metrics_history.json"
EXPERIMENTS_FILE = RESULTS_DIR / "experiments.csv"


def load_baseline():
    if not HISTORY_FILE.exists():
        raise SystemExit(
            "❌ Не найден logs/metrics_history.json. "
            "Сначала запусти основной pipeline."
        )

    history = json.loads(
        HISTORY_FILE.read_text(encoding="utf-8")
    )

    if not history:
        raise SystemExit("❌ История метрик пуста.")

    return history[-1]


def ensure_csv():
    if EXPERIMENTS_FILE.exists():
        return

    with open(
        EXPERIMENTS_FILE,
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.writer(f)

        writer.writerow([
            "timestamp",
            "experiment",
            "accuracy",
            "log_loss",
            "brier",
            "draw_precision",
            "draw_recall",
            "draw_f1",
            "draw_predictions",
            "bookmaker_accuracy",
            "notes",
        ])


def add_experiment(name, metrics, notes=""):
    ensure_csv()

    with open(
        EXPERIMENTS_FILE,
        "a",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.writer(f)

        writer.writerow([
            datetime.now().isoformat(timespec="seconds"),
            name,
            metrics.get("accuracy"),
            metrics.get("log_loss"),
            metrics.get("brier"),
            metrics.get("draw_precision"),
            metrics.get("draw_recall"),
            metrics.get("draw_f1"),
            metrics.get("draw_predictions"),
            metrics.get("bookmaker_accuracy"),
            notes,
        ])


def print_metrics(metrics):
    print(f"Accuracy:           {metrics.get('accuracy', 'n/a')}")
    print(f"Log Loss:           {metrics.get('log_loss', 'n/a')}")
    print(f"Brier:              {metrics.get('brier', 'n/a')}")
    print(f"DRAW Precision:     {metrics.get('draw_precision', 'n/a')}")
    print(f"DRAW Recall:        {metrics.get('draw_recall', 'n/a')}")
    print(f"DRAW F1:            {metrics.get('draw_f1', 'n/a')}")
    print(f"DRAW Predictions:   {metrics.get('draw_predictions', 'n/a')}")
    print(f"Bookmaker Accuracy: {metrics.get('bookmaker_accuracy', 'n/a')}")


def main():
    baseline = load_baseline()

    print()
    print("=" * 80)
    print("FOOTBALL AI — EXPERIMENT SYSTEM")
    print("=" * 80)

    print()
    print("Текущий production baseline:")
    print_metrics(baseline)

    ensure_csv()

    existing_text = EXPERIMENTS_FILE.read_text(
        encoding="utf-8"
    )

    if "\nbaseline," not in existing_text:
        add_experiment(
            "baseline",
            baseline,
            "Production baseline before automated experiments",
        )
        print()
        print("✅ Baseline добавлен в таблицу экспериментов.")
    else:
        print()
        print("➖ Baseline уже есть в таблице.")

    print()
    print(f"Таблица экспериментов: {EXPERIMENTS_FILE}")
    print()
    print("Production-файлы НЕ изменены.")
    print("=" * 80)


if __name__ == "__main__":
    main()
