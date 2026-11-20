from fastapi import APIRouter, Request, Response

from ..models.country import Country
from ..database import CountryService
from .caching import cached_json


country_router = APIRouter(prefix='/country', tags=['Country'])


@country_router.get('/all', response_model=list[Country])
def get_all_countries(
    request: Request,
    response: Response,
    v: str | None = None,
):
    cached = cached_json(
        request,
        response,
        key='country/all',
        version=v,
    )
    if cached is not None:
        return cached

    return CountryService.get_all()
