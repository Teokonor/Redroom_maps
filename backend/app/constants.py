import os
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = Path(
    os.environ.get('REDROOM_DATA_DIR', PROJECT_DIR / 'data')
).resolve()
WORK_DIR = DATA_DIR / 'work'

DEFAULT_RUNTIME_DIR = DATA_DIR / 'runtime'

# Production can point this to data/current or a release directory.
RUNTIME_DIR = Path(
    os.environ.get('REDROOM_RUNTIME_DIR', DEFAULT_RUNTIME_DIR)
).resolve()

DATABASE_PATH = RUNTIME_DIR / 'db' / 'redroom_maps.db'
MAPS_DIR = RUNTIME_DIR / 'maps' / 'topojson'
GZIP_MAPS_DIR = RUNTIME_DIR / 'maps' / 'gzip'
COLOR_IDS_PATH = RUNTIME_DIR / 'maps' / 'color_ids.json'
PREVIEWS_DIR = RUNTIME_DIR / 'previews'

# Curated country -> history-group map. It is part of the application (not
# runtime data) so the server does not need data/work.
HISTORY_GROUPS_PATH = (
    Path(__file__).resolve().parent / 'data' / 'history_groups.json'
)
