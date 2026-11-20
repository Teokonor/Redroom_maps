"""Pre-compress all TopoJSON map files into maps/gzip.

Run from the project root:

    python maps/compress_maps.py

The server serves these files directly with Content-Encoding: gzip.
"""

from __future__ import annotations

import argparse
import gzip
import os
import time
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent
MAPS_DIR = PROJECT_DIR / 'data' / 'runtime' / 'maps' / 'topojson'
GZIP_DIR = PROJECT_DIR / 'data' / 'runtime' / 'maps' / 'gzip'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Compress TopoJSON files into maps/gzip.'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Recompress files even if the gzip version is up to date.',
    )
    parser.add_argument(
        '--level',
        type=int,
        default=9,
        choices=range(1, 10),
        metavar='1-9',
        help='Gzip compression level (default: 9).',
    )
    return parser.parse_args()


def compress_file(source: Path, target: Path, level: int, force: bool) -> bool:
    if not force and target.is_file():
        if target.stat().st_mtime_ns >= source.stat().st_mtime_ns:
            return False

    data = source.read_bytes()
    compressed = gzip.compress(data, compresslevel=level, mtime=0)

    tmp_path = target.with_name(f'{target.name}.tmp')
    tmp_path.write_bytes(compressed)
    os.replace(tmp_path, target)
    return True


def main() -> None:
    args = parse_args()
    GZIP_DIR.mkdir(exist_ok=True)

    sources = sorted(MAPS_DIR.glob('*.topojson'))
    if not sources:
        print('No TopoJSON files found.')
        return

    started_at = time.perf_counter()
    compressed_count = 0
    skipped_count = 0
    source_bytes = 0
    gzip_bytes = 0

    for source in sources:
        target = GZIP_DIR / f'{source.name}.gz'
        source_bytes += source.stat().st_size

        if compress_file(source, target, args.level, args.force):
            compressed_count += 1
            print(f'compressed  {source.name}')
        else:
            skipped_count += 1

        gzip_bytes += target.stat().st_size

    # Remove gzip files whose source TopoJSON no longer exists.
    removed_count = 0
    source_names = {f'{source.name}.gz' for source in sources}
    for target in GZIP_DIR.glob('*.topojson.gz'):
        if target.name in source_names:
            continue
        target.unlink()
        removed_count += 1
        print(f'removed     {target.name}')

    elapsed = time.perf_counter() - started_at
    ratio = source_bytes / gzip_bytes if gzip_bytes else 0

    print()
    print(f'Files:       {len(sources)}')
    print(f'Compressed:  {compressed_count}')
    print(f'Skipped:     {skipped_count}')
    print(f'Removed:     {removed_count}')
    print(f'Source size: {source_bytes / (1024 * 1024):.1f} MB')
    print(f'Gzip size:   {gzip_bytes / (1024 * 1024):.1f} MB')
    print(f'Ratio:       {ratio:.2f}x')
    print(f'Elapsed:     {elapsed:.1f}s')


if __name__ == '__main__':
    main()
