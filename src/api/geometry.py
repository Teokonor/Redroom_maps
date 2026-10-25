from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from ..constants import PROJECT_DIR


map_router = APIRouter(prefix='/map')

# world609m is the background for years up to and including -609;
# world is used from -608 onwards.
WORLD_609M_LAST_YEAR = -609


@map_router.get('/geometry/{year}')
def get_map_geometry(year: int):
    filename = f"_{abs(year)}.topojson" if year < 0 else f"{year}.topojson"
    file_path = (PROJECT_DIR / 'maps' / filename).resolve()
    if not file_path.exists():
        return { "error": "File not found" }
    return FileResponse(path=file_path, media_type="application/json")


@map_router.get('/world/{year}')
def get_world_geometry(year: int):
    filename = (
        'world609m.topojson'
        if year <= WORLD_609M_LAST_YEAR
        else 'world.topojson'
    )
    file_path = (PROJECT_DIR / 'maps' / filename).resolve()
    if not file_path.exists():
        raise HTTPException(status_code=404, detail='File not found')
    return FileResponse(path=file_path, media_type="application/json")


@map_router.get('/colors')
def get_color_ids():
    file_path = (PROJECT_DIR / 'maps' / 'color_ids.json').resolve()
    if not file_path.exists():
        return { "error": "File not found" }
    return FileResponse(path=file_path, media_type="application/json")
