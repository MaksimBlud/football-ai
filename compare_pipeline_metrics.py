from pathlib import Path
import json
import re
import sys


ROOT = Path(__file__).resolve().parent
LOG_DIR = ROOT / "logs"
HISTORY_FILE = LOG_DIR / "metrics_history.json"


def find_latest_pipeline_log():
    logs = sorted(
        LOG_DIR.glob("pipeline_*.log"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    if not logs:
        raise SystemExit("❌ Не найдено ни одного pipeline log.")

    return logs[0]


def extract(pattern, text, name):
    match = re.search(pattern, text, flags=re.MULTILINE)

    if not match:
        raise SystemExit(
            f"❌ Не удалось извлечь метрику: {name}"
        )

    return float(match.group(1))


def extract_metrics(text):
    weighted_match = re.search(
        r"===== ВЗВЕШЕННЫЕ ПО ВСЕМ TEST-МАТЧАМ =====(.*?)(?:Confusion matrix:)",
        text,
        flags=re.DOTALL,
    )

    if not weighted_match:
        raise SystemExit(
            "❌ Не найден блок взвешенных итоговых метрик."
        )

    block = weighted_match.group(1)

    metrics = {
        "accuracy": extract(
            r"Accuracy:\s*([0-9.]+)",
            block,
            "Accuracy",
        ),
        "log_loss": extract(
            r"Log Loss:\s*([0-9.]+)",
            block,
            "Log Loss",
        ),
        "brier": extract(
            r"Brier:\s*([0-9.]+)",
            block,
            "Brier",
        ),
    }

    bookmaker_match = re.search(
        r"bookmaker_accuracy\s+([0-9.]+)",
        text,
    )

    if bookmaker_match:
        metrics["bookmaker_accuracy"] = float(
            bookmaker_match.group(1)
        )

    final_report_match = re.search(
        r"===== ВЗВЕШЕННЫЕ ПО ВСЕМ TEST-МАТЧАМ =====.*?"
        r"Classification report:(.*?)(?:Предсказаний классов:)",
        text,
        flags=re.DOTALL,
    )

    if final_report_match:
        final_report = final_report_match.group(1)

        draw_report = re.search(
            r"DRAW\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+\d+",
            final_report,
        )

        if draw_report:
            metrics["draw_precision"] = float(draw_report.group(1))
            metrics["draw_recall"] = float(draw_report.group(2))
            metrics["draw_f1"] = float(draw_report.group(3))

    draw_predictions = re.search(
        r"DRAW\s+(\d+)\s*$",
        text,
        flags=re.MULTILINE,
    )

    if draw_predictions:
        metrics["draw_predictions"] = int(
            draw_predictions.group(1)
        )

    return metrics


def load_history():
    if not HISTORY_FILE.exists():
        return []

    try:
        return json.loads(
            HISTORY_FILE.read_text(encoding="utf-8")
        )
    except Exception:
        return []


def save_history(history):
    HISTORY_FILE.write_text(
        json.dumps(
            history,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def delta(current, previous, key):
    if key not in current or key not in previous:
        return None

    return current[key] - previous[key]


def format_change(value, lower_is_better=False):
    if value is None:
        return "   n/a"

    if abs(value) < 1e-12:
        return f"{value:+.4f} ➖"

    improved = (
        value < 0
        if lower_is_better
        else value > 0
    )

    icon = "✅" if improved else "❌"
    return f"{value:+.4f} {icon}"


def verdict(current, previous):
    if previous is None:
        return "ПЕРВЫЙ ЗАПУСК — создана базовая точка сравнения."

    score = 0

    acc = delta(current, previous, "accuracy")
    ll = delta(current, previous, "log_loss")
    br = delta(current, previous, "brier")
    dr = delta(current, previous, "draw_recall")

    if acc is not None:
        score += 1 if acc > 0 else -1 if acc < 0 else 0

    if ll is not None:
        score += 1 if ll < 0 else -1 if ll > 0 else 0

    if br is not None:
        score += 1 if br < 0 else -1 if br > 0 else 0

    if dr is not None:
        score += 1 if dr > 0 else -1 if dr < 0 else 0

    changes = [
        value
        for value in [acc, ll, br, dr]
        if value is not None
    ]

    if changes and all(abs(value) < 1e-12 for value in changes):
        return "➖ NO CHANGE"

    if score >= 2:
        return "✅ MODEL IMPROVED"

    if score <= -2:
        return "❌ MODEL WORSE"

    return "⚠️ MIXED RESULT"


def main():
    latest_log = find_latest_pipeline_log()

    text = latest_log.read_text(
        encoding="utf-8",
        errors="replace",
    )

    current = extract_metrics(text)
    current["source_log"] = latest_log.name

    history = load_history()

    previous = history[-1] if history else None

    print()
    print("=" * 88)
    print("FOOTBALL AI — AUTOMATIC MODEL COMPARISON")
    print("=" * 88)
    print(f"Источник: {latest_log.name}")
    print()

    if previous is None:
        print("Предыдущего запуска пока нет.")
        print()
        print(f"Accuracy:            {current['accuracy']:.4f}")
        print(f"Log Loss:            {current['log_loss']:.4f}")
        print(f"Brier:               {current['brier']:.4f}")

        if "bookmaker_accuracy" in current:
            print(
                f"Bookmaker Accuracy:  "
                f"{current['bookmaker_accuracy']:.4f}"
            )

        if "draw_recall" in current:
            print(
                f"DRAW Recall:         "
                f"{current['draw_recall']:.4f}"
            )

        if "draw_predictions" in current:
            print(
                f"DRAW Predictions:    "
                f"{current['draw_predictions']}"
            )

    else:
        print(
            f"{'METRIC':<24}"
            f"{'PREVIOUS':>12}"
            f"{'CURRENT':>12}"
            f"{'CHANGE':>18}"
        )
        print("-" * 66)

        rows = [
            ("Accuracy", "accuracy", False),
            ("Log Loss", "log_loss", True),
            ("Brier", "brier", True),
            ("DRAW Recall", "draw_recall", False),
            ("DRAW F1", "draw_f1", False),
        ]

        for label, key, lower_is_better in rows:
            if key not in current or key not in previous:
                continue

            change = delta(current, previous, key)

            print(
                f"{label:<24}"
                f"{previous[key]:>12.4f}"
                f"{current[key]:>12.4f}"
                f"{format_change(change, lower_is_better):>18}"
            )

        if (
            "bookmaker_accuracy" in current
            and "bookmaker_accuracy" in previous
        ):
            print(
                f"{'Bookmaker Accuracy':<24}"
                f"{previous['bookmaker_accuracy']:>12.4f}"
                f"{current['bookmaker_accuracy']:>12.4f}"
                f"{delta(current, previous, 'bookmaker_accuracy'):>+12.4f}"
            )

    print()
    print("VERDICT:")
    print(verdict(current, previous))

    history.append(current)

    save_history(history)

    print()
    print(f"История сохранена: {HISTORY_FILE}")
    print("=" * 88)


if __name__ == "__main__":
    main()
