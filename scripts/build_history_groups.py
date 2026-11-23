"""Build the history-group data used by the API.

Source: data/work/periods/histories/index.csv and the per-group CSV files.
The result is committed as backend/app/data/history_groups.json because the
site needs it at runtime and data/work is not shipped to the server.

The file contains two maps:
- country_groups: country_id -> its primary history group;
- groups: group -> every entity that belongs to that history.

Usage:
    python scripts/build_history_groups.py
"""

import csv
import json
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
HISTORIES_DIR = PROJECT_DIR / 'data' / 'work' / 'periods' / 'histories'
INDEX_PATH = HISTORIES_DIR / 'index.csv'
OUTPUT_PATH = PROJECT_DIR / 'backend' / 'app' / 'data' / 'history_groups.json'

# These aggregate groups overlap almost every specific group. They are only
# map-work fallbacks and must not define the site's history scope: using them
# would put half the world into every country's history.
AGGREGATE_GROUPS = {'africa', 'america', 'europe'}


def split_ids(value: str | None) -> list[str]:
    return [item.strip() for item in (value or '').split(',') if item.strip()]


def read_group_ids(filename: str) -> list[str]:
    path = HISTORIES_DIR / filename
    if not path.is_file():
        return []

    with path.open('r', encoding='utf-8-sig', newline='') as file:
        return [
            row['id']
            for row in csv.DictReader(file, delimiter=';')
            if row.get('id')
        ]


def build_data() -> dict:
    with INDEX_PATH.open('r', encoding='utf-8-sig', newline='') as file:
        all_groups = list(csv.DictReader(file, delimiter=';'))

    specific = [
        group
        for group in all_groups
        if group['id'].strip() not in AGGREGATE_GROUPS
    ]
    skipped = [
        group['id'].strip()
        for group in all_groups
        if group['id'].strip() in AGGREGATE_GROUPS
    ]

    group_entities: dict[str, list[str]] = {}
    declared: dict[str, str] = {}

    for group in specific:
        group_id = group['id'].strip()
        entities = [
            *read_group_ids(group['file'].strip()),
            *split_ids(group.get('members')),
            *split_ids(group.get('extras')),
        ]
        group_entities[group_id] = sorted(dict.fromkeys(entities))

        # A modern country always belongs to the group that declares it.
        for country_id in (
            split_ids(group.get('members')) + split_ids(group.get('extras'))
        ):
            declared.setdefault(country_id, group_id)

    # For historical entities choose the first specific group that lists them.
    # A union (Rome -> Italy + Greece + Turkey) would pull later Ottoman
    # history into ancient Rome.
    primary: dict[str, str] = dict(declared)
    for group in specific:
        group_id = group['id'].strip()
        for country_id in group_entities[group_id]:
            primary.setdefault(country_id, group_id)

    for group_id in skipped:
        print(f'Skipped aggregate group: {group_id}')

    mismatched = [
        (country_id, group_id, primary.get(country_id))
        for country_id, group_id in declared.items()
        if primary.get(country_id) != group_id
    ]
    if mismatched:
        print(f'Warning: {len(mismatched)} declared countries reassigned')

    return {
        'country_groups': dict(sorted(primary.items())),
        'groups': dict(sorted(group_entities.items())),
    }


def main() -> None:
    data = build_data()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            sort_keys=True,
            separators=(',', ':'),
        ),
        encoding='utf-8',
    )

    print(
        f'Wrote {OUTPUT_PATH}: '
        f'{len(data["country_groups"])} countries, '
        f'{len(data["groups"])} groups, '
        f'{OUTPUT_PATH.stat().st_size} bytes'
    )


if __name__ == '__main__':
    main()
