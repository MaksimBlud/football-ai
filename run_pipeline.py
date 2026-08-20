from pathlib import Path
from datetime import datetime
import subprocess
import sys
import time


# ============================================================
# FOOTBALL AI — AUTOMATIC PIPELINE
# ============================================================

PIPELINE = [
    ("Feature engineering", "feature_engineering.py"),
    ("ELO features", "add_elo_features.py"),
    ("Train XGBoost 1X2", "train_model_xgboost_elo.py"),
    ("Walk-forward production evaluation", "evaluate_walk_forward_production.py"),
    ("Compare model metrics", "compare_pipeline_metrics.py"),
]


ROOT = Path(__file__).resolve().parent
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = LOG_DIR / f"pipeline_{timestamp}.log"


def print_and_log(text=""):
    print(text)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(text + "\n")


def run_step(number, name, script):
    script_path = ROOT / script

    print_and_log()
    print_and_log("=" * 80)
    print_and_log(f"[{number}/{len(PIPELINE)}] {name}")
    print_and_log(f"Файл: {script}")
    print_and_log("=" * 80)

    if not script_path.exists():
        print_and_log(f"❌ Файл не найден: {script_path}")
        return False

    started = time.time()

    process = subprocess.Popen(
        [sys.executable, str(script_path)],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    for line in process.stdout:
        line = line.rstrip()
        print_and_log(line)

    return_code = process.wait()
    elapsed = time.time() - started

    if return_code != 0:
        print_and_log()
        print_and_log(
            f"❌ Этап завершился с ошибкой "
            f"(код {return_code}, {elapsed:.1f} сек.)"
        )
        return False

    print_and_log()
    print_and_log(f"✅ Готово за {elapsed:.1f} сек.")
    return True


def dry_run():
    print()
    print("=" * 80)
    print("FOOTBALL AI — ПРОВЕРКА PIPELINE")
    print("=" * 80)

    all_ok = True

    for number, (name, script) in enumerate(PIPELINE, start=1):
        path = ROOT / script
        status = "✅" if path.exists() else "❌"
        print(f"{status} [{number}] {name}: {script}")

        if not path.exists():
            all_ok = False

    print()

    if all_ok:
        print("✅ Все необходимые скрипты найдены.")
        print("Pipeline можно запускать.")
    else:
        print("❌ Некоторые файлы отсутствуют.")
        print("Pipeline пока НЕ запускаем.")

    return 0 if all_ok else 1


def main():
    if "--dry-run" in sys.argv:
        sys.exit(dry_run())

    print_and_log("=" * 80)
    print_and_log("🚀 FOOTBALL AI — AUTOMATIC PIPELINE")
    print_and_log("=" * 80)
    print_and_log(f"Начало: {datetime.now():%Y-%m-%d %H:%M:%S}")
    print_and_log(f"Лог: {log_file}")

    pipeline_started = time.time()

    for number, (name, script) in enumerate(PIPELINE, start=1):
        success = run_step(number, name, script)

        if not success:
            print_and_log()
            print_and_log("=" * 80)
            print_and_log("🛑 PIPELINE ОСТАНОВЛЕН")
            print_and_log("=" * 80)
            print_and_log(
                "Следующие этапы не запускались, "
                "чтобы не получить некорректные результаты."
            )
            sys.exit(1)

    total_time = time.time() - pipeline_started

    print_and_log()
    print_and_log("=" * 80)
    print_and_log("✅ FOOTBALL AI PIPELINE УСПЕШНО ЗАВЕРШЁН")
    print_and_log("=" * 80)
    print_and_log(f"Общее время: {total_time:.1f} сек.")
    print_and_log(f"Лог сохранён: {log_file}")


if __name__ == "__main__":
    main()
