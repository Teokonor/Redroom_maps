import argparse
import shutil
import sqlite3
import tempfile
from pathlib import Path

from import_videos import get_quality


DB_PATH = Path(__file__).parent / "redroom_maps.db"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Пересчитать цвета качества видео по номеру"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="только показать изменения, не менять базу",
    )
    args = parser.parse_args()

    connection = sqlite3.connect(DB_PATH)
    rows = connection.execute(
        "select num, quality from videos order by num"
    ).fetchall()

    changes = [
        (num, old, get_quality(num))
        for num, old in rows
        if old != get_quality(num)
    ]
    unchanged = len(rows) - len(changes)

    print(f"Всего видео: {len(rows)}")
    print(f"Цвет изменится: {len(changes)}")
    print(f"Останется без изменений: {unchanged}")

    samples = {10, 330, 660, 990, 1300, 1310, 3680}
    print("\nПримеры:")
    for num, old, new in changes + [
        (num, old, old) for num, old in rows if old == get_quality(num)
    ]:
        if num in samples:
            print(f"  {num}: {old} -> {new}")

    if args.dry_run:
        print("\nDRY RUN: база не изменена.")
        connection.close()
        return

    backup_dir = Path(tempfile.gettempdir()) / "opencode"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / "redroom_maps_before_quality.db"
    shutil.copy2(DB_PATH, backup_path)

    connection.executemany(
        "update videos set quality = ? where num = ?",
        [(new, num) for num, _, new in changes],
    )
    connection.commit()

    still_wrong = sum(
        1
        for num, quality in connection.execute("select num, quality from videos")
        if quality != get_quality(num)
    )
    connection.close()

    print(f"\nРезервная копия: {backup_path}")
    print("База обновлена.")
    print(f"Осталось несоответствий: {still_wrong}")


if __name__ == "__main__":
    main()
