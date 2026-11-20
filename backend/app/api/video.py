from fastapi import APIRouter, HTTPException, Query, Request, Response

from ..database import CountryService, TagService, VideoService
from ..models.period import Period
from ..models.video import HistoryVideoSelection, Video, VideoSelection
from .caching import cached_json


video_router = APIRouter(prefix='/video', tags=['Video'])


def _ensure_country_exists(country_id: str) -> None:
    if not CountryService.exists(country_id):
        raise HTTPException(status_code=404, detail='Country not found')


@video_router.get('', response_model=list[Video])
def get_videos(
    request: Request,
    response: Response,
    tag: str | None = Query(None, description='Идентификатор тега'),
    v: str | None = None,
):
    key = f'video/tag/{tag}' if tag else 'video/all'
    cached = cached_json(request, response, key=key, version=v)
    if cached is not None:
        return cached

    if tag:
        if not TagService.exists(tag):
            raise HTTPException(status_code=404, detail='Tag not found')
        return VideoService.get_for_tag(tag)

    return VideoService.get_all()


@video_router.get('/{video_num}/periods', response_model=list[Period])
def get_video_periods(
    video_num: int,
    request: Request,
    response: Response,
    v: str | None = None,
):
    cached = cached_json(
        request,
        response,
        key=f'video/{video_num}/periods',
        version=v,
    )
    if cached is not None:
        return cached

    return VideoService.get_periods(video_num)


@video_router.get('/{country_id}/all', response_model=HistoryVideoSelection)
def get_all_country_videos(
    country_id: str,
    request: Request,
    response: Response,
    v: str | None = None,
):
    cached = cached_json(
        request,
        response,
        key=f'video/{country_id}/all',
        version=v,
    )
    if cached is not None:
        return cached

    _ensure_country_exists(country_id)
    return VideoService.get_for_history(country_id)


@video_router.get('/{country_id}', response_model=VideoSelection)
def get_country_videos(
    country_id: str,
    request: Request,
    response: Response,
    begin: int = Query(..., description='Начало периода включительно'),
    end: int = Query(..., description='Конец периода включительно'),
    v: str | None = None,
):
    cached = cached_json(
        request,
        response,
        key=f'video/{country_id}?begin={begin}&end={end}',
        version=v,
    )
    if cached is not None:
        return cached

    if begin > end:
        raise HTTPException(
            status_code=400,
            detail='begin must be less than or equal to end',
        )

    _ensure_country_exists(country_id)
    return VideoService.get_for_period(country_id, begin, end)
