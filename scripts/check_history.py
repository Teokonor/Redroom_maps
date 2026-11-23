"""Sanity-check history groups and video classification.

Usage:
    python scripts/check_history.py
    python scripts/check_history.py russia ukraine belarus
"""

import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / 'backend'))

from app.database.videos import (  # noqa: E402
    VideoService,
    _history_scope,
)


DEFAULT_COUNTRIES = [
    'russia',
    'ukraine',
    'belarus',
    'france',
    'germany',
    'poland',
    'italy',
    'rome',
    'greece',
    'turkey',
    'ottoman',
    'serbia',
    'kosovo',
    'japan',
    'china',
    'india',
    'usa',
    'brazil',
    'egypt',
    'south_africa',
]

# Video 3360 is about Kosovo. Its only East Slavic connection is an indirect
# mention of Ottoman Crimea. It must stay indirect there, be absent from
# unrelated histories, and be main for the Ottoman/Yugoslav region.
EXPECTED_3360 = {
    'russia': 'indirect',
    'ukraine': 'indirect',
    'belarus': 'indirect',
    'greece': 'indirect',
    'france': 'absent',
    'germany': 'absent',
    'poland': 'absent',
    'italy': 'absent',
    'rome': 'absent',
    'japan': 'absent',
    'china': 'absent',
    'serbia': 'main',
    'kosovo': 'main',
    'turkey': 'main',
    'ottoman': 'main',
}


def classify(data: dict, video_num: int) -> str:
    if any(video.num == video_num for video in data['main']):
        return 'main'
    if any(video.num == video_num for video in data['indirectly']):
        return 'indirect'
    return 'absent'


def check_country(country_id: str) -> list[str]:
    errors: list[str] = []
    cache_key, scope = _history_scope(country_id)
    data = VideoService.get_for_history(country_id)
    main = {video.num for video in data['main']}
    indirectly = {video.num for video in data['indirectly']}

    overlap = main & indirectly
    if overlap:
        errors.append(f'{country_id}: videos in both lists: {sorted(overlap)}')

    known = main | indirectly
    period_videos = {
        video_num
        for period in data['periods']
        for video_num in period['video_nums']
    }
    missing = period_videos - known
    if missing:
        errors.append(
            f'{country_id}: timeline videos missing from lists: '
            f'{sorted(missing)}'
        )

    if not scope:
        errors.append(f'{country_id}: empty history scope')

    print(
        f'{country_id:10s} scope={cache_key:24s} '
        f'main={len(main):3d} indirect={len(indirectly):3d} '
        f'periods={len(data["periods"]):4d} '
        f'video3360={classify(data, 3360)}'
    )
    return errors


def main() -> int:
    countries = sys.argv[1:] or DEFAULT_COUNTRIES
    errors: list[str] = []

    for country_id in countries:
        errors.extend(check_country(country_id))

    for country_id, expected in EXPECTED_3360.items():
        data = VideoService.get_for_history(country_id)
        actual = classify(data, 3360)

        if actual != expected:
            errors.append(
                f'{country_id}: video 3360 expected {expected}, '
                f'got {actual}'
            )

    if errors:
        print('\nFAILED:')
        for error in errors:
            print(f'  - {error}')
        return 1

    print('\nAll history checks passed')
    return 0


if __name__ == '__main__':
    sys.exit(main())
