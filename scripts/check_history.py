"""Sanity-check per-country history scopes and video classification.

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
    'russia1783',
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
    'australia',
    'new_zealand',
]

# Video 3360 is about Kosovo. Its only East Slavic connection is an indirect
# mention of Ottoman Crimea. It must stay indirect there, be absent from
# unrelated histories, and be main for the Ottoman/Yugoslav region.
EXPECTED_3360 = {
    'russia': 'indirect',
    'russia1783': 'indirect',
    'ukraine': 'indirect',
    'belarus': 'indirect',
    'greece': 'indirect',
    'france': 'absent',
    'germany': 'absent',
    'poland': 'absent',
    'italy': 'absent',
    'rome': 'indirect',
    'japan': 'absent',
    'china': 'absent',
    'australia': 'absent',
    'new_zealand': 'absent',
    'serbia': 'main',
    'kosovo': 'main',
    'turkey': 'main',
    'ottoman': 'main',
}

# Modern countries must not pull each other into their ancestor graphs.
# Shared historical ancestors are fine; shared modern countries are not.
MODERN_ISOLATION = {
    'russia': ['ukraine', 'belarus', 'kosovo', 'serbia'],
    'ukraine': ['russia', 'belarus', 'kosovo'],
    'belarus': ['russia', 'ukraine', 'kosovo'],
    'australia': ['new_zealand'],
    'new_zealand': ['australia'],
}


def classify(data: dict, video_num: int) -> str:
    if any(video.num == video_num for video in data['main']):
        return 'main'
    if any(video.num == video_num for video in data['indirectly']):
        return 'indirect'
    return 'absent'


def check_country(country_id: str) -> list[str]:
    errors: list[str] = []
    data = VideoService.get_for_history(country_id)
    scope = _history_scope(country_id)
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
        f'{country_id:10s} countries={len(scope):4d} '
        f'main={len(main):3d} indirect={len(indirectly):3d} '
        f'periods={len(data["periods"]):4d} '
        f'video3360={classify(data, 3360)}'
    )
    return errors


def check_family_links() -> list[str]:
    errors: list[str] = []
    russia = set(_history_scope('russia'))
    empire = set(_history_scope('russia1783'))

    for sibling in ('ukraine', 'belarus'):
        if sibling in russia:
            errors.append(
                f'russia: modern {sibling} must not be in the backward graph'
            )

    for successor in ('russia', 'ukraine', 'belarus'):
        if successor not in empire:
            errors.append(
                f'russia1783: future {successor} is missing from the graph'
            )

    if 'tuva_ssr' not in russia:
        errors.append('russia: tuva_ssr is missing from the backward graph')
    if 'tuva_ssr' in empire:
        errors.append(
            'russia1783: tuva_ssr must not be in the future of the empire'
        )
    if 'mongolia' in empire:
        errors.append(
            'russia1783: modern mongolia must not be in the empire graph'
        )

    return errors


def main() -> int:
    countries = sys.argv[1:] or DEFAULT_COUNTRIES
    errors: list[str] = []

    for country_id in countries:
        errors.extend(check_country(country_id))

    errors.extend(check_family_links())

    for country_id, expected in EXPECTED_3360.items():
        data = VideoService.get_for_history(country_id)
        actual = classify(data, 3360)

        if actual != expected:
            errors.append(
                f'{country_id}: video 3360 expected {expected}, '
                f'got {actual}'
            )

    for country_id, others in MODERN_ISOLATION.items():
        scope = set(_history_scope(country_id))
        for other_id in others:
            if other_id in scope:
                errors.append(
                    f'{country_id}: history includes modern {other_id}'
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
