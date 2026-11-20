from time import perf_counter

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, Response
from loguru import logger
from ..constants import COLOR_IDS_PATH, GZIP_MAPS_DIR, MAPS_DIR


map_router = APIRouter(prefix='/map')

# world609m is the background for years up to and including -609;
# world is used from -608 onwards.
WORLD_609M_LAST_YEAR = -609


def _cache_headers(version: str | None) -> dict[str, str]:
    if version:
        # URL версионирован, поэтому содержимое можно кэшировать надолго.
        return {'Cache-Control': 'public, max-age=31536000, immutable'}
    # Запрос без версии — короткий кэш, чтобы правки подхватывались.
    return {'Cache-Control': 'public, max-age=300'}


def _accepts_gzip(request: Request) -> bool:
    header = request.headers.get('accept-encoding', '')

    for part in header.split(','):
        token, *params = [item.strip() for item in part.split(';')]
        if token.lower() != 'gzip':
            continue

        for param in params:
            key, _, value = param.partition('=')
            if key.strip().lower() != 'q':
                continue

            try:
                quality = float(value)
            except ValueError:
                quality = 0

            if quality <= 0:
                return False

        return True

    return False


def _topojson_response(
    filename: str,
    request: Request,
    version: str | None,
) -> FileResponse:
    headers = _cache_headers(version)
    source_path = (MAPS_DIR / filename).resolve()

    if _accepts_gzip(request):
        gzip_path = (GZIP_MAPS_DIR / f'{filename}.gz').resolve()

        # Prefer the pre-compressed file only when it is not stale.
        if gzip_path.is_file() and (
            not source_path.is_file()
            or gzip_path.stat().st_mtime_ns >= source_path.stat().st_mtime_ns
        ):
            return FileResponse(
                path=gzip_path,
                media_type='application/json',
                headers={
                    **headers,
                    'Content-Encoding': 'gzip',
                    'Vary': 'Accept-Encoding',
                },
            )

    if not source_path.is_file():
        logger.debug('Map file not found: {}', filename)
        raise HTTPException(status_code=404, detail='File not found')

    return FileResponse(
        path=source_path,
        media_type='application/json',
        headers=headers,
    )


_map_version_cache: str | None = None


def _compute_maps_version() -> str:
    started_at = perf_counter()
    paths = list(MAPS_DIR.glob('*.topojson'))
    if GZIP_MAPS_DIR.is_dir():
        paths.extend(GZIP_MAPS_DIR.glob('*.topojson.gz'))
    paths.append(COLOR_IDS_PATH)

    latest = 0
    total_size = 0
    found = 0
    for path in paths:
        try:
            stat = path.stat()
        except OSError:
            continue
        latest = max(latest, stat.st_mtime_ns)
        total_size += stat.st_size
        found += 1

    version = f'{latest}-{found}-{total_size}'
    logger.info(
        'Map version computed: {} files, {:.0f} ms, version={}',
        found,
        (perf_counter() - started_at) * 1000,
        version,
    )
    return version


def warm_map_version() -> str:
    """Compute the map version once per worker before serving requests."""
    global _map_version_cache

    if _map_version_cache is None:
        _map_version_cache = _compute_maps_version()

    return _map_version_cache


@map_router.get('/version')
def get_maps_version():
    version = _map_version_cache
    if version is None:
        version = warm_map_version()

    return Response(
        content=version,
        media_type='text/plain',
        headers={'Cache-Control': 'no-store'},
    )


@map_router.get('/geometry/{year}')
def get_map_geometry(year: int, request: Request, v: str | None = None):
    filename = f"_{abs(year)}.topojson" if year < 0 else f"{year}.topojson"
    return _topojson_response(filename, request, v)


@map_router.get('/world/{year}')
def get_world_geometry(year: int, request: Request, v: str | None = None):
    filename = (
        'world609m.topojson'
        if year <= WORLD_609M_LAST_YEAR
        else 'world.topojson'
    )
    return _topojson_response(filename, request, v)


@map_router.get('/colors')
def get_color_ids(v: str | None = None):
    file_path = COLOR_IDS_PATH.resolve()
    if not file_path.exists():
        logger.debug('Color ids file not found: {}', file_path)
        raise HTTPException(status_code=404, detail='File not found')
    return FileResponse(
        path=file_path,
        media_type="application/json",
        headers=_cache_headers(v),
    )
