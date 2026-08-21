from pathlib import Path
import time
import requests


RECORD = "17835138"
TARGET = "player_day_panel.csv"

OUT_DIR = Path("data/external")
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT = OUT_DIR / TARGET

META_URL = (
    f"https://zenodo.org/api/records/{RECORD}"
)

session = requests.Session()


def get_metadata(attempts=5):
    last_error = None

    for attempt in range(1, attempts + 1):
        try:
            print(
                f"Metadata attempt "
                f"{attempt}/{attempts}..."
            )

            r = session.get(
                META_URL,
                timeout=(20, 120),
            )

            r.raise_for_status()
            return r.json()

        except requests.RequestException as exc:
            last_error = exc
            print(
                f"⚠️ {type(exc).__name__}: {exc}"
            )

            if attempt < attempts:
                time.sleep(5)

    raise last_error


print("=" * 100)
print("PLAYER DAY PANEL — RESUMABLE DOWNLOAD")
print("=" * 100)

record = get_metadata()

file_info = next(
    (
        f
        for f in record["files"]
        if f["key"] == TARGET
    ),
    None,
)

if file_info is None:
    raise SystemExit(
        f"❌ {TARGET} не найден."
    )

url = file_info["links"]["self"]
expected = int(file_info["size"])

print()
print("Файл:", TARGET)
print(
    "Размер:",
    f"{expected / 1024 / 1024:.2f} MB",
)


# ============================================================
# RESUMABLE DOWNLOAD
# ============================================================

max_attempts = 20

for attempt in range(1, max_attempts + 1):

    existing = (
        OUTPUT.stat().st_size
        if OUTPUT.exists()
        else 0
    )

    if existing == expected:
        print()
        print("✅ Файл уже полностью скачан.")
        break

    if existing > expected:
        print(
            "⚠️ Локальный файл больше ожидаемого. "
            "Удаляю и начинаю заново."
        )
        OUTPUT.unlink()
        existing = 0

    headers = {}

    mode = "wb"

    if existing > 0:
        headers["Range"] = (
            f"bytes={existing}-"
        )
        mode = "ab"

    print()
    print(
        f"Попытка {attempt}/{max_attempts}"
    )
    print(
        f"Уже скачано: "
        f"{existing / 1024 / 1024:.2f} MB"
    )

    try:
        with session.get(
            url,
            headers=headers,
            stream=True,
            timeout=(30, 300),
        ) as r:

            # Если сервер проигнорировал Range,
            # нельзя append-ить полный файл.
            if (
                existing > 0
                and r.status_code == 200
            ):
                print(
                    "⚠️ Сервер не поддержал resume. "
                    "Начинаю файл заново."
                )

                existing = 0
                mode = "wb"

            elif (
                existing > 0
                and r.status_code != 206
            ):
                r.raise_for_status()

            else:
                r.raise_for_status()

            with OUTPUT.open(mode) as f:

                downloaded = existing
                last_print = time.time()

                for chunk in r.iter_content(
                    chunk_size=1024 * 1024
                ):
                    if not chunk:
                        continue

                    f.write(chunk)
                    downloaded += len(chunk)

                    if (
                        time.time() - last_print
                        >= 5
                    ):
                        pct = (
                            downloaded
                            / expected
                            * 100
                        )

                        print(
                            f"\r"
                            f"{downloaded / 1024 / 1024:8.1f}"
                            f" / "
                            f"{expected / 1024 / 1024:8.1f}"
                            f" MB "
                            f"({pct:5.1f}%)",
                            end="",
                            flush=True,
                        )

                        last_print = time.time()

        print()

    except requests.RequestException as exc:

        print()
        print(
            f"⚠️ Download error: "
            f"{type(exc).__name__}: {exc}"
        )

        if attempt < max_attempts:
            print(
                "Повтор через 5 секунд..."
            )
            time.sleep(5)

        continue


# ============================================================
# VERIFY
# ============================================================

if not OUTPUT.exists():
    raise SystemExit(
        "❌ Файл не создан."
    )

actual = OUTPUT.stat().st_size

print()
print("=" * 100)
print("DOWNLOAD RESULT")
print("=" * 100)

print(
    "Ожидаемый размер:",
    expected,
)

print(
    "Фактический размер:",
    actual,
)

print(
    "Размер MB:",
    f"{actual / 1024 / 1024:.2f}",
)

if actual != expected:
    raise SystemExit(
        "❌ Размер не совпадает. "
        "Повтори запуск — скрипт попробует продолжить."
    )

print()
print("✅ player_day_panel.csv скачан полностью.")
print("Production-файлы НЕ изменены.")
