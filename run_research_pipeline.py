from pathlib import Path
from datetime import datetime
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parent

LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

LOG_FILE = (
    LOG_DIR
    / f"research_pipeline_{timestamp}.log"
)


# ============================================================
# FOOTBALL AI — RESEARCH PIPELINE
#
# Здесь только исследовательские проверки.
# Production pipeline НЕ меняется.
# ============================================================

RESEARCH_STEPS = [
    (
        "Production baseline check",
        "compare_pipeline_metrics.py",
    ),

    (
        "Saved experiments",
        "run_experiment.py",
    ),

    (
        "Feature groups signal",
        "feature_group_signal_test.py",
    ),

    (
        "XG LAST5/LAST10 comparison",
        "compare_xg_windows.py",
    ),

    (
        "Opponent-adjusted XG comparison",
        "compare_adjusted_xg.py",
    ),

    (
        "Nested XG blend",
        "nested_xg_blend_test.py",
    ),

    (
        "Nested adjusted XG blend",
        "nested_adjusted_xg_blend_test.py",
    ),

    (
        "Challenger vs bookmaker",
        "compare_challenger_vs_bookmaker.py",
    ),

    (
        "Model/market disagreement",
        "analyze_model_market_disagreement.py",
    ),

    (
        "Rest/congestion signal",
        "rest_congestion_signal_test.py",
    ),

    (
        "Weighted injury signal",
        "weighted_injury_signal_test.py",
    ),

    (
        "Market movement predictability",
        "market_movement_predictability_test.py",
    ),

    (
        "Nested closing edge segments",
        "nested_closing_edge_segments.py",
    ),

    (
        "Value bet backtest",
        "value_bet_backtest.py",
    ),

    (
        "Market calibrated meta model",
        "market_calibrated_meta_model.py",
    ),

    (
        "Research promotion gate",
        "research_gate.py",
    ),
]


def log(text=""):
    print(text)

    with open(
        LOG_FILE,
        "a",
        encoding="utf-8",
    ) as f:
        f.write(
            text + "\n"
        )


def run_step(
    number,
    name,
    script,
):
    path = ROOT / script

    log()
    log("=" * 100)
    log(
        f"[{number}/{len(RESEARCH_STEPS)}] "
        f"{name}"
    )
    log(
        f"Файл: {script}"
    )
    log("=" * 100)

    if not path.exists():

        log(
            f"⚠️ SKIP: файл не найден: "
            f"{script}"
        )

        return {
            "status": "SKIPPED",
            "seconds": 0.0,
        }

    started = time.time()

    process = subprocess.Popen(
        [
            sys.executable,
            str(path),
        ],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    for line in process.stdout:

        log(
            line.rstrip()
        )

    return_code = process.wait()

    elapsed = (
        time.time()
        - started
    )

    if return_code != 0:

        log()
        log(
            f"❌ FAILED "
            f"(code={return_code}, "
            f"{elapsed:.1f}s)"
        )

        return {
            "status": "FAILED",
            "seconds": elapsed,
        }

    log()
    log(
        f"✅ PASSED "
        f"({elapsed:.1f}s)"
    )

    return {
        "status": "PASSED",
        "seconds": elapsed,
    }


def dry_run():

    print()
    print("=" * 100)
    print(
        "FOOTBALL AI — "
        "RESEARCH PIPELINE CHECK"
    )
    print("=" * 100)

    found = 0
    missing = 0

    for number, (
        name,
        script,
    ) in enumerate(
        RESEARCH_STEPS,
        start=1,
    ):

        exists = (
            ROOT / script
        ).exists()

        icon = (
            "✅"
            if exists
            else "⚠️"
        )

        print(
            f"{icon} "
            f"[{number}] "
            f"{name}: "
            f"{script}"
        )

        if exists:
            found += 1
        else:
            missing += 1

    print()
    print(
        "Найдено:",
        found,
    )

    print(
        "Отсутствует:",
        missing,
    )

    print()

    if missing == 0:
        print(
            "✅ Все research-скрипты найдены."
        )
    else:
        print(
            "⚠️ Отсутствующие скрипты "
            "будут автоматически пропущены."
        )


def main():

    if "--dry-run" in sys.argv:
        dry_run()
        return

    log("=" * 100)
    log(
        "🧪 FOOTBALL AI — "
        "AUTOMATIC RESEARCH PIPELINE"
    )
    log("=" * 100)

    log(
        f"Начало: "
        f"{datetime.now():%Y-%m-%d %H:%M:%S}"
    )

    log(
        f"Лог: {LOG_FILE}"
    )

    started = time.time()

    results = []


    for number, (
        name,
        script,
    ) in enumerate(
        RESEARCH_STEPS,
        start=1,
    ):

        result = run_step(
            number,
            name,
            script,
        )

        results.append({
            "name": name,
            "script": script,
            **result,
        })


    total = (
        time.time()
        - started
    )


    passed = sum(
        r["status"] == "PASSED"
        for r in results
    )

    failed = sum(
        r["status"] == "FAILED"
        for r in results
    )

    skipped = sum(
        r["status"] == "SKIPPED"
        for r in results
    )


    log()
    log("=" * 100)
    log(
        "RESEARCH PIPELINE — SUMMARY"
    )
    log("=" * 100)


    for result in results:

        if (
            result["status"]
            == "PASSED"
        ):
            icon = "✅"

        elif (
            result["status"]
            == "FAILED"
        ):
            icon = "❌"

        else:
            icon = "⚠️"


        log(
            f"{icon} "
            f"{result['status']:<8} "
            f"{result['name']}"
        )


    log()
    log(
        f"PASSED:  {passed}"
    )

    log(
        f"FAILED:  {failed}"
    )

    log(
        f"SKIPPED: {skipped}"
    )

    log(
        f"TIME:    {total:.1f}s"
    )


    log()
    log("=" * 100)
    log("AUTOMATIC VERDICT")
    log("=" * 100)


    if failed > 0:

        log(
            "❌ RESEARCH PIPELINE HAS ERRORS"
        )

        log(
            "Не использовать новые "
            "экспериментальные результаты "
            "до исправления FAILED этапов."
        )

    else:

        log(
            "✅ RESEARCH PIPELINE HEALTHY"
        )

        log(
            "Все доступные исследования "
            "успешно воспроизводятся."
        )

        log()
        log(
            "Текущий установленный вывод:"
        )

        log(
            "• bookmaker остаётся "
            "основным probability baseline;"
        )

        log(
            "• текущие модели и xG-ветки "
            "пока не подтвердили "
            "устойчивый nested edge;"
        )

        log(
            "• новые feature families "
            "следует проверять через "
            "тот же OOS/nested процесс."
        )


    log()
    log(
        "Production pipeline НЕ изменён."
    )

    log(
        f"Лог сохранён: {LOG_FILE}"
    )


if __name__ == "__main__":
    main()
