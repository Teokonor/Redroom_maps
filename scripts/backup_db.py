"""Create a consistent SQLite backup without stopping the backend.

Usage:
    python scripts/backup_db.py
    python scripts/backup_db.py --destination D:\\backups\\redroom.db
"""

import argparse
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / 'backend'))

from app.constants import DATABASE_PATH  # noqa: E402


def backup(destination: Path) -> None:
    if not DATABASE_PATH.is_file():
        raise SystemExit(f'Database not found: {DATABASE_PATH}')

    destination.parent.mkdir(parents=True, exist_ok=True)
    source = sqlite3.connect(f'file:{DATABASE_PATH}?mode=ro', uri=True)
    target = sqlite3.connect(destination)

    try:
        source.backup(target)
    finally:
        target.close()
        source.close()


def main() -> None:
    default_name = f'redroom_maps-{datetime.now():%Y%m%d-%H%M%S}.db'
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--destination',
        type=Path,
        default=PROJECT_DIR / 'data' / 'backups' / default_name,
        help='backup file path',
    )
    args = parser.parse_args()

    backup(args.destination)
    print(f'Backup written: {args.destination}')


if __name__ == '__main__':
    main()
