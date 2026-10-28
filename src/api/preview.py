import mimetypes
import re
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from ..constants import PROJECT_DIR


preview_router = APIRouter(prefix='/preview', tags=['Preview'])
PREVIEWS_DIR = (PROJECT_DIR / 'video_previews').resolve()
FILENAME_PATTERN = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.-]*$')


@preview_router.get('/{filename}')
def get_video_preview(filename: str):
    if (
        not FILENAME_PATTERN.fullmatch(filename)
        or Path(filename).name != filename
    ):
        raise HTTPException(status_code=404, detail='Preview not found')

    preview_path = PREVIEWS_DIR / filename
    if not preview_path.is_file():
        raise HTTPException(status_code=404, detail='Preview not found')

    media_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
    return FileResponse(
        preview_path,
        media_type=media_type,
        headers={'Cache-Control': 'public, max-age=31536000, immutable'},
    )
