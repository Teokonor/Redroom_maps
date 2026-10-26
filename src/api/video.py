from typing import List

from fastapi import APIRouter, HTTPException, Query

from ..database import CountryService, TagService, VideoService
from ..models.video import Video, VideoSelection


video_router = APIRouter(prefix='/video', tags=['Video'])


def _ensure_country_exists(country_id: str) -> None:
    if not CountryService.exists(country_id):
        raise HTTPException(status_code=404, detail='Country not found')


@video_router.get('', response_model=List[Video])
def get_videos(tag: str | None = Query(None, description='Идентификатор тега')):
    if tag:
        if not TagService.exists(tag):
            raise HTTPException(status_code=404, detail='Tag not found')
        return VideoService.get_for_tag(tag)

    return VideoService.get_all()


@video_router.get('/{country_id}/all', response_model=VideoSelection)
def get_all_country_videos(country_id: str):
    _ensure_country_exists(country_id)
    return VideoService.get_for_history(country_id)


@video_router.get('/{country_id}', response_model=VideoSelection)
def get_country_videos(
    country_id: str,
    begin: int = Query(..., description='Начало периода включительно'),
    end: int = Query(..., description='Конец периода включительно'),
):
    if begin > end:
        raise HTTPException(
            status_code=400,
            detail='begin must be less than or equal to end',
        )

    _ensure_country_exists(country_id)
    return VideoService.get_for_period(country_id, begin, end)
