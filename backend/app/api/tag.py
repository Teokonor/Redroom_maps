from fastapi import APIRouter, Request, Response

from ..database import TagService
from ..models.tag import Tag
from .caching import cached_json


tag_router = APIRouter(prefix='/tag', tags=['Tag'])


@tag_router.get('/all', response_model=list[Tag])
def get_all_tags(
    request: Request,
    response: Response,
    v: str | None = None,
):
    cached = cached_json(
        request,
        response,
        key='tag/all',
        version=v,
    )
    if cached is not None:
        return cached

    return TagService.get_all()
