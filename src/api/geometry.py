from fastapi import APIRouter
from fastapi.responses import FileResponse
from ..constants import PROJECT_DIR


map_router = APIRouter(prefix='/map')

@map_router.get('/geometry/{year}')
def get_map_geometry(year: int):
    filename = f"_{abs(year)}.topojson" if year < 0 else f"{year}.topojson"
    file_path = (PROJECT_DIR / 'maps' / filename).resolve()
    if not file_path.exists():
        return { "error": "File not found" }
    return FileResponse(path=file_path, media_type="application/json")


@map_router.get('/colors')
def get_color_ids():
    file_path = (PROJECT_DIR / 'maps' / 'color_ids.json').resolve()
    if not file_path.exists():
        return { "error": "File not found" }
    return FileResponse(path=file_path, media_type="application/json")
